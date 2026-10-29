"""CPU checks: owner-paused profiles cannot launch or enter nightly qualification."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
import llama_runtime
import strata_runtime
from model_catalog import catalog

class ModelPauses(unittest.TestCase):
    def test_catalog_keeps_working_route_and_omits_paused_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'dsh').mkdir()
            (root/'dsh/models.json').write_text(json.dumps([{'id':'working','name':'working','context':32},{'id':'paused','name':'paused','context':32,'enabled':False}]))
            self.assertEqual(set(catalog(root)),{'working'})

    def test_explicit_llama_pause_rejects_before_worker_device_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'llama-runtime.json').write_text(json.dumps({'backend':'hip-amd','models':['working','paused'],'paused_models':{'paused':'Owner pause until RAM notice'}}))
            with patch.object(llama_runtime,'ROOT',root),patch.object(llama_runtime,'require_worker_scope') as scope,patch.object(llama_runtime,'amd_devices') as devices:
                with self.assertRaisesRegex(RuntimeError,'Owner pause'):
                    llama_runtime.launch_spec(model='paused')
                scope.assert_not_called();devices.assert_not_called()

    def test_all_paused_strata_rejects_before_host_device_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'dsh').mkdir();(root/'dsh/strata-profiles.json').write_text(json.dumps({'paused':{'enabled':False}}))
            with patch.object(strata_runtime,'ROOT',root),patch.object(strata_runtime,'host_memory') as host,patch.object(strata_runtime,'amd_devices') as devices:
                with self.assertRaisesRegex(RuntimeError,'paused or disabled'):
                    strata_runtime.require_strata()
                host.assert_not_called();devices.assert_not_called()

    def test_launchers_do_not_handover_or_spawn_for_all_paused_backend(self):
        import backend_switch,rocm_runtime,terminal_logs,signal,subprocess
        original=Path.read_text
        for kind in ('strata','sglang'):
            with self.subTest(kind=kind):
                def read(path,*a,**kw):
                    if path==ROOT/'dsh'/f'{kind}-profiles.json':return json.dumps({'paused':{'enabled':False}})
                    return original(path,*a,**kw)
                output=io.StringIO()
                with patch.object(Path,'read_text',read),patch.object(backend_switch,'startup_handover') as handover,patch.object(backend_switch,'clear_owner'),patch.object(rocm_runtime,'require_rocm') as rocm,patch.object(subprocess,'Popen') as spawn,patch.object(signal,'signal'),patch.object(terminal_logs,'stop_monitor'),patch.object(sys,'argv',['launch-backend.py',kind,'--no-browser']if kind=='strata'else['launch-backend.py',kind]),contextlib.redirect_stderr(output):
                    with self.assertRaises(SystemExit) as result:runpy.run_path(str(ROOT/'dsh/launch-backend.py'),run_name='__main__')
                    self.assertIn('paused or disabled',str(result.exception)+output.getvalue());handover.assert_not_called();spawn.assert_not_called();rocm.assert_not_called()

    def test_nightly_skips_paused_engine_before_version_fetch_build_or_gpu(self):
        spec=importlib.util.spec_from_file_location('daily_pause_test',ROOT/'hardware/daily-update/daily_update.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
        engine=Mock(name='paused-engine');engine.name='paused';engine.models.return_value=[]
        engine.current.side_effect=AssertionError('Paused engine version queried');engine.latest.side_effect=AssertionError('Paused engine upstream queried')
        with patch.object(up,'ENGINES',{'paused':engine}),patch.object(up,'load_state',return_value={'engines':{}}),patch.object(up,'cleanup'),patch.object(up.signal,'signal'),patch.object(up,'take_lock') as gpu,patch.object(up,'stop_backends') as stop,patch.object(sys,'argv',['daily_update.py','--engines','paused']),contextlib.redirect_stdout(io.StringIO()):
            up.main();engine.prepare.assert_not_called();engine.install.assert_not_called();gpu.assert_not_called();stop.assert_not_called()

if __name__=='__main__':unittest.main()
