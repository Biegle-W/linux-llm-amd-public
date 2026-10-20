"""Native UI launch and immutable runtime boundary; no GPU or browser required."""
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
import backend_switch
import native_frontend as ui
spec=importlib.util.spec_from_file_location('native_ui_server',ROOT/'dsh/native-ui-server.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)


class FrontendTests(unittest.TestCase):
    def test_native_chat_keeps_its_handler_but_runtime_mutations_are_blocked(self):
        class Handler:
            def do_POST(self):self.native_called=True
            def _json(self,code,body):self.reply=(code,body)
        class Service:
            def context_limits(self):return {'context':32768,'min':4096,'max':262144}
        module=SimpleNamespace(make_handler=lambda _:Handler,Service=Service)
        server.install_guard(module)
        guarded=module.make_handler(Service())
        for path in ('/api/context','/api/update','/config','/unload','/load','/api/context?x=1'):
            request=guarded();request.path=path;request.do_POST()
            self.assertEqual(request.reply[0],409);self.assertFalse(getattr(request,'native_called',False))
        for path in ('/v1/chat/completions','/settings','/api/tokens','/v1/strata/cancel'):
            request=guarded();request.path=path;request.do_POST();self.assertTrue(request.native_called)
        self.assertEqual(Service().context_limits(),{'context':32768,'min':32768,'max':32768})

    def test_headless_and_explicit_no_browser_do_not_start_an_application(self):
        with patch.dict(ui.os.environ,{},clear=True),patch.object(ui.subprocess,'Popen') as launch:
            stopped=ui.start_frontend('maya',Mock());stopped.set();launch.assert_not_called()
        with patch.dict(ui.os.environ,{'DISPLAY':':0'},clear=True),patch.object(ui.subprocess,'Popen') as launch:
            ui.start_frontend('strata',Mock(),enabled=False);launch.assert_not_called()

    def test_ready_ui_opens_exact_existing_worker_once(self):
        backend=Mock();backend.poll.return_value=None
        managed=io.BytesIO(json.dumps({'status':'ok','active_model':'validated'}).encode())
        response=io.BytesIO(json.dumps({'model':'validated','unloaded':False,'loaded':True}).encode())
        opener=Mock();opener.open.side_effect=[managed,response]
        def thread(*,target,**_):return SimpleNamespace(start=target)
        with patch.dict(ui.os.environ,{'DISPLAY':':0'},clear=True), \
                patch.object(ui.urllib.request,'build_opener',return_value=opener), \
                patch.object(ui.threading,'Thread',side_effect=thread), \
                patch.object(ui.subprocess,'Popen') as launch:
            ui.start_frontend('maya',backend)
            self.assertEqual(launch.call_count,1)
            self.assertEqual(launch.call_args.args[0],['xdg-open','http://127.0.0.1:30031/'])

    def test_exited_backend_never_opens_a_stale_frontend(self):
        backend=Mock();backend.poll.return_value=1
        def thread(*,target,**_):return SimpleNamespace(start=target)
        with patch.dict(ui.os.environ,{'DISPLAY':':0'},clear=True), \
                patch.object(ui.threading,'Thread',side_effect=thread), \
                patch.object(ui.subprocess,'Popen') as launch:
            ui.start_frontend('strata',backend);launch.assert_not_called()

    def test_wrapped_worker_ownership_is_exact(self):
        root=Path('/test-llm')
        def process(args):return backend_switch.Process(10,1,'1',tuple(args),'','S')
        for project in ('maya','strata'):
            self.assertTrue(backend_switch.is_inference(process(['python3',str(root/'dsh/native-ui-server.py'),'--project',project]),root))
        for args in (['python3','training.py',str(root/'dsh/native-ui-server.py'),'--project','maya'],
                     ['python3',str(root/'dsh/native-ui-server.py'),'--project','unrelated']):
            self.assertFalse(backend_switch.is_inference(process(args),root))


if __name__=='__main__':unittest.main()
