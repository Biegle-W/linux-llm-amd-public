"""CPU regressions for short benchmarks and the unchanged real-time swap gate."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('BENCHMARK_TEST_ROOT', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT/'hardware'))
from swap_activity import SwapActivity, validate_summary

source = Path(os.environ.get('BENCHMARK_TEST_SOURCE', ROOT/'hardware/benchmark-current-amd.py'))
spec = importlib.util.spec_from_file_location('benchmark_window_test_target', source)
bench = importlib.util.module_from_spec(spec)
bench.__file__ = str(ROOT/'hardware/benchmark-current-amd.py')
spec.loader.exec_module(bench)


class Monitor:
    def __init__(self, now):
        self.now = now
        self.activity = SwapActivity()

    def sample(self):
        self.activity.observe(dict(timestamp=self.now[0], swapin_bytes=0,
            swapout_bytes=0, available_bytes=8*1024**3, memory_full_psi_avg10=0),
            'inference', 0)


class EvidenceWindowTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'loading-swap-v4'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def monitor(self, seconds):
        now = [0.0]
        monitor = Monitor(now)
        for second in range(seconds+1):
            now[0] = float(second)
            monitor.sample()
        return now, monitor

    def test_short_real_work_closes_original_thirty_second_gate(self):
        now, monitor = self.monitor(21)
        self.assertIn('no_inference_window', validate_summary(monitor.activity.summary(), require_inference=True))
        calls = []
        def work(*args, **kwargs):
            calls.append(kwargs['limit'])
            now[0] += 2
            return {'usage': {'completion_tokens': 128}}, 'generated text'
        with patch.object(bench, 'time', SimpleNamespace(monotonic=lambda: now[0])), patch.object(bench, 'stream', work):
            probes = bench.complete_inference_window('vllm', 'fast-model', monitor)
        self.assertTrue(calls)
        self.assertEqual(len(calls), len(probes))
        self.assertGreaterEqual(now[0], 30)
        self.assertEqual(validate_summary(monitor.activity.summary(), require_inference=True), [])

    def test_complete_window_does_not_add_work(self):
        now, monitor = self.monitor(31)
        with patch.object(bench, 'time', SimpleNamespace(monotonic=lambda: now[0])), patch.object(bench, 'stream', side_effect=AssertionError('unnecessary work')):
            self.assertEqual(bench.complete_inference_window('vllm', 'covered', monitor), [])

    def test_invalid_telemetry_stays_a_failure(self):
        now, monitor = self.monitor(21)
        monitor.activity.observe(None, 'inference')
        with patch.object(bench, 'time', SimpleNamespace(monotonic=lambda: now[0])), patch.object(bench, 'stream', side_effect=AssertionError('work after invalid evidence')):
            with self.assertRaisesRegex(AssertionError, 'Invalid swap telemetry'):
                bench.complete_inference_window('vllm', 'invalid', monitor)

    def test_missing_window_is_bounded_and_never_fabricated(self):
        now = [0.0]
        monitor = SimpleNamespace(activity=SimpleNamespace(summary=lambda: {'inference_window_samples': 0}, failures=lambda: []), sample=lambda: None)
        def work(*args, **kwargs):
            now[0] += 20
            return {'usage': {'completion_tokens': 128}}, 'generated text'
        with patch.object(bench, 'time', SimpleNamespace(monotonic=lambda: now[0])), patch.object(bench, 'stream', work):
            with self.assertRaisesRegex(AssertionError, 'No complete inference observation window'):
                bench.complete_inference_window('vllm', 'missing', monitor)


if __name__ == '__main__':
    unittest.main()
