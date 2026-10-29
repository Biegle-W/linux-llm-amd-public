"""Desktop headroom thresholds and owned-worker-only shutdown behavior."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import signal
import subprocess
import threading
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from strata_memory import MemoryGuard, GIB, startup_vram_blocker


class StrataGuardTests(unittest.TestCase):
    def test_loaded_startup_accepts_five_gib_on_both_cards(self):
        self.assertIsNone(startup_vram_blocker([{'free':5*GIB}, {'free':5*GIB}]))
        self.assertIsNone(startup_vram_blocker([{'free':5785194496}, {'free':6730600448}]))

    def test_loaded_startup_refuses_either_card_below_five_gib(self):
        for free in ([5*GIB-1,6*GIB], [6*GIB,5*GIB-1]):
            with self.subTest(free=free):
                self.assertIn('5 GiB',startup_vram_blocker([{'free':v} for v in free]))

    def test_loaded_startup_refuses_missing_card_telemetry(self):
        for readings in (None, [], [{'free':6*GIB}]):
            with self.subTest(readings=readings):
                self.assertIn('Both AMD',startup_vram_blocker(readings))

    def test_router_admits_five_gib_and_stops_owned_worker_below_it(self):
        for free,accepted in (([5*GIB,5*GIB],True),([5*GIB-1,6*GIB],False),([6*GIB,5*GIB-1],False)):
            with self.subTest(free=free), tempfile.TemporaryDirectory() as folder:
                spec=importlib.util.spec_from_file_location('strata_startup',ROOT/'dsh/strata-router.py')
                router=importlib.util.module_from_spec(spec);spec.loader.exec_module(router)
                root=Path(folder);(root/'logs').mkdir()
                config_name=router.PROFILES[router.DEFAULT]['config']
                (root/config_name).write_bytes((ROOT/'dsh'/config_name).read_bytes())
                proc=Mock();proc.pid=1234;proc.poll.return_value=None
                health={'loaded':True,'model':router.DEFAULT,'max_context':router.PROFILES[router.DEFAULT]['context']}
                with patch.object(router,'ROOT',root), \
                     patch('hardware_guard.require_strata'), \
                     patch.object(router,'swap_guard') as swap_guard, \
                     patch.object(router.urllib.request,'urlopen',return_value=io.StringIO(json.dumps(health))), \
                     patch.object(router,'vram_snapshot',return_value=[{'free':v} for v in free]), \
                     patch.object(router.os,'killpg') as kill:
                    swap_guard.spawn.return_value = proc
                    if accepted:
                        router.ensure_worker(router.DEFAULT)
                        self.assertEqual(router.active,router.DEFAULT)
                        kill.assert_not_called()
                        router.stop_worker()
                    else:
                        with self.assertRaisesRegex(RuntimeError,'5 GiB'):
                            router.ensure_worker(router.DEFAULT)
                        self.assertIsNone(router.worker)
                        self.assertIsNone(router.active)
                        kill.assert_called_once_with(proc.pid,signal.SIGTERM)

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
        self.assertIsNone(self.sample(MemoryGuard(), swap=12*GIB))
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
