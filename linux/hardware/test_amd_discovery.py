"""Regressions for dual AMD discovery and NVIDIA-free backend handover."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import amd_device
import backend_switch
import rocm_runtime


class DiscoveryTests(unittest.TestCase):
    def device(self, root, address, vendor='0x1002', cls='0x030000'):
        d = root / address
        d.mkdir()
        for key, value in {'vendor': vendor, 'class': cls, 'device': '0x744c',
                           'mem_info_vram_total': str(24 * 1024**3)}.items():
            (d / key).write_text(value)
        (d / 'driver').symlink_to(root / 'amdgpu', target_is_directory=True)
        return d

    def test_renumbered_identical_cards_and_unrelated_usb(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            expected = [self.device(root, a) for a in ('0000:03:00.0', '0000:0a:00.0')]
            self.device(root, '0000:06:00.0', '0x1b21', '0x0c0330')
            with patch.object(amd_device, 'PCI_ROOT', root):
                self.assertEqual(amd_device.amd_devices(), expected)

    def test_missing_card_is_blocked(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.device(root, '0000:03:00.0')
            with patch.object(amd_device, 'PCI_ROOT', root), self.assertRaisesRegex(RuntimeError, 'found 1'):
                amd_device.amd_devices()

    def test_no_nvidia_does_not_call_missing_driver(self):
        with patch.object(backend_switch, 'graphics_devices', return_value=[]), \
                patch.object(backend_switch.subprocess, 'run') as run:
            self.assertEqual(backend_switch.gpu_compute_pids(), set())
            run.assert_not_called()

    def busy_second_card(self, used_second, legacy, min_free_gib=21):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            devices = [self.device(root, a) for a in ('0000:03:00.0', '0000:0a:00.0')]
            (devices[0] / 'mem_info_vram_used').write_text('0')
            (devices[1] / 'mem_info_vram_used').write_text(str(used_second))
            with patch.dict(os.environ, {'LOCAL_LLM_LEGACY_RESOURCE_VALIDATION': '1' if legacy else '0'}), \
                    patch.object(rocm_runtime, 'amd_devices', return_value=devices), \
                    patch.object(rocm_runtime.time, 'sleep'):
                rocm_runtime.require_rocm_headroom(min_free_gib)

    def test_busy_second_card_blocks_loading(self):
        # Commit 99ec1b1 (owner-headroom-v1): live floor is 128 MiB free VRAM on each card.
        total, floor = 24 * 1024**3, rocm_runtime.resource_policy.VRAM_RESERVE_BYTES
        self.assertEqual(floor, 128 * 1024**2)
        with self.assertRaisesRegex(RuntimeError, 'each card'):
            self.busy_second_card(total - floor + 1, legacy=False)
        self.busy_second_card(total - floor, legacy=False)

    def test_busy_second_card_blocks_loading_legacy_replay(self):
        # Historical 21 GiB per-card admission, explicit replay opt-in only.
        with self.assertRaisesRegex(RuntimeError, 'each card'):
            self.busy_second_card(5 * 1024**3, legacy=True)

    def test_present_nvidia_still_checks_compute_processes(self):
        xml = '<nvidia_smi_log><gpu><processes><process_info><pid>42</pid><type>C</type></process_info></processes></gpu></nvidia_smi_log>'
        with patch.object(backend_switch, 'graphics_devices', return_value=[Path('/fake')]), \
                patch.object(backend_switch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, xml, '')):
            self.assertEqual(backend_switch.gpu_compute_pids(), {42})


if __name__ == '__main__':
    unittest.main()
