#!/usr/bin/python3
"""One direct read per mount. systemd owns timeout and prevents overlapping workers."""
import json, mmap, os, sys, time
from pathlib import Path
ROOT = Path('/opt/data/homelab/monitoring')
MOUNTS = {'library': '/mnt/media-library', 'library-alias': '/media-library',
          'downloads': '/mnt/media-downloads', 'storage': '/mnt/storage', 'k8s': '/mnt/k8s-services'}
SHARES = {'library': 'media-library', 'library-alias': 'media-library',
          'downloads': 'media-downloads', 'storage': 'storage', 'k8s': 'k8s-services'}
CONTENT = b'homelab-monitoring-read-probe-v1\n'
def mount_ok(name, text):
    for line in text.splitlines():
        left, right = line.split(' - ', 1)
        fields, fs = left.split(), right.split()
        if fields[4] == MOUNTS[name]:
            return fs[0] in ('nfs', 'nfs4') and fs[1] == '192.168.11.131:/volume2/' + SHARES[name]
    return False

def run(name, initialize=False):
    assert mount_ok(name, Path('/proc/self/mountinfo').read_text()), 'unexpected or missing mount'
    target = Path(MOUNTS[name]) / '.homelab-monitoring-probe'
    if initialize:
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            assert target.read_bytes() == CONTENT
        else:
            with os.fdopen(fd, 'wb') as f:
                f.write(CONTENT); f.flush(); os.fsync(f.fileno())
        return
    start = time.monotonic()
    # O_DIRECT avoids reporting a successful read solely from the client page cache.
    with mmap.mmap(-1, 4096) as buf:
        fd = os.open(target, os.O_RDONLY | os.O_DIRECT | os.O_NOFOLLOW)
        try:
            length = os.readv(fd, [buf])
            assert bytes(buf[:length]) == CONTENT
        finally:
            os.close(fd)
    result = {'timestamp': time.time(), 'duration': time.monotonic()-start, 'ok': 1}
    p = ROOT / 'nfs' / (name + '.json')
    tmp = p.with_suffix('.tmp'); tmp.write_text(json.dumps(result)); tmp.replace(p)
if __name__ == '__main__':
    run(sys.argv[1], '--initialize' in sys.argv)
