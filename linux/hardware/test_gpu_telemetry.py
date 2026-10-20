"""CPU-only ABI, missing-sensor, lifecycle and benchmark-hook checks."""
import importlib.util
import json
from pathlib import Path
import runpy
import struct
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dsh'))
from gpu_telemetry import ThermalRecorder, decode_metrics, record_request, snapshot


def metrics(mask=0):
    data = bytearray(120)
    struct.pack_into('<HBB', data, 0, 120, 1, 3)
    struct.pack_into('<I', data, 68, 2)
    struct.pack_into('<Q', data, 112, mask)
    return data


class ThermalTests(unittest.TestCase):
    def test_masks_separate_heat_power_and_current(self):
        decoded = decode_metrics(metrics((1<<36)|(1<<2)|(1<<17)))
        self.assertTrue(decoded['hotspot_limit'])
        self.assertTrue(decoded['thermal_limit'])
        self.assertTrue(decoded['power_limit'])
        self.assertTrue(decoded['current_limit'])
        self.assertEqual(decoded['asic_mask'], '0x2')
        power = decode_metrics(metrics(1))
        self.assertTrue(power['power_limit'])
        self.assertFalse(power['thermal_limit'])

    def test_unknown_abi_and_sentinels_are_not_false_healthy(self):
        for data in [b'', metrics()[:112], metrics(2**64-1)]:
            self.assertIsNone(decode_metrics(data)['thermal_limit'])
        data = metrics()
        data[3] = 4
        self.assertEqual(decode_metrics(data)['status'], 'unsupported_or_truncated_abi')
        self.assertIsNone(decode_metrics(data)['power_limit'])

    def fixture(self, root):
        pci = root/'pci'
        for address in ['0000:06:00.0','0000:03:00.0']:
            device = pci/address
            hw = device/'hwmon/hwmon3'
            hw.mkdir(parents=True)
            values = {'vendor':'0x1002','class':'0x030000','gpu_busy_percent':'80'}
            for key, value in values.items():
                (device/key).write_text(value)
            (device/'gpu_metrics').write_bytes(metrics(1<<36))
            for key, value in {'temp1_input':'55000','temp1_label':'edge',
                               'temp2_input':'87000','temp2_label':'junction',
                               'temp3_input':'65535000','temp3_label':'mem',
                               'power1_average':'210000000','freq1_input':'2200000000',
                               'fan1_input':'1500'}.items():
                (hw/key).write_text(value)
        return pci

    def test_units_pci_order_and_missing_or_invalid_sensors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci = self.fixture(root)
            sample = snapshot(pci, root/'cpu')
            self.assertEqual([g['pci'] for g in sample['cards']], ['0000:03:00.0','0000:06:00.0'])
            gpu = sample['cards'][0]
            self.assertEqual(gpu['temperature_c']['junction'], 87)
            self.assertIsNone(gpu['temperature_c']['mem'])
            self.assertEqual(gpu['power_average_w'], 210)
            self.assertEqual(gpu['gfx_clock_mhz'], 2200)
            self.assertIsNone(gpu['memory_clock_mhz'])

    def test_recorder_persists_partial_and_complete_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci = self.fixture(root)
            recorder = ThermalRecorder('test', directory=root/'logs', pci_root=pci,
                                       hwmon_root=root/'cpu', interval=60).start()
            live = json.loads(recorder.summary_path.read_text())
            self.assertEqual(live['status'], 'recording')
            result = recorder.stop()
            gpu = result['cards']['0000:03:00.0']
            self.assertEqual(gpu['peak_temperature_c']['junction'], 87)
            self.assertEqual(gpu['peak_busy_temperature_c']['junction'], 87)
            self.assertEqual(gpu['thermal_limit_samples'], result['samples'])
            self.assertGreaterEqual(result['samples'], 2)
            self.assertEqual(json.loads(recorder.summary_path.read_text())['status'], 'complete')
            self.assertFalse(recorder._thread.is_alive())
            self.assertEqual(recorder.raw_path.stat().st_mode & 0o777, 0o600)
            for line in recorder.raw_path.read_text().splitlines():
                self.assertEqual(len(json.loads(line)['cards']), 2)

    def test_raw_cap_keeps_updating_peaks_without_overwriting_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci = self.fixture(root)
            with ThermalRecorder('same', directory=root/'logs', pci_root=pci,
                                 hwmon_root=root/'cpu', interval=60, max_raw_bytes=1) as first:
                pass
            with ThermalRecorder('same', directory=root/'logs', pci_root=pci,
                                 hwmon_root=root/'cpu', interval=60) as second:
                pass
            self.assertNotEqual(first.raw_path, second.raw_path)
            result = first.summary()
            self.assertEqual(result['raw_samples_dropped'], result['samples'])
            self.assertEqual(result['cards']['0000:03:00.0']['peak_temperature_c']['junction'], 87)

    def test_read_and_write_failure_does_not_stop_the_workload(self):
        with tempfile.TemporaryDirectory() as tmp:
            recorder = ThermalRecorder('unwritable', directory=Path(tmp)/'logs')
            with patch('gpu_telemetry.os.open', side_effect=PermissionError):
                recorder.start()
            self.assertEqual(recorder.stop()['status'], 'logging_unavailable')
            recorder = ThermalRecorder('read-error', directory=Path(tmp)/'logs', interval=60)
            with patch('gpu_telemetry.snapshot', side_effect=OSError):
                with recorder:
                    pass
            self.assertEqual(recorder.summary()['status'], 'complete_with_errors')
            self.assertGreater(recorder.summary()['sample_errors'], 0)

    def test_unavailable_throttle_stays_null_in_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci = self.fixture(root)
            for device in pci.iterdir():
                (device/'gpu_metrics').unlink()
            with ThermalRecorder('unknown', directory=root/'logs', pci_root=pci,
                                 hwmon_root=root/'cpu', interval=60) as recorder:
                pass
            gpu = recorder.summary()['cards']['0000:03:00.0']
            self.assertIsNone(gpu['thermal_limit_samples'])
            self.assertEqual(gpu['throttle_samples_available'], 0)

    def test_benchmark_hook_preserves_timing_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = ThermalRecorder
            with patch('gpu_telemetry.ThermalRecorder', side_effect=lambda label: real(label, directory=root/'logs', pci_root=root/'pci', hwmon_root=root/'cpu')):
                @record_request
                def request(kind, model):
                    return {'ttft_seconds': 0.123, 'decode_tps_sse': 78.9}, 'unchanged'
                record, text = request('test', 'model')
            self.assertEqual(record['ttft_seconds'], 0.123)
            self.assertEqual(record['decode_tps_sse'], 78.9)
            self.assertEqual(text, 'unchanged')
            self.assertEqual(record['thermal']['status'], 'complete')

    def test_pid_observer_checks_start_time_and_zombies(self):
        script = Path(__file__).with_name('log-gpu-temps.py')
        spec = importlib.util.spec_from_file_location('thermal_cli', script)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        running = '42 (name with spaces) S ' + ' '.join(['0']*18+['12345'])
        with patch.object(Path, 'read_text', return_value=running):
            self.assertEqual(cli.process_identity(42), '12345')
        with patch.object(Path, 'read_text', return_value=running.replace(') S ', ') Z ')):
            self.assertIsNone(cli.process_identity(42))

    def test_launcher_stops_its_collector_if_backend_spawn_fails(self):
        root = Path(__file__).resolve().parents[1]
        recorder = MagicMock()
        with patch.object(sys, 'argv', ['launch-backend.py','llama']), \
             patch('llama_runtime.launch_spec', return_value=(Path('/fake/bin'),Path('/fake/preset'),{},None)), \
             patch('shared_storage.ensure_llama_models'), \
             patch('backend_switch.startup_handover'), \
             patch('backend_switch.clear_owner'), \
             patch('backend_guard.require_worker_ports_free'), \
             patch('terminal_logs.start_monitor'), \
             patch('terminal_logs.stop_monitor'), \
             patch('native_frontend.start_frontend'), \
             patch('gpu_telemetry.ThermalRecorder') as factory, \
             patch('subprocess.Popen', side_effect=OSError('test spawn failure')), \
             patch('signal.signal'), \
             patch.object(Path, 'open', mock_open()), \
             self.assertRaises(SystemExit):
            factory.return_value.start.return_value = recorder
            runpy.run_path(str(root/'dsh/launch-backend.py'),run_name='__main__')
        factory.assert_called_once_with('backend-llama')
        recorder.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
