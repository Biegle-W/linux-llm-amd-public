"""Discover the two AMD inference devices without relying on a PCI bus number."""
from pathlib import Path

PCI_ROOT = Path('/sys/bus/pci/devices')


def graphics_devices(vendor, pci_root=None):
    root = PCI_ROOT if pci_root is None else Path(pci_root)
    devices = []
    for device in sorted(root.iterdir()):
        if ((device / 'vendor').read_text().strip() == vendor
                and int((device / 'class').read_text().strip(), 16) >> 16 == 0x03):
            devices.append(device)
    return devices


def amd_devices():
    devices = graphics_devices('0x1002')
    if len(devices) != 2:
        raise RuntimeError('Expected two AMD GPUs for the dual-card profiles; '
                           f'found {len(devices)}. Device selection must be validated '
                           'before handover. No backend has been stopped.')
    for device in devices:
        if ((device / 'device').read_text().strip() != '0x744c'
            or (device / 'driver').resolve().name != 'amdgpu'
            or int((device / 'mem_info_vram_total').read_text()) < 23 * 1024**3):
            raise RuntimeError('The detected AMD device is not the expected 24 GB Navi 31 GPU.')
    return devices
