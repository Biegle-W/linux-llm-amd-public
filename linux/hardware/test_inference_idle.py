"""Idle unloading safety with synthetic clocks/processes; no GPU or real signals."""
import fcntl
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
import inference_idle as idle
import model_hub


class IdleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'hardware/generated').mkdir(parents=True)
        self.now = 1000
        self.activity = idle.Activity(self.root / 'dsh/data/inference-idle', clock=lambda: self.now)
        self.stop = Mock(return_value=True)
        self.timer = idle.IdleUnloader(self.stop, lambda: 'vllm', self.activity, self.root)
        self.activity.touch()
        self.timer.identity = (None, None)
        for name, value in [('engine_busy', False), ('backend_connections', False)]:
            patcher = patch.object(idle, name, return_value=value)
            patcher.start(); self.addCleanup(patcher.stop)

    def test_600_seconds_unloads_and_releases_only_its_gpu_lock(self):
        self.now += 599
        self.assertFalse(self.timer.tick())
        self.now += 1
        self.assertTrue(self.timer.tick())
        self.stop.assert_called_once()
        self.assertFalse((self.root / 'hardware/generated/GPU-LOCK').exists())

    def test_active_stream_never_unloads_even_after_ten_minutes(self):
        with self.activity.request():
            self.now += 1200
            self.assertFalse(self.timer.tick())
        self.assertEqual(self.activity.elapsed(), 0)
        self.stop.assert_not_called()
        self.now += 599
        self.assertFalse(self.timer.tick())

    def test_new_request_cannot_enter_during_unload(self):
        self.now += 600
        def stopping():
            with self.activity.file('requests.lock') as file:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(file, fcntl.LOCK_SH | fcntl.LOCK_NB)
            return True
        self.stop.side_effect = stopping
        self.assertTrue(self.timer.tick())

    def test_status_poll_does_not_reset_idle_clock(self):
        self.now += 600
        request = object.__new__(model_hub.Handler)
        request.path = '/health'
        request.send_json = Mock()
        with patch.object(model_hub.hub, 'serving', return_value=False), patch.object(idle, 'activity', self.activity):
            request.do_GET()
        self.assertEqual(self.activity.elapsed(), 600)

    def test_post_tracking_covers_native_or_direct_inference_and_completion(self):
        @idle.inference_request
        def generation():
            self.now += 1200
            with self.activity.idle_guard() as due:
                self.assertFalse(due)
        with patch.object(idle, 'activity', self.activity):
            generation()
        self.assertEqual(self.activity.elapsed(), 0)

    def test_settings_token_count_and_mcp_background_posts_do_not_keep_model_loaded(self):
        @idle.inference_request
        def do_POST(request):
            return 'ok'
        self.now += 600
        with patch.object(idle, 'activity', self.activity):
            for path in ('/settings', '/mcp', '/api/tokens', '/v1/messages/count_tokens'):
                self.assertEqual(do_POST(Mock(path=path)), 'ok')
                self.assertEqual(self.activity.elapsed(), 600)

    def test_agent_gpu_lock_is_never_removed(self):
        path = self.root / 'hardware/generated/GPU-LOCK'
        path.write_text('{"owner":"test-agent"}')
        self.now += 601
        self.assertFalse(self.timer.tick())
        self.assertEqual(path.read_text(), '{"owner":"test-agent"}')
        self.stop.assert_not_called()

    def test_background_generation_resets_idle_clock(self):
        self.now += 601
        with patch.object(idle, 'engine_busy', return_value=True):
            self.assertFalse(self.timer.tick())
        self.assertEqual(self.activity.elapsed(), 0)
        self.stop.assert_not_called()

    def test_unknown_queue_status_never_authorizes_shutdown(self):
        self.now += 601
        with patch.object(idle, 'engine_busy', side_effect=ValueError('unknown')):
            with self.assertRaises(ValueError):
                self.timer.tick()
        self.stop.assert_not_called()
        self.assertFalse((self.root / 'hardware/generated/GPU-LOCK').exists())

    def test_existing_backend_connections_defer_unload(self):
        self.now += 601
        with patch.object(idle, 'backend_connections', return_value=True):
            self.assertFalse(self.timer.tick())
        self.stop.assert_not_called()

    def test_backend_launch_and_owner_change_reset_or_block_timeout(self):
        owner = self.root / 'dsh/data/backend-owner.json'
        owner.write_text(json.dumps({'pid': 123, 'start': '1', 'backend': 'maya'}))
        self.now += 601
        self.assertFalse(self.timer.tick())
        self.assertEqual(self.activity.elapsed(), 0)
        self.now += 601
        with (self.root / 'dsh/data/backend-start.lock').open('a') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            self.assertFalse(self.timer.tick())
        self.stop.assert_not_called()

    def test_failed_stop_releases_gpu_lock_and_request_lock(self):
        self.now += 601
        self.stop.side_effect = RuntimeError('failed stop')
        with self.assertRaises(RuntimeError):
            self.timer.tick()
        self.assertFalse((self.root / 'hardware/generated/GPU-LOCK').exists())
        with self.activity.request():
            pass

    def test_hub_stops_only_through_existing_owned_backend_cleanup(self):
        hub = model_hub.Hub()
        hub.active = 'vllm'
        with patch('backend_switch.stop_other_backends') as stop:
            hub.inflight = 1
            self.assertFalse(hub.unload_idle())
            stop.assert_not_called()
            hub.inflight = 0
            self.assertTrue(hub.unload_idle())
            stop.assert_called_once_with(model_hub.ROOT.parent, model_hub.ROOT / 'data/backend-owner.json', idle=True)
        self.assertIsNone(hub.active)
        self.assertFalse(hub.switching)

    def test_hub_next_request_reloads_after_idle_shutdown(self):
        running = [True]
        def launch(*_):
            running[0] = True
            return Mock(poll=Mock(return_value=None))
        hub = model_hub.Hub(serving=lambda *_: running[0], launch=launch)
        hub.active = 'vllm'
        with patch('backend_switch.stop_other_backends', side_effect=lambda *_, **kw: running.__setitem__(0, False)):
            self.assertTrue(hub.unload_idle())
        with patch.object(model_hub, 'gpu_lock_owner', return_value=None):
            hub.acquire('vllm', 'test-model')
        self.assertTrue(running[0])
        hub.release()


class NativeStatus(unittest.TestCase):
    def test_framework_queues_and_missing_metrics(self):
        for kind, prefix, a, b in [('vllm', 'vllm', 'num_requests_running', 'num_requests_waiting'),
                                  ('sglang', 'sglang', 'num_running_reqs', 'num_queue_reqs')]:
            with self.subTest(kind=kind), patch.object(idle, 'read_json', return_value={'active_model': 'model'}):
                for busy in (0, 1):
                    body = f'{prefix}:{a}{{model="test"}} {busy}\n{prefix}:{b} 0\n'
                    with patch.object(idle.OPENER, 'open', return_value=io.BytesIO(body.encode())):
                        self.assertEqual(idle.engine_busy(kind), bool(busy))
                with patch.object(idle.OPENER, 'open', return_value=io.BytesIO(b'# no metrics')):
                    with self.assertRaises(ValueError):
                        idle.engine_busy(kind)

    def test_llama_slots_never_autoload(self):
        replies = [{'status': 'ok'}, {'data': [{'id': 'test-model', 'status': {'value': 'loaded'}}]},
                   [{'is_processing': True}]]
        with patch.object(idle, 'read_json', side_effect=replies) as read:
            self.assertTrue(idle.engine_busy('llama'))
            self.assertIn('autoload=false', read.call_args.args[1])

    def test_native_async_jobs_are_busy(self):
        root = Path(__file__).resolve().parents[1]
        for kind in ('strata', 'maya'):
            profiles = json.loads((root / 'dsh' / (kind + '-profiles.json')).read_text())
            model = next(iter(profiles))
            config = json.dumps({'api_key': ''})
            with self.subTest(kind=kind), patch.object(idle, 'read_json', side_effect=[
                    {'active_model': model}, {'busy': False, 'queued': 1}]), \
                 patch.object(Path, 'read_text', side_effect=[json.dumps(profiles), config]):
                self.assertTrue(idle.engine_busy(kind))


if __name__ == '__main__':
    unittest.main()
