#!/usr/bin/env python3
"""Stage boot-time AMD peer-access disable; never reset or unbind live GPUs."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

PARAMS = ('amdgpu.pcie_p2p=0', 'amdgpu.use_xgmi_p2p=0')
BODY = ('# Managed local-llm AMD peer-access disable; no live GPU changes.\n'
        'GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} ' + ' '.join(PARAMS) + '"\n').encode()
CONFIG = Path('/etc/default/grub.d/zz-local-llm-amd-no-p2p.cfg')
STATE = Path('/var/lib/local-llm-amd-no-p2p/state.json')
GRUB = Path('/boot/grub/grub.cfg')
ROUTING_CONFIG = Path('/etc/default/grub.d/zz-local-llm-amd-p2p.cfg')
ROUTING_STATE = Path('/var/lib/local-llm-amd-p2p/state.json')


def atomic(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def entries(text):
    rows = [shlex.split(l) for l in text.splitlines()
            if re.match(r'^\s*linux(?:efi)?\s+.*vmlinuz', l)]
    if not rows:
        raise RuntimeError('No Ubuntu kernel entries found')
    return rows


def validate_generated(before, after, removing=False, routing_args=()):
    old, new = entries(before), entries(after)
    if len(old) != len(new):
        raise RuntimeError('Kernel entry count changed unexpectedly')
    for a, b in zip(old, new):
        if removing:
            expected = [x for x in a if x not in PARAMS]
        else:
            if any(x.split('=')[0] in {p.split('=')[0] for p in PARAMS} for x in a):
                raise RuntimeError('Existing P2P kernel option requires review')
            expected = [x for x in a if x not in routing_args]
        stripped = [x for x in b if x not in (routing_args if removing else PARAMS)]
        if stripped != expected or (not removing and any(b.count(p) != 1 for p in PARAMS)):
            raise RuntimeError('Generated entry changed unrelated arguments or lost P2P options')
        if any((b.count(p) != 1 if removing else p in b) for p in routing_args):
            raise RuntimeError('Managed routing arguments were not restored/removed exactly')


def stage(config=CONFIG, state=STATE, grub=GRUB, run=subprocess.run,
          routing_config=ROUTING_CONFIG, routing_state=ROUTING_STATE, sources=None):
    if config.exists() or state.exists():
        raise RuntimeError('Existing disable state requires verification; refusing overwrite')
    if sources is None:
        sources = [Path('/etc/default/grub'), *Path('/etc/default/grub.d').glob('*.cfg')]
    for p in sources:
        if re.search(r'amdgpu\.(?:pcie_p2p|use_xgmi_p2p)\s*=', p.read_text()):
            raise RuntimeError('Existing P2P boot option requires review: ' + str(p))
    before = grub.read_bytes()
    entries(before.decode())
    routing_body = routing_record = None
    routing_args = []
    if routing_config.exists() or routing_state.exists():
        routing_body, routing_record = routing_config.read_bytes(), routing_state.read_bytes()
        old = json.loads(routing_record)
        if (not routing_body.startswith(b'# Managed local-llm AMD PEX peer routing; no live PCI writes.')
                or hashlib.sha256(routing_body).hexdigest() != old['dropin_sha256']
                or not old['parameter'].startswith('pci=config_acs=')):
            raise RuntimeError('Existing routing policy is not authenticated; refusing overwrite')
        routing_args = [old['parameter']]
        if old.get('IOMMU_policy_changed'):
            routing_args.append('iommu=pt')
        # Remove only arguments proved to come from this managed file.
        value = subprocess.check_output(['sh', '-c',
            'GRUB_CMDLINE_LINUX=""; . "$1"; printf "%s" "$GRUB_CMDLINE_LINUX"',
            'sh', str(routing_config)], text=True)
        if shlex.split(value) != routing_args:
            raise RuntimeError('Managed routing drop-in has unexpected settings')
        for row in entries(before.decode()):
            if any(row.count(p) != 1 for p in routing_args):
                raise RuntimeError('Existing boot entries do not match managed routing')
    state.parent.mkdir(parents=True, exist_ok=True)
    state.parent.chmod(0o700)
    backup = state.parent / 'grub.before.cfg'
    if backup.exists():
        raise RuntimeError('Existing backup requires review')
    atomic(backup, before, 0o600)
    try:
        if routing_body is not None:
            atomic(state.parent / 'routing.before.cfg', routing_body, 0o600)
            atomic(state.parent / 'routing.before.json', routing_record, 0o600)
            routing_config.unlink()
            routing_state.unlink()
        atomic(config, BODY)
        run(['update-grub'], check=True)
        run(['grub-script-check', str(grub)], check=True)
        validate_generated(before.decode(), grub.read_text(), routing_args=routing_args)
        record = {'status': 'staged; reboot and runtime verification pending',
                  'parameters': PARAMS, 'dropin_sha256': hashlib.sha256(BODY).hexdigest(),
                  'previous_grub_sha256': hashlib.sha256(before).hexdigest(),
                  'boot_id_at_install': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  'removed_managed_routing_arguments': routing_args,
                  'routing_dropin_sha256': hashlib.sha256(routing_body).hexdigest() if routing_body else None,
                  'reboot_required': True, 'live_gpu_changes': False}
        atomic(state, (json.dumps(record, indent=2) + '\n').encode(), 0o600)
        return record
    except BaseException:
        config.unlink(missing_ok=True)
        atomic(grub, before, 0o600)
        state.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)
        if routing_body is not None:
            atomic(routing_config, routing_body)
            atomic(routing_state, routing_record, 0o600)
        raise


def rollback(config=CONFIG, state=STATE, grub=GRUB, run=subprocess.run,
             routing_config=ROUTING_CONFIG, routing_state=ROUTING_STATE):
    d = json.loads(state.read_text())
    if hashlib.sha256(config.read_bytes()).hexdigest() != d['dropin_sha256']:
        raise RuntimeError('Managed drop-in differs; refusing rollback')
    before, body = grub.read_bytes(), config.read_bytes()
    routing_args = d['removed_managed_routing_arguments']
    if routing_args:
        if routing_config.exists() or routing_state.exists():
            raise RuntimeError('Routing policy now exists; refusing overwrite')
        rb = (state.parent / 'routing.before.cfg').read_bytes()
        rs = (state.parent / 'routing.before.json').read_bytes()
        if (hashlib.sha256(rb).hexdigest() != d['routing_dropin_sha256']
                or json.loads(rs)['dropin_sha256'] != d['routing_dropin_sha256']):
            raise RuntimeError('Routing backup authentication failed')
    try:
        config.unlink()
        if routing_args:
            atomic(routing_config, rb)
            atomic(routing_state, rs, 0o600)
        run(['update-grub'], check=True)
        run(['grub-script-check', str(grub)], check=True)
        validate_generated(before.decode(), grub.read_text(), removing=True, routing_args=routing_args)
    except BaseException:
        atomic(config, body)
        atomic(grub, before, 0o600)
        if routing_args:
            routing_config.unlink(missing_ok=True)
            routing_state.unlink(missing_ok=True)
        raise
    state.rename(state.with_suffix('.rolled-back.json'))
    return {'status': 'next-boot disable removed; current driver unchanged', 'reboot_required': True}


def verify():
    params = Path('/sys/module/amdgpu/parameters')
    actual = {n: (params / n).read_text().strip() for n in ('pcie_p2p', 'use_xgmi_p2p')}
    tokens = Path('/proc/cmdline').read_text().split()
    off = actual == {'pcie_p2p': 'N', 'use_xgmi_p2p': '0'}
    routing_retired = not any(x.startswith('pci=config_acs=') for x in tokens)
    topology = Path('/sys/class/kfd/kfd/topology/nodes')
    nodes = [n for n in topology.iterdir() if (n / 'gpu_id').read_text().strip() != '0']
    gpu_nodes = {int(n.name) for n in nodes}
    peer_links = []
    for node in nodes:
        for kind in ('io_links', 'p2p_links'):
            for link in (node / kind).glob('*/properties'):
                props = dict(line.split() for line in link.read_text().splitlines())
                if int(props['node_to']) in gpu_nodes and props['node_from'] != props['node_to']:
                    peer_links.append(props)
    redirect = None
    routing_audit = None
    if os.geteuid() == 0:
        from amd_p2p_support import audit
        routing_audit = audit()
        redirect = (len(routing_audit['selected_bridges']) == 6
                    and not routing_audit['admission_errors']
                    and all(r['acs']['control'] == 0x1d for r in routing_audit['selected_bridges']))
    return {'parameters': actual, 'boot_options_present': all(p in tokens for p in PARAMS),
            'verified_boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'driver_peer_access_disabled': off,
            'managed_peer_routing_retired': routing_retired,
            'kfd_gpu_count': len(nodes),
            'kfd_gpu_to_gpu_links': peer_links,
            'six_bridge_acs_redirect_restored': redirect,
            'routing_audit': routing_audit,
            'status': 'driver off; HIP negative checks still required' if off else 'P2P IS NOT DISABLED',
            'reboot_performed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'install', 'verify', 'rollback'])
    args = parser.parse_args()
    if args.action == 'plan':
        print(BODY.decode(), end='')
        print('# Also retire authenticated managed ACS/IOMMU P2P-enabling policy, if present.')
        return
    if args.action == 'verify':
        d = verify()
    else:
        if os.geteuid() != 0:
            raise RuntimeError('Administrator authentication required; run with sudo')
        with open('/run/lock/local-llm-amd-p2p-disable.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Preserve active work. Persistent fault-hold files are intentionally untouched.
            if any(Path('/sys/class/kfd/kfd/proc').iterdir()):
                raise RuntimeError('Active KFD clients; preserve their work')
            d = stage() if args.action == 'install' else rollback()
    print(json.dumps(d, indent=2))
    if args.action == 'verify' and (not d['driver_peer_access_disabled'] or not d['boot_options_present']
            or not d['managed_peer_routing_retired'] or d['six_bridge_acs_redirect_restored'] is False
            or d['kfd_gpu_count'] != 2 or d['kfd_gpu_to_gpu_links']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
