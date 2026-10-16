#!/usr/bin/env python3
"""Serialize the configured native llama.cpp models behind one DSH endpoint."""
import argparse
import http.client
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from llama_runtime import launch_spec

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / 'models.json').read_text())
lock = threading.Lock()
native = None
native_port = 0


def call(port, path, data=None, timeout=5):
    req = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
        None if data is None else json.dumps(data).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def stop_process(proc):
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
            data = call(native_port, '/v1/models')['data']
            return self.respond(200, {'object': 'list', 'data': data})
        with lock:
            self.proxy(native_port, 'GET')

    def do_POST(self):
        try:
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            data = json.loads(body or b'{}')
            model = data.get('model')
            if model not in {m['id'] for m in CATALOG}:
                return self.respond(400, {'error': {'message': 'Select an activated model from /v1/models; other hardware profiles are still deferred.'}})
            with lock:
                self.proxy(native_port, 'POST', body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as error:
            self.respond(503, {'error': {'message': str(error), 'type': 'backend_error'}})

    def proxy(self, port, method, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=86400)
        started = False
        try:
            connection.request(method, self.path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
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
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
        native = subprocess.Popen([str(binary),
            '--models-preset', str(preset), '--models-max', '1',
            '--host', '127.0.0.1', '--port', str(native_port)], env=worker_env, start_new_session=True)
        ready(native, native_port)
        print(f'Local llama.cpp model router listening on {args.port}', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if server:
            server.server_close()
        stop_process(native)
