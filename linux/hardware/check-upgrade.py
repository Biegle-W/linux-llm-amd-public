#!/usr/bin/env python3
"""Read-only upgrade inventory. Never loads weights, installs drivers or stops jobs."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from hardware_guard import nvidia_inventory


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
            cards.append(card)
        except (OSError, ValueError):
            continue
    try:
        nvidia, error = nvidia_inventory(), None
    except RuntimeError as exc:
        nvidia, error = [], str(exc)
    # Navi31's PCI ID covers multiple products; 24 GiB VRAM distinguishes this target.
    amd = [c for c in cards if c['vendor'] == '0x1002' and c['device_id'] == '0x744c'
           and c.get('mem_info_vram_total', 0) >= 23 * 1024**3 and c['driver'] == 'amdgpu']
    target = bool(amd and len(nvidia) == 1 and 'RTX 4070' in nvidia[0]['name'])
    return {
        'target_hardware_detected': target,
        'system_memory_bytes': mem['MemTotal'],
        'available_memory_bytes': mem['MemAvailable'],
        'swap_used_bytes': mem['SwapTotal'] - mem['SwapFree'],
        'pci_gpus': cards, 'nvidia': nvidia, 'nvidia_error': error,
        'kfd_read_write': os.access('/dev/kfd', os.R_OK | os.W_OK),
        'render_nodes': [{'node': p.name, 'read_write': os.access(p, os.R_OK | os.W_OK)}
                         for p in sorted(Path('/dev/dri').glob('renderD*'))],
        'vulkan_server_built': (ROOT / 'llama.cpp/build-vulkan/bin/llama-server').is_file(),
        'hip_server_built': (ROOT / 'llama.cpp/build-hip/bin/llama-server').is_file(),
        'strata_hip_built': (ROOT / 'strata/build-hip/strata').is_file(),
        'strata_mmap_experts_present': Path('/mnt/llm-models/Strata/packs/iq3_xxs/experts.bin').is_file(),
        'active_amd_launcher_configured': (ROOT / 'dsh/llama-runtime.json').exists() and json.loads((ROOT / 'dsh/llama-runtime.json').read_text()).get('backend') in ('vulkan-amd', 'hip-amd'),
        'inference_validation_report': 'hardware/LLAMA-MIGRATION-2026-10-16.md',
        'rocm_profiles': {kind: {key: {'runtime': value.get('runtime', 'cuda'),
                                     'context': value['context']}
                               for key, value in json.loads((ROOT / 'dsh' / (kind + '-profiles.json')).read_text()).items()}
                          for kind in ('sglang', 'vllm')},
        'rocm_validation_report': 'hardware/rocm-2026-10-16/README.md',
        'note': 'Inventory only. Follow hardware/UPGRADE-7900XTX-4070.md for driver and inference validation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = inventory()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('RX 7900 XTX + RTX 4070 upgrade readiness')
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
    sys.exit(0 if report['target_hardware_detected'] else 2)
