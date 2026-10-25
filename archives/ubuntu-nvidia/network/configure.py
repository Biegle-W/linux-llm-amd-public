#!/usr/bin/env python3
"""Discover private Linux addresses and create an ignored bearer-key configuration."""
import ipaddress
import json
import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
private = ROOT / 'dsh/data'
private.mkdir(exist_ok=True)
routes = json.loads(subprocess.check_output(['ip', '-j', '-4', 'route'], text=True))
route = next(r for r in routes if r.get('dst') == 'default' and r.get('prefsrc'))
interface = route['dev']
lan = route['prefsrc']
addresses = json.loads(subprocess.check_output(['ip', '-j', '-4', 'address'], text=True))
prefix = next(a['prefixlen'] for i in addresses if i['ifname'] == interface
              for a in i['addr_info'] if a.get('local') == lan)
network = ipaddress.ip_network(f'{lan}/{prefix}', strict=False)
rfc1918 = [ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
assert any(network.subnet_of(n) for n in rfc1918), 'Default interface is not a private LAN'
tail = json.loads(subprocess.check_output(['tailscale', 'status', '--json'], text=True))
assert tail.get('BackendState') == 'Running', 'Tailscale must be signed in and running'
ts = next(a for a in tail['TailscaleIPs'] if ipaddress.ip_address(a).version == 4)
assert ipaddress.ip_address(ts) in ipaddress.ip_network('100.64.0.0/10')
key = private / 'network-api.key'
if not key.exists():
    fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write(secrets.token_urlsafe(48) + '\n')
key.chmod(0o600)
config = {'listen': ['127.0.0.1', lan, ts], 'port': 10000,
          'allowed_subnets': ['127.0.0.0/8', str(network), '100.64.0.0/10'],
          'key_file': str(key), 'lan_interface': interface,
          'tailscale_dns': tail.get('Self', {}).get('DNSName', '').rstrip('.'),
          'default_model': 'qwen3.8-flash-next-iq3_xxs'}
path = private / 'network-access.json'
tmp = path.with_suffix('.tmp')
tmp.write_text(json.dumps(config, indent=2) + '\n')
tmp.chmod(0o600)
os.replace(tmp, path)
print('LAN:', f'http://{lan}:10000/v1')
print('Tailscale:', f'http://{ts}:10000/v1')
print('API key saved privately; not printed.')
