#!/usr/bin/python3
"""Validate backup artifacts; never equate file age with job success."""
import configparser, datetime, json, sqlite3, tempfile, time, urllib.request, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path('/opt/data/homelab/monitoring')
CONFIG=Path('/opt/data/homelab/config')

def validate_archive(path, service, tempdir, config="config.xml", info=True):
    assert path.stat().st_size <= 64*1024*1024
    with zipfile.ZipFile(path) as z:
        entries=z.infolist()
        assert len(entries)<=16 and sum(e.file_size for e in entries)<=512*1024*1024
        names=z.namelist(); assert service+'.db' in names
        if config: assert config in names
        if info: assert 'INFO' in names
        assert z.testzip() is None
        if config=='config.xml': ET.fromstring(z.read(config))
        elif config: assert len(z.read(config))>0
        data=z.read(service+'.db'); assert data.startswith(b'SQLite format 3\x00')
        # A private disposable copy only. No opening/changing the application's DB.
        with tempfile.TemporaryDirectory(dir=tempdir) as td:
            p=Path(td)/'backup.db';p.write_bytes(data)
            db=sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True)
            try:
                deadline=time.monotonic()+8
                db.set_progress_handler(lambda: int(time.monotonic()>deadline),10000)
                assert db.execute('pragma quick_check').fetchall()==[('ok',)]
                assert db.execute("select count(*) from sqlite_master where type='table'").fetchone()[0]>0
            finally: db.close()

def tautulli_artifacts(folder):
    # Manual and scheduled backups have the same contents. Config and database
    # jobs run independently, so their filenames need not share a timestamp.
    database=max(folder.glob('tautulli.backup-*.db.zip'),key=lambda p:p.stat().st_mtime)
    config=max(folder.glob('config.backup-*.ini.zip'),key=lambda p:p.stat().st_mtime)
    return database, config, min(database.stat().st_mtime,config.stat().st_mtime)

def validate_tautulli_config(path):
    assert path.stat().st_size<1024*1024
    with zipfile.ZipFile(path) as z:
        assert len(z.infolist())==1 and z.infolist()[0].file_size<1024*1024
        assert z.testzip() is None
        c=configparser.ConfigParser();c.read_string(z.read('config.ini').decode());assert c.has_section('General')

def run():
    keys=json.loads((ROOT/'app-keys.json').read_text());rows=[]
    for s,p,v in [('sonarr',8989,3),('radarr',7878,3),('prowlarr',9696,1)]:
        valid=0; stamp=0; threshold=8*86400
        try:
            def get(route):
                req=urllib.request.Request(f'http://127.0.0.1:{p}/api/v{v}/'+route,headers={'X-Api-Key':keys[s]})
                with urllib.request.urlopen(req,timeout=4) as r:return json.loads(r.read(1024*1024))
            cfg=get('config/host'); assert cfg['backupFolder']=='Backups'
            threshold=(cfg['backupInterval']+1)*86400
            records=[x for x in get('system/backup') if x['type']=='scheduled']
            latest=max(records,key=lambda x:x['time']);name=latest['name']; assert Path(name).name==name
            stamp=datetime.datetime.fromisoformat(latest['time'].replace('Z','+00:00')).timestamp()
            assert stamp<=time.time()+60
            validate_archive(CONFIG/s/'Backups/scheduled'/name,s,ROOT/'backup-checks')
            valid=1
        except Exception: pass
        if (ROOT/('phase3-fault-backup-'+s)).exists():valid=0;stamp=0
        for metric,value in [('archive_valid',valid),('artifact_timestamp',stamp),('max_age_seconds',threshold)]:
            rows.append(f'homelab_backup_{metric}{{host="bb9b",service="{s}"}} {value}')
    # Tautulli config/DB backups may be scheduled or manual. Both must be fresh.
    # Bazarr is weekly. Only artifact checks are claimed; no job success inferred.
    for service,folder,pattern,limit in [('tautulli','backups','tautulli.backup-*.db.zip',12*3600),('bazarr','backup','*.zip',8*86400)]:
        valid=0;stamp=0
        try:
            path=max((CONFIG/service/folder).glob(pattern),key=lambda p:p.stat().st_mtime)
            stamp=path.stat().st_mtime
            if service=='tautulli':
                path,companion,stamp=tautulli_artifacts(CONFIG/service/folder)
                assert max(path.stat().st_mtime,companion.stat().st_mtime)<=time.time()+60
                validate_archive(path,service,ROOT/'backup-checks',config=None,info=False)
                validate_tautulli_config(companion)
            else: validate_archive(path,service,ROOT/'backup-checks',config='config.yaml',info=False)
            valid=1
        except Exception: pass
        for metric,value in [('archive_valid',valid),('artifact_timestamp',stamp),('max_age_seconds',limit)]:
            rows.append(f'homelab_backup_{metric}{{host="bb9b",service="{service}"}} {value}')
    rows.append(f'homelab_backup_checks_timestamp{{host="bb9b",service="backup-checks"}} {time.time()}')
    p=ROOT/'textfile/backups.prom';tmp=p.with_suffix('.tmp');tmp.write_text('\n'.join(rows)+'\n');tmp.chmod(0o644);tmp.replace(p)
if __name__=='__main__':
    run()
    import recovery_checks
    recovery_checks.run()
