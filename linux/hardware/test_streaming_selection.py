"""Held siblings must not block or unload an admitted streaming model."""
import argparse,ast,contextlib,importlib.util,io,runpy,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
R=Path(__file__).resolve().parents[1];W=R
sys.path.insert(0,str(R/'dsh'))
import maya_runtime,backend_switch

class SelectedAdmission(unittest.TestCase):
 def test_launcher_admits_only_requested_profile_before_any_handover(self):
  model='deepseek-v4.1-flash-1017-maya'
  with patch.object(sys,'argv',[str(W/'dsh/launch-backend.py'),'maya','--model',model]),patch.object(maya_runtime,'require_maya') as require,patch.object(backend_switch,'startup_handover',side_effect=RuntimeError('fixture boundary')),patch.object(backend_switch,'clear_owner'),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   with self.assertRaises(SystemExit):runpy.run_path(str(W/'dsh/launch-backend.py'),run_name='__main__')
  require.assert_called_once_with(model,before_handover=True)
 def test_router_admits_requested_profile_before_worker_launch(self):
  source=ast.parse((W/'dsh/maya-router.py').read_text());main=next(node for node in source.body if isinstance(node,ast.If) and ast.unparse(node.test)=="__name__ == '__main__'")
  env={'__name__':'__main__','argparse':argparse,'DEFAULT':'glm-5.3-flash-maya','PROFILES':{'glm-5.3-flash-maya':{},'deepseek-v4.1-flash-1017-maya':{}}}
  model='deepseek-v4.1-flash-1017-maya'
  with patch.object(sys,'argv',['maya-router.py','--model',model]),patch.object(maya_runtime,'require_maya',side_effect=RuntimeError('fixture boundary')) as require:
   with self.assertRaises(SystemExit):exec(compile(ast.Module(body=[main],type_ignores=[]),'maya-selection','exec'),env)
  require.assert_called_once_with(model)


 def test_strata_rejects_incompatible_sibling_before_unloading_good_worker(self):
  spec=importlib.util.spec_from_file_location('strata_preflight_fixture',R/'dsh/strata-router.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  proc=Mock();proc.poll.return_value=None
  module.worker=proc;module.active='qwen3.8-flash-next-iq3_xxs';module.swap_guard=Mock();module.stop_worker=Mock()
  target='deepseek-v4.1-flash-1017-strata-xs'
  with patch('hardware_guard.require_strata',side_effect=RuntimeError('fixture RAM gate')) as require:
   with self.assertRaisesRegex(RuntimeError,'fixture RAM gate'):module.ensure_worker.__wrapped__(target)
  require.assert_called_once_with(before_handover=True,model=target)
  module.stop_worker.assert_not_called();self.assertIs(module.worker,proc)
  self.assertEqual(module.active,'qwen3.8-flash-next-iq3_xxs')

if __name__=='__main__':unittest.main()
