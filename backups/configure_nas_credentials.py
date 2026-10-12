#!/usr/bin/env python3
"""Run interactively as root; never accept secrets as command arguments."""
import getpass,os,tempfile
from pathlib import Path
if os.geteuid()!=0:raise SystemExit('Run with sudo in a private terminal.')
root=Path('/opt/data/homelab/backups');root.mkdir(mode=0o700,exist_ok=True)
password=getpass.getpass('NAS homelab-backup password (hidden): ')
if not password or '\n' in password or '\r' in password:raise SystemExit('Invalid password')
fd,name=tempfile.mkstemp(prefix='.nas-auth-',dir=root)
try:
    os.fchmod(fd,0o600)
    with os.fdopen(fd,'w') as f:
        f.write('username = homelab-backup\npassword = '+password+'\n')
        f.flush();os.fsync(f.fileno())
    os.replace(name,root/'nas-smb.auth')
finally:
    if os.path.exists(name):os.unlink(name)
print('Saved root-only NAS authentication file. No credential was printed.')
