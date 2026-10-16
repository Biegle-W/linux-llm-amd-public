#!/usr/bin/env python3
"""Local serial profile switcher for the configured vLLM or HyperQwen worker."""
import http.client
import json
import os
import signal
import socket
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from rocm_runtime import require_rocm_headroom

ROOT = Path('/opt/local-llm/dsh')
BACKEND = os.environ.get('LOCAL_VLLM_BACKEND', 'vllm')
if BACKEND not in ('vllm', 'hyperqwen'):
    raise SystemExit('Unknown local vLLM backend: ' + BACKEND)
PROFILES = json.loads((ROOT / (BACKEND + '-profiles.json')).read_text())
PUBLIC_PORT, WORKER_PORT = (18020, 18021) if BACKEND == 'hyperqwen' else (30010, 30011)
MODEL = '/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ'
DEFAULT = 'qwen3.8-27b-hyperqwen-dflash2' if BACKEND == 'hyperqwen' else 'qwen3.8-27b-vllm'
lock = threading.Lock()
lifecycle = threading.RLock()
closing = threading.Event()
worker = None
active = None
logfile = None

def stop_worker():
    global worker, active, logfile
    with lifecycle:
        process, worker = worker, None
        active = None
        if process is not None:
            # vLLM can leave a rank alive when another rank fails during startup.
            # Clean the entire owned group even if the API parent already exited.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        if logfile is not None:
            logfile.close()
            logfile = None

def get_worker(path):
    with urllib.request.urlopen(f'http://127.0.0.1:{WORKER_PORT}' + path, timeout=2) as response:
        body = response.read()
        return json.loads(body) if body else {}

def ensure_worker(model):
    global worker, active, logfile
    if active == model and worker is not None and worker.poll() is None:
        return
    stop_worker()
    cfg = PROFILES[model]
    if cfg.get('runtime') == 'rocm':
        require_rocm_headroom()
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', WORKER_PORT)) == 0:
            raise RuntimeError(f'{BACKEND} worker port {WORKER_PORT} is already occupied. Close the other server first.')
    worker_env = os.environ.copy()
    if BACKEND == 'hyperqwen':
        args = ['bash', str(ROOT.parent / 'hyperqwen/start-test')]
        worker_env.update(HYPERQWEN_SPEC=cfg['spec'], HYPERQWEN_PORT=str(WORKER_PORT),
                          HYPERQWEN_SERVED_MODEL=model, HYPERQWEN_CONTEXT=str(cfg['context']),
                          HYPERQWEN_KV_BYTES=str(cfg['kv_cache_bytes']))
    else:
        launcher = cfg.get('launcher', '/opt/local-llm/vllm/start-qwen')
        args = [launcher,
                '--port', str(WORKER_PORT), '--served-model-name', model,
                '--max-model-len', str(cfg['context']),
                '--gpu-memory-utilization', str(cfg['memory_fraction'])]
        if cfg.get('kv_cache_bytes'):
            args += ['--kv-cache-memory-bytes', str(cfg['kv_cache_bytes'])]
        args += cfg.get('extra_args', [])
        if cfg['mtp']:
            args += ['--speculative-config', json.dumps({
                'method': 'mtp', 'num_speculative_tokens': 3})]
    with lifecycle:
        if closing.is_set():
            raise RuntimeError(BACKEND + ' router is stopping')
        logfile = (ROOT / 'logs' / (BACKEND + '-' + model + '.log')).open('a')
        worker = subprocess.Popen(args, stdout=logfile, stderr=subprocess.STDOUT,
                                  env=worker_env,
                                  start_new_session=True)
    for _ in range(1200):
        if closing.is_set():
            raise RuntimeError(BACKEND + ' router is stopping')
        if worker.poll() is not None:
            stop_worker()
            raise RuntimeError(BACKEND + ' failed to load; see Desktop/local-llm/dsh/logs/' + BACKEND + '-' + model + '.log')
        try:
            get_worker('/health')
            info = get_worker('/v1/models')
        except Exception:
            time.sleep(1)
            continue
        capacities = [item.get('max_model_len', 0) for item in info.get('data', [])]
        if not capacities or min(capacities) < cfg['context']:
            stop_worker()
            raise RuntimeError('Worker context does not match profile: ' + str(capacities))
        active = model
        return
    stop_worker()
    raise RuntimeError(BACKEND + ' startup timed out')

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
            return self.send_json(200, {'status': 'ok', 'active_model': active,
                                        'active_mode': PROFILES.get(active, {}).get('spec')})
        if self.path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': [
                {'id': key, 'object': 'model', 'owned_by': 'local-' + BACKEND,
                 'context_length': cfg['context']} for key, cfg in PROFILES.items()]})
        self.send_json(404, {'error': 'Unknown endpoint'})

    def do_POST(self):
        if self.path not in ('/v1/chat/completions', '/v1/completions', '/generate'):
            return self.send_json(404, {'error': 'Unknown endpoint'})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            model = data.get('model', DEFAULT)
            # Preserve chats made with the first single-mode HyperQwen catalog.
            if BACKEND == 'hyperqwen' and model == 'qwen3.8-27b':
                model = DEFAULT
                data['model'] = model
            if model not in PROFILES:
                return self.send_json(400, {'error': 'Unknown model: ' + str(model)})
        except (ValueError, TypeError):
            return self.send_json(400, {'error': 'Invalid JSON request'})
        started = False
        connection = None
        try:
            with lock:
                ensure_worker(model)
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

def interrupted(*args):
    raise KeyboardInterrupt

if __name__ == '__main__':
    if BACKEND == 'hyperqwen':
        from hardware_guard import require_hyperqwen
        require_hyperqwen()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    ThreadingHTTPServer.daemon_threads = True
    server = ThreadingHTTPServer(('127.0.0.1', PUBLIC_PORT), Handler)
    if BACKEND == 'hyperqwen':
        def warmup():
            try:
                with lock:
                    ensure_worker(DEFAULT)
            except Exception as error:
                if not closing.is_set():
                    print('HyperQwen initial load failed:', error, flush=True)
        threading.Thread(target=warmup, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        closing.set()
        server.server_close()
        stop_worker()
