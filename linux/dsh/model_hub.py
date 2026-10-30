#!/usr/bin/env python3
"""Loopback OpenAI API for every enabled local model; starts or switches backends on demand.

A request naming any catalog model is proxied to its backend. If that backend is not
serving, the normal guarded launcher (dsh/start-backend-terminal) is started headlessly;
its startup handover stops the previous backend and keeps every memory/VRAM guard.
Switches wait for in-flight replies on the old backend, never run while an agent holds
hardware/generated/GPU-LOCK, and are serialized. Streaming clients receive SSE comment
keep-alives while a model loads.
After ten minutes of inference inactivity, the guarded idle watcher stops only
managed inference; DSH/gateway stay up and the next request starts it again.
"""
import argparse
from collections import deque
import http.client
import json
import os
from pathlib import Path
import signal
import select
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from model_catalog import BACKENDS, catalog
from inference_idle import inference_request, IdleUnloader, TIMEOUT
from hub_transport import clean_text, clean_error_body, error_payload, sse_error, relay_sse

PORT = 30100
GPU_LOCK = ROOT.parent / 'hardware/generated/GPU-LOCK'
LAUNCHER = ROOT / 'start-backend-terminal'
MAX_BODY = 32 * 1024 * 1024
LOAD_TIMEOUT = 1800
DRAIN_TIMEOUT = 900
KEEPALIVE = 10
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class HubError(Exception):
    def __init__(self, status, message, code):
        super().__init__(message)
        self.status, self.code = status, code


def serving(kind, model):
    """True when the backend's public router answers and lists the model."""
    try:
        with opener.open(f'http://127.0.0.1:{BACKENDS[kind][1]}/v1/models', timeout=3) as response:
            return model in {m.get('id') for m in json.load(response).get('data', [])}
    except (OSError, ValueError):
        return False


def gpu_lock_owner():
    try:
        return json.loads(GPU_LOCK.read_text()).get('owner', 'unknown')
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return 'unknown'


def launcher_error(kind):
    try:
        lines = (ROOT / 'logs' / f'{kind}-launcher.log').read_text(errors='replace').splitlines()
    except OSError:
        return ''
    failed = [line for line in lines[-40:] if 'failed' in line.lower() or 'requires' in line.lower()]
    return (failed or lines[-1:] or [''])[-1].strip()


class Hub:
    def __init__(self, serving=serving, launch=None, sleep=time.sleep,
                 capacities=None, max_queued=None, max_queued_bytes=MAX_BODY):
        self.cond = threading.Condition()
        # AMD routers hold their request locks through the complete response.
        # No native execution/concurrency setting is changed here.
        self.capacities = capacities or {kind: 1 for kind in BACKENDS}
        self.max_queued = len(catalog()) if max_queued is None else max_queued
        if self.max_queued < 1 or max_queued_bytes < 1 or any(v < 1 for v in self.capacities.values()):
            raise ValueError('Admission limits must be positive')
        self.max_queued_bytes = max_queued_bytes
        self.waiters = deque()
        self.queued_bytes = 0
        self.active = self.active_model = self.loading_model = None
        self.inflight = 0
        self.switching = False
        self.process = None
        self.serving, self.sleep = serving, sleep
        self.launch = launch or self._launch

    def snapshot(self):
        with self.cond:
            return {'status': 'ok', 'active_backend': self.active,
                    'active_model': self.active_model, 'loading_model': self.loading_model,
                    'switching': self.switching, 'inflight': self.inflight,
                    'queued': len(self.waiters), 'queued_bytes': self.queued_bytes,
                    'max_queued': self.max_queued, 'max_queued_bytes': self.max_queued_bytes,
                    'max_inflight': self.capacities.get(self.active, 1),
                    'capacity_by_backend': dict(self.capacities),
                    'idle_timeout_seconds': TIMEOUT}

    def _launch(self, kind, model):
        args = [str(LAUNCHER), kind]
        if kind in ('strata', 'maya'):
            args.append('--no-browser')
        if kind in ('maya','strata'):
            args += ['--model', model]
        print(f'Starting {BACKENDS[kind][2]} for {model}.', flush=True)
        return subprocess.Popen(args, cwd=ROOT / 'workspace', stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)

    def acquire(self, kind, model, progress=lambda: None, body_bytes=0, timeout=DRAIN_TIMEOUT):
        """FIFO admission; only a contiguous same-model cohort may share capacity."""
        deadline = time.monotonic() + timeout
        ticket = object()
        queued = claimed = granted = False
        progress()
        try:
            with self.cond:
                immediate = not self.waiters and not self.switching and (
                    self.inflight == 0 or (self.active, self.active_model) == (kind, model)
                    and self.inflight < self.capacities[kind])
                if not immediate:
                    if len(self.waiters) >= self.max_queued or self.queued_bytes + body_bytes > self.max_queued_bytes:
                        raise HubError(429, 'The inference queue is full; retry later.', 'queue_full')
                self.waiters.append((ticket, body_bytes))
                self.queued_bytes += body_bytes
                queued = True
            while True:
                progress()  # Socket checks and writes never hold the admission condition.
                with self.cond:
                    if time.monotonic() >= deadline:
                        raise HubError(503, 'Inference queue wait expired; retry later.', 'queue_timeout')
                    at_head = not queued or self.waiters[0][0] is ticket
                    compatible = (self.active, self.active_model) == (kind, model)
                    if at_head and not self.switching and (self.inflight == 0 or
                            compatible and self.inflight < self.capacities[kind]):
                        if queued:
                            self.waiters.popleft()
                            self.queued_bytes -= body_bytes
                            queued = False
                        if self.inflight:
                            self.inflight += 1
                            granted = True
                            self.cond.notify_all()
                            return
                        self.switching = claimed = True
                        self.loading_model = model
                        break
                    self.cond.wait(min(.25, max(0, deadline - time.monotonic())))
            # Readiness probes and guarded launcher waits run outside the condition.
            self._start(kind, model, progress)
            progress()
            with self.cond:
                self.active, self.active_model = kind, model
                self.inflight += 1
                granted = True
        finally:
            with self.cond:
                if queued:
                    self.waiters.remove((ticket, body_bytes))
                    self.queued_bytes -= body_bytes
                if claimed:
                    self.switching = False
                    if not granted:
                        self.loading_model = None
                self.cond.notify_all()

    def response_started(self):
        with self.cond:
            self.loading_model = None

    def release(self):
        with self.cond:
            if self.inflight <= 0:
                raise RuntimeError('No inference admission is held')
            self.inflight -= 1
            if not self.inflight:
                self.loading_model = None
            self.cond.notify_all()

    def unload_idle(self):
        """Called only under the cross-process activity/startup/GPU locks."""
        with self.cond:
            if self.inflight or self.switching or self.waiters:
                return False
            self.switching = True
        stopped = False
        try:
            from backend_switch import stop_other_backends
            stop_other_backends(ROOT.parent, ROOT / 'data/backend-owner.json', idle=True)
            stopped = True
            return True
        finally:
            with self.cond:
                if stopped:
                    self.active = self.active_model = self.process = None
                self.switching = False
                self.cond.notify_all()

    def _start(self, kind, model, progress):
        if self.serving(kind, model):
            return
        owner = gpu_lock_owner()
        if owner:
            raise HubError(503, 'GPUs are reserved; no backend was started.', 'gpu_reserved')
        try:
            self.process = self.launch(kind, model)
        except OSError as error:
            raise HubError(503, clean_text(str(error)), 'backend_start_failed') from error
        deadline = time.monotonic() + LOAD_TIMEOUT
        while time.monotonic() < deadline:
            if self.serving(kind, model):
                return
            if self.process is not None and self.process.poll() is not None:
                detail = clean_text(launcher_error(kind))
                raise HubError(503, f'{BACKENDS[kind][2]} could not start: {detail or "see its launcher log"}',
                               'backend_start_failed')
            progress()
            self.sleep(KEEPALIVE / 5)
        raise HubError(504, f'{BACKENDS[kind][2]} did not become ready in {LOAD_TIMEOUT // 60} minutes.',
                       'backend_start_timeout')


hub = Hub()
idle = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        # Never log request or response bodies.
        print(self.command, urlsplit(self.path).path, flush=True)

    def send_json(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if status in (429, 503):
            self.send_header('Retry-After', '5')
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, status, message, code):
        self.send_json(status, {'error': {'message': clean_text(message), 'code': code,
                                          'type': 'invalid_request_error' if status < 500 else 'backend_error'}})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/health':
            state = hub.snapshot()
            state.update(gpu_reserved=bool(gpu_lock_owner()), idle_state=idle.status if idle else 'not started')
            return self.send_json(200, state)
        models = catalog()
        state = hub.snapshot()
        for model in models.values():
            model['loaded'] = (model['backend'] == state['active_backend'] and
                               model['id'] == state['active_model'])
            model['auto_start'] = True
        if path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': list(models.values())})
        if path.startswith('/v1/models/'):
            model = models.get(unquote(path.removeprefix('/v1/models/')))
            return self.send_json(200, model) if model else self.error_json(404, 'Unknown model.', 'model_not_found')
        self.error_json(404, 'Unknown endpoint.', 'not_found')

    @inference_request
    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ('/v1/chat/completions', '/v1/completions', '/v1/responses'):
            return self.error_json(404, 'Only OpenAI chat/completion/Responses endpoints are exposed.', 'not_found')
        try:
            if self.headers.get('Transfer-Encoding'):
                raise ValueError
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.error_json(413, 'Request must be between 1 byte and 32 MiB.', 'body_size')
            self.connection.settimeout(60)
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError
            data = json.loads(body)
            if not isinstance(data, dict) or not isinstance(data.get('model'), str):
                raise ValueError
        except (ValueError, OSError):
            return self.error_json(400, 'Invalid JSON request; a model ID is required.', 'bad_request')
        model = catalog().get(data['model'])
        if model is None:
            return self.error_json(404, 'Unknown or retired model. Use GET /v1/models.', 'model_not_found')
        kind = model['backend']
        if kind in ('strata', 'maya') and path not in ('/v1/chat/completions', '/v1/responses'):
            return self.error_json(400, f'{BACKENDS[kind][2]} supports chat completions and Responses.', 'unsupported_endpoint')
        self.close_connection = True
        if data.get('stream'):
            return self.stream(kind, model['id'], path, body)
        try:
            hub.acquire(kind, model['id'], self.check_client, body_bytes=len(body))
        except HubError as error:
            return self.error_json(error.status, str(error), error.code)
        except OSError:
            return
        try:
            self.forward(kind, path, body)
        finally:
            hub.release()

    def check_client(self):
        readable, _, _ = select.select([self.connection], [], [], 0)
        if readable and not self.connection.recv(1, socket.MSG_PEEK):
            raise ConnectionResetError('Client disconnected')

    def forward(self, kind, path, body):
        connection = http.client.HTTPConnection('127.0.0.1', BACKENDS[kind][1], timeout=86400)
        started = False
        try:
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            hub.response_started()
            payload = response.read()
            if response.status >= 400:
                payload = clean_error_body(payload)
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            self.send_header('Content-Length', str(len(payload)))
            if response.getheader('Retry-After'):
                self.send_header('Retry-After', response.getheader('Retry-After'))
            self.end_headers()
            started = True
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (OSError, http.client.HTTPException):
            if not started:
                self.error_json(503, 'Backend connection failed; see its launcher log.', 'backend_unavailable')
        finally:
            connection.close()

    def stream(self, kind, model, path, body):
        # Loading keep-alives require early HTTP headers; later failures use SSE.
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        lock = threading.Lock()
        def write(chunk):
            with lock:
                self.wfile.write(chunk)
                self.wfile.flush()
        last = [time.monotonic()]
        def progress():
            self.check_client()
            if time.monotonic() - last[0] >= KEEPALIVE:
                write(f': loading {model}\n\n'.encode())
                last[0] = time.monotonic()
        acquired = False
        first = threading.Event()
        connection = None
        try:
            hub.acquire(kind, model, progress, body_bytes=len(body))
            acquired = True
            def keepalive():
                while not first.wait(KEEPALIVE):
                    try:
                        write(f': loading {model}\n\n'.encode())
                    except OSError:
                        return
            threading.Thread(target=keepalive, daemon=True).start()
            connection = http.client.HTTPConnection('127.0.0.1', BACKENDS[kind][1], timeout=86400)
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            hub.response_started()
            if response.status >= 400 or 'text/event-stream' not in response.getheader('Content-Type', ''):
                first.set()
                return write(sse_error(error_payload(response.read(65536), response.status if response.status >= 400 else 502), responses=path == '/v1/responses'))
            def output(chunk):
                first.set()
                write(chunk)
            relay_sse(response, output, responses=path == "/v1/responses")
        except HubError as error:
            write(sse_error({'message': str(error), 'code': error.code, 'status': error.status}, responses=path == '/v1/responses'))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (OSError, http.client.HTTPException):
            try:
                write(sse_error({'message': 'Backend stream interrupted.', 'code': 'backend_unavailable', 'status': 503}, responses=path == '/v1/responses'))
            except OSError:
                pass
        finally:
            first.set()
            if connection is not None:
                connection.close()
            if acquired:
                hub.release()


def detect_active():
    """Adopt a backend that is already serving when the hub starts."""
    for kind in BACKENDS:
        try:
            with opener.open(f'http://127.0.0.1:{BACKENDS[kind][1]}/v1/models', timeout=2):
                hub.active = kind
                return
        except OSError:
            continue


def main():
    global idle
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=PORT)
    args = parser.parse_args()
    detect_active()
    idle = IdleUnloader(hub.unload_idle, lambda: hub.active).start()
    ThreadingHTTPServer.daemon_threads = True
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    def stop(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    print(f'Local model hub on 127.0.0.1:{args.port}; active backend: {hub.active or "none"}.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        idle.done.set()
        # Backends keep running; they are owned by their launchers, not the hub.
        server.server_close()


if __name__ == '__main__':
    main()
