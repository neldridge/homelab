#!/usr/bin/env python3
"""Verify a completed local, NAS, or decrypted cloud restore without running apps."""
import argparse, configparser, hashlib, json, sqlite3, time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def verify(root):
    root=Path(root).resolve()
    assert (root/'COMPLETE').read_text().strip()==digest(root/'manifest.json'),'manifest checksum'
    m=json.loads((root/'manifest.json').read_text()); dbs=0
    assert m['schema']==1
    for item in m['files']:
        rel=Path(item['path']); assert not rel.is_absolute() and '..' not in rel.parts
        path=root/rel
        assert path.resolve().is_relative_to(root) and not path.is_symlink()
        assert path.stat().st_size==item['bytes'] and digest(path)==item['sha256'],f'checksum: {rel}'
        if item['method']=='sqlite-online-backup':
            with sqlite3.connect(f'file:{quote(str(path))}?mode=ro&immutable=1',uri=True) as db:
                deadline=time.monotonic()+120
                db.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
                assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)],str(rel)
                assert db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]==item['tables']
            dbs+=1
        if rel.name in ('settings.json','settings.old.json','app-keys.json','synology-snmp.json'): json.loads(path.read_text())
        if rel.name=='config.xml': ET.parse(path)
        if rel==Path('config/tautulli/config.ini'):
            cfg=configparser.ConfigParser();cfg.read(path);assert cfg.has_section('General')
    return dict(id=m['id'],files=len(m['files']),databases=dbs,bytes=sum(x['bytes'] for x in m['files']),verified=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('bundle');a=p.parse_args();print(json.dumps(verify(a.bundle)))
