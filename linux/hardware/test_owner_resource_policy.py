"""Owner-requested resource and storage-health boundaries; no GPU or disk I/O."""
from pathlib import Path
import copy
import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'dsh'), str(ROOT / 'hardware')]
import resource_policy as policy
import storage_health as storage
from inference_swap import OwnedWorkerWatch
from strata_memory import MemoryGuard, startup_vram_blocker
from streaming_memory import scope_limits, scope_properties
from swap_activity import SwapActivity, validate_summary

GIB, MIB = 1024**3, 1024**2

def host(t=0, written=0, read=0, available=8*GIB):
    return dict(timestamp=float(t), swapin_bytes=read, swapout_bytes=written,
                available_bytes=available, memory_full_psi_avg10=0.0)

def healthy():
    return [{'device': 'nvme0n1', 'nvme': True, 'updated': 1000,
             'temperature_K': 310, 'critical_warning': [], 'failing': False,
             'failing_attributes': 0, 'media_errors': 0, 'spare': 100, 'spare_threshold': 5}]

class OwnerPolicy(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ, {'LOCAL_LLM_LEGACY_RESOURCE_VALIDATION': '0',
            'LOCAL_LLM_LEGACY_SWAP_VALIDATION': '0', 'LOCAL_LLM_SWAP_POLICY': 'loading-swap-v4'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exact_headroom_boundaries(self):
        cards = [{'free': 128*MIB}, {'free': 128*MIB}]
        self.assertIsNone(policy.headroom_failure(GIB, cards))
        self.assertIn('RAM', policy.headroom_failure(GIB-1, cards))
        cards[1]['free'] -= 1
        self.assertIn('VRAM', policy.headroom_failure(GIB, cards))

    def test_strata_startup_and_runtime_use_same_floor(self):
        cards = [{'free': 128*MIB}, {'free': 128*MIB}]
        self.assertIsNone(startup_vram_blocker(cards))
        self.assertIsNone(MemoryGuard().check(GIB, 30*GIB, 0, cards))
        self.assertIsNotNone(MemoryGuard().check(GIB-1, 0, 0, cards))

    def test_dynamic_scope_disables_high_and_retains_only_existing_swap(self):
        limits = policy.scope_limits({'MemTotal': 64*GIB, 'SwapTotal': 36000755712})
        self.assertEqual(limits, {'memory.high': 'max', 'memory.max': 63*GIB,
                                 'memory.swap.max': 36000755712})
        with patch.object(policy, 'scope_limits', return_value=limits):
            self.assertEqual(scope_limits({'host_ram_profile': '32gb-v1'}), limits)
            self.assertIn('--property=MemoryHigh=infinity', scope_properties({}))

    def test_old_inherited_policy_cannot_restore_throughput_stops(self):
        activity = SwapActivity(write_budget_bytes_per_second=MIB)
        activity.observe(host(), 'inference', 30*GIB)
        activity.observe(host(30, 300*GIB, 300*GIB), 'inference', 30*GIB)
        self.assertEqual(activity.failures(), [])
        summary = activity.summary()
        self.assertEqual(summary['policy'], 'loading-swap-v5')
        self.assertIsNone(summary['write_budget_bytes_per_second'])
        self.assertEqual(validate_summary(summary, True), [])

    def test_owned_watch_stops_on_resource_floor_only(self):
        proc = Mock()
        proc.poll.return_value = None
        stop = Mock()
        state = host()
        watch = OwnedWorkerWatch(proc, stop, host_reader=lambda: state,
            memory_reader=lambda: dict(swap=30*GIB, spill=0, processes=1),
            headroom_reader=lambda: [{'free':128*MIB}, {'free':128*MIB}])
        watch.ready()
        watch.sample()
        state.update(host(30, 300*GIB, 300*GIB))
        watch.sample()
        stop.assert_not_called()
        state['available_bytes'] = GIB-1
        watch.sample()
        stop.assert_called_once_with(proc, watch.fault)

    def test_storage_healthy_and_warning_cases(self):
        self.assertIsNone(storage.evaluate(healthy(), {'nvme0': 99.99}, 1000))
        self.assertIn('100 C', storage.evaluate(healthy(), {'nvme0':100}, 1000))
        records=healthy()
        records[0]['temperature_K']=373.15
        self.assertIn('100 C', storage.evaluate(records, {'nvme0':30}, 1000))
        for field, value in [('critical_warning',['read-only']), ('media_errors',1), ('spare',4)]:
            records=healthy()
            records[0][field]=value
            self.assertIsNotNone(storage.evaluate(records, {'nvme0':30}, 1000))
        with self.assertRaises(ValueError):
            storage.evaluate(healthy(), {'nvme0':30}, 2201)
        with self.assertRaises(ValueError):
            storage.evaluate([], {'nvme0':30}, 1000)

    def test_health_is_checked_without_stopping_on_normal_wear(self):
        records=healthy()
        records[0]['wear_used_percent']=100
        self.assertIsNone(storage.evaluate(records, {'nvme0':30}, 1000))
        now=[0]
        reader=Mock(return_value=records)
        monitor=storage.StorageHealthMonitor(reader=reader, temperatures=lambda:{'nvme0':30},
            clock=lambda:now[0], wall=lambda:1000)
        monitor.check()
        now[0]=29
        monitor.check()
        reader.assert_called_once()
        now[0]=30
        monitor.check()
        self.assertEqual(reader.call_count,2)

    def test_storage_failure_stops_only_owned_worker(self):
        proc=Mock()
        proc.poll.return_value=None
        stop=Mock()
        monitor=Mock()
        monitor.check.side_effect=RuntimeError('SSD SMART health warning')
        watch=OwnedWorkerWatch(proc,stop,host_reader=host,
            memory_reader=lambda:dict(swap=0,spill=0,processes=1),storage_monitor=monitor)
        watch.sample()
        stop.assert_called_once_with(proc,watch.fault)
        self.assertIn('telemetry_error',watch.fault)

if __name__=='__main__':
    unittest.main()
