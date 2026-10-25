"""CPU-only regressions for bounded worker swap and rollback; no real launcher."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hardware'))
sys.path.insert(0, str(ROOT / 'dsh'))
import inference_memory as mem
from backend_switch import Process

spec = importlib.util.spec_from_file_location('daily_memory_test', ROOT / 'hardware/daily-update/daily_update.py')
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)


def record():
    memory = {'max_worker_swap_bytes': 0, 'max_nonresident_vram_bytes': 0}
    return {'profiles': [{'model': 'test-model', 'status': 'passed', 'summary': {'prefill_tps': 100},
                         'short': {name: {'median_decode_tps': 100, 'median_ttft_seconds': 1}
                                   for name in ('code', 'prose')},
                         'prefill': [{'markers_passed': True}], 'memory': memory}],
            'lifecycle_memory': {**memory, 'worker_samples': 5, 'sampling_errors': 0}}


class Accounting(unittest.TestCase):
    def test_descendants_and_shared_gpu_clients_count_once_and_other_apps_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = {}
            for pid in range(1, 13):
                args = ('python3', str(ROOT / 'dsh/vllm-router.py')) if pid == 1 else ('python3', 'worker.py')
                snapshot[pid] = Process(pid, pid - 1, '1', args, '', 'S')
                base = root / str(pid)
                (base / 'fdinfo').mkdir(parents=True)
                (base / 'status').write_text(f'VmSwap:\t{pid} kB\n')
                (base / 'fdinfo/1').write_text('drm-driver:\tamdgpu\ndrm-pdev:\t0000:03:00.0\n'
                    'drm-client-id:\t12\ndrm-total-vram:\t10 KiB\ndrm-resident-vram:\t8 KiB\n')
            snapshot[99] = Process(99, 0, '1', ('python3', 'training.py'), '', 'S')
            background = root / '99'
            (background / 'fdinfo').mkdir(parents=True)
            (background / 'status').write_text('VmSwap:\t1000000000 kB\n')
            # This background task's swap must not affect the inference reading.
            sample = mem.sample_memory(snapshot, root)
            self.assertEqual(sample, {'swap': sum(range(1, 13)) * 1024, 'spill': 2048, 'processes': 12})

    def test_missing_swap_counter_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '1').mkdir()
            (root / '1/status').write_text('Name:\tworker\n')
            proc = Process(1, 0, '1', ('python3', str(ROOT / 'dsh/vllm-router.py')), '', 'S')
            with self.assertRaises(KeyError):
                mem.sample_memory({1: proc}, root)

    def test_loading_swap_and_sampling_errors_remain_latched(self):
        monitor = mem.MemoryMonitor()
        with patch.object(mem, 'sample_memory', side_effect=[
                {'swap': mem.WORKER_SWAP_LIMIT_BYTES + 1, 'spill': 0},
                {'swap': 0, 'spill': 0}, PermissionError('unreadable')]):
            for _ in range(3):
                monitor.sample()
        self.assertEqual(monitor.summary['max_worker_swap_bytes'], mem.WORKER_SWAP_LIMIT_BYTES + 1)
        self.assertEqual(monitor.summary['sampling_errors'], 1)
        self.assertEqual(mem.lifecycle_failures({'lifecycle_memory': monitor.summary}),
                         ['worker_swap', 'lifecycle_sampling_errors'])

    def test_absent_workers_cannot_supply_zero_evidence(self):
        monitor = mem.MemoryMonitor()
        with patch.object(mem, 'sample_memory', return_value=None):
            monitor.sample()
        self.assertIn('no_lifecycle_worker_samples', mem.lifecycle_failures({'lifecycle_memory': monitor.summary}))

    def test_unexpected_sampler_failure_is_latched_instead_of_killing_monitor(self):
        monitor = mem.MemoryMonitor()
        with patch.object(mem, 'sample_memory', side_effect=IndexError('malformed counter')):
            monitor.sample()
        self.assertEqual(monitor.summary['sampling_errors'], 1)


class Comparator(unittest.TestCase):
    def compare(self, candidate, lifecycle=False):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'baseline.json').write_text(json.dumps(record()))
            (base / 'candidate.json').write_text(json.dumps(candidate))
            command = [sys.executable, str(ROOT / 'hardware/compare-runtime-candidate.py'),
                       '--baseline', str(base / 'baseline.json'), str(base / 'candidate.json')]
            if lifecycle:
                command.append('--require-lifecycle-memory')
            return subprocess.run(command, capture_output=True, text=True)

    def test_zero_swap_and_spill_pass(self):
        result = self.compare(record(), True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_minor_swap_including_limit_passes_per_model_and_lifecycle(self):
        for value in (1, 4096, 33 * 1024**2, mem.WORKER_SWAP_LIMIT_BYTES):
            with self.subTest(value=value):
                candidate = record()
                candidate['profiles'][0]['memory']['max_worker_swap_bytes'] = value
                candidate['lifecycle_memory']['max_worker_swap_bytes'] = value
                result = self.compare(candidate, True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(f'worker_swap_limit_bytes | | {mem.WORKER_SWAP_LIMIT_BYTES}', result.stdout)

    def test_swap_above_limit_rejects_and_prints_amount(self):
        candidate = record()
        value = mem.WORKER_SWAP_LIMIT_BYTES + 1
        candidate['profiles'][0]['memory']['max_worker_swap_bytes'] = value
        result = self.compare(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FAIL: worker_swap', result.stdout)
        self.assertIn(f'max_worker_swap_bytes | | {value}', result.stdout)

    def test_missing_and_invalid_swap_fail_closed(self):
        for value in [None, -1, False, '0', 0.0, 'missing']:
            with self.subTest(value=value):
                candidate = record()
                memory = candidate['profiles'][0]['memory']
                if value == 'missing':
                    memory.pop('max_worker_swap_bytes')
                else:
                    memory['max_worker_swap_bytes'] = value
                result = self.compare(candidate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('worker_swap_telemetry_invalid', result.stdout)

    def test_missing_or_invalid_lifecycle_evidence_rejects(self):
        for field, value in [('worker_samples', 0), ('sampling_errors', 1),
                             ('max_worker_swap_bytes', mem.WORKER_SWAP_LIMIT_BYTES + 1),
                             ('max_nonresident_vram_bytes', 1)]:
            with self.subTest(field=field):
                candidate = record()
                candidate['lifecycle_memory'][field] = value
                self.assertNotEqual(self.compare(candidate, True).returncode, 0)
        candidate = record()
        candidate.pop('lifecycle_memory')
        self.assertNotEqual(self.compare(candidate, True).returncode, 0)

    def test_spill_performance_regression_and_missing_model_still_reject(self):
        for change in ['spill', 'speed', 'missing', 'duplicate']:
            with self.subTest(change=change):
                candidate = record()
                if change == 'spill':
                    candidate['profiles'][0]['memory']['max_nonresident_vram_bytes'] = 1
                elif change == 'speed':
                    candidate['profiles'][0]['short']['code']['median_decode_tps'] = 94
                elif change == 'missing':
                    candidate['profiles'] = []
                else:
                    candidate['profiles'] *= 2
                self.assertNotEqual(self.compare(candidate).returncode, 0)


class Updater(unittest.TestCase):
    def exercise(self, candidate, baseline=None):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            engine = Mock(kind='vllm', name='unused')
            engine.name = 'test engine'
            engine.models.return_value = ['test-model']
            current = ['old']
            engine.install.side_effect = lambda *_: current.__setitem__(0, 'new')
            engine.rollback.side_effect = lambda *_: current.__setitem__(0, 'old')
            engine.current.side_effect = lambda: current[0]
            state = {'engines': {'vllm': {'production': 'old'}}}
            def benchmark(kind, models, stage, label, logfile):
                data = copy.deepcopy((baseline or record()) if label == 'baseline' else candidate)
                (stage / (label + '.json')).write_text(json.dumps(data))
                return data
            with patch.object(daily, 'launcher_bench', side_effect=benchmark), \
                 patch.object(daily, 'save_state'), patch.object(daily, 'stop_backends'), \
                 patch.object(daily, 'smoke', return_value=True) as smoke, patch.object(daily, 'log'):
                result = daily.test_engine(engine, 'old', 'new', stage, state, stage / 'log')
            return result, state, engine, smoke

    def test_swap_candidate_rolls_back_and_smokes_restored_build(self):
        candidate = record()
        candidate['profiles'][0]['memory']['max_worker_swap_bytes'] = mem.WORKER_SWAP_LIMIT_BYTES + 1
        result, state, engine, smoke = self.exercise(candidate)
        self.assertEqual(result['result'], 'rejected')
        self.assertIn('worker_swap', result['gates'])
        self.assertIn('rollback verified', result['detail'])
        engine.rollback.assert_called_once()
        engine.finalize.assert_not_called()
        smoke.assert_called_once()
        self.assertEqual(state['engines']['vllm']['production'], 'old')
        self.assertEqual(state['engines']['vllm']['rejected'], 'new')
        self.assertNotIn('provisional', state)

    def test_load_only_swap_and_unknown_telemetry_roll_back(self):
        for change in ['loading', 'missing', 'error']:
            with self.subTest(change=change):
                candidate = record()
                if change == 'loading':
                    candidate['lifecycle_memory']['max_worker_swap_bytes'] = mem.WORKER_SWAP_LIMIT_BYTES + 1
                elif change == 'missing':
                    candidate.pop('lifecycle_memory')
                else:
                    candidate['lifecycle_memory']['sampling_errors'] = 1
                result, _, engine, smoke = self.exercise(candidate)
                self.assertEqual(result['result'], 'rejected')
                engine.rollback.assert_called_once()
                smoke.assert_called_once()
                engine.finalize.assert_not_called()

    def test_swapping_production_baseline_skips_install(self):
        baseline = record()
        baseline['lifecycle_memory']['max_worker_swap_bytes'] = mem.WORKER_SWAP_LIMIT_BYTES + 1
        result, _, engine, smoke = self.exercise(record(), baseline)
        self.assertEqual(result['result'], 'skipped (production baseline failed)')
        engine.install.assert_not_called()
        engine.rollback.assert_not_called()
        smoke.assert_not_called()

    def test_missing_production_profile_skips_install(self):
        baseline = record()
        baseline['profiles'] = []
        result, _, engine, _ = self.exercise(record(), baseline)
        self.assertEqual(result['result'], 'skipped (production baseline failed)')
        engine.install.assert_not_called()

    def test_clean_candidate_promotes(self):
        result, state, engine, smoke = self.exercise(record())
        self.assertEqual(result['result'], 'promoted')
        engine.finalize.assert_called_once()
        engine.rollback.assert_not_called()
        smoke.assert_not_called()
        self.assertEqual(state['engines']['vllm']['production'], 'new')

    def test_minor_swap_baseline_and_candidate_can_promote(self):
        baseline, candidate = record(), record()
        for data in (baseline, candidate):
            data['profiles'][0]['memory']['max_worker_swap_bytes'] = mem.WORKER_SWAP_LIMIT_BYTES
            data['lifecycle_memory']['max_worker_swap_bytes'] = mem.WORKER_SWAP_LIMIT_BYTES
        result, _, engine, _ = self.exercise(candidate, baseline)
        self.assertEqual(result['result'], 'promoted')
        engine.finalize.assert_called_once()
        engine.rollback.assert_not_called()

    def test_lifecycle_monitor_wraps_normal_launcher_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            events = []
            monitor = Mock()
            monitor.start.side_effect = lambda: events.append('monitor-start') or monitor
            monitor.stop.side_effect = lambda: events.append('monitor-stop') or record()['lifecycle_memory']
            launcher = Mock(pid=999)
            launcher.poll.return_value = 0  # No real signal is sent.
            def spawn(*args, **kwargs):
                events.append('launcher')
                return launcher
            def bench(*args, **kwargs):
                events.append('benchmark')
                (stage / 'candidate-test-model.json').write_text(json.dumps(record()))
            with patch.object(daily, 'MemoryMonitor', return_value=monitor), \
                 patch.object(daily.subprocess, 'Popen', side_effect=spawn), \
                 patch.object(daily, 'wait_port'), patch.object(daily, 'post'), \
                 patch.object(daily, 'sh', side_effect=bench), patch.object(daily, 'log'), \
                 patch.object(daily, 'stop_backends', side_effect=lambda: events.append('shutdown')), \
                 patch.object(daily, 'wait_idle'):
                result = daily.launcher_bench('vllm', ['test-model'], stage, 'candidate', stage / 'log')
            self.assertEqual(events, ['monitor-start', 'launcher', 'benchmark', 'shutdown', 'monitor-stop'])
            self.assertEqual(result['lifecycle_memory']['worker_samples'], 5)


if __name__ == '__main__':
    unittest.main()
