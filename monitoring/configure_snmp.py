#!/usr/bin/env python3
"""Render private SNMP auth configuration; run with sudo on the monitoring host."""
import json
import os
from pathlib import Path

runtime = Path('/opt/data/homelab/monitoring')
credentials = json.loads((runtime / 'synology-snmp.json').read_text())
auth = {
    'version': 3, 'security_level': 'authPriv',
    'username': credentials['username'],
    'password': credentials['auth_password'],
    'auth_protocol': credentials['auth_protocol'],
    'priv_password': credentials['priv_password'],
    'priv_protocol': credentials['priv_protocol'],
}
# JSON is valid YAML; auth values are never interpolated into shell commands/logs.
fd = os.open(runtime / 'snmp.yml', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.fchmod(fd, 0o600)
with os.fdopen(fd, 'w') as output:
    output.write('auths: ' + json.dumps({'synology_v3': auth}) + '\n')
    output.write(Path(__file__).with_name('snmp-modules.yml').read_text())
