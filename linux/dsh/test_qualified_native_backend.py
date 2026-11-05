"""Select the tested native server family before importing an engine."""
from pathlib import Path
import importlib.util,json,sys,tempfile,types,unittest
from unittest.mock import Mock,patch

class NativeLauncher(unittest.TestCase):
    def launch(self,family,explicit=None):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp);config=source/'profile.json';config.write_text(json.dumps({'model_name':'tested'}))
            record={'family':family,'source':str(source)}
            registry=types.ModuleType('qualified_native_runtime');registry.record_for=Mock(return_value=record);registry.require_profile=Mock()
            spec=importlib.util.spec_from_file_location('native_launcher_under_test',Path(__file__).with_name('qualified_native_backend.py'))
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'qualified_native_runtime':registry}):spec.loader.exec_module(module)
            server=types.SimpleNamespace(main=Mock(side_effect=lambda:list(sys.argv)))
            managed=types.SimpleNamespace(install_guard=Mock())
            managed_spec=types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda _:None))
            argv=['launcher','--config',str(config),'--port','30032']
            if explicit is not None:argv+=['--engine',explicit]
            with patch.object(sys,'argv',argv),patch.object(sys,'path',list(sys.path)),patch.object(module.importlib,'import_module',return_value=server) as imported,patch.object(module.importlib.util,'spec_from_file_location',return_value=managed_spec),patch.object(module.importlib.util,'module_from_spec',return_value=managed):
                try:result=module.main()
                except RuntimeError:
                    imported.assert_not_called();registry.require_profile.assert_not_called();raise
            registry.require_profile.assert_called_once();managed.install_guard.assert_called_once_with(server)
            return result
    def test_maya_uses_maya_server_engine(self):
        args=self.launch('maya');self.assertEqual(args[args.index('--engine')+1],'maya')
    def test_strata_retains_strata_engine(self):
        args=self.launch('strata');self.assertEqual(args[args.index('--engine')+1],'strata')
    def test_conflicting_family_rejected_before_import(self):
        with self.assertRaisesRegex(RuntimeError,'family'):self.launch('maya','strata')
    def test_unknown_family_rejected_before_import(self):
        with self.assertRaisesRegex(RuntimeError,'family'):self.launch('other')
    def test_matching_explicit_engine_is_not_duplicated(self):
        self.assertEqual(self.launch('maya','maya').count('--engine'),1)

if __name__=='__main__':unittest.main()
