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
import resource_policy
from strata_memory import MemoryGuard, GIB, startup_vram_blocker

MIB = 1024**2
# Owner headroom policy (commit 99ec1b1, Nov 3 2026, hardware/RESOURCE-GUARDS-2026-11-03.md):
# 128 MiB free VRAM per card and 1 GiB available RAM, for startup and the runtime guard.
FLOOR = resource_policy.VRAM_RESERVE_BYTES


def load_profiles():
    return list(json.loads((ROOT/'dsh'/'strata-profiles.json').read_text()).values())


def load_router_fixture(spec,module):
    """Keep guard tests independent of owner-paused production catalogs."""
    original=Path.read_text
    def read(path,*args,**kwargs):
        if path.name=='strata-profiles.json':
            data=json.loads(original(ROOT/'dsh'/path.name,*args,**kwargs))
            for row in data.values():row['enabled']=True
            return json.dumps(data)
        return original(path,*args,**kwargs)
    with patch.object(Path,'read_text',read):spec.loader.exec_module(module)


class StrataGuardTests(unittest.TestCase):
    def test_owner_policy_floor_is_128_mib_per_card(self):
        self.assertEqual(FLOOR, 128*MIB)

    def test_loaded_startup_accepts_policy_floor_on_both_cards(self):
        self.assertIsNone(startup_vram_blocker([{'free':FLOOR}, {'free':FLOOR}]))
        self.assertIsNone(startup_vram_blocker([{'free':5785194496}, {'free':6730600448}]))

    def test_loaded_startup_refuses_either_card_below_policy_floor(self):
        for free in ([FLOOR-1,6*GIB], [6*GIB,FLOOR-1]):
            with self.subTest(free=free):
                self.assertIn('0.125 GiB',startup_vram_blocker([{'free':v} for v in free]))

    def test_loaded_startup_refuses_missing_card_telemetry(self):
        for readings in (None, [], [{'free':6*GIB}]):
            with self.subTest(readings=readings):
                self.assertIn('Both AMD',startup_vram_blocker(readings))

    def test_router_admits_policy_floor_and_stops_owned_worker_below_it(self):
        # DEFAULT is the Qwen route; the deepseek41-only reserve-minus-1GiB floor (b92147a) does not apply.
        self.assertNotEqual(load_profiles()[0].get('family'), 'deepseek41')
        for free,accepted in (([FLOOR,FLOOR],True),([FLOOR-1,6*GIB],False),([6*GIB,FLOOR-1],False)):
            with self.subTest(free=free), tempfile.TemporaryDirectory() as folder:
                spec=importlib.util.spec_from_file_location('strata_startup',ROOT/'dsh/strata-router.py')
                router=importlib.util.module_from_spec(spec);load_router_fixture(spec,router)
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
                        with self.assertRaisesRegex(RuntimeError,'0.125 GiB'):
                            router.ensure_worker(router.DEFAULT)
                        self.assertIsNone(router.worker)
                        self.assertIsNone(router.active)
                        kill.assert_called_once_with(proc.pid,signal.SIGTERM)

    def sample(self, guard, free=4, **kw):
        return guard.check(kw.get('available', 10)*GIB, kw.get('swap', 0),
                           kw.get('spill', 0), [{'free':free*GIB}, {'free':5*GIB}])

    def test_two_cards_and_healthy_headroom_pass(self):
        self.assertIsNone(self.sample(MemoryGuard()))

    def test_policy_floor_unloads_immediately(self):
        guard = MemoryGuard()
        cards = lambda free: [{'free':free}, {'free':5*GIB}]
        self.assertIsNone(guard.check(10*GIB, 0, 0, cards(FLOOR)))
        self.assertIn('VRAM', guard.check(10*GIB, 0, 0, cards(FLOOR-1)))
        self.assertIn('VRAM', MemoryGuard().check(10*GIB, 0, 0, [{'free':5*GIB}, {'free':FLOOR-1}]))
        self.assertIsNone(MemoryGuard().check(GIB, 0, 0, cards(5*GIB)))
        self.assertIn('RAM', MemoryGuard().check(GIB-1, 0, 0, cards(5*GIB)))

    def test_invalid_runtime_telemetry_is_rejected(self):
        with self.assertRaises(ValueError):
            MemoryGuard().check(10*GIB, 0, 0, [{'free':2.8*GIB}, {'free':5*GIB}])
        self.assertIn('Both AMD', MemoryGuard().check(10*GIB, 0, 0, [{'free':5*GIB}]))

    def test_missing_telemetry_fails_closed(self):
        guard = MemoryGuard()
        self.assertIsNone(guard.check(10*GIB, 0, 0, None))
        self.assertIsNone(guard.check(10*GIB, 0, 0, None))
        self.assertIn('telemetry', guard.check(10*GIB, 0, 0, None))

    def test_router_stops_only_its_worker_and_latches_reload(self):
        spec = importlib.util.spec_from_file_location('strata_router', ROOT/'dsh/strata-router.py')
        router = importlib.util.module_from_spec(spec)
        load_router_fixture(spec,router)
        proc = Mock(); proc.poll.return_value = None
        router.worker = proc
        router.stopping = Mock(); router.stopping.wait.side_effect = [False, True]
        with patch.object(router, 'host_memory', return_value=(30*GIB, 10*GIB)), \
             patch.object(router, 'worker_memory', return_value=(0,0)), \
             patch.object(router, 'vram_snapshot', return_value=[{'free':FLOOR-1},{'free':5*GIB}]), \
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
        load_router_fixture(spec,router)
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
