"""HTTP security, switch serialization/recovery and frontend reuse regressions."""
import contextlib
import http.client
from http.server import ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from maya_web import make_web_handler
import dsh_frontend
from backend_switch import Process


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / 'index.html').write_text('<body>Original Maya</body>')
        (root / 'app.js').write_text('/* original pinned frontend */')
        self.controller = SimpleNamespace(requests=threading.Lock(), web_api_keys=lambda: [],
            worker_ready=lambda: False, web_status=lambda: {'models': [{'id': 'validated'}]},
            queue_model_switch=Mock(return_value={'operation': {'state': 'loading'}}))
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_web_handler(self.controller, root, 1))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, data=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            conn.request('GET' if data is None else 'POST', path, data, headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    def test_ui_and_catalog_survive_an_unloaded_worker(self):
        code, body = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn(b'Original Maya', body)
        self.assertIn(b'/managed/model-switch.js', body)
        self.assertEqual(self.request('/managed/model-switch.js')[0], 200)
        self.assertEqual(self.request('/managed/models')[0], 200)
        self.assertEqual(self.request('/web/app.js')[0], 200)
        self.assertEqual(self.request('/web/../app.js')[0], 503)
        self.assertEqual(self.request('/health')[0], 503)

    def test_same_origin_json_only_no_config_overrides(self):
        for path in ['/managed/models/load', '/settings']:
            self.assertEqual(self.request(path, '{}', {'Host': 'evil.example'})[0], 403)
            self.assertEqual(self.request(path, '{}', {'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.request('/managed/models/load', '{}')[0], 415)
        for payload in [{'model': 'validated', 'config': '/tmp/custom'}, [], {'model': 1}, {'model': ['bad']}]:
            self.assertEqual(self.request('/managed/models/load', json.dumps(payload), {'Content-Type': 'application/json'})[0], 400)
        self.controller.queue_model_switch.assert_not_called()
        for path in ['/load', '/unload', '/api/context', '/api/update', '/config']:
            self.assertEqual(self.request(path, '{}', {'Content-Type': 'application/json'})[0], 409)

    def test_native_authentication_and_busy_errors_are_preserved(self):
        self.controller.web_api_keys = lambda: ['test-secret']
        self.assertEqual(self.request('/managed/models')[0], 401)
        self.assertEqual(self.request('/managed/models', headers={'Authorization': 'Bearer test-secret'})[0], 200)
        self.controller.queue_model_switch.side_effect = BlockingIOError('answer in progress')
        code, body = self.request('/managed/models/load', '{"model":"validated"}',
            {'Authorization': 'Bearer test-secret', 'Content-Type': 'application/json'})
        self.assertEqual(code, 409)
        self.assertIn(b'answer in progress', body)

    def test_loading_serializes_native_chat_but_does_not_block_cancellation(self):
        self.controller.requests.acquire()
        try:
            self.assertEqual(self.request('/v1/chat/completions', '{}')[0], 409)
            self.assertEqual(self.request('/v1/strata/cancel', '{}')[0], 503)  # unloaded, not locked
        finally:
            self.controller.requests.release()


class ControllerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('maya_switch_test', ROOT / 'dsh/maya-router.py')
        self.router = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.router
        spec.loader.exec_module(self.router)
        self.model = next(iter(self.router.PROFILES))

    def wait_done(self):
        deadline = time.monotonic() + 3
        while self.router.requests.locked():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.01)

    def test_invalid_or_busy_request_never_stops_the_existing_worker(self):
        with patch.object(self.router, 'ensure_worker') as ensure:
            with self.assertRaises(ValueError): self.router.queue_model_switch('not-enabled')
            self.router.requests.acquire()
            try:
                with self.assertRaises(BlockingIOError): self.router.queue_model_switch(self.model)
            finally: self.router.requests.release()
            ensure.assert_not_called()

    def test_async_progress_failure_and_explicit_retry_keep_the_guarded_path(self):
        entered, release = threading.Event(), threading.Event()
        def load(_):
            entered.set(); release.wait(2)
            raise RuntimeError('52 GiB admission rejected')
        with patch.object(self.router, 'ensure_worker', side_effect=load) as ensure:
            self.router.queue_model_switch(self.model)
            self.assertTrue(entered.wait(1))
            self.assertEqual(self.router.web_status()['operation']['state'], 'loading')
            release.set(); self.wait_done()
            self.assertIn('admission rejected', self.router.web_status()['operation']['error'])
            self.assertEqual(ensure.call_args.args, (self.model,))
        with patch.object(self.router, 'ensure_worker'):
            self.router.queue_model_switch(self.model); self.wait_done()
            self.assertEqual(self.router.web_status()['operation']['state'], 'ready')

    def test_background_generation_rejects_switch_and_releases_lock(self):
        for status in ({'busy': True}, {'busy': False, 'queued': 1}, {'busy': False, 'active': 1}):
            with self.subTest(status=status), patch.object(self.router, 'worker_ready', return_value=True), \
                 patch.object(self.router.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(status).encode())):
                with self.assertRaises(BlockingIOError): self.router.queue_model_switch(self.model)
                self.assertFalse(self.router.requests.locked())


class DSHReuseTests(unittest.TestCase):
    def test_only_exact_dsh_web_entrypoint_is_recognized(self):
        root = dsh_frontend.ROOT
        def proc(args): return Process(123, 1, '1', tuple(args), '', 'S')
        args = ['node', str(root / 'node_modules/.bin/dsh'), 'web', '--host', '127.0.0.1', '--port', '3080']
        self.assertTrue(dsh_frontend.is_dsh_web(proc(args)))
        for bad in [['node', 'training.js', *args[1:]], ['python', *args[1:]], [*args[:-1], '9999']]:
            self.assertFalse(dsh_frontend.is_dsh_web(proc(bad)))

    def test_duplicate_reuses_only_the_owned_listener_and_never_kills_it(self):
        probe = Mock(); probe.connect_ex.return_value = 0
        context = Mock(); context.__enter__ = Mock(return_value=probe); context.__exit__ = Mock(return_value=False)
        with patch.object(dsh_frontend.socket, 'socket', return_value=context), \
             patch.object(dsh_frontend, 'processes', return_value={1: object()}), \
             patch.object(dsh_frontend, 'is_dsh_web', return_value=True), \
             patch.object(dsh_frontend, 'owns_listener', return_value=True), \
             patch.dict(dsh_frontend.os.environ, {}, clear=True):
            self.assertTrue(dsh_frontend.reuse_existing())
            with patch.object(dsh_frontend, 'owns_listener', return_value=False):
                with self.assertRaisesRegex(RuntimeError, 'another application'):dsh_frontend.reuse_existing()


if __name__ == '__main__':
    unittest.main()
