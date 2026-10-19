"""Desktop headroom thresholds and owned-worker-only shutdown behavior."""
import importlib.util
from pathlib import Path
import sys
import signal
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from strata_memory import MemoryGuard, GIB


class StrataGuardTests(unittest.TestCase):
    def sample(self, guard, free=4, **kw):
        return guard.check(kw.get('available', 10)*GIB, kw.get('swap', 0),
                           kw.get('spill', 0), [{'free':free*GIB}, {'free':5*GIB}])

    def test_two_cards_and_healthy_headroom_pass(self):
        self.assertIsNone(self.sample(MemoryGuard()))

    def test_hard_floor_unloads_immediately(self):
        self.assertIn('VRAM', self.sample(MemoryGuard(), free=1))

    def test_soft_floor_requires_two_samples_and_recovers(self):
        guard = MemoryGuard()
        self.assertIsNone(self.sample(guard, free=2.8))
        self.assertIsNone(self.sample(guard, free=4))
        self.assertIsNone(self.sample(guard, free=2.8))
        self.assertIn('VRAM', self.sample(guard, free=2.8))

    def test_missing_telemetry_fails_closed(self):
        guard = MemoryGuard()
        self.assertIsNone(guard.check(10*GIB, 0, 0, None))
        self.assertIsNone(guard.check(10*GIB, 0, 0, None))
        self.assertIn('telemetry', guard.check(10*GIB, 0, 0, None))

    def test_owned_swap_and_spill_trigger(self):
        self.assertIn('unsafe', self.sample(MemoryGuard(), swap=257*1024**2))
        self.assertIn('unsafe', self.sample(MemoryGuard(), spill=257*1024**2))

    def test_router_stops_only_its_worker_and_latches_reload(self):
        spec = importlib.util.spec_from_file_location('strata_router', ROOT/'dsh/strata-router.py')
        router = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(router)
        proc = Mock(); proc.poll.return_value = None
        router.worker = proc
        router.stopping = Mock(); router.stopping.wait.side_effect = [False, True]
        with patch.object(router, 'host_memory', return_value=(30*GIB, 10*GIB)), \
             patch.object(router, 'worker_memory', return_value=(0,0)), \
             patch.object(router, 'vram_snapshot', return_value=[{'free':GIB},{'free':5*GIB}]), \
             patch.object(router, 'stop_worker') as stop:
            router.watch_memory()
        stop.assert_called_once_with(timeout=3)
        self.assertIn('VRAM', router.memory_fault)
        router.stopping = threading.Event()
        with self.assertRaisesRegex(RuntimeError, 'explicitly'):
            router.ensure_worker(router.DEFAULT)

    def test_emergency_stop_signals_only_the_owned_group(self):
        spec = importlib.util.spec_from_file_location('strata_router_stop', ROOT/'dsh/strata-router.py')
        router = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(router)
        proc=Mock();proc.pid=1234;proc.poll.return_value=None
        proc.wait.side_effect=[subprocess.TimeoutExpired('owned worker',3),None]
        router.worker=proc
        with patch.object(router.os,'killpg') as kill:
            router.stop_worker(timeout=3)
        self.assertEqual(kill.call_args_list, [unittest.mock.call(1234,signal.SIGTERM),
                                              unittest.mock.call(1234,signal.SIGKILL)])
        self.assertIsNone(router.worker)


if __name__ == '__main__':
    unittest.main()
