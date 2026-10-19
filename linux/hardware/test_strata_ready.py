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
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, 8*GIB))

    def test_reclaimable_old_worker_does_not_block_handover_but_new_load_is_gated(self):
        self.assertEqual(strata_runtime.memory_blockers(30*GIB, 8*GIB, check_available=False), [])
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, 8*GIB))
        self.assertTrue(strata_runtime.memory_blockers(20*GIB, 18*GIB, check_available=False))

    def test_64gb_profile_refuses_32gb(self):
        self.assertTrue(strata_runtime.memory_blockers(30*GIB, 29*GIB, 60, 20))

    def test_64gb_profile_accepts_restored_ram_and_budget(self):
        self.assertEqual(strata_runtime.memory_blockers(62*GIB, 40*GIB, 60, 20), [])

    def test_profile_cannot_remove_desktop_vram_reserve(self):
        cfg = {'backend':'hip','gpu':[0,1],'parallel':1,'worker_swap_max_bytes':0,
               'minimum_host_ram_gib':29,
               'args':['--resident-cpu-experts','--resident-budget-gib','10',
                       '--vram-reserve-mib','3072']}
        with self.assertRaisesRegex(RuntimeError, '6 GiB'):
            strata_runtime.check_config(cfg,30*GIB,24*GIB)
        cfg['args'][-1]='6144'
        strata_runtime.check_config(cfg,30*GIB,24*GIB)
        cfg['args'] += ['--vram-reserve-later-mib','1024']
        with self.assertRaisesRegex(RuntimeError, '6 GiB'):
            strata_runtime.check_config(cfg,30*GIB,24*GIB)

    def test_owned_hip_engine_is_stopped_but_comfyui_is_not(self):
        root = Path('/opt/local-llm')
        def proc(exe, args=(), cwd=''):
            return backend_switch.Process(7, 1, '42', (exe, *args), cwd, 'S')
        self.assertTrue(backend_switch.is_inference(proc(str(root/'strata/build-hip/strata')),root))
        self.assertFalse(backend_switch.is_inference(proc(str(root/'runtime/comfyui/.venv/bin/python'), ('main.py',)),root))

if __name__ == '__main__':
    unittest.main()
