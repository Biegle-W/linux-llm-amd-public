import sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dsh'))
import resource_policy
from streaming_memory import GIB,check_32gb,check_64gb_qwen
import strata_runtime
LIMITS={'memory.high':'max','memory.max':63*GIB,'memory.swap.max':8*GIB}
class QwenLargeBudget(unittest.TestCase):
 # 64gb-qwen-v1 (owner choice, November 17 2026): 12/20/24 GiB expert budget on a host with at least 60 GiB.
 def setUp(self):
  p=patch.object(resource_policy,'scope_limits',return_value=dict(LIMITS));p.start();self.addCleanup(p.stop)
 def cfg(self,budget='24'):
  return {'host_ram_profile':'64gb-qwen-v1','minimum_host_ram_gib':60,
          'args':['--max-context','262144','--kv-resident','32768','--resident-budget-gib',budget]}
 def test_admitted_through_legacy_entrypoint(self):
  for budget in ['12','20','24']:
   need=GIB   # the one free-RAM floor since November 18 (was budget + 1 GiB)
   self.assertTrue(check_32gb(self.cfg(budget),61.5*GIB,need,'qwen'))
   with self.assertRaisesRegex(RuntimeError,'available RAM'):check_32gb(self.cfg(budget),61.5*GIB,need-1,'qwen')
 def test_small_host_refused_even_with_swap(self):
  with self.assertRaises(RuntimeError):check_64gb_qwen(self.cfg(),60*GIB-1,100*GIB,'qwen')
  with self.assertRaises(RuntimeError):check_64gb_qwen(self.cfg(),31*GIB,1,'qwen',check_available=False)
 def test_pre_handover_keeps_physical_admission(self):
  self.assertTrue(check_64gb_qwen(self.cfg(),61*GIB,1,'qwen',check_available=False))
 def test_other_budgets_and_layouts_refused(self):
  for budget in ['8','25','32','48']:
   with self.assertRaises(RuntimeError):check_64gb_qwen(self.cfg(budget),64*GIB,60*GIB,'qwen')
  c=self.cfg();c['args'][1]='131072'
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
  c=self.cfg();c['args'][3]='65536'
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
  c=self.cfg();c['minimum_host_ram_gib']=29
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
 def test_other_engines_cannot_use_the_tier(self):
  for family in ['glm','deepseek']:
   with self.assertRaises(RuntimeError):check_32gb(self.cfg(),64*GIB,60*GIB,family)
 def test_32gb_tier_still_refuses_24(self):
  c=self.cfg();c['host_ram_profile']='32gb-v1';c['minimum_host_ram_gib']=29
  with self.assertRaises(RuntimeError):check_32gb(c,64*GIB,60*GIB,'qwen')
 def whole(self):
  return {'host_ram_profile':'64gb-qwen-v1','minimum_host_ram_gib':60,'expert_ram_mode':'all-off-card',
          'args':['--max-context','262144','--kv-resident','32768','--resident-cpu-experts']}
 def test_all_off_card_mode_uses_the_plain_floor(self):
  self.assertTrue(check_32gb(self.whole(),61.5*GIB,GIB,'qwen'))
  with self.assertRaisesRegex(RuntimeError,'available RAM'):check_32gb(self.whole(),61.5*GIB,GIB-1,'qwen')
  with self.assertRaises(RuntimeError):check_64gb_qwen(self.whole(),60*GIB-1,100*GIB,'qwen')
 def test_all_off_card_mode_refuses_a_budget_or_missing_backing(self):
  c=self.whole();c['args']+=['--resident-budget-gib','24']
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
  c=self.whole();c['args'].remove('--resident-cpu-experts')
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
  c=self.whole();c['expert_ram_mode']='everything'
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
  c=self.cfg();del c['args'][4:]
  with self.assertRaises(RuntimeError):check_64gb_qwen(c,64*GIB,60*GIB,'qwen')
 def strata(self,cfg):
  cfg.update(backend='hip',gpu=[0,1],parallel=1,worker_swap_max_bytes=None)
  cfg['args']+=['--vram-reserve-mib','128']+([] if '--resident-cpu-experts' in cfg['args'] else ['--resident-cpu-experts']);return cfg
 def test_strata_admission_is_the_plain_floor_with_or_without_a_budget(self):
  # November 18 2026: neither the expert budget nor the 3.35 GiB host KV of the 256K layout is counted.
  for cfg in [self.strata(self.whole()),self.strata(self.cfg('24'))]:
   strata_runtime.check_config(cfg,61.5*GIB,GIB)
   with self.assertRaisesRegex(RuntimeError,'available RAM'):strata_runtime.check_config(cfg,61.5*GIB,GIB-1)
   strata_runtime.check_config(cfg,61.5*GIB,1,check_available=False)
   with self.assertRaisesRegex(RuntimeError,'OS-visible|physical'):strata_runtime.check_config(cfg,59*GIB,50*GIB)
  self.assertIsNone(strata_runtime.expert_budget_gib(self.strata(self.whole())))
  self.assertEqual(strata_runtime.expert_budget_gib(self.strata(self.cfg('24'))),24.0)
 def test_other_engines_cannot_use_the_all_off_card_mode(self):
  with self.assertRaises(RuntimeError):check_32gb(self.whole(),64*GIB,60*GIB,'deepseek')
if __name__=='__main__':unittest.main()
