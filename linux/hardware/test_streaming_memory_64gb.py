import sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dsh'))
import resource_policy
from streaming_memory import GIB,check_32gb,check_64gb
LIMITS={'memory.high':'max','memory.max':63*GIB,'memory.swap.max':8*GIB}
class FinalHardwareAdmission(unittest.TestCase):
 # 64gb-q1-v1 admission under owner-headroom-v1 (commit 99ec1b1); worker scope limits
 # (MemTotal-1GiB) are covered by test_owner_resource_policy.
 def setUp(self):
  p=patch.object(resource_policy,'scope_limits',return_value=dict(LIMITS));p.start();self.addCleanup(p.stop)
 def cfg(self):
  return {'host_ram_profile':'64gb-q1-v1','args':['--max-context','32768','--cpu-threads','20'],'env':{'DS4_WARM_CAP_GB':'28','DS4_ENGRAM_CACHE_MB':'1024'}}
 def test_available_memory_floor(self):
  c=self.cfg();self.assertTrue(check_32gb(c,61.55*GIB,29*GIB,'deepseek'))
  with self.assertRaises(RuntimeError):check_32gb(c,61.55*GIB,29*GIB-1,'deepseek')
 def test_swap_never_substitutes_for_final_physical_capacity(self):
  with self.assertRaises(RuntimeError):check_64gb(self.cfg(),60*GIB-1,100*GIB,'deepseek')
 def test_pre_handover_keeps_physical_admission(self):
  self.assertTrue(check_64gb(self.cfg(),61*GIB,1,'deepseek',check_available=False))
  with self.assertRaises(RuntimeError):check_64gb(self.cfg(),30*GIB,1,'deepseek',check_available=False)
 def test_wrong_engine_cannot_select_a_larger_scope(self):
  for family in ['qwen','glm']:
   with self.assertRaises(RuntimeError):check_32gb(self.cfg(),64*GIB,50*GIB,family)
 def test_cache_growth_and_oversubscribed_cpu_settings_are_rejected(self):
  for edit in ['expert','engram','threads','context']:
   c=self.cfg()
   if edit=='expert':c['env']['DS4_WARM_CAP_GB']='40'
   elif edit=='engram':c['env']['DS4_ENGRAM_CACHE_MB']='8192'
   elif edit=='threads':c['args'][-1]='24'
   else:c['args'][1]='131072'
   with self.assertRaises(RuntimeError):check_64gb(c,64*GIB,50*GIB,'deepseek')
 def test_unknown_tiers_still_fail_closed(self):
  c=self.cfg();c['host_ram_profile']='64gb-unchecked'
  with self.assertRaisesRegex(RuntimeError,'Unknown streaming RAM profile'):check_32gb(c,64*GIB,50*GIB,'deepseek')
if __name__=='__main__':unittest.main()
