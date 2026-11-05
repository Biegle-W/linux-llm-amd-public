"""Final supervisor failure must not retain an uncommitted engine promotion."""
from pathlib import Path
import json,sys,tempfile,types,unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh')]
import nightly

class FinalGuardRollback(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.stage=Path(self.temp.name);(self.stage/'result').mkdir();self.prior={'production':'old','manual_note':'preserve'};(self.stage/'engine-before.private.json').write_text(json.dumps(self.prior));(self.stage/'result/result.private.json').write_text(json.dumps({'result':'promoted','status':'passed','detail':'Inner checks passed'}));self.state={'engines':{'test':{'production':'new'},'other':{'production':'untouched'}}};self.plan={'current':'old','latest':'new','stage':str(self.stage)};self.engine=types.SimpleNamespace(kind='test',current=Mock(return_value='new'))
  def rollback(*_):self.engine.current.return_value='old'
  self.engine.rollback=Mock(side_effect=rollback);self.guard={'runner_pid':999,'owned_cgroups_empty':True,'remaining_KFD_clients':[]}
 def run_recovery(self):
  with patch.object(nightly.builders,'load_state',return_value=self.state),patch.object(nightly.builders,'save_state'):
   return nightly.reject_failed_guard(self.engine,self.stage,self.plan,self.guard)
 def test_inner_pass_followed_by_final_failure_restores_previous_production(self):
  self.assertTrue(self.run_recovery());self.engine.rollback.assert_called_once();self.assertEqual(self.state['engines']['test']['production'],'old');self.assertEqual(self.state['engines']['test']['manual_note'],'preserve');self.assertEqual(self.state['engines']['test']['rejected'],'new');self.assertEqual(self.state['engines']['other'],{'production':'untouched'});self.assertNotIn('provisional',self.state)
  result=json.loads((self.stage/'result/result.private.json').read_text());self.assertEqual(result['inner_result'],'promoted');self.assertEqual(result['result'],'rejected');self.assertTrue(result['rollback_verified']);self.assertFalse(json.loads((self.stage/'outer-guard-recovery.private.json').read_text())['hold_released'])
 def test_unclean_worker_boundary_retains_provisional_and_never_moves_runtime(self):
  self.guard['owned_cgroups_empty']=False;self.assertFalse(self.run_recovery());self.engine.rollback.assert_not_called();self.assertTrue(self.state['provisional']['outer_guard_failure']);self.assertEqual(self.state['engines']['test']['production'],'new')
 def test_another_provisional_transaction_is_preserved(self):
  self.state['provisional']={'engine':'other','stage':'other-stage'}
  with self.assertRaisesRegex(RuntimeError,'Another provisional'):self.run_recovery()
  self.engine.rollback.assert_not_called();self.assertEqual(self.state['provisional']['stage'],'other-stage')
 def test_admission_block_without_runner_does_not_reject_untested_source(self):
  self.guard.pop('runner_pid');before=json.dumps(self.state,sort_keys=True);self.assertTrue(self.run_recovery());self.engine.rollback.assert_not_called();self.assertEqual(json.dumps(self.state,sort_keys=True),before)

if __name__=='__main__':unittest.main()
