"""CPU-only primary-GPU policy tests; never install rules or restart a session."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('desktop_primary_test', ROOT/'hardware/desktop_primary.py')
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)


class DesktopPrimaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def device(self, address, vendor='0x1002', device='0x744c', kind='0x030000',
               driver='amdgpu', gib=24):
        p = self.root/address
        p.mkdir()
        for name, value in [('vendor', vendor), ('device', device), ('class', kind),
                            ('mem_info_vram_total', str(gib*1024**3))]:
            (p/name).write_text(value)
        (p/'driver').symlink_to(self.root/'drivers'/driver)
        return p

    def test_first_amd_is_pci_order_not_creation_order_or_intel(self):
        self.device('0000:06:00.0')
        self.device('0000:00:02.0', '0x8086', '0xa780', driver='i915')
        self.device('0000:03:00.0')
        self.assertEqual(desktop.first_amd(self.root), '0000:03:00.0')

    def test_amd_audio_function_is_not_a_graphics_card(self):
        self.device('0000:03:00.0'); self.device('0000:06:00.0')
        self.device('0000:03:00.1', device='0xab30', kind='0x040300')
        self.assertEqual(desktop.first_amd(self.root), '0000:03:00.0')

    def test_missing_card_fails_closed(self):
        self.device('0000:03:00.0')
        with self.assertRaisesRegex(RuntimeError, 'exactly two'):
            desktop.first_amd(self.root)

    def test_unexpected_third_card_fails_closed(self):
        for address in ['0000:03:00.0','0000:06:00.0','0000:09:00.0']:
            self.device(address)
        with self.assertRaisesRegex(RuntimeError, 'exactly two'):
            desktop.first_amd(self.root)

    def test_wrong_driver_fails_closed(self):
        self.device('0000:03:00.0'); self.device('0000:06:00.0', driver='vfio-pci')
        with self.assertRaisesRegex(RuntimeError, 'amdgpu'):
            desktop.first_amd(self.root)

    def test_wrong_gpu_model_fails_closed(self):
        self.device('0000:03:00.0'); self.device('0000:06:00.0', device='0x1234')
        with self.assertRaisesRegex(RuntimeError, 'Navi31'):
            desktop.first_amd(self.root)

    def test_small_vram_fails_closed(self):
        self.device('0000:03:00.0'); self.device('0000:06:00.0', gib=16)
        with self.assertRaisesRegex(RuntimeError, '24 GB'):
            desktop.first_amd(self.root)

    def test_rule_selects_only_one_identical_amd_and_clears_old_exclusions(self):
        rule = desktop.make_rule('0000:03:00.0')
        self.assertEqual(rule.count('TAG+="mutter-device-preferred-primary"'), 1)
        self.assertIn('KERNELS=="0000:03:00.0"', rule)
        self.assertIn('TAG-="mutter-device-ignore"', rule)
        self.assertIn('/dev/dri/renderD[0-9]*', rule)
        self.assertNotIn('@AMD_PRIMARY_PCI@', rule)

    def test_invalid_pci_rule_data_is_refused(self):
        for value in ['0000:03:00.0"', '*', '0000:03:00.0\nRUN+="bad"']:
            with self.assertRaises(ValueError):
                desktop.make_rule(value)


if __name__ == '__main__':
    unittest.main()
