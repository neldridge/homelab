#!/usr/bin/env python3
"""Independent stage evidence; local completion never proves NAS/cloud success."""
import json, time
from pathlib import Path
ROOT=Path('/opt/data/homelab/monitoring')
BACKUPS=Path('/opt/data/homelab/backups')

def metrics(base=BACKUPS, now=None):
    now=time.time() if now is None else now
    rows=[]
    for stage,filename in [('local','local-status.json'),('nas','nas-status.json'),('cloud','cloud-status.json')]:
        known=0; success=0; completed=0; observed=0
        try:
            s=json.loads((base/filename).read_text())
            # NAS must report remote verification; cloud needs a real HB observer.
            expected={'local':'bundle-validator','nas':'nas-readback','cloud':'hyper-backup-observer'}[stage]
            assert s['source']==expected
            completed=float(s['completed']);observed=float(s['observed'])
            assert 0 < completed <= observed+60 and observed <= now+60
            assert isinstance(s['success'],bool)
            known=1;success=int(s['success'])
        except (OSError,ValueError,KeyError,TypeError,AssertionError): pass
        for name,value in [('known',known),('success',success),('completed_timestamp',completed),('observed_timestamp',observed)]:
            rows.append(f'homelab_recovery_{name}{{host="bb9b",stage="{stage}"}} {value}')
    rows.append(f'homelab_recovery_checks_timestamp{{host="bb9b"}} {now}')
    return '\n'.join(rows)+'\n'

def run():
    out=ROOT/'textfile/recovery.prom';tmp=out.with_suffix('.tmp')
    tmp.write_text(metrics());tmp.chmod(0o644);tmp.replace(out)
if __name__=='__main__':run()
