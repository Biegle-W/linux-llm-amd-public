import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dsh'))
from streaming_memory import GIB,scope_limits,scope_properties,check_32gb,check_64gb
class FinalHardwareAdmission(unittest.TestCase):
 def cfg(self):
  return {'host_ram_profile':'64gb-q1-v1','worker_memory_limits':{'memory.high':42*GIB,'memory.max':44*GIB,'memory.swap.max':'max'},'args':['--max-context','32768','--cpu-threads','20'],'env':{'DS4_WARM_CAP_GB':'28','DS4_ENGRAM_CACHE_MB':'1024'}}
 def test_available_memory_is_reserved_beyond_enforced_cgroup(self):
  c=self.cfg();self.assertTrue(check_32gb(c,61.55*GIB,47*GIB,'deepseek'))
  with self.assertRaises(RuntimeError):check_32gb(c,61.55*GIB,47*GIB-1,'deepseek')
  self.assertIn('--property=MemoryMax='+str(44*GIB),scope_properties(c))
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
 def test_cgroup_limits_cannot_be_relaxed_or_mistyped(self):
  for name,value in [('memory.max',52*GIB),('memory.high',43*GIB),('memory.swap.max',0),('memory.max',float(44*GIB))]:
   c=self.cfg();c['worker_memory_limits'][name]=value
   with self.assertRaises(RuntimeError):scope_limits(c)
 def test_unknown_tiers_still_fail_closed(self):
  c=self.cfg();c['host_ram_profile']='64gb-unchecked'
  with self.assertRaises(RuntimeError):scope_limits(c)
if __name__=='__main__':unittest.main()
