"""CPU-only FIFO, lifecycle and transport regressions; no real launcher/worker."""
import http.client
import importlib.util
import ipaddress
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
import model_hub as mh
import hub_transport as tr
from inference_idle import Activity
spec = importlib.util.spec_from_file_location('test_gateway', ROOT/'network/gateway.py')
gw = importlib.util.module_from_spec(spec); spec.loader.exec_module(gw)


def until(predicate, timeout=3):
    end = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > end:
            raise AssertionError('Timed out waiting for fixture state')
        time.sleep(.005)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.h = mh.Hub(serving=lambda *_: True, max_queued=3, max_queued_bytes=20)
        self.errors = []
        self.threads = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for t in self.threads:
            t.join(3)
        self.assertFalse(any(t.is_alive() for t in self.threads))

    def waiter(self, kind, model, action=lambda: None, **kwargs):
        def run():
            try:
                self.h.acquire(kind, model, **kwargs)
                try: action()
                finally: self.h.release()
            except BaseException as e:
                self.errors.append(e)
        t = threading.Thread(target=run, daemon=True); t.start(); self.threads.append(t)
        return t

    def test_fifo_switch_cannot_be_starved_by_later_same_model_traffic(self):
        self.h.acquire('llama', 'A')
        order = []
        self.waiter('vllm', 'B', lambda: order.append('B'))
        until(lambda: self.h.snapshot()['queued'] == 1)
        for _ in range(2):
            self.waiter('llama', 'A', lambda: order.append('A'))
        until(lambda: self.h.snapshot()['queued'] == 3)
        self.assertEqual(order, [])
        self.h.release()
        until(lambda: len(order) == 3)
        self.assertEqual(order, ['B', 'A', 'A']); self.assertEqual(self.errors, [])

    def test_queue_count_backpressure(self):
        self.h.max_queued = 1
        self.h.acquire('llama', 'A'); self.waiter('llama', 'A')
        until(lambda: self.h.snapshot()['queued'] == 1)
        try:
            with self.assertRaises(mh.HubError) as e: self.h.acquire('vllm', 'B')
            self.assertEqual((e.exception.status, e.exception.code), (429, 'queue_full'))
        finally: self.h.release()

    def test_queue_aggregate_body_budget(self):
        self.h.acquire('llama', 'A'); self.waiter('llama', 'A', body_bytes=15)
        until(lambda: self.h.snapshot()['queued'] == 1)
        try:
            with self.assertRaises(mh.HubError): self.h.acquire('llama', 'A', body_bytes=6)
            self.assertEqual(self.h.snapshot()['queued_bytes'], 15)
        finally: self.h.release()
        until(lambda: self.h.snapshot()['queued_bytes'] == 0)

    def test_timeout_removes_waiter(self):
        self.h.acquire('llama', 'A'); self.waiter('vllm', 'B', timeout=.03, body_bytes=10)
        until(lambda: self.errors)
        self.assertEqual(self.errors[0].code, 'queue_timeout')
        self.assertEqual(self.h.snapshot()['queued_bytes'], 0); self.h.release()

    def test_cancelled_head_does_not_block_successor(self):
        cancelled = threading.Event()
        def progress():
            if cancelled.is_set(): raise ConnectionResetError()
        self.h.acquire('llama', 'A'); self.waiter('vllm', 'B', progress=progress, body_bytes=7)
        until(lambda: self.h.snapshot()['queued'] == 1)
        self.waiter('llama', 'A'); until(lambda: self.h.snapshot()['queued'] == 2)
        cancelled.set(); until(lambda: self.errors)
        self.assertIsInstance(self.errors[0], ConnectionResetError)
        self.assertEqual(self.h.snapshot()['queued_bytes'], 0)
        self.h.release(); until(lambda: self.h.snapshot()['queued'] == 0)

    def test_idle_cannot_overtake_queued_work(self):
        with self.h.cond:
            self.h.waiters.append((object(), 0))
        self.assertFalse(self.h.unload_idle())
        self.assertFalse(self.h.switching)
        self.h.waiters.clear()

    def test_idle_cannot_stop_active_or_loading(self):
        self.h.acquire('llama', 'A'); self.assertFalse(self.h.unload_idle()); self.h.release()
        self.h.switching = True; self.assertFalse(self.h.unload_idle()); self.h.switching = False

    def test_progress_does_not_hold_condition(self):
        entered = threading.Event(); resume = threading.Event()
        def progress(): entered.set(); resume.wait(2)
        self.waiter('llama', 'A', progress=progress)
        self.assertTrue(entered.wait(2)); self.assertEqual(self.h.snapshot()['inflight'], 0)
        resume.set()

    def test_start_failure_releases_claim_and_queue_recovers(self):
        with patch.object(self.h, '_start', side_effect=mh.HubError(503, 'failed', 'backend_start_failed')):
            with self.assertRaises(mh.HubError): self.h.acquire('vllm', 'B')
        self.assertFalse(self.h.switching); self.assertIsNone(self.h.loading_model)
        self.h.acquire('llama', 'A'); self.h.release()

    def test_launcher_oserror_is_useful_sanitized_and_releases_claim(self):
        self.h.serving = lambda *_: False
        self.h.launch = Mock(side_effect=OSError('Could not execute /home/private/launcher'))
        with patch.object(mh, 'gpu_lock_owner', return_value=None):
            with self.assertRaises(mh.HubError) as e: self.h.acquire('vllm', 'B')
        self.assertEqual(e.exception.code, 'backend_start_failed')
        self.assertIn('Could not execute', str(e.exception)); self.assertNotIn('/home', str(e.exception))
        self.assertFalse(self.h.switching)

    def test_start_timeout_releases_claim(self):
        self.h.serving = lambda *_: False
        with patch.object(mh, 'gpu_lock_owner', return_value=None), patch.object(mh, 'LOAD_TIMEOUT', 0):
            self.h.launch = lambda *_: Mock(poll=lambda: None)
            with self.assertRaises(mh.HubError) as e: self.h.acquire('vllm', 'B')
        self.assertEqual(e.exception.code, 'backend_start_timeout'); self.assertFalse(self.h.switching)

    def test_gpu_reservation_is_generic_and_launch_is_not_called(self):
        self.h.serving = lambda *_: False; self.h.launch = Mock()
        with patch.object(mh, 'gpu_lock_owner', return_value='/home/private/secret'):
            with self.assertRaises(mh.HubError) as e: self.h.acquire('vllm', 'B')
        self.h.launch.assert_not_called(); self.assertNotIn('private', str(e.exception))

    def test_future_qualified_capacity_is_preserved_with_switch_drain(self):
        self.h.capacities['llama'] = 2
        self.h.acquire('llama', 'A'); self.h.acquire('llama', 'A')
        done = threading.Event(); self.waiter('vllm', 'B', done.set)
        until(lambda: self.h.snapshot()['queued'] == 1)
        self.h.release(); self.assertFalse(done.is_set()); self.h.release()
        self.assertTrue(done.wait(2))

    def test_different_model_same_backend_waits_for_drain(self):
        self.h.capacities['llama'] = 2; self.h.acquire('llama', 'A')
        done = threading.Event(); self.waiter('llama', 'B', done.set)
        until(lambda: self.h.snapshot()['queued'] == 1)
        self.assertFalse(done.is_set()); self.h.release(); self.assertTrue(done.wait(2))

    def test_loading_remains_visible_until_backend_headers_and_release_clears(self):
        self.h.acquire('llama', 'A')
        self.assertEqual(self.h.snapshot()['loading_model'], 'A')
        self.h.response_started(); self.assertIsNone(self.h.snapshot()['loading_model'])
        self.h.release(); self.assertIsNone(self.h.snapshot()['loading_model'])

    def test_cancelled_start_preserves_launched_process_and_releases_claim(self):
        process = Mock(poll=lambda: None)
        self.h.serving = lambda *_: False
        self.h.launch = Mock(return_value=process)
        def progress():
            if self.h.process is process: raise ConnectionResetError()
        with patch.object(mh, 'gpu_lock_owner', return_value=None):
            with self.assertRaises(ConnectionResetError): self.h.acquire('vllm', 'B', progress=progress)
        self.assertIs(self.h.process, process); process.terminate.assert_not_called()
        self.assertFalse(self.h.switching); self.assertIsNone(self.h.loading_model)

    def test_release_without_admission_fails(self):
        with self.assertRaises(RuntimeError): self.h.release()

    def test_effective_amd_capacity_and_pending_bound(self):
        h = mh.Hub()
        self.assertEqual(set(h.snapshot()['capacity_by_backend'].values()), {1})
        self.assertEqual(h.max_queued, len(mh.catalog()))
        self.assertEqual(h.max_queued_bytes, mh.MAX_BODY)


class Response:
    def __init__(self, chunks): self.chunks = iter(chunks)
    def read1(self, _): return next(self.chunks, b'')


class TransportTests(unittest.TestCase):
    def relay(self, data, split=1, secrets=()):
        out = []
        tr.relay_sse(Response([data[i:i+split] for i in range(0, len(data), split)]), out.append, secrets)
        return b''.join(out)

    def test_tool_call_and_alias_events_unchanged_at_every_chunk_boundary(self):
        data = b'data: {"model":"alias","choices":[{"delta":{"tool_calls":[{"function":{"arguments":"{}"}}]}}]}\n\ndata: [DONE]\n\n'
        for split in range(1, len(data)+1): self.assertEqual(self.relay(data, split), data)

    def test_crlf_stream_and_keepalive_unchanged(self):
        data = b': loading\r\n\r\ndata: {"choices":[]}\r\n\r\ndata: [DONE]\r\n\r\n'
        self.assertEqual(self.relay(data), data)

    def test_http_error_preserves_code_type_status(self):
        e = tr.error_payload(b'{"error":{"message":"too long","code":"context_length","type":"invalid_request_error"}}', 422)
        self.assertEqual((e['code'], e['type'], e['status']), ('context_length', 'invalid_request_error', 422))

    def test_plaintext_error_and_private_paths_redacted(self):
        e = tr.error_payload(b'failed /home/person/log.txt Bearer secret', 503)
        self.assertIn('failed', e['message']); self.assertNotIn('/home', e['message']); self.assertNotIn('secret', e['message'])

    def test_stream_error_keeps_fields_redacts_split_secret_and_finishes(self):
        data = b'data: {"error":{"message":"bad TOPSECRET","code":"overloaded","status":429}}\n\ndata: {"choices":[]}\n\n'
        out = self.relay(data, secrets=('TOPSECRET',))
        self.assertIn(b'overloaded', out); self.assertIn(b'429', out); self.assertNotIn(b'TOPSECRET', out)
        self.assertNotIn(b'choices', out); self.assertEqual(out.count(b'[DONE]'), 1)

    def test_event_error_plaintext_is_preserved(self):
        out = self.relay(b'event: error\ndata: backend exploded\n\n')
        self.assertIn(b'backend exploded', out); self.assertIn(b'502', out)

    def test_named_error_event_preserves_top_level_status(self):
        for data in [b'event: error\ndata: {"message":"busy","code":"limit","status":429}\n\n',
                     b'data: {"error":{"message":"busy","code":"limit"},"status":429}\n\n']:
            out = self.relay(data)
            error = json.loads(out.split(b'\n\n')[0][6:])['error']
            self.assertEqual((error['status'], error['code']), (429, 'limit'))

    def test_openai_error_object_with_numeric_code_keeps_status(self):
        out = self.relay(b'data: {"object":"error","message":"bad prompt","code":400}\n\n')
        error = json.loads(out.split(b'\n\n')[0][6:])['error']
        self.assertEqual((error['status'], error['code']), (400, 400))

    def test_truncated_stream_is_failure(self):
        with self.assertRaises(http.client.HTTPException): self.relay(b'data: {"choices":[]}\n\n')

    def test_json_body_redaction_preserves_valid_json(self):
        out = tr.clean_error_body(b'{"error":{"message":"/home/person/file api_key=secret TOPSECRET"}}', ('TOPSECRET',))
        self.assertNotIn(b'TOPSECRET', out); self.assertNotIn(b'api_key=secret', out); json.loads(out)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.activity = Activity(Path(self.tmp.name))
        self.patches = [patch.object(mh, 'hub', mh.Hub(serving=lambda *_: True)),
                        patch('inference_idle.activity', self.activity),
                        patch.object(mh, 'gpu_lock_owner', return_value='/home/private/reservation'),
                        patch.object(gw, 'token', b'fixture-external-secret'),
                        patch.object(gw, 'allowed', [ipaddress.ip_network('127.0.0.0/8')])]
        for p in self.patches: p.start(); self.addCleanup(p.stop)
        self.hub_server = self.server(mh.Handler)
        self.patches.append(patch.object(gw, 'HUB_PORT', self.hub_server.server_port))
        self.patches[-1].start(); self.addCleanup(self.patches[-1].stop)
        self.gateway = self.server(gw.Handler)
        self.fixture = self
        class Backend(BaseHTTPRequestHandler):
            def log_message(*_): pass
            def do_POST(inner):
                self.headers = dict(inner.headers)
                self.body = inner.rfile.read(int(inner.headers['Content-Length']))
                inner.send_response(self.backend_status)
                inner.send_header('Content-Type', self.backend_type)
                inner.send_header('Content-Length', str(len(self.payload)))
                inner.send_header('Retry-After', '7'); inner.end_headers(); inner.wfile.write(self.payload)
        self.backend = self.server(Backend)
        self.backend_status = 200; self.backend_type = 'application/json'; self.payload = b'{"model":"sage-a1.5","choices":[]}'
        self.patches.append(patch.dict(mh.BACKENDS, {'vllm': ('vllm-profiles.json', self.backend.server_port, 'fixture')}))
        self.patches[-1].start(); self.addCleanup(self.patches[-1].stop)

    def server(self, handler):
        s = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        s.daemon_threads = True
        threading.Thread(target=s.serve_forever, daemon=True).start()
        self.addCleanup(s.server_close); self.addCleanup(s.shutdown)
        return s

    def request(self, method='POST', path='/v1/chat/completions', data=None, auth=True, hub=False):
        s = self.hub_server if hub else self.gateway
        c = http.client.HTTPConnection('127.0.0.1', s.server_port, timeout=5)
        headers = {'Content-Type': 'application/json'}
        if auth: headers['Authorization'] = 'Bearer fixture-external-secret'
        c.request(method, path, json.dumps(data or {'model': 'sage-a1.5', 'messages': []}) if method == 'POST' else None, headers)
        r = c.getresponse(); body = r.read(); result = (r.status, dict(r.getheaders()), body); c.close(); return result

    def test_health_requires_authentication(self):
        self.assertEqual(self.request('GET', '/health', auth=False)[0], 401)

    def test_network_filter_precedes_health(self):
        with patch.object(gw, 'allowed', []): self.assertEqual(self.request('GET', '/health')[0], 403)

    def test_consistent_sanitized_health_no_activity_or_load(self):
        with patch.object(mh.hub, 'serving', side_effect=AssertionError('Health must not probe workers')):
            a = self.request('GET', '/health'); b = self.request('GET', '/health', hub=True)
        self.assertEqual(json.loads(a[2]), json.loads(b[2])); self.assertNotIn(b'/home', a[2])
        self.assertNotIn(b'gpu_reserved_by', a[2]); self.assertTrue(json.loads(a[2])['gpu_reserved'])
        self.assertFalse((Path(self.tmp.name)/'timestamp').exists())

    def test_catalog_does_not_load_or_mark_activity(self):
        with patch.object(gw, 'backend_models', return_value=set()), patch.object(mh.hub, 'serving', side_effect=AssertionError):
            self.assertEqual(self.request('GET', '/v1/models')[0], 200)
            self.assertEqual(self.request('GET', '/v1/models', hub=True)[0], 200)
        self.assertFalse((Path(self.tmp.name)/'timestamp').exists())

    def test_external_credentials_not_forwarded_and_alias_body_intact(self):
        status, _, _ = self.request()
        self.assertEqual(status, 200); self.assertNotIn('Authorization', self.headers)
        self.assertEqual(json.loads(self.body)['model'], 'sage-a1.5')

    def test_backend_http_json_status_and_code_survive_gateway(self):
        self.backend_status = 422; self.payload = b'{"error":{"message":"too long", "code":"context_length"}}'
        status, headers, data = self.request()
        self.assertEqual(status, 422); self.assertEqual(headers['Retry-After'], '7')
        self.assertEqual(json.loads(data)['error']['code'], 'context_length')

    def test_backend_plaintext_status_detail_and_redaction(self):
        self.backend_status = 503; self.backend_type = 'text/plain'; self.payload = b'out of memory /home/private/log Bearer worker-secret fixture-external-secret'
        status, _, data = self.request()
        self.assertEqual(status, 503); self.assertIn(b'out of memory', data)
        for secret in [b'/home', b'worker-secret', b'fixture-external-secret']: self.assertNotIn(secret, data)

    def test_streamed_http_error_keeps_status_code_and_done(self):
        self.backend_status = 429; self.payload = b'{"error":{"message":"busy", "code":"limit", "type":"rate_limit_error"}}'
        status, _, data = self.request(data={'model': 'sage-a1.5', 'stream': True})
        self.assertEqual(status, 200); e = json.loads(data.split(b'\n\n')[0][6:])['error']
        self.assertEqual((e['status'], e['code'], e['type']), (429, 'limit', 'rate_limit_error'))
        self.assertEqual(data.count(b'[DONE]'), 1); until(lambda: mh.hub.inflight == 0)

    def test_streamed_plaintext_backend_failure(self):
        self.backend_status = 500; self.payload = b'worker refused /tmp/private/file'
        _, _, data = self.request(data={'model': 'sage-a1.5', 'stream': True})
        self.assertIn(b'worker refused', data); self.assertIn(b'500', data); self.assertNotIn(b'/tmp', data)

    def test_tool_sse_survives_both_hops(self):
        self.backend_type = 'text/event-stream'
        self.payload = b'data: {"model":"sage-a1.5","choices":[{"delta":{"tool_calls":[]}}]}\n\ndata: [DONE]\n\n'
        self.assertEqual(self.request(data={'model': 'sage-a1.5', 'stream': True})[2], self.payload)
        until(lambda: mh.hub.inflight == 0)

    def test_error_inside_200_sse_preserves_code_and_redacts_external_key(self):
        self.backend_type = 'text/event-stream'; self.payload = b'data: {"error":{"message":"fixture-external-secret", "code":"native_failure", "status":500}}\n\n'
        data = self.request(data={'model': 'sage-a1.5', 'stream': True})[2]
        self.assertNotIn(b'fixture-external-secret', data); self.assertIn(b'native_failure', data)
        self.assertEqual(data.count(b'[DONE]'), 1)

    def test_queue_full_retry_after_and_no_forward(self):
        with patch.object(mh.hub, 'acquire', side_effect=mh.HubError(429, 'retry', 'queue_full')):
            status, headers, data = self.request()
        self.assertEqual(status, 429); self.assertEqual(headers['Retry-After'], '5')
        self.assertEqual(json.loads(data)['error']['code'], 'queue_full')

    def test_unknown_model_and_management_routes_are_rejected(self):
        self.assertEqual(self.request(data={'model': 'unknown'})[0], 404)
        self.assertEqual(self.request(path='/models/load')[0], 404)

    def test_external_stream_disconnect_removes_hub_waiter(self):
        mh.hub.acquire('llama', 'A')
        c = http.client.HTTPConnection('127.0.0.1', self.gateway.server_port)
        c.request('POST', '/v1/chat/completions', json.dumps({'model':'sage-a1.5','stream':True}),
                  {'Authorization':'Bearer fixture-external-secret'})
        try:
            response = c.getresponse()
            self.assertEqual(response.status, 200)
            until(lambda: mh.hub.snapshot()['queued'] == 1)
            response.close(); c.close()
            until(lambda: mh.hub.snapshot()['queued'] == 0)
        finally: mh.hub.release(); c.close()

    def test_external_nonstream_disconnect_removes_hub_waiter(self):
        mh.hub.acquire('llama', 'A')
        c = http.client.HTTPConnection('127.0.0.1', self.gateway.server_port)
        c.request('POST', '/v1/chat/completions', json.dumps({'model':'sage-a1.5'}),
                  {'Authorization':'Bearer fixture-external-secret'})
        try:
            until(lambda: mh.hub.snapshot()['queued'] == 1); c.close()
            until(lambda: mh.hub.snapshot()['queued'] == 0)
        finally: mh.hub.release(); c.close()

    def test_stream_request_json_error_with_http_200_is_reported(self):
        self.payload = b'{"error":{"message":"native refused","code":"native_error"}}'
        _, _, data = self.request(data={'model':'sage-a1.5','stream':True})
        self.assertIn(b'native refused', data); self.assertIn(b'native_error', data)
        self.assertEqual(data.count(b'[DONE]'), 1)

    def test_nonstream_disconnected_waiter_is_removed(self):
        mh.hub.acquire('llama', 'A')
        c = http.client.HTTPConnection('127.0.0.1', self.hub_server.server_port)
        c.request('POST', '/v1/chat/completions', json.dumps({'model':'sage-a1.5'}))
        try:
            until(lambda: mh.hub.snapshot()['queued'] == 1); c.close()
            until(lambda: mh.hub.snapshot()['queued'] == 0)
        finally: mh.hub.release(); c.close()


if __name__ == '__main__': unittest.main()
