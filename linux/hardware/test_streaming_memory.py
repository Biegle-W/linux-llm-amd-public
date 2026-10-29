import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from streaming_memory import GIB,check_32gb,scope_limits,scope_properties

class BoundedTiers(unittest.TestCase):
 def cfg(self,family='deepseek',maximum=20):
  cfg={'host_ram_profile':'32gb-v1','worker_memory_limits':{'memory.high':(maximum-2)*GIB,'memory.max':maximum*GIB,'memory.swap.max':'max'},'args':['--max-context','32768']}
  if family=='qwen':cfg.update(minimum_host_ram_gib=29,args=['--max-context','262144','--kv-resident','32768','--resident-budget-gib','8'])
  if family=='glm':cfg['env']={'MAYA_GLM_RAM_GB':'8','MAYA_GLM_RAM_HEADROOM_GB':'12'}
  return cfg
 def test_legacy64_scope_and_admission_unchanged(self):
  self.assertEqual(scope_limits({}),{'memory.max':52*GIB,'memory.swap.max':'max'})
  self.assertFalse(check_32gb({},1,1,'deepseek'))
 def test_all_families_both_bounded_tiers(self):
  for f in ['qwen','glm','deepseek']:
   for cap in [20,22]:
    c=self.cfg(f,cap);self.assertTrue(check_32gb(c,30.56*GIB,(cap+3)*GIB,f));self.assertIn('--property=MemoryMax='+str(cap*GIB),scope_properties(c))
 def test_old32_rejects_insufficient_physical_ram(self):
  for f in ['qwen','glm','deepseek']:
   with self.assertRaises(RuntimeError):check_32gb(self.cfg(f),28.99*GIB,26*GIB,f)
 def test_reserve_three_gib_beyond_cap(self):
  for cap in [20,22]:
   with self.assertRaises(RuntimeError):check_32gb(self.cfg(maximum=cap),31*GIB,(cap+2.99)*GIB,'deepseek')
 def test_pre_handover_keeps_physical_gate(self):
  self.assertTrue(check_32gb(self.cfg(),31*GIB,1,'deepseek',check_available=False))
  with self.assertRaises(RuntimeError):check_32gb(self.cfg(),28*GIB,1,'deepseek',check_available=False)
 def test_memory_cap_cannot_be_increased_or_omitted(self):
  for v in [0,24*GIB,52*GIB,'max',20.0*GIB,True]:
   c=self.cfg();c['worker_memory_limits']['memory.max']=v
   with self.assertRaises(RuntimeError):scope_limits(c)
  c=self.cfg();c.pop('worker_memory_limits')
  with self.assertRaises(RuntimeError):scope_limits(c)
 def test_high_boundary_cannot_be_changed(self):
  c=self.cfg();c['worker_memory_limits']['memory.high']=20*GIB
  with self.assertRaises(RuntimeError):scope_limits(c)
 def test_phase_aware_swap_is_preserved(self):
  for v in [0,1,None]:
   c=self.cfg();c['worker_memory_limits']['memory.swap.max']=v
   with self.assertRaises(RuntimeError):scope_limits(c)
 def test_unknown_tier_rejected(self):
  c=self.cfg();c['host_ram_profile']='unchecked'
  with self.assertRaises(RuntimeError):scope_limits(c)
 def test_qwen_cannot_fake_unbounded_profile(self):
  c=self.cfg('qwen');c['args'][-1]='24'
  with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,'qwen')
 def test_glm_cannot_lower_native_headroom(self):
  c=self.cfg('glm');c['env']['MAYA_GLM_RAM_HEADROOM_GB']='6'
  with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,'glm')
 def test_context_must_remain_qualified(self):
  for f in ['qwen','glm','deepseek']:
   c=self.cfg(f);c['args'][1]='8192'
   with self.assertRaises(RuntimeError):check_32gb(c,31*GIB,26*GIB,f)

if __name__=='__main__':unittest.main()
