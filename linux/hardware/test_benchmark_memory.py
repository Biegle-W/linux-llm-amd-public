"""CPU-only execution of the benchmark collector; no sockets, GPU or models."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'hardware'))
sys.path.insert(0, str(ROOT/'dsh'))
import inference_memory as mem

spec = importlib.util.spec_from_file_location('benchmark_memory_test', ROOT/'hardware/benchmark-current-amd.py')
assert spec is not None and spec.loader is not None
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)
GIB = 1024**3
SCRATCH = Path(tempfile.gettempdir())


class BenchmarkCollector(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ, {'LOCAL_LLM_LEGACY_SWAP_VALIDATION':'1'})
        env.start();self.addCleanup(env.stop)

    def compare(self, result):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            path = Path(directory)/'controlled-collector-fixture.json'
            path.write_text(json.dumps(result))
            return subprocess.run([sys.executable, '-B', str(ROOT/'hardware/compare-runtime-candidate.py'),
                                   '--baseline', str(path), str(path)], capture_output=True, text=True,
                                  env={**os.environ, 'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1'})

    def exercise(self, models=('first',), step=5, smoke_text='323', fail_at=None, spill=0,
                 missing_workers=False, policy='low-churn-v1'):
        monitors, events, calls = [], [], []
        host_seen = threading.Event()
        clock = {'time': 0}

        class ControlledMonitor(mem.MemoryMonitor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                monitors.append(self)
                self.started = False
                self.stopped = None

            def start(self):
                super().start()
                self.thread.join(5)
                self.started = True
                events.append('memory-start')
                self.sample()
                return self

            def stop(self):
                events.append(('memory-stop', self.phase))
                self.stopped = super().stop()
                return self.stopped

        class Thermal:
            def __init__(self, label):
                events.append(('thermal', label))

            def start(self):
                events.append('thermal-start')
                return self

            def stop(self):
                events.append('thermal-stop')
                return {'fixture': True}

        def host_activity():
            clock['time'] += step
            return dict(timestamp=clock['time'], swapin_bytes=0, swapout_bytes=0,
                        available_bytes=8*GIB, memory_full_psi_avg10=0.0)

        def host_memory():
            host_seen.set()
            return 16*GIB, 8*GIB

        def stream(kind, model, prompt, **kwargs):
            calls.append((model, prompt, kwargs))
            smoke = prompt.startswith('What is 17 times 19?')
            events.append(('request', model, 'smoke' if smoke else 'observation',
                           monitors[-1].phase if monitors else None))
            if not smoke:
                self.assertTrue(host_seen.wait(5), 'host/VRAM collector did not start')
                if monitors and monitors[-1].started:
                    monitors[-1].sample()
            if fail_at == len(calls):
                raise OSError('controlled request failure')
            trial = {'usage': {'completion_tokens': 128, 'prompt_tokens': 8192},
                     'ttft_seconds': 1.0, 'decode_tps_sse': 100.0,
                     'cached_tokens': 0, 'prefill_native_tps': 200.0}
            return trial, smoke_text if smoke else 'ALPHA-734 BRAVO-915 CHARLIE-268'

        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory, \
             patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': policy}), \
             patch.object(mem.MemoryMonitor, '_run', return_value=None), \
             patch.object(mem, 'sample_memory', return_value=None if missing_workers else dict(swap=GIB, spill=spill)), \
             patch.object(mem, 'read_host_activity', side_effect=host_activity), \
             patch.object(benchmark, 'MemoryMonitor', ControlledMonitor, create=True), \
             patch.object(benchmark, 'sample_memory', return_value=dict(swap=17, spill=0), create=True), \
             patch.object(benchmark, 'host_memory', side_effect=host_memory), \
             patch.object(benchmark, 'vram_snapshot', return_value=[dict(used=3*GIB), dict(used=4*GIB)]), \
             patch.object(benchmark, 'ThermalRecorder', Thermal), \
             patch.object(benchmark, 'amd_devices'), \
             patch.object(benchmark, 'profiles', return_value=[(m, 32768) for m in models]), \
             patch.object(benchmark, 'prefill_prompt', side_effect=lambda index: f'marker fixture {index}'), \
             patch.object(benchmark, 'stream', side_effect=stream):
            output = Path(directory)/'benchmark.json'
            with patch.object(sys, 'argv', ['benchmark-current-amd.py', '--kind', 'vllm',
                                          '--output', str(output)]):
                exit_code = 0
                try:
                    benchmark.main()
                except SystemExit as error:
                    exit_code = error.code
            result = json.loads(output.read_text())
        return result, monitors, events, calls, exit_code

    def test_profile_serializes_same_real_monitors_activity_and_peaks_without_changing_trials(self):
        result, monitors, events, calls, exit_code = self.exercise()
        self.assertEqual(exit_code, 0)
        profile = result['profiles'][0]
        memory = profile['memory']
        self.assertIn('swap_activity', memory)
        self.assertEqual(len(monitors), 1)
        monitor = monitors[0]
        for field in ('swap_activity', 'max_worker_swap_bytes', 'max_nonresident_vram_bytes',
                      'worker_samples', 'sampling_errors'):
            self.assertEqual(memory[field], monitor.stopped[field])
        self.assertEqual(memory['max_worker_swap_bytes'], GIB)
        self.assertEqual(memory['swap_activity']['worker_swap_peak_bytes'], GIB)
        with patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'}):
            self.assertEqual(mem.memory_failures(memory), [])
        self.assertEqual(profile['status'], 'passed')
        self.assertEqual([len(profile['short'][task]['trials']) for task in ('code', 'prose')], [3, 3])
        self.assertEqual(len(profile['prefill']), 3)
        self.assertEqual(profile['marker_checks_passed'], 3)
        self.assertEqual(len(calls), 12)  # arithmetic + two warmups + six timed + three prefill
        self.assertEqual(memory['peak_vram_gib'], [3.0, 4.0])
        self.assertEqual(memory['minimum_available_gib'], 8.0)
        self.assertIn(('memory-stop', 'shutdown'), events)
        self.assertEqual(events[-1], 'thermal-stop')
        self.assertFalse(monitor.thread.is_alive())
        self.assertTrue(monitor.done.is_set())
        comparison = self.compare(result)
        self.assertEqual(comparison.returncode, 0, comparison.stdout + comparison.stderr)

    def test_missing_workers_cannot_be_replaced_by_host_and_vram_samples(self):
        for policy in ('low-churn-v1', 'bounded-64mib'):
            with self.subTest(policy=policy):
                result, monitors, events, calls, exit_code = self.exercise(missing_workers=True, policy=policy)
                self.assertEqual(exit_code, 1)
                self.assertEqual(result['profiles'][0]['status'], 'failed')
                self.assertEqual(result['profiles'][0]['memory']['worker_samples'], 0)
                self.assertIn(('memory-stop', 'shutdown'), events)

    def test_short_profiles_use_real_untimed_observation_and_preserve_timed_trials(self):
        result, monitors, events, calls, exit_code = self.exercise(models=('first', 'second'), step=2)
        self.assertEqual(exit_code, 0)  # Real untimed requests now close the existing observation window.
        self.assertEqual(len(monitors), 2)
        self.assertIsNot(monitors[0], monitors[1])
        with patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'}):
            for profile, monitor in zip(result['profiles'], monitors):
                memory = profile['memory']
                self.assertGreaterEqual(memory['swap_activity']['inference_window_samples'], 1)
                self.assertGreaterEqual(memory['swap_activity']['elapsed_seconds'], 30)
                self.assertEqual(mem.memory_failures(memory), [])
                self.assertTrue(profile['memory_observation_probes'])
                self.assertEqual([len(profile['short'][task]['trials'])for task in ('code','prose')],[3,3])
                self.assertEqual(len(profile['prefill']),3)
                self.assertEqual(memory['swap_activity'], monitor.stopped['swap_activity'])
        requests = [e for e in events if isinstance(e, tuple) and e[0] == 'request']
        self.assertTrue(all(e[3] == 'loading' for e in requests if e[2] == 'smoke'))
        self.assertTrue(all(e[3] == 'inference' for e in requests if e[2] == 'observation'))
        self.assertEqual(len(calls),24+sum(len(profile['memory_observation_probes'])for profile in result['profiles']))
        comparison = self.compare(result)
        self.assertEqual(comparison.returncode,0,comparison.stdout+comparison.stderr)

    def test_failed_arithmetic_readiness_never_starts_inference_observation(self):
        result, monitors, events, calls, exit_code = self.exercise(smoke_text='wrong')
        self.assertEqual(exit_code, 1)
        self.assertEqual(result['profiles'][0]['status'], 'failed')
        self.assertNotIn('memory', result['profiles'][0])
        self.assertFalse(monitors[0].started)
        self.assertFalse(monitors[0].thread.is_alive())
        self.assertNotIn('memory-start', events)
        self.assertEqual(events[-1], 'thermal-stop')
        self.assertEqual(len(calls), 1)

    def test_request_failure_still_serializes_observed_memory_and_stops_thermal(self):
        result, monitors, events, calls, exit_code = self.exercise(fail_at=3)
        self.assertEqual(exit_code, 1)
        profile = result['profiles'][0]
        self.assertEqual(profile['status'], 'failed')
        self.assertEqual(profile['error_type'], 'OSError')
        memory = profile['memory']
        for field in ('swap_activity', 'max_worker_swap_bytes', 'max_nonresident_vram_bytes'):
            self.assertEqual(memory[field], monitors[0].stopped[field])
        self.assertIn(('memory-stop', 'shutdown'), events)
        self.assertEqual(events[-1], 'thermal-stop')
        self.assertTrue(monitors[0].done.is_set())
        self.assertFalse(monitors[0].thread.is_alive())
        with patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'}):
            self.assertIn('swap_activity_no_inference_window', mem.memory_failures(memory))

    def test_dedicated_spill_from_the_activity_monitor_still_rejects_profile(self):
        result, monitors, events, calls, exit_code = self.exercise(spill=1)
        self.assertEqual(exit_code, 1)
        profile = result['profiles'][0]
        self.assertEqual(profile['status'], 'failed')
        self.assertEqual(profile['memory']['max_nonresident_vram_bytes'], 1)
        self.assertEqual(profile['memory']['max_nonresident_vram_bytes'],
                         monitors[0].stopped['max_nonresident_vram_bytes'])


if __name__ == '__main__':
    unittest.main()
