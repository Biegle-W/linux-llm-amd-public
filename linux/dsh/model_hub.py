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
import http.client
import json
import os
from pathlib import Path
import signal
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
    def __init__(self, serving=serving, launch=None, sleep=time.sleep):
        self.cond = threading.Condition()
        self.active = None      # backend kind the hub currently routes to
        self.inflight = 0       # proxied requests on self.active
        self.switching = False
        self.process = None
        self.serving, self.sleep = serving, sleep
        self.launch = launch or self._launch

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

    def acquire(self, kind, model, progress=lambda: None):
        """Reserve the backend for one request, starting or switching it if needed."""
        deadline = time.monotonic() + DRAIN_TIMEOUT
        with self.cond:
            while True:
                if not self.switching and self.active == kind and self.serving(kind, model):
                    self.inflight += 1
                    return
                if not self.switching and self.inflight == 0:
                    if self.serving(kind, model):
                        # Started outside the hub (Desktop shortcut or terminal).
                        self.active = kind
                        self.inflight += 1
                        return
                    self.switching = True
                    break
                if time.monotonic() >= deadline:
                    raise HubError(503, 'Another model is still answering; retry when it finishes.', 'backend_busy')
                self.cond.wait(KEEPALIVE)
                progress()
        try:
            self._start(kind, model, progress)
        except BaseException:
            with self.cond:
                self.switching = False
                self.cond.notify_all()
            raise
        with self.cond:
            self.switching = False
            self.active = kind
            self.inflight += 1
            self.cond.notify_all()

    def release(self):
        with self.cond:
            self.inflight -= 1
            self.cond.notify_all()

    def unload_idle(self):
        """Called only under the cross-process activity/startup/GPU locks."""
        with self.cond:
            if self.inflight or self.switching:
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
                    self.active = self.process = None
                self.switching = False
                self.cond.notify_all()

    def _start(self, kind, model, progress):
        if self.serving(kind, model):
            return
        owner = gpu_lock_owner()
        if owner:
            raise HubError(503, f'GPUs are reserved for a test ({owner}); no backend was started.', 'gpu_reserved')
        self.process = self.launch(kind, model)
        deadline = time.monotonic() + LOAD_TIMEOUT
        while time.monotonic() < deadline:
            if self.serving(kind, model):
                return
            if self.process is not None and self.process.poll() is not None:
                detail = launcher_error(kind)
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
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, status, message, code):
        self.send_json(status, {'error': {'message': message, 'code': code,
                                          'type': 'invalid_request_error' if status < 500 else 'backend_error'}})

    def do_GET(self):
        path = urlsplit(self.path).path
        models = catalog()
        loaded = {kind: kind == hub.active for kind in BACKENDS}
        for model in models.values():
            model['loaded'] = hub.serving(model['backend'], model['id']) if loaded[model['backend']] else False
            model['auto_start'] = True
        if path == '/health':
            return self.send_json(200, {'status': 'ok', 'active_backend': hub.active,
                                        'switching': hub.switching, 'gpu_reserved_by': gpu_lock_owner(),
                                        'inflight': hub.inflight, 'idle_timeout_seconds': TIMEOUT,
                                        'idle_state': idle.status if idle else 'not started'})
        if path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': list(models.values())})
        if path.startswith('/v1/models/'):
            model = models.get(unquote(path.removeprefix('/v1/models/')))
            return self.send_json(200, model) if model else self.error_json(404, 'Unknown model.', 'model_not_found')
        self.error_json(404, 'Unknown endpoint.', 'not_found')

    @inference_request
    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ('/v1/chat/completions', '/v1/completions'):
            return self.error_json(404, 'Only OpenAI chat/completion endpoints are exposed.', 'not_found')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.error_json(413, 'Request must be between 1 byte and 32 MiB.', 'body_size')
            body = self.rfile.read(length)
            data = json.loads(body)
            if not isinstance(data, dict) or not isinstance(data.get('model'), str):
                raise ValueError
        except ValueError:
            return self.error_json(400, 'Invalid JSON request; a model ID is required.', 'bad_request')
        model = catalog().get(data['model'])
        if model is None:
            return self.error_json(404, 'Unknown or retired model. Use GET /v1/models.', 'model_not_found')
        kind = model['backend']
        if kind in ('strata', 'maya') and path != '/v1/chat/completions':
            return self.error_json(400, f'{BACKENDS[kind][2]} supports chat completions.', 'unsupported_endpoint')
        self.close_connection = True
        if data.get('stream'):
            return self.stream(kind, model['id'], path, body)
        try:
            hub.acquire(kind, model['id'])
        except HubError as error:
            return self.error_json(error.status, str(error), error.code)
        try:
            self.forward(kind, path, body)
        finally:
            hub.release()

    def forward(self, kind, path, body):
        connection = http.client.HTTPConnection('127.0.0.1', BACKENDS[kind][1], timeout=86400)
        try:
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except OSError:
            self.error_json(503, 'Backend connection failed; see its launcher log.', 'backend_unavailable')
        finally:
            connection.close()

    def stream(self, kind, model, path, body):
        # Headers go out at once so clients see progress while a backend loads.
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
        def event_error(status, message, code):
            write(b'data: ' + json.dumps({'error': {'message': message, 'code': code, 'status': status}}).encode()
                  + b'\n\ndata: [DONE]\n\n')
        last = [time.monotonic()]
        def progress():
            if time.monotonic() - last[0] >= KEEPALIVE:
                write(f': loading {model}\n\n'.encode())
                last[0] = time.monotonic()
        try:
            hub.acquire(kind, model, progress)
        except HubError as error:
            return event_error(error.status, str(error), error.code)
        except OSError:
            return
        first = threading.Event()
        def keepalive():
            # Routers load a model on first request; keep the stream alive until output starts.
            while not first.wait(KEEPALIVE):
                try:
                    write(f': loading {model}\n\n'.encode())
                except OSError:
                    return
        threading.Thread(target=keepalive, daemon=True).start()
        connection = http.client.HTTPConnection('127.0.0.1', BACKENDS[kind][1], timeout=86400)
        try:
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            if response.status != 200:
                payload = response.read()
                first.set()
                try:
                    message = json.loads(payload)['error']['message']
                except (ValueError, KeyError, TypeError):
                    message = payload.decode(errors='replace')[:500]
                return event_error(response.status, message, 'backend_error')
            while chunk := response.read1(65536):
                first.set()
                write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except OSError:
            first.set()
            try:
                event_error(503, 'Backend connection failed; see its launcher log.', 'backend_unavailable')
            except OSError:
                pass
        finally:
            first.set()
            connection.close()
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
