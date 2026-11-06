"""CPU-only kernel admission: reject before handover, preserve working owners."""
from pathlib import Path
import sys
import importlib
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import inference_kernel as kernel
import backend_switch


class KernelAdmissionTests(unittest.TestCase):
    def test_stock_rejected_without_reading_module(self):
        with patch.object(kernel.platform, 'release', return_value='7.0.0-42-generic'), \
             patch.object(Path, 'read_text') as read:
            with self.assertRaisesRegex(RuntimeError, 'Boot the installed inference kernel'):
                kernel.require_inference_kernel()
            read.assert_not_called()

    def test_exact_running_pair_admitted(self):
        with patch.object(kernel.platform, 'release', return_value=kernel.REQUIRED_RELEASE), \
             patch.object(Path, 'read_text', return_value=kernel.REQUIRED_AMDGPU_SRCVERSION + '\n'):
            kernel.require_inference_kernel()

    def test_wrong_or_unreadable_loaded_module_rejected(self):
        with patch.object(kernel.platform, 'release', return_value=kernel.REQUIRED_RELEASE):
            for value in ('wrong', OSError('unreadable')):
                with self.subTest(value=str(value)), patch.object(Path, 'read_text', **(
                        {'side_effect': value} if isinstance(value, Exception) else {'return_value': value})):
                    with self.assertRaises(RuntimeError):
                        kernel.require_inference_kernel()

    def test_rejected_handover_never_stops_or_creates_owner_state(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(kernel.platform, 'release', return_value='stock'), \
             patch.object(backend_switch, 'stop_other_backends') as stop:
            root = Path(directory)
            with self.assertRaises(RuntimeError):
                with backend_switch.startup_handover('maya', root):
                    self.fail('Rejected kernel reached startup')
            stop.assert_not_called()
            self.assertFalse((root / 'dsh/data').exists())

    def test_direct_backend_admission_rejects_stock_before_profile_or_hardware_checks(self):
        entries = [('llama_runtime', 'launch_spec', ()),
                   ('maya_runtime', 'require_maya', ()),
                   ('strata_runtime', 'require_strata', ()),
                   ('rocm_runtime', 'require_rocm_headroom', ()),
                   ('qualified_native_runtime', 'require_profile', ({}, {}))]
        with patch.object(kernel.platform, 'release', return_value='stock'):
            for module, function, args in entries:
                with self.subTest(backend=module):
                    with self.assertRaisesRegex(RuntimeError, 'Boot the installed inference kernel'):
                        getattr(importlib.import_module(module), function)(*args)

    def test_updater_defers_stock_before_client_or_gpu_checks(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('kernel_gate_daily', root / 'hardware/daily-update/daily_update.py')
        daily = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(daily)
        with patch.object(kernel.platform, 'release', return_value='stock'), \
             patch.object(daily.subprocess, 'run') as run:
            self.assertIn('Boot the installed inference kernel', daily.busy())
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
