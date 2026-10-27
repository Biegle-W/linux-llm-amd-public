"""CPU regressions for keeping a blocked model on its qualified runtime."""
import importlib.util,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class RuntimePin(unittest.TestCase):
 def launch(self,override=None):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'vllm').mkdir();shutil.copy2(ROOT/'vllm/start-bolt-rocm',root/'vllm/start-bolt-rocm')
   stub=root/'vllm/run-rocm';stub.write_text('#!/usr/bin/env python3\nimport os,json\nprint(json.dumps({"runtime":os.environ["VLLM_ENV_PATH"]}))\n');stub.chmod(0o755)
   env=os.environ.copy();env.pop('VLLM_ENV_PATH',None)
   if override:env['VLLM_ENV_PATH']=override
   value=json.loads(subprocess.check_output(['bash',str(root/'vllm/start-bolt-rocm')],env=env,text=True));return value['runtime'],str(root/'vllm/bolt-dev435/.venv-rocm')
 def test_bolt_defaults_to_held_runtime(self):
  value,expected=self.launch();self.assertEqual(value,expected)
 def test_explicit_candidate_override_remains_testable(self):
  value,_=self.launch('/test/isolated-candidate');self.assertEqual(value,'/test/isolated-candidate')
 def test_updater_excludes_pins_and_disabled_profiles(self):
  spec=importlib.util.spec_from_file_location('runtime_pin_daily',ROOT/'hardware/daily-update/daily_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'dsh').mkdir();(root/'dsh/vllm-profiles.json').write_text(json.dumps({'a':{},'held':{'manual_runtime_pin':'old'},'disabled':{'enabled':False},'b':{'enabled':True}}))
   with patch.object(m,'ROOT',root):self.assertEqual(m.Vllm().models(),['a','b'])
 def test_publisher_reports_held_runtime_separately(self):
  import types,sys
  spec=importlib.util.spec_from_file_location('runtime_pin_publish',ROOT/'hardware/daily-update/publish.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'dsh').mkdir();(root/'dsh/vllm-profiles.json').write_text(json.dumps({'held':{'manual_runtime_pin':'old'}}))
   fake=types.SimpleNamespace(ENGINES={'vllm':types.SimpleNamespace(name='vLLM',current=lambda:'new')})
   with patch.object(m,'ROOT',root),patch.dict(sys.modules,{'daily_update':fake}):
    rows=m.versions();self.assertTrue(any('`new`' in v for v in rows));self.assertTrue(any('held (manual runtime pin)' in v and '`old`' in v for v in rows))
 def test_publisher_header_retains_current_swap_policy(self):
  spec=importlib.util.spec_from_file_location('runtime_pin_publish_header',ROOT/'hardware/daily-update/publish.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  self.assertIn('loading-swap-v2',m.HEADER);self.assertIn('loading/parked swap is allowed',m.HEADER);self.assertNotIn('64 MiB',m.HEADER)
if __name__=='__main__':unittest.main()
