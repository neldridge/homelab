#!/usr/bin/env python3
"""Publish verified archives via encrypted, bounded SMB; never mount the NAS."""
import argparse, fcntl, json, os, re, subprocess, tarfile, time
from pathlib import Path
from verify_bundle import verify, digest

ROOT = Path('/opt/data/homelab/backups')
AUTH = ROOT / 'nas-smb.auth'

def smb(command, timeout=1800):
    result = subprocess.run(['smbclient', '//192.168.11.131/homelab-recovery',
        '-A', str(AUTH), '--client-protection=encrypt', '-t', '30', '-c', command],
        capture_output=True, text=True, timeout=timeout, env={**os.environ, "TZ": "UTC", "LC_ALL": "C"})
    if result.returncode or 'NT_STATUS_' in result.stdout + result.stderr:
        raise RuntimeError('SMB operation failed: ' + (result.stdout + result.stderr)[-1500:])
    return result.stdout

def status(value):
    tmp = ROOT / 'nas-status.tmp'
    tmp.write_text(json.dumps(value) + '\n'); tmp.chmod(0o600)
    tmp.replace(ROOT / 'nas-status.json')

def main(bundle):
    os.umask(0o077)
    from retention import lock_file, safe_tree
    if ROOT.is_symlink() or ROOT.resolve() != ROOT.absolute():
        raise RuntimeError('Symlink backup root')
    builder_lock = lock_file(ROOT / 'bundle.lock')
    lock = lock_file(ROOT / 'transfer.lock')
    bundle = Path(bundle)
    if bundle.is_symlink() or bundle.absolute() != bundle.resolve():
        raise RuntimeError('Symlink bundle path')
    bundle = bundle.resolve()
    assert bundle.parent == ROOT and re.fullmatch(r'\d{8}T\d{6}Z', bundle.name)
    safe_tree(bundle)
    evidence = verify(bundle); ident = evidence['id']
    if (ROOT/'transfers').is_symlink(): raise RuntimeError('Symlink transfer root')
    work = ROOT / 'transfers' / ident
    work.mkdir(parents=True, exist_ok=False, mode=0o700)
    archive = work / 'recovery.tar'
    try:
        with tarfile.open(archive, 'w', format=tarfile.PAX_FORMAT) as tar:
            tar.add(bundle, arcname=ident)
        sha = digest(archive)
        # Staging and retained prior archives are outside HB's selected folder.
        listing = smb('ls', 45)
        for directory in ('staging', 'published', 'prior'):
            if not re.search(r'^\s*' + directory + r'\s+D', listing, re.M):
                smb('mkdir ' + directory, 45)
        remote = f'staging/{ident}.tar'
        smb(f'put "{archive}" "{remote}"')
        readback = work / 'nas-readback.tar'
        smb(f'get "{remote}" "{readback}"')
        assert digest(readback) == sha, 'NAS archive checksum mismatch'
        restored = work / 'readback'
        restored.mkdir(mode=0o700)
        with tarfile.open(readback) as tar:
            tar.extractall(restored, filter='data')
        assert verify(restored / ident) == evidence, 'NAS bundle verification mismatch'
        previous = smb('cd published; ls', 45)
        if re.search(r'^\s*recovery.tar\s+', previous, re.M):
            smb(f'rename published/recovery.tar prior/before-{ident}.tar', 45)
        smb(f'rename "{remote}" published/recovery.tar', 45)
        # Verify the published path as well, after rename.
        final = work / 'published-readback.tar'
        smb(f'get published/recovery.tar "{final}"')
        assert digest(final) == sha, 'Published archive checksum mismatch'
        from retention import prune_nas
        prune_nas(smb, ident, apply=True)
        now = time.time()
        status(dict(source='nas-readback', success=True, completed=now, observed=now,
                    bundle_id=ident, sha256=sha, archive_bytes=archive.stat().st_size,
                    path='homelab-recovery/published/recovery.tar', **{'validation': evidence}))
        print(json.dumps(dict(bundle_id=ident, nas_verified=True, sha256=sha,
                              archive_bytes=archive.stat().st_size)))
    except Exception:
        previous = {}
        try: previous = json.loads((ROOT / 'nas-status.json').read_text())
        except (OSError, ValueError): pass
        now = time.time()
        status(dict(source='nas-readback', success=False,
                    completed=previous.get('completed', now), observed=now, bundle_id=ident))
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('bundle')
    main(parser.parse_args().bundle)
