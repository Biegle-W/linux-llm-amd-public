"""Keep MoE admission bounded and leave dense/loaded models alone."""
import sys
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dsh'))
import moe_memory

GIB = 1024**3
PROFILE = {'host_expert_bytes': 9*GIB, 'minimum_host_ram_gib': 28}


class MoeMemoryTests(unittest.TestCase):
    def run_monitor(self, active, available):
        proc = Mock()
        proc.poll.return_value = None
        event = Mock()
        event.wait.side_effect = [False, False, False, True]
        thread = Mock()
        stopped = []
        def make_thread(*args, **kwargs):
            thread.start.side_effect = kwargs['target']
            return thread
        with patch.object(moe_memory, 'profiles', return_value={'moe': PROFILE}), \
             patch.object(moe_memory, 'host_memory', return_value=(30*GIB, available)), \
             patch.object(moe_memory, 'worker_memory', return_value=(0, 0)), \
             patch.object(moe_memory.threading, 'Event', return_value=event), \
             patch.object(moe_memory.threading, 'Thread', side_effect=make_thread):
            moe_memory.watch_worker(proc, lambda: active, stopped.append)
        return proc, stopped

    def test_sustained_low_ram_stops_only_the_owned_native_worker(self):
        proc, stopped = self.run_monitor('moe', 2*GIB)
        self.assertEqual(stopped, [proc])

    def test_memory_watch_does_not_stop_dense_models(self):
        _, stopped = self.run_monitor('dense', 2*GIB)
        self.assertEqual(stopped, [])

    def test_profile_without_explicit_vram_reserve_keeps_existing_behavior(self):
        self.assertIsNone(moe_memory.vram_headroom_reason(PROFILE))

    def test_whole_card_reserve_counts_other_gpu_consumers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            device = root/'gpu'
            device.mkdir()
            (device/'mem_info_vram_total').write_text(str(24*GIB))
            (device/'mem_info_vram_used').write_text(str(22*GIB))
            with patch('amd_device.amd_devices', return_value=[device]):
                self.assertIn('free VRAM', moe_memory.vram_headroom_reason({'min_free_vram_gib':3}))
                self.assertIsNone(moe_memory.vram_headroom_reason({'min_free_vram_gib':1}))

    def test_sustained_vram_reserve_violation_stops_only_owned_worker(self):
        with patch.object(moe_memory, 'vram_headroom_reason', return_value='Low whole-card VRAM'):
            proc, stopped = self.run_monitor('moe', 10*GIB)
        self.assertEqual(stopped, [proc])

    def test_actual_32gb_can_admit_bounded_experts(self):
        self.assertIsNone(moe_memory.memory_reason(PROFILE, 30*GIB, 14*GIB))

    def test_extra_swap_does_not_replace_available_ram(self):
        self.assertIn('available', moe_memory.memory_reason(PROFILE, 30*GIB, 5*GIB))

    def test_loaded_model_does_not_reserve_its_weights_twice(self):
        self.assertIsNone(moe_memory.memory_reason(PROFILE, 30*GIB, 6*GIB, True))
        self.assertIsNotNone(moe_memory.memory_reason(PROFILE, 30*GIB, 2*GIB, True))

    def test_64gb_candidate_refuses_32gb_before_unload(self):
        future = {**PROFILE, 'minimum_host_ram_gib': 60}
        calls = []
        with patch.object(moe_memory, 'profiles', return_value={'moe': future}), \
             patch.object(moe_memory, 'host_memory', return_value=(30*GIB, 25*GIB)):
            with self.assertRaisesRegex(RuntimeError, 'OS-visible'):
                moe_memory.admit_model('moe', lambda *a, **k: calls.append(a), 8081)
        self.assertEqual(calls, [])

    def test_dense_request_does_not_trigger_unload_or_memory_check(self):
        with patch.object(moe_memory, 'profiles', return_value={'moe': PROFILE}), \
             patch.object(moe_memory, 'host_memory', side_effect=AssertionError('unexpected check')):
            moe_memory.admit_model('dense', lambda *a: self.fail('unexpected API call'), 8081)

    def test_loaded_model_keeps_its_cache(self):
        calls = []
        def api(port, path, *args, **kwargs):
            calls.append(path)
            return {'data': [{'id': 'moe', 'status': {'value': 'loaded'}}]}
        with patch.object(moe_memory, 'profiles', return_value={'moe': PROFILE}), \
             patch.object(moe_memory, 'host_memory', return_value=(30*GIB, 6*GIB)):
            moe_memory.admit_model('moe', api, 8081)
        self.assertEqual(calls, ['/v1/models'])

    def test_idle_old_model_released_before_next_cpu_expert_load(self):
        calls = []
        def api(port, path, *args, **kwargs):
            calls.append((path, args))
            return {'data': [{'id': 'old', 'status': {'value': 'loaded'}}]} if path == '/v1/models' else {'success': True}
        with patch.object(moe_memory, 'profiles', return_value={'moe': PROFILE}), \
             patch.object(moe_memory, 'host_memory', side_effect=[(30*GIB, 5*GIB), (30*GIB, 20*GIB)]):
            moe_memory.admit_model('moe', api, 8081)
        self.assertEqual(calls[1], ('/models/unload', ({'model':'old'},)))


    def test_catalogued_moe_cannot_silently_become_gpu_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'models.json').write_text(json.dumps([{'id':'moe','expert_count':256}]))
            with self.assertRaisesRegex(RuntimeError, 'requires explicit'):
                moe_memory.validate_profiles(root)

    def test_missing_cpu_override_rejected_even_if_metadata_claims_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'models.json').write_text(json.dumps([{'id':'moe','expert_count':256}]))
            plan = {'backend':'hip-amd','cpu_expert_layers':[0,2],'gpu_expert_cache_mib':4096}
            (root/'moe-offload.json').write_text(json.dumps({'models':{'moe':plan}}))
            (root/'models-hip.ini').write_text('version = 1\n[*]\n[moe]\nmoe-cache-mib = 4096\n')
            with self.assertRaisesRegex(RuntimeError, 'no longer matches'):
                moe_memory.validate_profiles(root)


if __name__ == '__main__':
    unittest.main()
