from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from short_test_timing import DiagnosticBudgetExpired, StageBudget, violation


class PrefillTimingTests(unittest.TestCase):
    limits = dict(heartbeat_seconds=6, load_seconds=900, first_token_seconds=None,
                  decode_stall_seconds=3, request_seconds=30,
                  idle_seconds=20, cleanup_seconds=15)

    def check_phase(self, now, progress, heartbeat=None, limits=None):
        return violation(now, {'monotonic': now if heartbeat is None else heartbeat},
                         progress, self.limits if limits is None else limits)

    def test_long_healthy_prefill_is_measured_not_rejected(self):
        self.assertIsNone(self.check_phase(180, dict(phase='prefill', phase_started=0,
                                                   request_started=0, last_output=0)))

    def test_request_budget_starts_at_first_output(self):
        p = dict(phase='decode', phase_started=180, request_started=0, last_output=181)
        self.assertIsNone(self.check_phase(181, p))
        p['last_output'] = 211
        self.assertEqual(self.check_phase(211, p), 'post-first-output request deadline')

    def test_stalled_decode_still_stops(self):
        p = dict(phase='decode', phase_started=180, request_started=0, last_output=181)
        self.assertEqual(self.check_phase(184.01, p), 'decode progress stalled')

    def test_independent_monitor_heartbeat_still_stops(self):
        self.assertEqual(self.check_phase(180, dict(phase='prefill', phase_started=0),
                                         heartbeat=173), 'supervisor heartbeat missing')

    def test_loading_idle_cleanup_limits_remain(self):
        for phase, age, reason in [('loading', 900.01, 'model loading deadline'),
                                   ('idle', 20.01, 'idle inter-request deadline'),
                                   ('cleanup', 15.01, 'owned cleanup deadline')]:
            with self.subTest(phase=phase):
                self.assertEqual(self.check_phase(age, dict(phase=phase, phase_started=0)), reason)

    def test_original_policies_can_be_replayed_without_relabeling_raw_evidence(self):
        old = dict(self.limits, first_token_seconds=20)
        self.assertEqual(self.check_phase(21, dict(phase='prefill', phase_started=0),
                                         limits=old), 'first output deadline')

    def test_client_wait_uses_remaining_existing_stage_budget(self):
        b = StageBudget(100, 990, 15)
        self.assertEqual(b.timeout_seconds(280), 795)
        self.assertEqual(b.timeout_ms(280), 795000)
        with self.assertRaises(DiagnosticBudgetExpired):
            b.timeout_seconds(1075)

    def test_invalid_or_unbounded_budget_is_rejected(self):
        for seconds, cleanup in [(float('inf'), 15), (15, 15), (990, 0)]:
            with self.subTest(seconds=seconds, cleanup=cleanup), self.assertRaises(ValueError):
                StageBudget(0, seconds, cleanup)


if __name__ == '__main__':
    unittest.main()
