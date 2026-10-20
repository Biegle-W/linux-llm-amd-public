#!/usr/bin/env python3
"""Read-only upgrade inventory. Never loads weights, installs drivers or stops jobs."""
import argparse
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def strata_experts_present():
    """Follow the configured pack rather than an obsolete drive location."""
    try:
        args = json.loads((ROOT / 'dsh/strata-iq3-profile.json').read_text())['args']
        return (Path(args[args.index('--pack') + 1]) / 'experts.bin').is_file()
    except (OSError, ValueError, KeyError, IndexError):
        return False


def is_target_pair(cards):
    """Require two actual 24 GiB Navi31 GPUs bound to amdgpu."""
    return sum(c['vendor'] == '0x1002' and c['device_id'] == '0x744c'
               and c.get('mem_info_vram_total', 0) >= 23 * 1024**3
               and c['driver'] == 'amdgpu' for c in cards) == 2


def pci_path(device):
    """Include parent links: the endpoint alone can show a GPU-internal x16 hop."""
    chain = []
    for hop in reversed([device.resolve(), *device.resolve().parents]):
        if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', hop.name):
            continue
        row = {'pci': hop.name}
        for key in ('vendor', 'device', 'class', 'current_link_speed', 'current_link_width'):
            try:
                row[key] = (hop / key).read_text().strip()
            except OSError:
                pass
        chain.append(row)
    return chain


def inventory():
    mem = {line.split(':')[0]: int(line.split()[1]) * 1024
           for line in Path('/proc/meminfo').read_text().splitlines()}
    cards = []
    for device in sorted(Path('/sys/bus/pci/devices').iterdir()):
        try:
            if int((device / 'class').read_text(), 16) >> 16 != 3:
                continue
            vendor = (device / 'vendor').read_text().strip()
            card = {'pci': device.name, 'vendor': vendor,
                    'device_id': (device / 'device').read_text().strip(),
                    'driver': (device / 'driver').resolve().name if (device / 'driver').exists() else None}
            for filename in ('mem_info_vram_total', 'current_link_width', 'max_link_width'):
                path = device / filename
                if path.exists():
                    card[filename] = int(path.read_text())
            card['pci_path'] = pci_path(device)
            cards.append(card)
        except (OSError, ValueError):
            continue
    nvidia = [c for c in cards if c['vendor'] == '0x10de']
    target = is_target_pair(cards)
    return {
        'target_hardware_detected': target,
        'system_memory_bytes': mem['MemTotal'],
        'available_memory_bytes': mem['MemAvailable'],
        'swap_used_bytes': mem['SwapTotal'] - mem['SwapFree'],
        'pci_gpus': cards, 'nvidia': nvidia, 'nvidia_error': None,
        'kfd_read_write': os.access('/dev/kfd', os.R_OK | os.W_OK),
        'render_nodes': [{'node': p.name, 'read_write': os.access(p, os.R_OK | os.W_OK)}
                         for p in sorted(Path('/dev/dri').glob('renderD*'))],
        'vulkan_server_built': (ROOT / 'llama.cpp/build-vulkan/bin/llama-server').is_file(),
        'hip_server_built': (ROOT / 'llama.cpp/build-hip/bin/llama-server').is_file(),
        'maya_hip_built': all((ROOT / 'maya/upstream/build-hip' / name).is_file() for name in ('maya','maya-ds4')),
        'maya_profiles': {k:{'context':v['context'],'enabled':v.get('enabled',False)} for k,v in json.loads((ROOT/'dsh/maya-profiles.json').read_text()).items()} if (ROOT/'dsh/maya-profiles.json').exists() else {},
        'strata_hip_built': (ROOT / 'strata/build-hip/strata').is_file(),
        'strata_mmap_experts_present': strata_experts_present(),
        'active_amd_launcher_configured': (ROOT / 'dsh/llama-runtime.json').exists() and json.loads((ROOT / 'dsh/llama-runtime.json').read_text()).get('backend') in ('vulkan-amd', 'hip-amd'),
        'inference_validation_report': 'hardware/UPGRADE-DUAL-7900XTX.md',
        'rocm_profiles': {kind: {key: {'runtime': value.get('runtime', 'cuda'),
                                     'context': value['context']}
                               for key, value in json.loads((ROOT / 'dsh' / (kind + '-profiles.json')).read_text()).items()}
                          for kind in ('sglang', 'vllm')},
        'rocm_validation_report': 'hardware/RUNTIME-UPGRADE-2026-10-18.md',
        'note': 'Inventory only: dual RX 7900 XTX. Read the full PCI path for slot width; endpoint width may be internal to the GPU. PCIe switch purchased, pending installation and P2P validation. See hardware/PCIE-P2P-2026-10-17.md.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = inventory()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('Dual RX 7900 XTX upgrade readiness')
        print('Target hardware detected:', report['target_hardware_detected'])
        print('Usable system RAM (GiB):', round(report['system_memory_bytes'] / 1024**3, 2))
        print('Available system RAM (GiB):', round(report['available_memory_bytes'] / 1024**3, 2))
        for card in report['pci_gpus']:
            print(' ', card['pci'], card['vendor'], card['device_id'], card['driver'])
        for key in ('kfd_read_write', 'hip_server_built', 'vulkan_server_built', 'strata_hip_built',
                    'strata_mmap_experts_present'):
            print(key + ':', report[key])
        if report['nvidia_error']:
            print(report['nvidia_error'])
        print(report['note'])
    raise SystemExit(0 if report['target_hardware_detected'] else 2)
