#!/usr/bin/env python3
"""Serve one validated Maya model at a time, with scoped memory guards and switching."""
import argparse
import http.client
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from inference_idle import inference_request
from inference_swap import WorkerSwapGuard
from moe_memory import host_memory, worker_memory
from strata_memory import MemoryGuard, vram_snapshot

ROOT = Path(__file__).resolve().parent
from maya_runtime import profiles, require_maya
PROFILES = profiles()
if not PROFILES:
    raise SystemExit("No validated Maya profile is enabled; complete setup/validation first.")
DEFAULT = next(iter(PROFILES))
WORKER_PORT = 30032
requests = threading.Lock()
lifecycle = threading.Lock()
stopping = threading.Event()
worker = active = logfile = None
memory_fault = None
swap_guard = WorkerSwapGuard()
startup_whole_card_free_bytes = None
switch_state_lock = threading.Lock()
switch_operation = None


def worker_ready():
    return active is not None and worker is not None and worker.poll() is None


def web_status():
    with switch_state_lock:
        operation = dict(switch_operation) if switch_operation else None
    return {'active_model': active if worker_ready() else None,
            'memory_fault': memory_fault, 'busy': requests.locked(), 'operation': operation,
            'models': [{'id': key, 'name': cfg['name'], 'context': cfg['context']} for key, cfg in PROFILES.items()]}


def web_api_keys():
    # Match the native server's configured key list, never expose it to the UI.
    model = active or (switch_operation or {}).get('model') or DEFAULT
    value = json.loads((ROOT / PROFILES[model]['config']).read_text()).get('api_key', '')
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(key) for key in value if str(key)]
    return [key.strip() for key in str(value).split(',') if key.strip()]


def queue_model_switch(model):
    global switch_operation
    if model not in PROFILES:
        raise ValueError('Unknown or disabled Maya model. Choose an enabled profile.')
    if stopping.is_set():
        raise RuntimeError('Maya is shutting down.')
    if not requests.acquire(blocking=False):
        raise BlockingIOError('Maya is loading or answering. Finish or cancel the current request first.')
    # Background native jobs may outlive their HTTP response. Check them too.
    try:
        if worker_ready():
            with urllib.request.urlopen(f'http://127.0.0.1:{WORKER_PORT}/status', timeout=3) as response:
                status = json.load(response)
                if status.get('busy') or status.get('queued') or status.get('active'):
                    raise BlockingIOError('Maya is answering. Finish or cancel the current request first.')
    except Exception as error:
        requests.release()
        if isinstance(error, BlockingIOError):
            raise
        raise RuntimeError('Cannot verify that the Maya worker is idle; try again after it is ready.') from error
    with switch_state_lock:
        switch_operation = {'id': uuid.uuid4().hex, 'model': model, 'state': 'loading', 'error': None}
    def load():
        global memory_fault
        try:
            with lifecycle:
                memory_fault = None  # Explicit, validated load only, same as /models/load.
            ensure_worker(model)
            with switch_state_lock:
                switch_operation['state'] = 'ready'
        except Exception as error:
            with switch_state_lock:
                switch_operation.update(state='error', error=str(error))
        finally:
            requests.release()
    try:
        threading.Thread(target=load, daemon=True).start()
    except Exception:
        requests.release()
        raise
    return web_status()


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
                    print('Maya memory guard: ' + reason +
                          '; unloading only the owned worker. Explicit reload or restart required.', flush=True)
                    stop_worker(timeout=3)
            guard = MemoryGuard()


def stop_worker(timeout=40):
    global worker, active, logfile, startup_whole_card_free_bytes
    swap_guard.stop(worker)
    proc, worker = worker, None
    active = None
    startup_whole_card_free_bytes = None
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


@inference_request
def ensure_worker(model):
    global worker, active, logfile, memory_fault, startup_whole_card_free_bytes
    swap_guard.check()
    with lifecycle:
        if stopping.is_set():
            raise RuntimeError('Maya is shutting down')
        if memory_fault:
            raise RuntimeError(memory_fault + '; use /models/load explicitly or restart after freeing GPU memory')
        if active == model and worker is not None and worker.poll() is None:
            return
        require_maya(model,before_handover=True)
        stop_worker()
        time.sleep(2)
        require_maya(model)
        profile = PROFILES[model]
        config = ROOT / profile['config']
        logfile = (ROOT / 'logs' / ('maya-' + model + '.log')).open('a')
        print('Loading', model, 'from its configured model volume; other Maya weights are unloaded.', flush=True)
        worker = swap_guard.spawn(['systemd-run', '--user', '--scope', '--quiet',
                                   '--property=MemorySwapMax=infinity', '--property=MemoryMax=52G', str(ROOT / 'run-maya-backend'),
                                   '--config', str(config), '--port', str(WORKER_PORT)],
                                  stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True)
        proc = worker
    try:
        for _ in range(1200):
            if stopping.is_set():
                raise RuntimeError('Maya is shutting down')
            if proc.poll() is not None:
                raise RuntimeError('Maya failed to load; see dsh/logs/maya-' + model + '.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{WORKER_PORT}/health', timeout=2) as response:
                    health = json.load(response)
            except (OSError, ValueError):
                stopping.wait(1)
                continue
            if health.get('unloaded',True):
                stopping.wait(1)
                continue
            if health.get('model') != model or health.get('max_context', 0) != profile['context']:
                raise RuntimeError('Maya worker has an unexpected model or context capacity')
            with lifecycle:
                if stopping.is_set():
                    raise RuntimeError('Maya is shutting down')
                free=[row['free'] for row in vram_snapshot()]
                if len(free)!=2 or min(free)<6*1024**3:
                    memory_fault='Maya whole-card startup headroom is below 6 GiB; close unrelated GPU apps before explicit reload'
                    raise RuntimeError(memory_fault)
                startup_whole_card_free_bytes=free
                swap_guard.ready(proc, phase='idle')
                active = model
            return
        raise RuntimeError('Maya startup exceeded 20 minutes')
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
                                        'active_model': active, 'memory_fault': memory_fault,
                                        'startup_whole_card_free_bytes': startup_whole_card_free_bytes})
        if self.path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': [
                {'id': key, 'object': 'model', 'owned_by': 'local-maya',
                 'context_length': cfg['context'],
                 'status': {'value': 'loaded' if active == key else 'unloaded'}}
                for key, cfg in PROFILES.items()]})
        self.send_json(404, {'error': 'Unknown endpoint'})

    @inference_request
    def do_POST(self):
        global memory_fault
        if self.path not in ('/v1/chat/completions', '/models/load', '/models/unload'):
            return self.send_json(404, {'error': 'Unknown endpoint'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 32*1024**2:
                return self.send_json(413, {'error':'Request body exceeds the 32 MiB limit'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected an object')
            model = data.get('model', DEFAULT)
            if model not in PROFILES:
                return self.send_json(400, {'error': {
                    'message': 'Unknown or disabled Maya model; select one of the enabled API IDs.',
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
                with swap_guard.inference(worker):
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
    from maya_runtime import require_maya
    try:
        require_maya()
    except RuntimeError as error:
        raise SystemExit(str(error))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=list(PROFILES), default=DEFAULT)
    args = parser.parse_args()
    DEFAULT = args.model
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    server = ThreadingHTTPServer(('127.0.0.1', 30030), Handler)
    from maya_web import make_web_handler
    web = ThreadingHTTPServer(('127.0.0.1', 30031), make_web_handler(
        sys.modules[__name__], ROOT.parent / 'maya/upstream/serve/web', WORKER_PORT))
    threading.Thread(target=web.serve_forever, daemon=True).start()
    threading.Thread(target=watch_memory, daemon=True).start()
    try:
        with requests:
            ensure_worker(DEFAULT)
        print('Maya ready on 30030:', DEFAULT, '(close this terminal before switching backends).', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        server.server_close()
        web.shutdown()
        web.server_close()
        with lifecycle:
            stop_worker()
