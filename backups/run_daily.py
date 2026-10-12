#!/usr/bin/env python3
"""Daily local snapshot followed by independent bounded NAS publication."""
import json, os, shutil, subprocess, time
from pathlib import Path
ROOT=Path('/opt/data/homelab/backups')
CODE=Path(__file__).resolve().parent
os.umask(0o077)
try:
    # No deletion is authorized. Fail visibly rather than accumulate forever.
    used=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
    reserve=8*1024**3
    if used+reserve>64*1024**3 or shutil.disk_usage(ROOT).free<reserve:
        raise RuntimeError('Recovery storage guard: reserve 8 GiB within 64 GiB budget; review retention')
    subprocess.run(['/usr/bin/python3',str(CODE/'create_bundle.py')],check=True,timeout=1200)
    status=json.loads((ROOT/'local-status.json').read_text())
    subprocess.run(['/usr/bin/python3',str(CODE/'verify_bundle.py'),str(ROOT/status['id'])],check=True,timeout=600)
except Exception:
    old={}
    try: old=json.loads((ROOT/'local-status.json').read_text())
    except (OSError,ValueError): pass
    now=time.time()
    old.update(source='bundle-validator',success=False,observed=now)
    old.setdefault('completed',now)
    tmp=ROOT/'local-status.tmp';tmp.write_text(json.dumps(old)+'\n');tmp.replace(ROOT/'local-status.json')
    raise
subprocess.run(['/usr/bin/python3',str(CODE/'publish_nas.py'),str(ROOT/status['id'])],check=True,timeout=2400)
