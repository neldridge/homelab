#!/usr/bin/python3
"""Observe local result files only; never traverse NFS from this collector."""
import json, subprocess, time
from pathlib import Path
from nfs_probe import ROOT, MOUNTS, mount_ok

def storage_metrics(mountinfo, results, now):
    rows = []
    for name in MOUNTS:
        present = int(mount_ok(name, mountinfo))
        result = results.get(name, {})
        age = max(0, now-result.get('timestamp', 0))
        ok = int(present and result.get('ok') == 1 and age < 45)
        for metric, value in [('mount_ok', present), ('read_ok', ok),
                              ('read_age_seconds', age), ('read_duration_seconds', result.get('duration', 0))]:
            rows.append(f'homelab_nfs_{metric}{{host="bb9b",service="nfs-{name}"}} {value}')
    return rows

def run():
    now = time.time(); results = {}
    for name in MOUNTS:
        try: results[name] = json.loads((ROOT/'nfs'/(name+'.json')).read_text())
        except (OSError, ValueError): pass
    rows = storage_metrics(Path('/proc/self/mountinfo').read_text(), results, now)
    rows.append(f'homelab_storage_checks_timestamp{{host="bb9b",service="storage-checks"}} {now}')
    fault = ROOT/'phase3-fault-nfs'
    if fault.exists():
        rows = [r.replace(' 1', ' 0') if 'service="nfs-library"' in r and ('mount_ok{' in r or 'read_ok{' in r) else r for r in rows]
    p = ROOT/'textfile/storage.prom'; tmp = p.with_suffix('.tmp')
    tmp.write_text('\n'.join(rows)+'\n'); tmp.chmod(0o644); tmp.replace(p)
if __name__ == '__main__': run()
