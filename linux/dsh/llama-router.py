#!/usr/bin/env python3
"""Serialize the configured native llama.cpp models behind one DSH endpoint."""
import argparse
import http.client
import json
import os
from pathlib import Path
from inference_idle import inference_request
from inference_swap import WorkerSwapGuard
import signal
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from llama_runtime import launch_spec, require_amd_headroom, runtime_identity
from moe_memory import admit_model, watch_worker, worker_limits_for_model, require_model_capacity

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / 'models.json').read_text())
lock = threading.Lock()
native = None
native_port = 0
active_model = None
active_mode = None
active_runtime = None
active_limits = None
memory_watch = None
swap_guard = WorkerSwapGuard()


def call(port, path, data=None, timeout=5):
    req = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
        None if data is None else json.dumps(data).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def stop_process(proc):
    swap_guard.stop(proc)
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()


def ready(proc, port):
    for _ in range(600):
        if proc.poll() is not None:
            raise RuntimeError(f'Backend exited with status {proc.returncode}; see terminal output.')
        try:
            if call(port, '/health', timeout=1).get('status') == 'ok':
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError('Backend startup exceeded 10 minutes')


def backend_for_model(model):
    settings = json.loads((ROOT / 'llama-runtime.json').read_text())
    return settings.get('runtime_overrides', {}).get(model, settings['backend'])


@inference_request
def activate_native(mode, spec=None, model=None):
    """Switch only this router's native worker; preserve the frontend and API port."""
    global native, active_mode, active_runtime, active_model, active_limits, memory_watch
    swap_guard.check()
    if model is not None:
        require_model_capacity(model)
    limits = worker_limits_for_model(model)
    if limits and mode != 'hip-amd':
        raise RuntimeError('Validated VRAM-only profiles require HIP AMD; no worker was changed.')
    identity = runtime_identity(mode, model)
    if native is not None and native.poll() is None and active_runtime == identity and active_limits == limits:
        return
    # Verify the requested binary/devices before unloading a working model.
    binary, preset, env, enabled = spec or launch_spec(mode, model=model)
    if memory_watch:
        memory_watch.set()
    stop_process(native)
    active_model = None
    if enabled is not None:
        require_amd_headroom()
    args = [str(binary),
        '--models-preset', str(preset), '--models-max', '1',
        '--host', '127.0.0.1', '--port', str(native_port)]
    if enabled is not None:
        args = ['systemd-run', '--user', '--scope', '--quiet',
                '--property=MemorySwapMax=0', *args]
    if limits:
        args[4:4] = ['--property=MemoryHigh='+str(limits['memory.high']),
                     '--property=MemoryMax='+str(limits['memory.max'])]
    native = swap_guard.spawn(args, env=env, start_new_session=True,
                              **({'expected_memory_limits':limits} if limits else {}))
    ready(native, native_port)
    swap_guard.ready(native)
    active_mode = mode
    active_runtime = identity
    active_limits = limits
    memory_watch = watch_worker(native, lambda: active_model, stop_process)
    print(f'llama.cpp native runtime selected: {mode}', flush=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def respond(self, code, data):
        content = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path)
        if path.path == '/health':
            return self.respond(200 if native.poll() is None else 503, {'status': 'ok' if native.poll() is None else 'error'})
        if path.path == '/v1/models':
            current = {item['id']: item for item in call(native_port, '/v1/models')['data']}
            # Profiles of the inactive runtime are loadable on request; the built-in Chat needs a status.
            data = [{**current.get(model['id'], {'id': model['id'], 'object': 'model',
                                               'owned_by': 'local-llm',
                                               'status': {'value': 'unloaded'}}),
                     'context_length': model['context'],
                     'runtime': backend_for_model(model['id'])} for model in CATALOG]
            return self.respond(200, {'object': 'list', 'data': data})
        if 'model' in urllib.parse.parse_qs(path.query) and 'autoload' not in path.query:
            # The built-in Chat must load models through the admitted POST path.
            self.path += '&autoload=false'
        if path.path == '/models/sse':
            # A long-lived status stream must not hold the request lock.
            return self.proxy(native_port, 'GET')
        with lock:
            self.proxy(native_port, 'GET')

    @inference_request
    def do_POST(self):
        global active_model
        try:
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            data = json.loads(body or b'{}')
            model = data.get('model')
            if model is None and urllib.parse.urlsplit(self.path).path == '/v1/streams/lookup':
                # The built-in Chat's resumable-stream lookup loads nothing.
                return self.proxy(native_port, 'POST', body)
            if model not in {m['id'] for m in CATALOG}:
                return self.respond(400, {'error': {'message': 'Select an activated model from /v1/models; other hardware profiles are still deferred.'}})
            with lock:
                activate_native(backend_for_model(model), model=model)
                admit_model(model, call, native_port)
                active_model = model
                self.proxy(native_port, 'POST', body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as error:
            self.respond(503, {'error': {'message': str(error), 'type': 'backend_error'}})

    def proxy(self, port, method, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=86400)
        started = False
        try:
            # The built-in Chat is served gzip-only, so its encoding headers must pass through.
            headers = {'Content-Type': 'application/json'}
            if self.headers.get('Accept-Encoding'):
                headers['Accept-Encoding'] = self.headers['Accept-Encoding']
            connection.request(method, self.path, body, headers)
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            for name in ('Content-Encoding', 'Cache-Control', 'ETag',
                         'Cross-Origin-Embedder-Policy', 'Cross-Origin-Opener-Policy'):
                if response.getheader(name):
                    self.send_header(name, response.getheader(name))
            self.send_header('Connection', 'close')
            self.end_headers()
            started = True
            while chunk := response.read1(65536):
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception:
            if not started:
                raise
        finally:
            self.close_connection = True
            connection.close()


def stop(*_):
    raise KeyboardInterrupt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    native_port = args.port + 1
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)
    binary, preset, worker_env, enabled = launch_spec()
    if enabled is not None:
        CATALOG = [m for m in CATALOG if m['id'] in enabled]
    server = None
    memory_watch = None
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
        activate_native(json.loads((ROOT / 'llama-runtime.json').read_text())['backend'],
                        (binary, preset, worker_env, enabled))
        print(f'Local llama.cpp model router listening on {args.port}', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if memory_watch:
            memory_watch.set()
        if server:
            server.server_close()
        stop_process(native)
