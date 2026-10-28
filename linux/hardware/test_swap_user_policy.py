"""Current user policy: swap telemetry alone must not terminate work."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hardware'),str(ROOT/'dsh')]
import swap_activity as p
import inference_memory as memory
from inference_swap import OwnedWorkerWatch
G=1024**3;M=1024**2
def host(t=0,si=0,so=0,ram=8*G,psi=0):return dict(timestamp=float(t),swapin_bytes=si,swapout_bytes=so,available_bytes=ram,memory_full_psi_avg10=psi)
def progress(n,**kw):return dict(dict(completed_units=n,baseline_units_per_second=100,workload_id='task',baseline_id='control',baseline_workload_id='task'),**kw)
class UserSwapPolicy(unittest.TestCase):
 def setUp(self):
  env=patch.dict(os.environ);env.start();self.addCleanup(env.stop)
  os.environ.pop('LOCAL_LLM_SWAP_POLICY',None);os.environ.pop('LOCAL_LLM_LEGACY_SWAP_VALIDATION',None)
 def window(self,si=0,so=0,end=None,budget=None):
  a=p.SwapActivity(write_budget_bytes_per_second=budget)
  a.observe(host(),phase='inference',worker_swap_bytes=20*G,progress=progress(0) if end is not None else None)
  a.observe(host(30,si,so),phase='inference',worker_swap_bytes=20*G,progress=end)
  return a
 def allowed(self,a):
  self.assertEqual(a.failures(),[]);self.assertEqual(p.validate_summary(a.summary(),True),[])
 def test_default_and_inherited_old_modes(self):
  self.assertEqual(p.selected_policy(),'loading-swap-v3')
  for old in ['loading-swap-v2','low-churn-v1','bounded-64mib']:
   os.environ['LOCAL_LLM_SWAP_POLICY']=old;self.assertEqual(p.selected_policy(),'loading-swap-v3');self.assertIsNone(memory.worker_swap_limit_bytes())
  os.environ['LOCAL_LLM_LEGACY_SWAP_VALIDATION']='1';self.assertEqual(p.selected_policy(),'bounded-64mib')
 def test_loading_then_parked_swap(self):
  a=p.SwapActivity();a.observe(host())
  for t in [1,2,3]:a.observe(host(t,t*10*G,t*20*G,psi=90),worker_swap_bytes=24*G)
  a.observe(host(4,30*G,60*G),phase='inference',worker_swap_bytes=24*G)
  a.observe(host(34,30*G,60*G),phase='inference',worker_swap_bytes=24*G);self.allowed(a)
 def test_reads_alone(self):
  a=self.window(si=300*G);self.allowed(a);self.assertIn('inference_swap_io_rate_observed',a.summary()['advisories'])
 def test_h3_read_heavy_replay(self):self.allowed(self.window(si=int(14.874*M*30)-48*1024,so=48*1024))
 def test_writes_without_measured_slowdown(self):self.allowed(self.window(so=6000*M,budget=M))
 def test_writes_and_slowdown_without_budget(self):
  a=self.window(so=6000*M,end=progress(1500));self.allowed(a);self.assertEqual(a.summary()['measured_slowdown_windows'],1)
 def test_reads_and_slowdown_with_write_budget(self):self.allowed(self.window(si=6000*M,end=progress(1500),budget=M))
 def test_writes_and_fast_compute(self):self.allowed(self.window(so=6000*M,end=progress(3000),budget=M))
 def test_explicit_budget_plus_matched_slowdown(self):
  a=self.window(so=60*M,end=progress(1500),budget=M)
  self.assertEqual(a.failures(),['sustained_writes_with_measured_slowdown'])
  self.assertEqual(p.validate_summary(a.summary(),True),a.failures())
  self.assertEqual(a.summary()['last_confirmed_write_slowdown']['throughput_ratio'],.5)
 def test_inclusive_budget_and_95_percent_boundary(self):
  for amount,units in [(30*M,0),(60*M,2850)]:self.allowed(self.window(so=amount,end=progress(units),budget=M))
 def test_bad_or_unmatched_progress(self):
  for end in [dict(progress(1),baseline_workload_id='other'),dict(progress(1),baseline_units_per_second=0),{},'bad',dict(progress(1),completed_units=-1),dict(progress(1),baseline_units_per_second=float('nan'))]:
   a=self.window(so=6000*M,end=end,budget=M);self.allowed(a);self.assertIn('invalid_or_unmatched_progress_evidence',a.summary()['advisories'])
 def test_endpoint_control_identity_must_match(self):
  for end in [dict(progress(1500),baseline_id='other'),dict(progress(1500),baseline_units_per_second=101),dict(progress(1500),workload_id='other',baseline_workload_id='other')]:self.allowed(self.window(so=6000*M,end=end,budget=M))
 def test_pressure_advisory_and_independent_physical_floor(self):
  a=p.SwapActivity()
  for t in [0,1,2]:a.observe(host(t,psi=90),phase='inference')
  self.assertEqual(a.failures(),[]);self.assertIn('active_memory_pressure_observed',a.summary()['advisories'])
  for t in [3,4,5]:a.observe(host(t,ram=G))
  self.assertIn('low_host_memory',a.failures())
 def test_phase_change_cannot_join_short_compute_windows(self):
  a=p.SwapActivity(write_budget_bytes_per_second=M);a.observe(host(),phase='inference',progress=progress(0));a.observe(host(29,so=200*M),phase='inference',progress=progress(1))
  a.set_phase('loading');a.set_phase('inference');a.observe(host(30,so=400*M),phase='inference',progress=progress(2));self.assertEqual(a.failures(),[]);self.assertEqual(a.summary()['inference_window_samples'],0)
 def test_stop_claim_requires_budget_and_measured_evidence(self):
  a=self.window(so=60*M,end=progress(1500),budget=M)
  for key,value in [('last_confirmed_write_slowdown',None),('write_budget_bytes_per_second',None)]:
   s=a.summary();s[key]=value;self.assertIn('invalid_progress_or_write_budget_evidence',p.validate_summary(s,True))
  s=a.summary();s['last_confirmed_write_slowdown']['throughput_ratio']=.99;self.assertIn('invalid_progress_or_write_budget_evidence',p.validate_summary(s,True))
 def test_evidence_copies_are_detached(self):
  a=self.window(so=60*M,end=progress(1500),budget=M);s=a.summary();s['last_confirmed_write_slowdown']['throughput_ratio']=.99;s['advisories'].append('mutated');self.assertEqual(a.summary()['last_confirmed_write_slowdown']['throughput_ratio'],.5);self.assertNotIn('mutated',a.summary()['advisories'])
 def test_router_does_not_terminate_for_swap(self):
  proc=Mock();proc.poll.return_value=None;stop=Mock();reading=host()
  watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:reading,memory_reader=lambda:dict(swap=24*G,spill=0,processes=1));watch.ready();watch.sample();reading.update(host(30,300*G,60*G,psi=90));watch.sample();self.assertIsNone(watch.fault);stop.assert_not_called()
 def test_router_still_protects_dedicated_vram_residency(self):
  proc=Mock();proc.poll.return_value=None;stop=Mock();watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:host(),memory_reader=lambda:dict(swap=24*G,spill=1,processes=1));watch.sample();self.assertIn('vram_spill',watch.fault);stop.assert_called_once_with(proc,watch.fault)
 def test_lifecycle_validator_does_not_reintroduce_caps_or_relabel_history(self):
  a=self.window(si=300*G,so=60*G);s=dict(max_worker_swap_bytes=20*G,max_nonresident_vram_bytes=0,swap_activity=a.summary());self.assertEqual(memory.memory_failures(s),[]);s['swap_activity']['policy']='loading-swap-v2';self.assertIn('swap_activity_invalid_policy',memory.memory_failures(s))
 def test_counter_reset_or_baseline_switch_cannot_create_a_slowdown_claim(self):
  for middle in [progress(0),dict(progress(100),baseline_id='other')]:
   a=p.SwapActivity(write_budget_bytes_per_second=M)
   a.observe(host(),phase='inference',progress=progress(100))
   a.observe(host(15,so=60*M),phase='inference',progress=middle)
   a.observe(host(30,so=120*M),phase='inference',progress=progress(200))
   self.allowed(a);self.assertEqual(a.summary()['measured_slowdown_windows'],0)
 def test_explicit_router_budget_needs_matching_progress(self):
  proc=Mock();proc.poll.return_value=None;stop=Mock();reading=host();units={'n':0}
  watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:reading,
   memory_reader=lambda:dict(swap=24*G,spill=0,processes=1,progress=progress(units['n'])),write_budget_bytes_per_second=M)
  watch.ready();watch.sample();reading.update(host(30,so=60*M));units['n']=1500;watch.sample()
  self.assertEqual(watch.fault,'sustained_writes_with_measured_slowdown');stop.assert_called_once_with(proc,watch.fault)
 def test_benchmark_monitor_records_progress_without_a_default_stop_budget(self):
  monitor=memory.MemoryMonitor();readings=[host(),host(30,so=60*M)]
  with patch.object(memory,'sample_memory',side_effect=[dict(swap=20*G,spill=0,progress=progress(0)),dict(swap=20*G,spill=0,progress=progress(1500))]),patch.object(memory,'read_host_activity',side_effect=readings):
   monitor.set_phase('inference');monitor.sample();monitor.sample()
  self.assertEqual(monitor.summary['swap_activity']['measured_slowdown_windows'],1)
  self.assertEqual(memory.memory_failures(monitor.summary),[])
 def test_advisory_logging_failure_cannot_terminate_work(self):
  proc=Mock();proc.poll.return_value=None;stop=Mock();reading=host()
  watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:reading,memory_reader=lambda:dict(swap=24*G,spill=0,processes=1))
  watch.ready();watch.sample();reading.update(host(30,300*G,60*G))
  with patch('builtins.print',side_effect=BrokenPipeError):watch.sample()
  self.assertIsNone(watch.fault);stop.assert_not_called();self.assertEqual(watch.advisory_log_errors,1)
 def test_bad_explicit_budgets_rejected(self):
  for budget in [0,-1,True,'1',float('inf'),float('nan')]:
   with self.assertRaises(ValueError):p.SwapActivity(write_budget_bytes_per_second=budget)
if __name__=='__main__':unittest.main()
