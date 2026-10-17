#!/usr/bin/env python3
"""Read PCIe/HIP peer capability without changing drivers or allocating GPU buffers."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def hip_probe(library):
    hip = ctypes.CDLL(str(library))
    count = ctypes.c_int()
    status = hip.hipGetDeviceCount(ctypes.byref(count))
    result = {'device_count': count.value, 'device_count_status': status, 'pairs': []}
    if status:
        return result
    for source in range(count.value):
        for target in range(count.value):
            if source == target:
                continue
            capable = ctypes.c_int()
            status = hip.hipDeviceCanAccessPeer(ctypes.byref(capable), source, target)
            result['pairs'].append({'from': source, 'to': target,
                                    'status': status, 'peer_access': bool(capable.value)})
    return result


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, PermissionError):
        return None


def pci_snapshot():
    rows = []
    for dev in sorted(Path('/sys/bus/pci/devices').iterdir()):
        vendor = read(dev / 'vendor')
        cls = read(dev / 'class') or ''
        if vendor != '0x1002' or not cls.startswith(('0x0300', '0x0302')):
            continue
        resource = (dev / 'resource').read_text().splitlines()[0].split()
        start, end = (int(x, 16) for x in resource[:2])
        parents = [p.name for p in dev.resolve().parents if (p / 'vendor').is_file()]
        rows.append({'pci': dev.name, 'vendor': vendor, 'device': read(dev / 'device'),
                     'bar0_bytes': end - start + 1, 'upstream_pci_devices': parents})
    return rows


def inspect(library):
    cpu = next((line.split(':', 1)[1].strip() for line in
                Path('/proc/cpuinfo').read_text().splitlines()
                if line.startswith('model name')), None)
    result = {'kernel': platform.release(), 'cpu': cpu,
              'board': read('/sys/class/dmi/id/board_name'),
              'amdgpu_pcie_p2p': read('/sys/module/amdgpu/parameters/pcie_p2p'),
              'gpus': pci_snapshot(), 'capability_cases': []}
    config = read('/boot/config-' + platform.release()) or ''
    keys = ('CONFIG_PCI_P2PDMA=', 'CONFIG_HSA_AMD_P2P=', 'CONFIG_DMABUF_MOVE_NOTIFY=')
    result['kernel_p2p_config'] = [line for line in config.splitlines() if line.startswith(keys)]
    root = Path('/sys/bus/pci/devices/0000:00:00.0')
    result['host_bridge'] = {'vendor': read(root / 'vendor'), 'device': read(root / 'device')}
    topology = Path('/sys/class/kfd/kfd/topology/nodes')
    result['kfd_gpu_links'] = []
    for node in sorted(topology.glob('*')):
        if read(node / 'gpu_id') in (None, '0'):
            continue
        links = []
        for link in sorted((node / 'io_links').glob('*/properties')):
            links.append(dict(line.split() for line in link.read_text().splitlines()))
        result['kfd_gpu_links'].append({'node': int(node.name), 'io_links': links})
    for label, settings in [('default', {}),
                            ('fine_grain_pcie', {'HSA_FORCE_FINE_GRAIN_PCIE': '1'}),
                            ('fine_grain_no_sdma', {'HSA_FORCE_FINE_GRAIN_PCIE': '1',
                                                    'HSA_ENABLE_SDMA': '0'})]:
        env = dict(os.environ)
        for name in ('NCCL_P2P_DISABLE', 'HSA_FORCE_FINE_GRAIN_PCIE', 'HSA_ENABLE_SDMA'):
            env.pop(name, None)
        env.update(settings)
        child = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                '--hip-library', str(library), '--hip-child'],
                               env=env, capture_output=True, text=True, timeout=30)
        if child.returncode:
            raise RuntimeError(f'{label}: HIP capability probe failed (exit {child.returncode})')
        result['capability_cases'].append({'name': label, 'environment': settings,
                                           **json.loads(child.stdout)})
    result['transfer_validation'] = 'Not performed: this is a capability-only diagnostic.'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hip-library', type=Path,
                        default=ROOT / 'llm-tools/rocm-sdk/opt/rocm-7.2.3/lib/libamdhip64.so')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--hip-child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    value = hip_probe(args.hip_library) if args.hip_child else inspect(args.hip_library)
    output = json.dumps(value, indent=2) + '\n'
    if args.output:
        args.output.write_text(output)
    print(output, end='')
