"""Keep low-RAM admission bounded and the future profile physically gated."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dsh'))
import strata_runtime
import backend_switch
GIB = 1024**3

class StrataMemoryTests(unittest.TestCase):
    def test_32gb_accepts_bounded_experts_with_headroom(self):
        self.assertEqual(strata_runtime.memory_blockers(30*GIB, 14*GIB), [])

    def test_swap_does_not_replace_physical_headroom(self):
        # Owner choice, November 18 2026: one 1 GiB free-RAM floor, no per-model figure.
        self.assertEqual(strata_runtime.memory_blockers(30*GIB, GIB), [])
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, GIB-1))

    def test_reclaimable_old_worker_does_not_block_handover_but_new_load_is_gated(self):
        self.assertEqual(strata_runtime.memory_blockers(30*GIB, GIB-1, check_available=False), [])
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, GIB-1))
        self.assertTrue(strata_runtime.memory_blockers(20*GIB, 18*GIB, check_available=False))

    def test_64gb_profile_refuses_32gb(self):
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, 29*GIB, 60))

    def test_64gb_profile_accepts_restored_ram(self):
        self.assertEqual(strata_runtime.memory_blockers(62*GIB, 40*GIB, 60), [])

    def test_streamed_context_host_kv_is_not_counted_at_admission(self):
        cfg = {'args':['--max-context','262144','--kv-resident','32768','--kv','int8']}
        backing = strata_runtime.kv_backing_gib(cfg)
        self.assertAlmostEqual(backing, 3.3515625)
        # November 18 2026: admission no longer adds the expert budget and host KV; the floor alone decides.
        self.assertEqual(strata_runtime.memory_blockers(30*GIB,GIB), [])
        self.assertTrue(strata_runtime.memory_blockers(30*GIB,GIB-1))

    def test_fully_resident_kv_needs_no_host_context_copy(self):
        cfg = {'args':['--max-context','32768','--kv-resident','32768','--kv','int8']}
        self.assertEqual(strata_runtime.kv_backing_gib(cfg),0)

    def test_q4_stream_keeps_int8_draft_backing(self):
        cfg = {'args':['--max-context','524288','--kv-resident','32768','--kv','q4_0']}
        self.assertAlmostEqual(strata_runtime.kv_backing_gib(cfg),3.890625)

    def test_profile_cannot_remove_desktop_vram_reserve(self):
        cfg = {'backend':'hip','gpu':[0,1],'parallel':1,'worker_swap_max_bytes':None,
               'minimum_host_ram_gib':29,
               'args':['--resident-cpu-experts','--resident-budget-gib','10',
                       '--vram-reserve-mib','127']}
        # Owner headroom policy (99ec1b1): per-card reserve floor is 128 MiB (was 6144 MiB).
        with self.assertRaisesRegex(RuntimeError, 'active resource policy'):
            strata_runtime.check_config(cfg,30*GIB,24*GIB)
        cfg['args'] = cfg['args'][:-2]
        with self.assertRaisesRegex(RuntimeError, 'active resource policy'):
            strata_runtime.check_config(cfg,30*GIB,24*GIB)
        cfg['args'] += ['--vram-reserve-mib','128']
        strata_runtime.check_config(cfg,30*GIB,24*GIB)
        cfg['args'] += ['--vram-reserve-later-mib','127']
        with self.assertRaisesRegex(RuntimeError, 'active resource policy'):
            strata_runtime.check_config(cfg,30*GIB,24*GIB)

    def test_owned_hip_engine_is_stopped_but_comfyui_is_not(self):
        root = Path('/opt/local-llm')
        def proc(exe, args=(), cwd=''):
            return backend_switch.Process(7, 1, '42', (exe, *args), cwd, 'S')
        self.assertTrue(backend_switch.is_inference(proc(str(root/'strata/build-hip/strata')),root))
        self.assertFalse(backend_switch.is_inference(proc(str(root/'runtime/comfyui/.venv/bin/python'), ('main.py',)),root))

if __name__ == '__main__':
    unittest.main()
