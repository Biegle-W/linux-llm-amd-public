"""CPU checks for strict coverage, selective native updates and exact rollback."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh')]
import nightly,native_updates

class ShortCoverage(unittest.TestCase):
 def result(self):return {'status':'passed-one-short-DSH-check','owned_unload_requested':True,'requests':[{'status':'completed'},{'status':'completed'}],'tool':{'final_marker_correct':True,'tool_call_result_ids_match':True}}
 def test_complete_strict_round_trip(self):nightly.verify_cases(['model'],{'model':self.result()})
 def test_missing_or_duplicate_model_cannot_promote(self):
  for models,results in [(['one','two'],{'one':self.result()}),(['one','one'],{'one':self.result()}),([], {})]:
   with self.assertRaises(RuntimeError):nightly.verify_cases(models,results)
 def test_partial_stream_or_wrong_marker_cannot_promote(self):
  for change in ['stream','marker','cleanup']:
   result=self.result()
   if change=='stream':result['requests'][1]['status']='starting'
   elif change=='marker':result['tool']['final_marker_correct']=False
   else:result['owned_unload_requested']=False
   with self.assertRaises(RuntimeError):nightly.verify_cases(['model'],{'model':result})

class Readiness(unittest.TestCase):
 def test_healthy_llama_router_requires_its_loaded_model_attestation(self):
  from server_ready import server_ready
  self.assertFalse(server_ready({'status':'ok'},'selected'))
  self.assertTrue(server_ready({'status':'ok'},'selected',{'backend':'llama','model':'selected','loaded':True}))
  self.assertFalse(server_ready({'status':'ok'},'selected',{'backend':'llama','model':'other','loaded':True}))
  self.assertFalse(server_ready({'status':'error'},'selected',{'backend':'llama','model':'selected','loaded':True}))
 def test_router_active_model_must_match(self):
  from server_ready import server_ready
  self.assertTrue(server_ready({'status':'ok','active_model':'selected'},'selected'))
  self.assertFalse(server_ready({'status':'ok','active_model':'other'},'selected'))
 def test_unloaded_health_overrides_attestation(self):
  from server_ready import server_ready
  self.assertFalse(server_ready({'status':'ok','unloaded':True},'selected',{'backend':'llama','model':'selected','loaded':True}))

class SelectiveNativeUpdates(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'dsh').mkdir()
  self.stage=self.root/'hardware/generated/daily-update/test/maya';self.stage.mkdir(parents=True)
  self.source=self.stage/'source';(self.source/'build-hip').mkdir(parents=True);(self.source/'build-hip/maya').write_bytes(b'new engine')
  self.catalog={'qualified':{'enabled':True,'config':'qualified.json'},'held':{'enabled':False,'config':'held.json'},'retired':{'enabled':False,'config':'retired.json'}}
  self.registry={'schema_version':1,'profiles':{k:{'family':'maya','status':'passed','source':'/old/source','source_commit':'a'*40,'binary_relative':'build-hip/maya'} for k in ['qualified','held','retired']}}
  for k in self.catalog:(self.root/'dsh'/(k+'.json')).write_text(json.dumps({'model_name':k,'exe':'/old/source/build-hip/maya','cwd':'/old/source','args':['unchanged'],'env':{'unchanged':'1'}}))
  (self.root/'dsh/maya-profiles.json').write_text(json.dumps(self.catalog));(self.root/'dsh/qualified-native-profiles.json').write_text(json.dumps(self.registry))
  self.before={p:p.read_bytes() for p in (self.root/'dsh').iterdir()}
  self.patch=patch.object(native_updates,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
 def test_only_enabled_qualified_profiles_change_and_exact_rollback(self):
  token=native_updates.install('maya',self.stage,'b'*40,self.source)
  registry=json.loads((self.root/'dsh/qualified-native-profiles.json').read_text())
  self.assertEqual(registry['profiles']['qualified']['status'],'candidate');self.assertEqual(registry['profiles']['qualified']['candidate_owner'],token)
  self.assertEqual(registry['profiles']['held'],self.registry['profiles']['held']);self.assertEqual(registry['profiles']['retired'],self.registry['profiles']['retired'])
  for model in ['held','retired']:self.assertEqual((self.root/'dsh'/(model+'.json')).read_bytes(),self.before[self.root/'dsh'/(model+'.json')])
  self.assertTrue(native_updates.rollback(self.stage))
  for path,old in self.before.items():self.assertEqual(path.read_bytes(),old)
 def test_finalization_changes_only_owned_candidate_and_drops_token(self):
  native_updates.install('maya',self.stage,'b'*40,self.source);native_updates.finalize(self.stage,'b'*40)
  registry=json.loads((self.root/'dsh/qualified-native-profiles.json').read_text())
  self.assertEqual(registry['profiles']['qualified']['status'],'passed');self.assertNotIn('candidate_owner',registry['profiles']['qualified'])
  self.assertEqual(registry['profiles']['held'],self.registry['profiles']['held'])
 def test_unknown_revision_cannot_be_finalized(self):
  native_updates.install('maya',self.stage,'b'*40,self.source)
  with self.assertRaises(RuntimeError):native_updates.finalize(self.stage,'c'*40)

class PublicationQueue(unittest.TestCase):
 def test_failed_publication_retains_queue_and_error(self):
  from unittest.mock import Mock
  import types
  state={'publication_pending':[{'engine':'test','runtime_files':[]}],'engines':{}}
  publish=Mock(side_effect=RuntimeError('offline'))
  with patch.dict(sys.modules,{'publish':types.SimpleNamespace(publish=publish)}),patch.object(nightly.builders,'save_state') as saved:
   self.assertFalse(nightly.retry_publication(state));saved.assert_called_once()
  self.assertEqual(state['publication_pending'][0]['engine'],'test');self.assertIn('offline',state['publication_error'])
 def test_successful_retry_clears_only_publication_state(self):
  from unittest.mock import Mock
  import types
  state={'publication_pending':[{'engine':'test'}],'publication_error':'offline','engines':{'maya':'preserved'}}
  with patch.dict(sys.modules,{'publish':types.SimpleNamespace(publish=Mock())}),patch.object(nightly.builders,'save_state'):
   self.assertTrue(nightly.retry_publication(state))
  self.assertEqual(state,{'engines':{'maya':'preserved'}})
 def test_no_pending_publication_has_no_side_effects(self):
  with patch.object(nightly.builders,'save_state') as saved:self.assertTrue(nightly.retry_publication({'engines':{}}));saved.assert_not_called()
 def test_only_controller_owned_runtime_files_are_candidates(self):
  import types
  self.assertEqual(nightly.changed_runtime_candidates(types.SimpleNamespace(kind='llama')),['dsh/llama-runtime.json'])
  self.assertEqual(nightly.changed_runtime_candidates(types.SimpleNamespace(kind='vllm')),[])

if __name__=='__main__':unittest.main()
