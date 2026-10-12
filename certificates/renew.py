#!/usr/bin/python3
"""Root-only Certbot DNS-01 runner; validated, recoverable per-lineage deployment."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import time

ROOT = Path('/opt/data/homelab/acme')
REPO = Path('/opt/data/homelab/repo')
SETS = {
    'a3f': ('/opt/data/homelab/nginx/certs', ['*.a3f.link'], [('overseerr.a3f.link', 443)], 0, 0o600),
    'requests': ('/opt/data/homelab/nginx/certs/requests', ['requests.neldridge.net'], [('requests.neldridge.net', 443)], 0, 0o600),
    'grafana': ('/opt/data/homelab/monitoring/tls', ['grafana.a3f.link', 'grafana.neldridge.net'], [('grafana.a3f.link', 3000), ('grafana.neldridge.net', 3000)], 472, 0o640),
}

def run(*args):
    return subprocess.check_output(args, stderr=subprocess.PIPE, timeout=900 if args[0] == 'certbot' else 180).strip()

def validate(folder, names):
    cert, key = str(folder / 'fullchain.pem'), str(folder / 'privkey.pem')
    public = run('openssl', 'x509', '-in', cert, '-pubkey', '-noout')
    assert public == run('openssl', 'pkey', '-in', key, '-pubout'), 'key mismatch'
    run('openssl', 'x509', '-in', cert, '-checkend', str(30*86400), '-noout')
    sans = ssl._ssl._test_decode_cert(cert)['subjectAltName']
    assert set(names) == {v for k, v in sans if k == 'DNS'}, 'unexpected SANs'
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        leaf = Path(tmp) / 'leaf.pem'
        leaf.write_bytes(run('openssl', 'x509', '-in', cert))
        run('openssl', 'verify', '-CApath', '/etc/ssl/certs', '-untrusted', cert, str(leaf))

def compose(name, *args):
    if name == 'grafana':
        return run('docker', 'compose', '--project-directory', str(REPO/'monitoring'), '--env-file', '/opt/data/homelab/monitoring/runtime.env', '-p', 'homelab-monitoring', *args)
    return run('docker', 'compose', '--project-directory', str(REPO/'compose'), '-p', 'homelab', '-f', str(REPO/'compose/compose.yaml'), '-f', str(REPO/'compose/compose.proxy.yaml'), *args)

def activate(name):
    if name == 'grafana':
        # Force recreation also covers any future single-file bind mounts.
        compose(name, 'up', '-d', '--no-deps', '--force-recreate', 'grafana')
    else:
        compose(name, 'exec', '-T', 'nginx', 'nginx', '-t')
        compose(name, 'exec', '-T', 'nginx', 'nginx', '-s', 'reload')

def health(name, folder):
    expected = ssl.PEM_cert_to_DER_cert(run('openssl', 'x509', '-in', str(folder/'fullchain.pem')).decode())
    for host, port in SETS[name][2]:
        with socket.create_connection(('192.168.11.10', port), timeout=5) as sock:
            with ssl.create_default_context().wrap_socket(sock, server_hostname=host) as tls:
                assert tls.getpeercert(binary_form=True) == expected, 'served certificate differs'
        path = '/api/health' if name == 'grafana' else '/api/v1/status'
        body = run('curl', '--fail', '--silent', '--show-error', '--max-time', '8', '--resolve', f'{host}:{port}:192.168.11.10', f'https://{host}:{port}{path}')
        data = json.loads(body)
        assert data.get('database') == 'ok' if name == 'grafana' else bool(data.get('version'))

def wait_health(name, folder):
    # Reload is asynchronous; recovery needs the same readiness window as deployment.
    for attempt in range(20):
        try:
            health(name, folder)
            return
        except Exception:
            if attempt == 19:
                raise
            time.sleep(2)

def replace(source, target, uid, mode):
    fd, tmp = tempfile.mkstemp(prefix='.renew-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(source.read_bytes()); f.flush(); os.fsync(f.fileno())
        os.chown(tmp, uid, 0); os.chmod(tmp, mode); os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def deploy(name, source):
    dest, names, _, uid, mode = SETS[name]; dest = Path(dest)
    validate(source, names)
    compose(name, 'config', '--quiet')
    if name != 'grafana':
        compose(name, 'exec', '-T', 'nginx', 'nginx', '-t')
    backup = ROOT/'backups'/f'{time.time_ns()}-{name}'
    backup.mkdir(parents=True, mode=0o700)
    for f in ('fullchain.pem', 'privkey.pem'): shutil.copy2(dest/f, backup/f)
    try:
        for f in ('privkey.pem', 'fullchain.pem'): replace(source/f, dest/f, uid, mode if f == 'privkey.pem' else (0o640 if uid else 0o644))
        activate(name)
        wait_health(name, dest)
    except Exception:
        for f in ('privkey.pem', 'fullchain.pem'): replace(backup/f, dest/f, uid, mode if f == 'privkey.pem' else (0o640 if uid else 0o644))
        activate(name); wait_health(name, dest)
        raise
    print(f'{name}: deployed; rollback backup {backup}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['staging', 'issue', 'renew', 'dry-run', 'verify', 'rollback'])
    parser.add_argument('--name', choices=SETS)
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    os.umask(0o077); ROOT.mkdir(mode=0o700, exist_ok=True)
    with (ROOT/'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'rollback':
            assert args.name and args.backup and args.backup.resolve().parent == (ROOT/'backups').resolve()
            deploy(args.name, args.backup); return
        if args.action == 'verify':
            for name, (dest, names, *_) in SETS.items(): validate(Path(dest), names); health(name, Path(dest)); print(name+': verified')
            return
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = str(ROOT/'aws-credentials')
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        staging = args.action == 'staging'
        state = ROOT/('staging' if staging else 'production')
        common = ['certbot', '--config-dir', str(state), '--work-dir', str(ROOT/'work'), '--logs-dir', str(ROOT/'logs'), '--non-interactive']
        success = False
        try:
            if args.action == 'dry-run':
                run(*common, 'renew', '--dry-run', '--no-random-sleep-on-renew')
                return
            if args.action == 'renew': run(*common, 'renew', '--no-random-sleep-on-renew')
            else:
                for name, (_, names, *_) in SETS.items():
                    command = common + ['certonly', '--dns-route53', '--agree-tos', '--email', 'nicholas.eldridge@gmail.com', '--cert-name', name]
                    if staging: command += ['--test-cert']
                    for domain in names: command += ['-d', domain]
                    run(*command)
            if not staging:
                for name, (dest, *_) in SETS.items():
                    source = state/'live'/name
                    # Reconcile on every run, including a previous deployment failure.
                    if run('openssl', 'x509', '-in', str(source/'fullchain.pem'), '-noout', '-fingerprint') != run('openssl', 'x509', '-in', str(Path(dest)/'fullchain.pem'), '-noout', '-fingerprint'):
                        deploy(name, source)
                    health(name, Path(dest))
            success = True
        finally:
            if not staging and args.action != 'dry-run':
                metrics = Path('/opt/data/homelab/monitoring/textfile/certificates.prom')
                previous = ROOT/'last-success'
                if success: previous.write_text(str(int(time.time())))
                content = f'homelab_certificate_renewal_success{{host="bb9b"}} {int(success)}\nhomelab_certificate_renewal_last_success_seconds{{host="bb9b"}} {previous.read_text() if previous.exists() else 0}\n'
                tmp = metrics.with_suffix('.tmp'); tmp.write_text(content); tmp.chmod(0o644); tmp.replace(metrics)

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        # Never echo subprocess output: DNS/client diagnostics may contain credentials.
        print('Certificate operation failed: '+type(exc).__name__)
        raise SystemExit(1)
