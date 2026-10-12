#!/usr/bin/env python3
"""Create private recovery trees. No NAS dependency and no live SQLite file copies."""
import datetime, fcntl, hashlib, json, os, shutil, sqlite3, stat, subprocess, time
from pathlib import Path
from urllib.parse import quote
BASE = Path('/opt/data/homelab')
OUT = BASE / 'backups'
APPS = ('sonarr','radarr','prowlarr','bazarr','seerr','tautulli','nzbget','plexmetamanager','overseerr','htpcmanager','muximux')
SKIP_DIRS = {'logs','log','cache','.cache','.yarn','lost+found','Backups','backups','backup','Sentry','MediaCover','broken','restore'}
SKIP_FILES = {'logs.db','config.cache','new.db','broken.db','corrupt_prowlarr.db','sonarr-recovered.db','dump.sql','dump.err','schema.sql','sonarr-recovery.sql','sonarr-recovery-fixed.sql'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def validate_db(path):
    with sqlite3.connect(f'file:{quote(str(path))}?mode=ro&immutable=1',uri=True) as db:
        deadline=time.monotonic()+120
        db.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
        if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
            raise RuntimeError('SQLite integrity check failed')
        return db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]

def copy_file(src,dst,records,stage):
    if src.is_symlink():
        raise RuntimeError(f'Symlink requires explicit scope: {src}')
    info=src.stat()
    if not stat.S_ISREG(info.st_mode): raise RuntimeError(f'Not a regular file: {src}')
    dst.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with src.open('rb') as f: sqlite=f.read(16)==b'SQLite format 3\x00'
    method='stable-file'; tables=None
    if sqlite:
        method='sqlite-online-backup'
        deadline=time.monotonic()+120
        def progress(status,remaining,total):
            if time.monotonic()>deadline: raise TimeoutError('SQLite snapshot timeout')
        with sqlite3.connect(f'file:{quote(str(src))}?mode=ro',uri=True,timeout=5) as source:
            with sqlite3.connect(dst) as target: source.backup(target,pages=256,progress=progress,sleep=.05)
        tables=validate_db(dst)
    else:
        if src.suffix in {'.db','.sqlite','.sqlite3'}: raise RuntimeError(f'Unknown database format: {src}')
        for attempt in range(3):
            before=src.stat(); shutil.copyfile(src,dst); after=src.stat()
            if (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns): break
        else: raise RuntimeError(f'File changing during copy: {src}')
    dst.chmod(0o600)
    records.append(dict(path=str(dst.relative_to(stage)),source=str(src),sha256=digest(dst),bytes=dst.stat().st_size,uid=info.st_uid,gid=info.st_gid,mode=stat.S_IMODE(info.st_mode),method=method,tables=tables))

def copy_tree(src,dst,records,stage,app=False):
    for root,dirs,files in os.walk(src,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not (app and d in SKIP_DIRS) and not d.startswith('._'))
        for d in dirs:
            if (Path(root)/d).is_symlink():
                link=Path(root)/d
                if link==BASE/'repo/compose/nginx/certs' and link.resolve()==BASE/'nginx/certs':
                    copy_tree(link.resolve(),dst/link.relative_to(src),records,stage)
                else: raise RuntimeError(f'Symlink requires scope: {link}')
        dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
        for name in sorted(files):
            if name.startswith('._') or name.endswith(('-wal','-shm','.pid','.log')): continue
            if app and (name in SKIP_FILES or '.before-' in name or '.backup-' in name or '.bak' in name or '.pre-recovery' in name or name.startswith('logs.db')): continue
            p=Path(root)/name
            copy_file(p,dst/p.relative_to(src),records,stage)

def main():
    os.umask(0o077); OUT.mkdir(mode=0o700,exist_ok=True)
    lock=(OUT/'bundle.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ident=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    stage=OUT/('.partial-'+ident); stage.mkdir(mode=0o700); records=[]
    for app in APPS:
        if not (BASE/'config'/app).is_dir(): raise RuntimeError(f'Missing app directory: {app}')
        copy_tree(BASE/'config'/app,stage/'config'/app,records,stage,app=True)
    copy_tree(BASE/'repo',stage/'deployment/server-repo',records,stage)
    for name in ('runtime.env','app-keys.json','snmp.yml','synology-snmp.json'):
        copy_file(BASE/'monitoring'/name,stage/'monitoring'/name,records,stage)
    copy_tree(BASE/'monitoring/tls',stage/'monitoring/tls',records,stage)
    copy_file(BASE/'monitoring/grafana/grafana.db',stage/'monitoring/grafana/grafana.db',records,stage)
    for name in ('plugins','provisioning'):
        p=BASE/'monitoring/grafana'/name
        if p.exists(): copy_tree(p,stage/'monitoring/grafana'/name,records,stage)
    for name in ('fstab','hostname','hosts','netplan','docker','cron.d','systemd/system'):
        p=Path('/etc')/name
        # Only regular homelab units; systemd enablement links are inventoried below.
        if name=='systemd/system':
            for unit in p.glob('*homelab*'):
                if unit.is_file() and not unit.is_symlink(): copy_file(unit,stage/'host/etc/systemd/system'/unit.name,records,stage)
        elif p.is_dir(): copy_tree(p,stage/'host/etc'/name,records,stage)
        elif p.exists(): copy_file(p,stage/'host/etc'/name,records,stage)
    if (OUT/'source-inputs').exists(): copy_tree(OUT/'source-inputs',stage/'deployment/source-inputs',records,stage)
    copy_tree(BASE/'rollback',stage/'rollback',records,stage)
    for name,args in {
        'packages':['dpkg-query','-W'],
        'units':['systemctl','list-unit-files','--no-pager'],
        'mounts':['findmnt','--json'],
        'containers':['docker','ps','-a','--no-trunc','--format','{{.Names}} {{.Image}} {{.Status}}'],
        'git-status':['git','-C',str(BASE/'repo'),'status','--porcelain=v1']
    }.items():
        data=subprocess.run(args,check=True,capture_output=True,timeout=30).stdout
        p=stage/'inventory'/f'{name}.txt'; p.parent.mkdir(exist_ok=True,mode=0o700);p.write_bytes(data)
        records.append(dict(path=str(p.relative_to(stage)),sha256=digest(p),bytes=len(data),method='inventory',uid=0,gid=0,mode=0o600))
    manifest=dict(schema=1,id=ident,created=time.time(),consistency='Per-database online snapshots; stable config files. Not a cross-application transaction.',files=records,excluded=['bulk media','downloads','logs','caches','historical app backup ZIPs','corrupt/recovery scratch DBs','Prometheus/Loki/Alloy history','Plex external host','host SSH private keys'])
    (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (stage/'COMPLETE').write_text(digest(stage/'manifest.json')+'\n')
    complete=OUT/ident;stage.rename(complete)
    status=dict(source='bundle-validator',observed=time.time(),success=True,id=ident,completed=time.time(),bytes=sum(r['bytes'] for r in records),files=len(records),databases=sum(r['method']=='sqlite-online-backup' for r in records))
    tmp=OUT/'local-status.tmp';tmp.write_text(json.dumps(status)+'\n');tmp.replace(OUT/'local-status.json')
    print(json.dumps(status))
if __name__=='__main__': main()
