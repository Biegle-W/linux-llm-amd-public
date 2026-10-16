#!/usr/bin/env python3
"""Load one selected Strata quant immediately and serve it until the terminal closes."""
import argparse
import http.client
import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from strata_prefix import add_document_prefix

ROOT = Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / 'strata-profiles.json').read_text())
DEFAULT = next(iter(PROFILES))
WORKER_PORT = 30021
requests = threading.Lock()
lifecycle = threading.Lock()
stopping = threading.Event()
worker = active = logfile = None


def stop_worker():
    global worker, active, logfile
    proc, worker = worker, None
    active = None
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=40)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    if logfile is not None:
        logfile.close()
        logfile = None


def ensure_worker(model):
    global worker, active, logfile
    with lifecycle:
        if stopping.is_set():
            raise RuntimeError('Strata is shutting down')
        if active == model and worker is not None and worker.poll() is None:
            return
        stop_worker()
        profile = PROFILES[model]
        config = ROOT / profile['config']
        logfile = (ROOT / 'logs' / ('strata-' + model + '.log')).open('a')
        print('Loading', model, 'from Shared SATA; other Strata weights are unloaded.', flush=True)
        worker = subprocess.Popen([str(ROOT / 'run-strata-backend'),
                                   '--config', str(config), '--port', str(WORKER_PORT)],
                                  stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True)
        proc = worker
    try:
        for _ in range(600):
            if stopping.is_set():
                raise RuntimeError('Strata is shutting down')
            if proc.poll() is not None:
                raise RuntimeError('Strata failed to load; see dsh/logs/strata-' + model + '.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{WORKER_PORT}/health', timeout=2) as response:
                    health = json.load(response)
            except (OSError, ValueError):
                stopping.wait(1)
                continue
            if not health.get('loaded'):
                stopping.wait(1)
                continue
            if health.get('model') != model or health.get('max_context', 0) < profile['context']:
                raise RuntimeError('Strata worker has an unexpected model or context capacity')
            with lifecycle:
                if stopping.is_set():
                    raise RuntimeError('Strata is shutting down')
                active = model
            return
        raise RuntimeError('Strata startup exceeded 10 minutes')
    except Exception:
        with lifecycle:
            stop_worker()
        raise


class Handler(BaseHTTPRequestHandler):
    def send_json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self.send_json(200, {'status': 'ok', 'active_model': active})
        if self.path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': [
                {'id': key, 'object': 'model', 'owned_by': 'local-strata',
                 'context_length': cfg['context'],
                 'status': {'value': 'loaded' if active == key else 'unloaded'}}
                for key, cfg in PROFILES.items()]})
        self.send_json(404, {'error': 'Unknown endpoint'})

    def do_POST(self):
        if self.path not in ('/v1/chat/completions', '/models/load', '/models/unload'):
            return self.send_json(404, {'error': 'Unknown endpoint'})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            if not isinstance(data, dict):
                raise ValueError('Expected an object')
            model = data.get('model', DEFAULT)
            if model not in PROFILES:
                return self.send_json(400, {'error': {
                    'message': f'Strata serves only {DEFAULT}. Q2 has been retired; select Q3 in your client.',
                    'type': 'invalid_request_error'}})
        except (ValueError, TypeError):
            return self.send_json(400, {'error': 'Invalid JSON request'})
        started = False
        connection = None
        try:
            with requests:
                if self.path == '/models/unload':
                    with lifecycle:
                        if active == model:
                            stop_worker()
                    return self.send_json(200, {'success': True})
                ensure_worker(model)
                if self.path == '/models/load':
                    return self.send_json(200, {'success': True})
                data = add_document_prefix(data)
                connection = http.client.HTTPConnection('127.0.0.1', WORKER_PORT, timeout=86400)
                connection.request('POST', self.path, json.dumps(data), {'Content-Type': 'application/json'})
                response = connection.getresponse()
                self.send_response(response.status)
                self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                self.send_header('Connection', 'close')
                self.end_headers()
                started = True
                while chunk := response.read1(65536):
                    self.wfile.write(chunk)
                    self.wfile.flush()
                self.close_connection = True
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as error:
            if not started:
                self.send_json(503, {'error': {'message': str(error), 'type': 'backend_error'}})
            self.close_connection = True
        finally:
            if connection is not None:
                connection.close()


def interrupted(*_):
    raise KeyboardInterrupt


if __name__ == '__main__':
    from hardware_guard import require_strata
    try:
        require_strata()
    except RuntimeError as error:
        raise SystemExit(str(error))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=list(PROFILES), default=DEFAULT)
    args = parser.parse_args()
    DEFAULT = args.model
    PROFILES = {DEFAULT: PROFILES[DEFAULT]}
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    server = ThreadingHTTPServer(('127.0.0.1', 30020), Handler)
    try:
        ensure_worker(DEFAULT)
        print('Strata Q3 ready on 30020:', DEFAULT, '(close this terminal before switching backends).', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        server.server_close()
        with lifecycle:
            stop_worker()
