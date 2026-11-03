#!/usr/bin/env python3
"""Generate a GNOME preference for the first validated AMD inference GPU."""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
from amd_device import graphics_devices


def first_amd(pci_root=Path('/sys/bus/pci/devices')):
    devices = graphics_devices('0x1002', pci_root)
    if len(devices) != 2:
        raise RuntimeError('Expected exactly two AMD graphics devices; no rule written.')
    for device in devices:
        if ((device / 'device').read_text().strip() != '0x744c'
                or (device / 'driver').resolve().name != 'amdgpu'
                or int((device / 'mem_info_vram_total').read_text()) < 23 * 1024**3):
            raise RuntimeError('Expected two amdgpu Navi31 24 GB cards; no rule written.')
    return devices[0].name


def make_rule(pci):
    if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', pci):
        raise ValueError('Invalid PCI address.')
    template = Path(__file__).with_name('63-local-llm-amd-primary.rules.in').read_text()
    return template.replace('@AMD_PRIMARY_PCI@', pci)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-rule', type=Path, help='Write the generated rule, without installing it')
    args = parser.parse_args()
    pci = first_amd()
    if args.write_rule:
        args.write_rule.write_text(make_rule(pci))
    else:
        print(json.dumps({'primary_amd_pci': pci, 'selection': 'first validated AMD in PCI order',
                          'changes_firmware_boot_GPU': False, 'restarts_desktop': False}))


if __name__ == '__main__':
    main()
