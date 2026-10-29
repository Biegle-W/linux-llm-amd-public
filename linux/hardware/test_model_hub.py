"""Model hub: on-demand backend start/switch without a GPU, browser or real backend."""
import http.client
import importlib.util
import json
from pathlib import Path
import sys
import threading
import tempfile
import time
from http.server import ThreadingHTTPServer
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
import model_hub as mh


def routing_catalog_fixture():
    """Exercise all routes without requiring production profiles to be enabled."""
    from model_catalog import catalog
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); (root/'dsh').mkdir()
        sources={'models.json':[{'id':'empero','name':'Empero','context':32}],
                 'vllm-profiles.json':{'nemotron-3.5-bolt-vllm':{'name':'Bolt','context':32},'sage-a1.5':{'name':'Sage','context':32}},
                 'strata-profiles.json':{'qwen3.8-flash-next-iq3_xxs':{'name':'Qwen Next','context':32}},
                 'sglang-profiles.json':{'qwen-dflash':{'name':'Qwen','context':32}}}
        for name,data in sources.items(): (root/'dsh'/name).write_text(json.dumps(data))
        return catalog(root)


class FakeBackends:
    """Backends that start serving only after the hub launches them."""
    def __init__(self, running=()):
        self.running = set(running)
        self.launches = []

    def serving(self, kind, model):
        return kind in self.running

    def launch(self, kind, model):
        self.launches.append((kind, model))
        self.running = {kind}
        return Mock(poll=Mock(return_value=None))


class HubTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(mh, 'gpu_lock_owner', return_value=None)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_catalog_maps_every_active_model_to_its_backend(self):
        models = routing_catalog_fixture()
        self.assertEqual(models['nemotron-3.5-bolt-vllm']['backend'], 'vllm')
        self.assertEqual(models['sage-a1.5']['backend'], 'vllm')
        self.assertEqual(models['qwen3.8-flash-next-iq3_xxs']['backend'], 'strata')
        self.assertNotIn('nemotron-3.5-bolt', models)
        self.assertNotIn('qwen3.8-27b-q4', models)

    def test_serving_backend_is_used_without_launching(self):
        fake = FakeBackends(running={'llama'})
        hub = mh.Hub(serving=fake.serving, launch=fake.launch, sleep=lambda _: None)
        hub.acquire('llama', 'empero-qwen3.8-35b-a3b'); hub.release()
        self.assertEqual(fake.launches, [])
        self.assertEqual(hub.active, 'llama')

    def test_switch_waits_for_inflight_reply_then_launches(self):
        fake = FakeBackends(running={'llama'})
        hub = mh.Hub(serving=fake.serving, launch=fake.launch, sleep=lambda _: None)
        hub.acquire('llama', 'empero-qwen3.8-35b-a3b')
        done = threading.Event()
        def other():
            hub.acquire('vllm', 'qwen3.8-27b-vllm'); done.set()
        thread = threading.Thread(target=other); thread.start()
        time.sleep(0.3)
        self.assertFalse(done.is_set(), 'switched while a reply was in flight')
        self.assertEqual(fake.launches, [])
        hub.release()
        thread.join(5)
        self.assertTrue(done.is_set())
        self.assertEqual(fake.launches, [('vllm', 'qwen3.8-27b-vllm')])
        self.assertEqual((hub.active, hub.inflight), ('vllm', 1))

    def test_gpu_lock_blocks_starting_but_not_a_serving_backend(self):
        fake = FakeBackends(running={'vllm'})
        hub = mh.Hub(serving=fake.serving, launch=fake.launch, sleep=lambda _: None)
        with patch.object(mh, 'gpu_lock_owner', return_value='Codex-Test'):
            hub.acquire('vllm', 'qwen3.8-27b-vllm'); hub.release()
            with self.assertRaises(mh.HubError) as raised:
                hub.acquire('llama', 'empero-qwen3.8-35b-a3b')
        self.assertEqual(raised.exception.code, 'gpu_reserved')
        self.assertEqual(fake.launches, [])
        self.assertFalse(hub.switching)

    def test_launcher_failure_is_reported_and_hub_recovers(self):
        failed = Mock(poll=Mock(return_value=1))
        hub = mh.Hub(serving=lambda kind, model: False, launch=lambda kind, model: failed, sleep=lambda _: None)
        with patch.object(mh, 'launcher_error', return_value='SGLang startup failed: requires 22.75 GiB'):
            with self.assertRaises(mh.HubError) as raised:
                hub.acquire('sglang', 'qwen3.8-27b-sglang-dflash2')
        self.assertEqual(raised.exception.code, 'backend_start_failed')
        self.assertIn('22.75 GiB', str(raised.exception))
        self.assertEqual((hub.switching, hub.inflight), (False, 0))

    def test_maya_and_strata_launch_headless_with_the_requested_model(self):
        for kind,model in [('maya','deepseek-v4.1-flash-1017-maya'),
                           ('strata','deepseek-v4.1-flash-1017-strata-xs')]:
            with self.subTest(kind=kind),patch.object(mh.subprocess,'Popen') as popen:
                mh.Hub()._launch(kind,model)
                args=popen.call_args.args[0]
                self.assertEqual(args[1:],[kind,'--no-browser','--model',model])
                self.assertTrue(popen.call_args.kwargs['start_new_session'])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), mh.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.shutdown)

    def post(self, body):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        connection.request('POST', '/v1/chat/completions', json.dumps(body), {'Content-Type': 'application/json'})
        response = connection.getresponse()
        return response.status, response.read()

    def test_unknown_model_is_rejected(self):
        status, body = self.post({'model': 'not-a-model', 'messages': []})
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)['error']['code'], 'model_not_found')

    def test_streaming_start_failure_becomes_an_sse_error_event(self):
        error = mh.HubError(503, 'GPUs are reserved for a test (X); no backend was started.', 'gpu_reserved')
        with patch.object(mh.hub, 'acquire', side_effect=error):
            status, body = self.post({'model': 'sage-a1.5', 'stream': True, 'messages': []})
        self.assertEqual(status, 200)
        event = json.loads(body.split(b'\n\n')[0].removeprefix(b'data: '))
        self.assertEqual(event['error']['code'], 'gpu_reserved')
        self.assertIn(b'data: [DONE]', body)

    def test_models_list_every_backend_with_auto_start(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        with patch.object(mh, 'catalog', return_value=routing_catalog_fixture()):
            connection.request('GET', '/v1/models')
            data = json.loads(connection.getresponse().read())['data']
        self.assertEqual({m['backend'] for m in data} >= {'llama', 'vllm', 'sglang', 'strata'}, True)
        self.assertTrue(all(m['auto_start'] for m in data))


if __name__ == '__main__':
    unittest.main()
