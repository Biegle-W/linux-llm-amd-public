import sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
import resource_policy
from streaming_memory import GIB,check_32gb

LIMITS={'memory.high':'max','memory.max':31*GIB,'memory.swap.max':8*GIB}

class BoundedTiers(unittest.TestCase):
 # 32 GB tier admission under owner-headroom-v1 (commit 99ec1b1, RESOURCE-GUARDS-2026-11-03.md).
 # Worker scope limits (MemTotal-1GiB) are covered by test_owner_resource_policy.
 def setUp(self):
  p=patch.object(resource_policy,'scope_limits',return_value=dict(LIMITS));p.start();self.addCleanup(p.stop)
 def cfg(self,family='deepseek'):
  cfg={'host_ram_profile':'32gb-v1','args':['--max-context','32768']}
  if family=='qwen':cfg.update(minimum_host_ram_gib=29,args=['--max-context','262144','--kv-resident','32768','--resident-budget-gib','8'])
  if family=='glm':cfg['env']={'MAYA_GLM_RAM_GB':'8','MAYA_GLM_RAM_HEADROOM_GB':'1'}
  return cfg
 def test_no_tier_is_not_a_32gb_profile(self):
  self.assertFalse(check_32gb({},1,1,'deepseek'))
 def test_all_families_admitted(self):
  for f in ['qwen','glm','deepseek']:
   self.assertTrue(check_32gb(self.cfg(f),30.56*GIB,9*GIB,f))
 def test_old32_rejects_insufficient_physical_ram(self):
  for f in ['qwen','glm','deepseek']:
   with self.assertRaises(RuntimeError):check_32gb(self.cfg(f),28.99*GIB,26*GIB,f)
 def test_available_ram_floor(self):
  # Qwen: expert budget + 1 GiB; GLM/DeepSeek: 9 GiB. Swap is not capacity.
  for f,budget,need in [('qwen','8',9),('qwen','12',13),('glm',None,9),('deepseek',None,9)]:
   c=self.cfg(f)
   if budget:c['args'][-1]=budget
   self.assertTrue(check_32gb(c,31*GIB,need*GIB,f))
   with self.assertRaisesRegex(RuntimeError,'available RAM'):check_32gb(c,31*GIB,need*GIB-1,f)
 def test_pre_handover_keeps_physical_gate(self):
  self.assertTrue(check_32gb(self.cfg(),31*GIB,1,'deepseek',check_available=False))
  with self.assertRaises(RuntimeError):check_32gb(self.cfg(),28*GIB,1,'deepseek',check_available=False)
 def test_unknown_tier_rejected(self):
  c=self.cfg();c['host_ram_profile']='unchecked'
  with self.assertRaisesRegex(RuntimeError,'Unknown streaming RAM profile'):check_32gb(c,31*GIB,26*GIB,'deepseek')
 def test_qwen_cannot_fake_unbounded_profile(self):
  c=self.cfg('qwen');c['args'][-1]='24'
  with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,'qwen')
 def test_glm_native_headroom_is_policy_value(self):
  for v in ['6','12',None]:
   c=self.cfg('glm');c['env']['MAYA_GLM_RAM_HEADROOM_GB']=v
   with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,'glm')
 def test_context_must_remain_qualified(self):
  for f in ['qwen','glm','deepseek']:
   c=self.cfg(f);c['args'][1]='8192'
   with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,f)
 def test_invalid_host_capacity_refuses(self):
  with patch.object(resource_policy,'scope_limits',side_effect=RuntimeError('Invalid physical RAM/swap capacity')):
   with self.assertRaisesRegex(RuntimeError,'Invalid physical'):check_32gb(self.cfg(),31*GIB,26*GIB,'deepseek')

if __name__=='__main__':unittest.main()
