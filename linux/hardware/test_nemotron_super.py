"""Check inactive candidate boundaries without allocating model memory."""
import json
from pathlib import Path
import sys
import unittest
import importlib.util
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
sys.path.insert(0,str(ROOT/'hardware'))
import moe_memory
from nemotron_super import GIB, server_args, overrides
spec = importlib.util.spec_from_file_location('activate_nemotron', ROOT/'hardware/activate-nemotron-super.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class NemotronCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT/'dsh/candidates/nemotron-super.json').read_text())

    def test_q4_remains_inactive_and_refuses_32gb_before_any_unload(self):
        profile = self.profiles['nemotron-3.5-super-q4']
        self.assertFalse(profile['enabled'])
        calls = []
        with patch.object(moe_memory,'profiles',return_value={profile['id']:profile}), \
             patch.object(moe_memory,'host_memory',return_value=(30*GIB,25*GIB)):
            with self.assertRaisesRegex(RuntimeError,'OS-visible'):
                moe_memory.admit_model(profile['id'],lambda *args:calls.append(args),8081)
        self.assertEqual(calls,[])

    def test_expert_byte_totals_match_selected_layers(self):
        for profile in self.profiles.values():
            self.assertEqual(profile['host_expert_bytes'],sum(profile['expert_layer_bytes'][str(layer)] for layer in profile['cpu_expert_layers']))
            self.assertNotIn(88,profile['cpu_expert_layers'])

    def test_dual_gpu_cache_and_explicit_cpu_override_are_not_optional(self):
        for profile in self.profiles.values():
            args = server_args(profile)
            self.assertEqual(args[args.index('--device')+1],'ROCm0,ROCm1')
            self.assertEqual(args[args.index('--split-mode')+1],'layer')
            self.assertEqual(args[args.index('--load-mode')+1],'none')
            self.assertGreater(int(args[args.index('--moe-cache-mib')+1]),0)
            self.assertIn('=CPU',overrides(profile))
            self.assertNotIn('--mmproj',args)

    def test_swap_is_not_added_to_admission_capacity(self):
        profile = self.profiles['nemotron-3.5-super-iq3']
        self.assertIsNotNone(moe_memory.memory_reason(profile,30*GIB,20*GIB))
        self.assertIsNone(moe_memory.memory_reason(profile,30*GIB,24*GIB))

    def test_failed_or_unmeasured_profile_cannot_be_activated(self):
        profile = self.profiles['nemotron-3.5-super-iq3']
        with self.assertRaisesRegex(ValueError,'passed result'):
            activation.check_result({'model':profile['id'],'status':'failed'},profile,30*GIB)

    def test_q4_activation_gate_does_not_depend_on_swap_or_profile_name(self):
        profile = self.profiles['nemotron-3.5-super-q4']
        with self.assertRaisesRegex(ValueError,'Physical RAM'):
            activation.check_result({'model':profile['id'],'status':'passed'},profile,30*GIB)


if __name__ == '__main__':
    unittest.main()
