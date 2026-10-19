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
from moe_memory import host_memory, worker_memory
from strata_memory import MemoryGuard, vram_snapshot

ROOT = Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / 'strata-profiles.json').read_text())
DEFAULT = next(iter(PROFILES))
WORKER_PORT = 30021
requests = threading.Lock()
lifecycle = threading.Lock()
stopping = threading.Event()
worker = active = logfile = None
memory_fault = None


def watch_memory():
    """Unload only the owned worker before desktop headroom is exhausted."""
    global memory_fault
    guard = MemoryGuard()
    while not stopping.wait(.5):
        proc = worker
        if proc is None or proc.poll() is not None:
            guard = MemoryGuard()
            continue
        _, available = host_memory()
        swap, spill = worker_memory(proc.pid)
        try:
            readings = vram_snapshot()
        except (OSError, ValueError, RuntimeError):
            readings = None
        reason = guard.check(available, swap, spill, readings)
        if reason:
            with lifecycle:
                if worker is proc:
                    memory_fault = reason
                    print('Strata memory guard: ' + reason +
                          '; unloading only the owned worker. Explicit reload or restart required.', flush=True)
                    stop_worker(timeout=3)
            guard = MemoryGuard()


def stop_worker(timeout=40):
    global worker, active, logfile
    proc, worker = worker, None
    active = None
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=timeout)
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
        if memory_fault:
            raise RuntimeError(memory_fault + '; use /models/load explicitly or restart after freeing GPU memory')
        if active == model and worker is not None and worker.poll() is None:
            return
        stop_worker()
        from hardware_guard import require_strata
        require_strata()
        profile = PROFILES[model]
        config = ROOT / profile['config']
        logfile = (ROOT / 'logs' / ('strata-' + model + '.log')).open('a')
        print('Loading', model, 'from Shared SATA; other Strata weights are unloaded.', flush=True)
        worker = subprocess.Popen(['systemd-run', '--user', '--scope', '--quiet',
                                   '--property=MemorySwapMax=0', str(ROOT / 'run-strata-backend'),
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
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def do_GET(self):
        if self.path == '/health':
            return self.send_json(200, {'status': 'degraded' if memory_fault else 'ok',
                                        'active_model': active, 'memory_fault': memory_fault})
        if self.path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': [
                {'id': key, 'object': 'model', 'owned_by': 'local-strata',
                 'context_length': cfg['context'],
                 'status': {'value': 'loaded' if active == key else 'unloaded'}}
                for key, cfg in PROFILES.items()]})
        self.send_json(404, {'error': 'Unknown endpoint'})

    def do_POST(self):
        global memory_fault
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
                if self.path == '/models/load':
                    with lifecycle:
                        memory_fault = None
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
    threading.Thread(target=watch_memory, daemon=True).start()
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
