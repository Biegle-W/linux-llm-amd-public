"""CPU-only historical low-churn-v1 regressions and strict validation override."""
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hardware'))
import inference_memory as mem

GIB = 1024 ** 3


def evidence(swap=GIB):
    return {
        'max_worker_swap_bytes': swap,
        'max_nonresident_vram_bytes': 0,
        'swap_activity': {
            'policy': 'low-churn-v1', 'samples': 65, 'sampling_errors': 0,
            'elapsed_seconds': 65.0, 'worker_swap_peak_bytes': swap,
            'total_swapin_bytes': 0, 'total_swapout_bytes': swap,
            'inference_window_samples': 31,
            'max_inference_swapout_bytes_per_second': 0.0,
            'max_inference_swap_io_bytes_per_second': 0.0,
            'min_available_bytes': 8 * GIB,
            'max_memory_full_psi_avg10': 0.0,
            'max_low_memory_consecutive_samples': 0,
            'max_full_psi_consecutive_samples': 0, 'failures': [],
        },
    }


class RelaxedSwap(unittest.TestCase):
    def setUp(self):
        policy = patch.dict(os.environ)
        policy.start()
        self.addCleanup(policy.stop)
        os.environ['LOCAL_LLM_SWAP_POLICY'] = 'low-churn-v1'
        os.environ['LOCAL_LLM_LEGACY_SWAP_VALIDATION'] = '1'

    def test_legacy_monitor_demonstrates_settled_swap_and_enforces_low_churn_evidence(self):
        with patch.dict(os.environ):
            os.environ['LOCAL_LLM_SWAP_POLICY'] = 'low-churn-v1'
            monitor = mem.MemoryMonitor()
            with patch.object(mem, 'sample_memory', return_value=dict(swap=GIB, spill=0)), \
                 patch.object(mem, 'read_host_activity', side_effect=[
                     host_reading(0), host_reading(1, GIB), host_reading(31, GIB)]):
                monitor.sample()
                monitor.set_phase('inference')
                monitor.sample()
                monitor.sample()
            self.assertEqual(mem.swap_policy(), 'low-churn-v1')
            self.assertEqual(mem.worker_swap_limit_bytes(), 4 * GIB)
            self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 1)
            self.assertEqual(mem.memory_failures(monitor.summary), [])
            self.assertEqual(mem.lifecycle_failures({'lifecycle_memory': monitor.summary}), [])

    def test_explicit_low_churn_and_bounded_overrides_are_preserved(self):
        memory = evidence()
        with patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'}):
            self.assertEqual(mem.memory_failures(memory), [])
        with patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'bounded-64mib', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'}):
            self.assertEqual(mem.worker_swap_limit_bytes(), 64 * 1024**2)
            self.assertIsNone(mem.MemoryMonitor().activity)
            self.assertIn('worker_swap', mem.memory_failures(memory))

    def test_legacy_rejects_worker_swap_above_four_gib(self):
        self.assertIn('worker_swap', mem.memory_failures(evidence(4 * GIB + 1)))

    def test_legacy_rejects_churn_budget_and_sustained_pressure(self):
        cases = [
            ({'total_swapout_bytes': 4 * GIB + 1}, 'swapout_budget'),
            ({'max_inference_swapout_bytes_per_second': 1024**2 + 1,
              'max_inference_swap_io_bytes_per_second': 1024**2 + 1}, 'inference_swapout_rate'),
            ({'max_inference_swap_io_bytes_per_second': 8 * 1024**2 + 1}, 'inference_swap_io_rate'),
            ({'min_available_bytes': 2 * GIB - 1,
              'max_low_memory_consecutive_samples': 3}, 'low_host_memory'),
            ({'max_memory_full_psi_avg10': 10.01,
              'max_full_psi_consecutive_samples': 3}, 'memory_full_psi'),
        ]
        for update, reason in cases:
            with self.subTest(reason=reason):
                memory = evidence()
                memory['swap_activity'].update(update)
                self.assertIn('swap_activity_' + reason, mem.memory_failures(memory))

    def test_legacy_rejects_missing_invalid_or_incomplete_activity_even_with_zero_swap(self):
        for activity in (None, {}, {'sampling_errors': 1}):
            with self.subTest(activity=activity):
                memory = evidence(0)
                memory['swap_activity'] = activity
                self.assertTrue(mem.memory_failures(memory))
        memory = evidence(0)
        memory.pop('swap_activity')
        self.assertIn('swap_activity_summary_missing', mem.memory_failures(memory))
        memory = evidence(0)
        memory['swap_activity']['inference_window_samples'] = 0
        self.assertIn('swap_activity_no_inference_window', mem.memory_failures(memory))
        memory = evidence()
        memory['swap_activity']['worker_swap_peak_bytes'] = 0
        self.assertIn('swap_activity_worker_peak_mismatch', mem.memory_failures(memory))

    def test_legacy_still_rejects_any_vram_spill(self):
        memory = evidence()
        memory['max_nonresident_vram_bytes'] = 1
        self.assertIn('vram_spill', mem.memory_failures(memory))

    def test_invalid_policy_is_rejected_not_silently_defaulted(self):
        for value in ('', 'unknown', 'low-churn-v1 ', 'bounded-64mib '):
            with self.subTest(policy=value), patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': value}):
                self.assertEqual(mem.memory_failures(evidence()), ['memory_policy_invalid'])
                with self.assertRaises(ValueError):
                    mem.worker_swap_limit_bytes()
                with self.assertRaises(ValueError):
                    mem.MemoryMonitor()


def host_reading(t, sout=0):
    return dict(timestamp=t, swapin_bytes=0, swapout_bytes=sout,
                available_bytes=8 * GIB, memory_full_psi_avg10=0.0)


class MonitorRegressions(unittest.TestCase):
    def setUp(self):
        self.policy = patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY': 'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '1'})
        self.policy.start()
        self.addCleanup(self.policy.stop)

    def test_callback_exceptions_are_latched_and_retried_once_without_thread_death(self):
        calls, uncaught = [], []
        monitor = mem.MemoryMonitor()
        monitor.set_phase('inference')

        def fail_notification(failures):
            calls.append(list(failures))
            raise RuntimeError('private callback detail must not enter evidence')

        monitor.on_violation = fail_notification
        iterations = []

        def next_iteration(_interval):
            iterations.append(1)
            if len(iterations) == 3:
                monitor.done.set()

        with patch.object(mem, 'sample_memory', return_value=dict(swap=0, spill=1)), \
             patch.object(mem, 'read_host_activity', side_effect=[host_reading(t) for t in (0, 30, 60)]), \
             patch.object(monitor.done, 'wait', side_effect=next_iteration), \
             patch.object(threading, 'excepthook', side_effect=uncaught.append):
            monitor.start()
            monitor.thread.join(5)
            self.assertFalse(monitor.thread.is_alive())
            result = monitor.stop()
        self.assertEqual(result['worker_samples'], 3, 'callback failure killed the sampling thread')
        self.assertEqual(uncaught, [])
        self.assertEqual(len(calls), 2, 'one retry on the next sample, then terminal failure')
        self.assertFalse(monitor.notified)
        self.assertEqual(result['enforcement_attempts'], 2)
        self.assertEqual(result['enforcement_errors'], 2)
        self.assertEqual(result['enforcement_state'], 'failed_terminal')
        self.assertEqual(result['first_enforcement_error_type'], 'RuntimeError')
        self.assertNotIn('private callback detail', repr(result))
        self.assertIn('violation_callback_errors', mem.memory_failures(result))
        self.assertIn('violation_callback_errors', mem.lifecycle_failures({'lifecycle_memory': result}))

    def test_missing_inference_workers_cannot_qualify_a_window(self):
        worker = dict(swap=0, spill=0)
        cases = [
            ('both_endpoints', [None, None], [1, 31], 2),
            ('start_endpoint', [None, worker], [1, 31], 1),
            ('end_endpoint', [worker, None], [1, 31], 1),
            ('interior_gap', [worker, None, worker], [1, 16, 31], 1),
        ]
        for name, observations, times, missing in cases:
            with self.subTest(case=name):
                monitor = mem.MemoryMonitor()
                with patch.object(mem, 'sample_memory', side_effect=[worker] + observations), \
                     patch.object(mem, 'read_host_activity',
                                  side_effect=[host_reading(t) for t in [0] + times]):
                    monitor.sample()  # A real loading sample cannot cover inference.
                    monitor.set_phase('inference')
                    for _ in observations:
                        monitor.sample()
                failures = mem.lifecycle_failures({'lifecycle_memory': monitor.summary})
                self.assertIn('lifecycle_sampling_errors', failures)
                self.assertIn('swap_activity_no_inference_window', failures)
                self.assertEqual(monitor.summary['sampling_errors'], missing)
                self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 0)
                self.assertIn('swap_activity_invalid_observation', mem.memory_failures(monitor.summary))

    def test_unsampled_phase_round_trip_restarts_monitor_window(self):
        monitor = mem.MemoryMonitor()
        monitor.set_phase('inference')
        with patch.object(mem, 'sample_memory', return_value=dict(swap=0, spill=0)), \
             patch.object(mem, 'read_host_activity',
                          side_effect=[host_reading(t) for t in (0, 29, 30, 60)]):
            monitor.sample()
            monitor.sample()
            monitor.set_phase('loading')
            monitor.set_phase('inference')
            monitor.sample()
            self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 0)
            self.assertIn('swap_activity_no_inference_window',
                          mem.lifecycle_failures({'lifecycle_memory': monitor.summary}))
            monitor.set_phase('inference')
            monitor.sample()
        self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 1)
        self.assertEqual(mem.lifecycle_failures({'lifecycle_memory': monitor.summary}), [])

    def test_worker_absence_is_allowed_before_launch_and_after_shutdown(self):
        worker = dict(swap=0, spill=0)
        monitor = mem.MemoryMonitor()
        with patch.object(mem, 'sample_memory', side_effect=[None, worker, worker, worker, None]), \
             patch.object(mem, 'read_host_activity',
                          side_effect=[host_reading(t) for t in (0, 1, 2, 32, 33)]):
            monitor.sample()  # Before launch.
            monitor.sample()  # Loaded worker.
            monitor.set_phase('inference')
            monitor.sample()
            monitor.sample()
            monitor.set_phase('shutdown')
            monitor.sample()  # Worker exited normally.
        self.assertEqual(monitor.summary['worker_samples'], 3)
        self.assertEqual(monitor.summary['sampling_errors'], 0)
        self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 1)
        self.assertEqual(mem.lifecycle_failures({'lifecycle_memory': monitor.summary}), [])

    def test_worker_gap_failure_stays_latched_after_fresh_valid_window(self):
        worker = dict(swap=0, spill=0)
        monitor = mem.MemoryMonitor()
        monitor.set_phase('inference')
        with patch.object(mem, 'sample_memory', side_effect=[worker, worker, None, worker, worker]), \
             patch.object(mem, 'read_host_activity',
                          side_effect=[host_reading(t) for t in (0, 30, 31, 32, 62)]):
            monitor.sample()
            monitor.sample()
            self.assertEqual(mem.lifecycle_failures({'lifecycle_memory': monitor.summary}), [])
            monitor.sample()
            monitor.sample()
            self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 1)
            monitor.sample()
        self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 2)
        self.assertEqual(monitor.summary['sampling_errors'], 1)
        self.assertIn('swap_activity_invalid_observation', mem.memory_failures(monitor.summary))
        self.assertIn('lifecycle_sampling_errors',
                      mem.lifecycle_failures({'lifecycle_memory': monitor.summary}))

    def test_successful_callback_retry_keeps_error_and_can_change_phase(self):
        monitor = mem.MemoryMonitor()
        calls, states = [], []

        def notify(failures):
            calls.append(list(failures))
            states.append(monitor.notified)
            monitor.set_phase('shutdown')  # Callback is outside the sampling lock.
            if len(calls) == 1:
                raise RuntimeError('first attempt failed')

        monitor.on_violation = notify
        with patch.object(mem, 'sample_memory', return_value=dict(swap=0, spill=1)), \
             patch.object(mem, 'read_host_activity', side_effect=[host_reading(t) for t in (0, 30, 60)]):
            # Run on a daemon to bound a regression that deadlocks a callback.
            def samples():
                for _ in range(3):
                    monitor.sample()

            thread = threading.Thread(target=samples, daemon=True)
            thread.start()
            thread.join(5)
            self.assertFalse(thread.is_alive(), 'callback deadlocked on phase transition')
        self.assertEqual(len(calls), 2)
        self.assertEqual(states, [False, False], 'must not claim notification before callback returns')
        self.assertTrue(monitor.notified)
        self.assertEqual(monitor.summary['enforcement_state'], 'notified')
        self.assertEqual(monitor.summary['enforcement_errors'], 1)
        self.assertEqual(monitor.summary['enforcement_attempts'], 2)
        # Isolate callback failure from the triggering spill and incomplete window.
        memory = evidence(swap=0)
        memory['enforcement_errors'] = monitor.summary['enforcement_errors']
        self.assertEqual(mem.memory_failures(memory), ['violation_callback_errors'])

    def test_phase_change_waits_for_worker_and_host_reading(self):
        for blocked_reader in ('sample_memory', 'read_host_activity'):
            with self.subTest(blocked_reader=blocked_reader):
                monitor = mem.MemoryMonitor()
                monitor.set_phase('inference')
                worker = dict(swap=0, spill=0)
                with patch.object(mem, 'sample_memory', return_value=worker), \
                     patch.object(mem, 'read_host_activity', side_effect=[host_reading(0), host_reading(30)]):
                    monitor.sample()
                    monitor.sample()

                entered, release, transition_attempted = (threading.Event() for _ in range(3))
                errors = []

                class ProbeLock:
                    """Signal lock contention, not scheduler timing or sleeps."""
                    def __init__(self):
                        self.lock = threading.Lock()

                    def __enter__(self):
                        if threading.current_thread().name == 'phase-setter':
                            transition_attempted.set()
                        self.lock.acquire()

                    def __exit__(self, *args):
                        self.lock.release()

                setattr(monitor, '_lock', ProbeLock())

                def blocked():
                    entered.set()
                    if not release.wait(5):
                        raise AssertionError('reader was not released')
                    return worker if blocked_reader == 'sample_memory' else host_reading(60, 60 * 1024**2)

                def run_sample():
                    try:
                        monitor.sample()
                    except Exception as error:
                        errors.append(error)

                def change_phase():
                    try:
                        monitor.set_phase('shutdown')
                    except Exception as error:
                        errors.append(error)
                    finally:
                        # On the defective implementation there is no lock attempt.
                        transition_attempted.set()

                sampler = threading.Thread(target=run_sample, daemon=True)
                setter = threading.Thread(target=change_phase, name='phase-setter', daemon=True)
                with patch.object(mem, 'sample_memory', return_value=worker) as read_worker, \
                     patch.object(mem, 'read_host_activity', return_value=host_reading(60, 60 * 1024**2)) as read_host:
                    (read_worker if blocked_reader == 'sample_memory' else read_host).side_effect = blocked
                    sampler.start()
                    try:
                        self.assertTrue(entered.wait(5), 'sample never entered reader')
                        setter.start()
                        self.assertTrue(transition_attempted.wait(5), 'setter never attempted transition')
                    finally:
                        release.set()
                        sampler.join(5)
                        if setter.ident is not None:
                            setter.join(5)
                self.assertFalse(sampler.is_alive())
                self.assertFalse(setter.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(monitor.phase, 'shutdown')
                self.assertIn('swap_activity_inference_swapout_rate',
                              mem.lifecycle_failures({'lifecycle_memory': monitor.summary}))
                self.assertEqual(monitor.summary['swap_activity']['inference_window_samples'], 2)


if __name__ == '__main__':
    unittest.main()
