"""Supervisor loss must latch a hold and clean only previously attested scopes."""
from pathlib import Path
import importlib.util,json,os,sys,tempfile,time,types,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh')]
spec=importlib.util.spec_from_file_location('watchdog_tested',ROOT/'hardware/daily-update/prevention_guard.py');watchdog=importlib.util.module_from_spec(spec);spec.loader.exec_module(watchdog)

class SupervisorLoss(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.stage=self.root/'stage';self.stage.mkdir();(self.root/'hardware/generated').mkdir(parents=True);self.owner='daily-update-owned-test';self.lock=self.root/'hardware/generated/GPU-LOCK';self.lock.write_text(json.dumps({'owner':self.owner}));self.stat=os.stat(self.stage);self.scopes=[]
  base=Path('/sys/fs/cgroup/user.slice')/('user-'+str(os.getuid())+'.slice')/('user@'+str(os.getuid())+'.service');self.unit='dsh-worker-owned-test.scope'
  h={'monotonic':time.monotonic(),'owner':self.owner,'controller_pid':123456789,'owned_units':[self.unit],'owned_scopes':{self.unit:{'directory':str(base/'app.slice'/self.unit),'device':self.stat.st_dev,'inode':self.stat.st_ino}},'runner_unit':'llm-update-run-owned.scope'};(self.stage/'check.heartbeat.private.json').write_text(json.dumps(h))
 def run_watchdog(self,ticks):
  outer=self
  class Scope:
   def __init__(self,path,unit):self.fd=os.open(outer.stage,os.O_RDONLY|os.O_DIRECTORY);self.unit=unit;self.terminated=False;outer.scopes.append(self)
   def terminate(self):self.terminated=True
   def close(self):os.close(self.fd)
  argv=['watchdog',str(self.stage),'check','123456789','expected',self.owner,json.dumps(watchdog.DEFAULT)]
  with patch.object(watchdog,'__file__',str(self.root/'hardware/daily-update/prevention_guard.py')),patch.object(sys,'argv',argv),patch.object(sys,'path',list(sys.path)),patch.dict(sys.modules,{'inference_swap':types.SimpleNamespace(OwnedScope=Scope)}),patch.object(watchdog,'start_ticks',side_effect=ticks),patch.object(watchdog.time,'sleep'),patch.object(watchdog.os,'kill') as kill:
   watchdog.main()
  return kill
 def test_dead_supervisor_pins_last_heartbeat_then_cleans_owned_scope(self):
  kill=self.run_watchdog(OSError('gone'));kill.assert_not_called();self.assertEqual([s.unit for s in self.scopes],[self.unit]);self.assertTrue(self.scopes[0].terminated)
  fault=json.loads((self.stage/'check.watchdog-fault.private.json').read_text());self.assertIn('supervisor process ended',fault['reason']);self.assertEqual(fault['cleanup_errors'],[]);self.assertEqual(json.loads(self.lock.read_text())['prior_owner'],self.owner)
 def test_reused_pid_is_not_signalled_and_another_lock_owner_is_untouched(self):
  other={'owner':'unrelated-current-owner'};self.lock.write_text(json.dumps(other));kill=self.run_watchdog(lambda _: 'different-start-ticks');kill.assert_not_called();self.assertTrue(self.scopes[0].terminated);self.assertEqual(json.loads(self.lock.read_text()),other)
 def test_normal_completed_stop_does_not_latch_a_fault(self):
  (self.stage/'check.watchdog-stop.private.json').write_text('{}');kill=self.run_watchdog(OSError('already completed'));kill.assert_not_called();self.assertFalse(self.scopes);self.assertFalse((self.stage/'check.watchdog-fault.private.json').exists());self.assertEqual(json.loads(self.lock.read_text())['owner'],self.owner)

if __name__=='__main__':unittest.main()
