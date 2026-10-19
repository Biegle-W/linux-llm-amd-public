"""Inventory regressions: distinguish the target GPUs and upstream PCI links."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('upgrade_inventory', Path(__file__).with_name('check-upgrade.py'))
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


class InventoryTests(unittest.TestCase):
    def test_missing_inadequate_or_unbound_second_card_does_not_report_ready(self):
        good = dict(vendor='0x1002', device_id='0x744c', driver='amdgpu', mem_info_vram_total=24 * 1024**3)
        self.assertTrue(upgrade.is_target_pair([good, good.copy()]))
        for second in (None, dict(good, vendor='0x10de'),
                       dict(good, mem_info_vram_total=12 * 1024**3),
                       dict(good, driver='vfio-pci')):
            with self.subTest(second=second):
                self.assertFalse(upgrade.is_target_pair([good] + ([second] if second else [])))

    def test_endpoint_x16_does_not_hide_upstream_x8(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = root / 'pci0000:00' / '0000:00:01.0'
            endpoint = parent / '0000:03:00.0'
            endpoint.mkdir(parents=True)
            (parent / 'current_link_width').write_text('8\n')
            (endpoint / 'current_link_width').write_text('16\n')
            alias = root / 'device'
            alias.symlink_to(endpoint)
            self.assertEqual([(p['pci'], p['current_link_width']) for p in upgrade.pci_path(alias)],
                             [('0000:00:01.0', '8'), ('0000:03:00.0', '16')])


if __name__ == '__main__':
    unittest.main()
