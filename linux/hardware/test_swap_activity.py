"""CPU-only, deterministic tests; fake proc trees stay in this directory."""
import importlib
import os
from unittest.mock import patch
import json
import tempfile
import unittest
from pathlib import Path

policy = importlib.import_module('swap_activity')

GiB = 1024**3
MiB = 1024**2


def reading(t=0, sin=0, sout=0, available=8*GiB, psi=0.0):
    return dict(timestamp=t, swapin_bytes=sin, swapout_bytes=sout,
                available_bytes=available, memory_full_psi_avg10=psi)


class SwapPolicyTests(unittest.TestCase):
    def setUp(self):
        scope=patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY':'low-churn-v1', 'LOCAL_LLM_LEGACY_SWAP_VALIDATION':'1'})
        scope.start(); self.addCleanup(scope.stop)

    def test_read_host_activity_converts_pages_and_reads_full_psi(self):
        self.assertTrue(callable(getattr(policy, 'read_host_activity', None)))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            (root / 'pressure').mkdir()
            (root / 'vmstat').write_text('nr_free_pages 88\npswpin 7\npswpout 11\n')
            (root / 'meminfo').write_text('MemTotal: 99 kB\nMemAvailable: 2097152 kB\n')
            (root / 'pressure/memory').write_text(
                'some avg10=90.00 avg60=0.00 avg300=0.00 total=1\n'
                'full avg10=4.25 avg60=0.00 avg300=0.00 total=2\n')
            first = policy.read_host_activity(root, page_size=8192)
            second = policy.read_host_activity(root, page_size=8192)
            self.assertEqual(first['swapin_bytes'], 7*8192)
            self.assertEqual(first['swapout_bytes'], 11*8192)
            self.assertEqual(first['available_bytes'], 2*GiB)
            self.assertEqual(first['memory_full_psi_avg10'], 4.25)
            self.assertGreaterEqual(second['timestamp'], first['timestamp'])
            import os
            self.assertEqual(policy.read_host_activity(root)['swapout_bytes'],
                             11*os.sysconf('SC_PAGE_SIZE'))

    def test_read_host_activity_rejects_missing_or_invalid_telemetry(self):
        defaults = {'vmstat': 'pswpin 1\npswpout 2\n',
                    'meminfo': 'MemAvailable: 2097152 kB\n',
                    'pressure/memory': 'full avg10=0.0 avg60=0.0 avg300=0.0 total=0\n'}
        bad_files = [('vmstat', None), ('vmstat', 'pswpin 1\n'),
                     ('vmstat', 'pswpin -1\npswpout 2\n'),
                     ('vmstat', 'pswpin 1\npswpout 2.0\n'),
                     ('meminfo', None), ('meminfo', 'MemFree: 10 kB\n'),
                     ('meminfo', 'MemAvailable: -1 kB\n'),
                     ('meminfo', 'MemAvailable: 10 MB\n'),
                     ('pressure/memory', None),
                     ('pressure/memory', 'some avg10=0.0\n'),
                     ('pressure/memory', 'full avg60=0.0\n')]
        bad_files += [('pressure/memory', 'full avg10='+v+'\n')
                      for v in ['nan', 'inf', '-1', '100.01', 'garbage']]
        for filename, content in bad_files:
            with self.subTest(filename=filename, content=content):
                with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
                    root = Path(folder)
                    (root / 'pressure').mkdir()
                    for name, value in defaults.items():
                        if name != filename or content is not None:
                            payload = content if name == filename else value
                            assert isinstance(payload, str)
                            (root / name).write_text(payload)
                    with self.assertRaises((OSError, ValueError, KeyError)):
                        policy.read_host_activity(root, 4096)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            (root / 'pressure').mkdir()
            for name, value in defaults.items():
                (root / name).write_text(value)
            for size in [True, 0, -1, 4096.0, '4096']:
                with self.subTest(size=size), self.assertRaises(ValueError):
                    policy.read_host_activity(root, size)

    def test_cold_settled_swap_is_allowed_with_self_contained_json_evidence(self):
        self.assertTrue(callable(getattr(policy, 'SwapActivity', None)))
        activity = policy.SwapActivity()
        activity.observe(reading(100, sin=10*GiB, sout=20*GiB),
                         worker_swap_bytes=4*GiB)
        activity.observe(reading(110, sin=10*GiB+7, sout=20*GiB+9),
                         worker_swap_bytes=4*GiB)
        result = activity.summary()
        expected = dict(policy='low-churn-v1', samples=2, sampling_errors=0,
                        elapsed_seconds=10, worker_swap_peak_bytes=4*GiB,
                        total_swapin_bytes=7, total_swapout_bytes=9,
                        inference_window_samples=0,
                        max_inference_swapout_bytes_per_second=0,
                        max_inference_swap_io_bytes_per_second=0,
                        min_available_bytes=8*GiB, max_memory_full_psi_avg10=0.0,
                        failures=[])
        for key, value in expected.items():
            self.assertEqual(result.get(key), value, key)
        self.assertEqual(activity.failures(), [])
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        result['samples'] = -1
        result['failures'].append('mutated')
        self.assertEqual(activity.summary()['samples'], 2)
        self.assertEqual(activity.failures(), [])

    def test_invalid_observations_latch_sampling_errors_without_poisoning_evidence(self):
        cases = [None, {}, [], 'unreadable']
        for field in reading():
            missing = reading(1)
            del missing[field]
            cases.append(missing)
            invalid = ([True, -1, 1.5, '1', None]
                       if field.endswith('_bytes') else
                       [True, -1, '1', None, float('nan'), float('inf')])
            if field == 'memory_full_psi_avg10':
                invalid.append(100.001)
            for value in invalid:
                cases.append(dict(reading(1), **{field: value}))
        arguments = [(case, {}) for case in cases]
        arguments += [(reading(1), {'worker_swap_bytes': v})
                      for v in [True, -1, 1.5, None, '1']]
        arguments += [(reading(1), {'phase': v}) for v in [None, '', 1, ' ', 'inference ']]
        for sample, kwargs in arguments:
            with self.subTest(sample=sample, kwargs=kwargs):
                activity = policy.SwapActivity()
                activity.observe(reading())
                try:
                    activity.observe(sample, **kwargs)
                except Exception as error:
                    self.fail('observe must latch, not raise: '+repr(error))
                self.assertEqual(activity.summary()['sampling_errors'], 1)
                self.assertEqual(activity.summary()['samples'], 1)
                self.assertIn('invalid_observation', activity.failures())
                activity.observe(reading(2))
                self.assertIn('invalid_observation', activity.failures())
                json.dumps(activity.summary(), allow_nan=False)

    def test_counter_resets_and_nonincreasing_timestamps_are_latched(self):
        cases = [(reading(11, sin=99, sout=200), 'swap_counter_reset'),
                 (reading(11, sin=100, sout=199), 'swap_counter_reset'),
                 (reading(9, sin=100, sout=200), 'nonmonotonic_time'),
                 (reading(10, sin=100, sout=200), 'nonmonotonic_time')]
        for sample, failure in cases:
            with self.subTest(sample=sample):
                activity = policy.SwapActivity()
                activity.observe(reading(10, sin=100, sout=200))
                activity.observe(sample)
                self.assertIn(failure, activity.failures())
                self.assertEqual(activity.summary()['sampling_errors'], 1)
                self.assertEqual(activity.summary()['samples'], 1)
                self.assertEqual(activity.summary()['total_swapout_bytes'], 0)
                activity.observe(reading(12, sin=101, sout=202))
                self.assertIn(failure, activity.failures())
                self.assertEqual(activity.summary()['total_swapout_bytes'], 2)

    def test_worker_limit_and_loading_swapout_budget_are_inclusive_and_latched(self):
        activity = policy.SwapActivity()
        activity.observe(reading(sin=50*GiB, sout=80*GiB), worker_swap_bytes=4*GiB)
        activity.observe(reading(1, sin=51*GiB, sout=84*GiB), worker_swap_bytes=4*GiB)
        self.assertEqual(activity.failures(), [])
        self.assertEqual(activity.summary()['total_swapout_bytes'], 4*GiB)
        self.assertEqual(activity.summary()['inference_window_samples'], 0)
        activity.observe(reading(2, sin=51*GiB, sout=84*GiB+1), worker_swap_bytes=4*GiB+1)
        self.assertIn('worker_swap_limit', activity.failures())
        self.assertIn('swapout_budget', activity.failures())
        activity.observe(reading(3, sin=51*GiB, sout=84*GiB+1), worker_swap_bytes=0)
        self.assertEqual(activity.summary()['worker_swap_peak_bytes'], 4*GiB+1)
        self.assertEqual(activity.summary()['sampling_errors'], 0)
        self.assertEqual(set(activity.failures()), {'worker_swap_limit', 'swapout_budget'})

    def test_pressure_needs_three_consecutive_samples_and_latches_after_recovery(self):
        cases = [('available', 2*GiB-1, 2*GiB, 'low_host_memory',
                  'max_low_memory_consecutive_samples'),
                 ('psi', 10.001, 10.0, 'memory_full_psi',
                  'max_full_psi_consecutive_samples')]
        for key, bad, good, failure, evidence in cases:
            with self.subTest(key=key):
                activity = policy.SwapActivity()
                values = [bad, bad, good, bad, bad]
                for index, value in enumerate(values):
                    activity.observe(reading(index, **{key: value}),
                                     phase='inference' if index % 2 else 'loading')
                self.assertEqual(activity.failures(), [])
                self.assertEqual(activity.summary().get(evidence), 2)
                activity.observe(reading(5, **{key: bad}))
                self.assertIn(failure, activity.failures())
                self.assertEqual(activity.summary()[evidence], 3)
                activity.observe(reading(6, **{key: good}))
                self.assertIn(failure, activity.failures())
                self.assertEqual(activity.summary()[evidence], 3)
                result = activity.summary()
                if key == 'available':
                    self.assertEqual(result['min_available_bytes'], bad)
                else:
                    self.assertEqual(result['max_memory_full_psi_avg10'], bad)
                self.assertEqual(result['sampling_errors'], 0)

    def test_startup_burst_is_excluded_from_exact_limit_inference_window(self):
        activity = policy.SwapActivity()
        activity.observe(reading(0))
        activity.observe(reading(1, sout=3*GiB))
        activity.observe(reading(2, sout=3*GiB), phase='inference')
        activity.observe(reading(31, sin=203*MiB, sout=3*GiB+29*MiB), phase='inference')
        self.assertEqual(activity.summary()['inference_window_samples'], 0)
        activity.observe(reading(32, sin=210*MiB, sout=3*GiB+30*MiB), phase='inference')
        result = activity.summary()
        self.assertEqual(result['inference_window_samples'], 1)
        self.assertEqual(result['max_inference_swapout_bytes_per_second'], MiB)
        self.assertEqual(result['max_inference_swap_io_bytes_per_second'], 8*MiB)
        self.assertEqual(result['total_swapout_bytes'], 3*GiB+30*MiB)
        self.assertEqual(activity.failures(), [])

    def test_true_churn_is_rejected_by_rolling_rates_and_stays_latched(self):
        cases = [(0, 30*MiB+1, 'inference_swapout_rate'),
                 (240*MiB+1, 0, 'inference_swap_io_rate'),
                 (210*MiB+1, 30*MiB, 'inference_swap_io_rate')]
        for incoming, outgoing, failure in cases:
            with self.subTest(incoming=incoming, outgoing=outgoing):
                activity = policy.SwapActivity()
                for t in [0, 30, 60]:
                    activity.observe(reading(t), phase='inference')
                activity.observe(reading(90, sin=incoming, sout=outgoing), phase='inference')
                self.assertIn(failure, activity.failures())
                self.assertEqual(activity.summary()['inference_window_samples'], 3)
                self.assertEqual(activity.summary()['max_inference_swapout_bytes_per_second'],
                                 outgoing / 30)
                self.assertEqual(activity.summary()['max_inference_swap_io_bytes_per_second'],
                                 (incoming + outgoing) / 30)
                activity.observe(reading(120, sin=incoming, sout=outgoing), phase='inference')
                self.assertIn(failure, activity.failures())
                self.assertNotIn('swapout_budget', activity.failures())
                self.assertEqual(activity.summary()['sampling_errors'], 0)

    def test_phase_changes_and_sampling_gaps_restart_the_inference_window(self):
        interruptions = [(reading(30, sout=GiB), 'loading', 0),
                         (None, 'loading', 1),
                         (None, 'inference', 1),
                         (reading(28), 'inference', 1),
                         (reading(30, sout=0), 'inference', 1)]
        for interrupt, phase, errors in interruptions:
            with self.subTest(interrupt=interrupt, phase=phase):
                activity = policy.SwapActivity()
                activity.observe(reading(0, sout=100), phase='inference')
                activity.observe(reading(29, sout=100), phase='inference')
                activity.observe(interrupt, phase=phase)
                activity.observe(reading(60, sout=GiB), phase='inference')
                activity.observe(reading(89, sout=GiB), phase='inference')
                self.assertEqual(activity.summary()['inference_window_samples'], 0)
                activity.observe(reading(90, sout=GiB), phase='inference')
                result = activity.summary()
                self.assertEqual(result['inference_window_samples'], 1)
                self.assertEqual(result['max_inference_swapout_bytes_per_second'], 0)
                self.assertEqual(result['sampling_errors'], errors)

    def test_validate_summary_fails_closed_on_missing_or_invalid_evidence(self):
        self.assertTrue(callable(getattr(policy, 'validate_summary', None)))
        activity = policy.SwapActivity()
        activity.observe(reading())
        valid = activity.summary()
        self.assertEqual(policy.validate_summary(valid), [])
        self.assertTrue(policy.validate_summary(policy.SwapActivity().summary()))
        for value in [None, [], 'evidence', {}]:
            self.assertTrue(policy.validate_summary(value), repr(value))
        for key, value in valid.items():
            missing = dict(valid)
            del missing[key]
            with self.subTest(missing=key):
                self.assertTrue(policy.validate_summary(missing))
            if key == 'policy':
                invalid = [None, 'other', True]
            elif key == 'failures':
                invalid = [None, 'failure', [1], [''], [False]]
            elif key not in ('elapsed_seconds', 'max_inference_swapout_bytes_per_second',
                              'max_inference_swap_io_bytes_per_second',
                              'max_memory_full_psi_avg10'):
                invalid = [None, True, -1, 1.5, '0']
            else:
                invalid = [None, True, -1, float('nan'), float('inf'), '0']
            for bad in invalid:
                with self.subTest(key=key, value=bad):
                    self.assertTrue(policy.validate_summary(dict(valid, **{key: bad})))
        self.assertTrue(policy.validate_summary(dict(valid, samples=0)))
        self.assertTrue(policy.validate_summary(dict(valid, sampling_errors=1)))
        self.assertTrue(policy.validate_summary(dict(valid, max_memory_full_psi_avg10=100.1)))
        self.assertIn('upstream_error', policy.validate_summary(dict(valid, failures=['upstream_error'])))

    def test_validate_summary_recomputes_inclusive_thresholds_not_just_failure_list(self):
        activity = policy.SwapActivity()
        activity.observe(reading(available=2*GiB, psi=10), worker_swap_bytes=4*GiB)
        activity.observe(reading(1, sout=4*GiB-30*MiB))
        activity.observe(reading(2, sout=4*GiB-30*MiB), phase='inference')
        activity.observe(reading(32, sin=210*MiB, sout=4*GiB), phase='inference')
        valid = activity.summary()
        self.assertEqual(policy.validate_summary(valid), [])
        cases = [({'worker_swap_peak_bytes': 4*GiB+1}, 'worker_swap_limit'),
                 ({'total_swapout_bytes': 4*GiB+1}, 'swapout_budget'),
                 ({'max_inference_swapout_bytes_per_second': MiB+0.01}, 'inference_swapout_rate'),
                 ({'max_inference_swap_io_bytes_per_second': 8*MiB+0.01}, 'inference_swap_io_rate'),
                 ({'max_low_memory_consecutive_samples': 3, 'min_available_bytes': 2*GiB-1},
                  'low_host_memory'),
                 ({'max_full_psi_consecutive_samples': 3, 'max_memory_full_psi_avg10': 10.001},
                  'memory_full_psi')]
        for update, failure in cases:
            with self.subTest(update=update):
                self.assertIn(failure, policy.validate_summary(dict(valid, **update)))
        transient = policy.SwapActivity()
        for t, (available, psi) in enumerate([(GiB, 11), (GiB, 11), (2*GiB, 10)]):
            transient.observe(reading(t, available=available, psi=psi))
        self.assertEqual(policy.validate_summary(transient.summary()), [])

    def test_require_inference_needs_a_complete_thirty_second_inference_window(self):
        activity = policy.SwapActivity()
        activity.observe(reading())
        activity.observe(reading(100))
        self.assertEqual(policy.validate_summary(activity.summary()), [])
        self.assertIn('no_inference_window', policy.validate_summary(activity.summary(), True))
        activity.observe(reading(101), phase='inference')
        activity.observe(reading(130), phase='inference')
        self.assertIn('no_inference_window', policy.validate_summary(activity.summary(), True))
        activity.observe(reading(131), phase='inference')
        self.assertEqual(policy.validate_summary(activity.summary(), True), [])
        for bad in [None, 'yes', 1]:
            with self.subTest(require_inference=bad):
                self.assertTrue(policy.validate_summary(activity.summary(), bad))

    def test_validate_summary_rejects_internally_inconsistent_evidence(self):
        activity = policy.SwapActivity()
        activity.observe(reading(), phase='inference')
        activity.observe(reading(30), phase='inference')
        valid = activity.summary()
        cases = [dict(elapsed_seconds=29), dict(elapsed_seconds=0),
                 dict(samples=1), dict(inference_window_samples=2),
                 dict(max_inference_swapout_bytes_per_second=1),
                 dict(max_inference_swap_io_bytes_per_second=1),
                 dict(max_low_memory_consecutive_samples=1),
                 dict(min_available_bytes=GiB),
                 dict(max_full_psi_consecutive_samples=1),
                 dict(max_memory_full_psi_avg10=11)]
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertTrue(policy.validate_summary(dict(valid, **changes), True))
        activity = policy.SwapActivity()
        activity.observe(reading())
        single = activity.summary()
        for changes in [dict(elapsed_seconds=1), dict(total_swapin_bytes=1),
                        dict(total_swapout_bytes=1),
                        dict(max_inference_swap_io_bytes_per_second=1)]:
            with self.subTest(changes=changes):
                self.assertTrue(policy.validate_summary(dict(single, **changes)))

    def test_no_samples_is_fail_closed_without_poisoning_future_valid_samples(self):
        activity = policy.SwapActivity()
        self.assertIn('no_samples', activity.failures())
        self.assertIn('no_samples', activity.summary()['failures'])
        json.dumps(activity.summary(), allow_nan=False)
        activity.observe(reading())
        self.assertEqual(activity.failures(), [])
        other = policy.SwapActivity()
        other.observe(None)
        self.assertIn('no_samples', other.failures())
        self.assertIn('invalid_observation', other.failures())
        other.observe(reading())
        self.assertNotIn('no_samples', other.failures())
        self.assertIn('invalid_observation', other.failures())

    def test_numeric_overflow_is_fail_closed_and_large_valid_counters_do_not_raise(self):
        huge = 10**400
        for field in reading():
            with self.subTest(field=field):
                activity = policy.SwapActivity()
                activity.observe(dict(reading(), **{field: huge}))
                self.assertEqual(activity.summary()['sampling_errors'], 1)
                self.assertIn('invalid_observation', activity.failures())
                json.dumps(activity.summary(), allow_nan=False)
        activity = policy.SwapActivity()
        activity.observe(reading(), phase='inference')
        activity.observe(reading(30.0, sin=10**308, sout=10**308), phase='inference')
        self.assertEqual(activity.summary()['sampling_errors'], 0)
        self.assertIn('inference_swap_io_rate', activity.failures())
        json.dumps(activity.summary(), allow_nan=False)
        self.assertTrue(policy.validate_summary(activity.summary()))
        activity = policy.SwapActivity()
        activity.observe(reading())
        self.assertTrue(policy.validate_summary(dict(activity.summary(), total_swapin_bytes=huge)))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            (root / 'pressure').mkdir()
            (root / 'vmstat').write_text('pswpin '+str(huge)+'\npswpout 0\n')
            (root / 'meminfo').write_text('MemAvailable: 2097152 kB\n')
            (root / 'pressure/memory').write_text('full avg10=0\n')
            with self.assertRaises(ValueError):
                policy.read_host_activity(root, 4096)

    def test_duplicate_host_telemetry_is_rejected_instead_of_silently_overwritten(self):
        valid = {'vmstat': 'pswpin 1\npswpout 2\n',
                 'meminfo': 'MemAvailable: 2097152 kB\n',
                 'pressure/memory': 'full avg10=0\n'}
        cases = [('vmstat', 'pswpin 0\npswpin 1\npswpout 2\n'),
                 ('meminfo', 'MemAvailable: 0 kB\nMemAvailable: 2097152 kB\n'),
                 ('pressure/memory', 'full avg10=20 avg10=0\n'),
                 ('pressure/memory', 'full avg10=0\nfull avg10=20\n')]
        for name, content in cases:
            with self.subTest(name=name, content=content):
                with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
                    root = Path(folder)
                    (root / 'pressure').mkdir()
                    for filename, value in valid.items():
                        (root / filename).write_text(content if filename == name else value)
                    with self.assertRaises(ValueError):
                        policy.read_host_activity(root, 4096)

    def test_other_named_phases_are_noninference_and_reset_the_window(self):
        activity = policy.SwapActivity()
        activity.observe(reading(0), phase='inference')
        activity.observe(reading(29), phase='inference')
        activity.observe(reading(30, sout=3*GiB), phase='warmup')
        self.assertEqual(activity.summary()['sampling_errors'], 0)
        activity.observe(reading(60, sout=3*GiB), phase='inference')
        activity.observe(reading(89, sout=3*GiB+29*MiB), phase='inference')
        self.assertEqual(activity.summary()['inference_window_samples'], 0)
        activity.observe(reading(90, sout=3*GiB+30*MiB), phase='inference')
        self.assertEqual(activity.summary()['inference_window_samples'], 1)
        self.assertEqual(activity.summary()['max_inference_swapout_bytes_per_second'], MiB)
        self.assertEqual(activity.failures(), [])

    def test_explicit_transitions_reset_unsampled_inference_history(self):
        activity = policy.SwapActivity()
        self.assertTrue(callable(getattr(activity, 'set_phase', None)))
        activity.observe(reading(0), phase='inference')
        activity.observe(reading(29), phase='inference')
        activity.set_phase('loading')
        activity.set_phase('inference')
        activity.observe(reading(30), phase='inference')
        self.assertEqual(activity.summary()['inference_window_samples'], 0)
        activity.set_phase('inference')  # No transition: do not discard history.
        activity.observe(reading(60), phase='inference')
        self.assertEqual(activity.summary()['inference_window_samples'], 1)
        activity.observe(reading(90, sout=60*MiB), phase='inference')
        activity.set_phase('shutdown')
        self.assertIn('inference_swapout_rate', activity.failures())
        self.assertEqual(activity.summary()['inference_window_samples'], 2)

    def test_policy_constants(self):
        self.assertIsNotNone(policy, 'swap_activity module is missing')
        expected = dict(POLICY_NAME='loading-swap-v3',
                        WORKER_SWAP_LIMIT_BYTES=4*GiB,
                        SWAPOUT_BUDGET_BYTES=4*GiB,
                        INFERENCE_SWAPOUT_RATE_LIMIT_BYTES=MiB,
                        INFERENCE_IO_RATE_LIMIT_BYTES=8*MiB,
                        RATE_WINDOW_SECONDS=30, MIN_AVAILABLE_BYTES=2*GiB,
                        MIN_PRESSURE_SAMPLES=3, MEMORY_FULL_PSI_AVG10_LIMIT=10.0)
        for key, value in expected.items():
            self.assertEqual(getattr(policy, key, None), value, key)


if __name__ == '__main__':
    unittest.main()
