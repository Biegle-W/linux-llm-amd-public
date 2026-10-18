#!/usr/bin/env python3
"""Local serial profile switcher for the configured SGLang worker."""
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
from rocm_runtime import require_rocm_headroom

ROOT = Path('/opt/local-llm/dsh')
PROFILES = json.loads((ROOT / 'sglang-profiles.json').read_text())
MODEL = '/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ'
DEFAULT = 'qwen3.8-27b-sglang-dflash2'
lock = threading.Lock()
worker = None
active = None
logfile = None

def stop_worker():
    global worker, active, logfile
    if worker is not None:
        try:
            os.killpg(worker.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            worker.wait(timeout=20)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(worker.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        worker.wait()
    worker = None
    active = None
    if logfile is not None:
        logfile.close()
        logfile = None

def get_worker(path):
    with urllib.request.urlopen('http://127.0.0.1:30001' + path, timeout=2) as response:
        body = response.read()
        return json.loads(body) if body else {}

def cache_capacities(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'max_total_num_tokens' and isinstance(item, int):
                yield item
            yield from cache_capacities(item)
    elif isinstance(value, list):
        for item in value:
            yield from cache_capacities(item)

def worker_environment(cfg):
    verify = cfg.get('rdna_verify', False)
    repair = cfg.get('rdna_verify_walk_fix', False)
    if verify and not repair:
        raise RuntimeError('Optimized verification requires the validated KV-walk repair')
    return {**os.environ, 'SGLANG_LOCAL_SHARE_QWEN_MTP': '1',
            'SGLANG_RDNA_VLLM_VERIFY': str(int(bool(verify))),
            'SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX': str(int(bool(repair)))}


def ensure_worker(model):
    global worker, active, logfile
    cfg = PROFILES[model]
    if not cfg.get('enabled', True):
        raise RuntimeError(cfg.get('disabled_reason', 'This profile is disabled.'))
    env = worker_environment(cfg)
    if active == model and worker is not None and worker.poll() is None:
        return
    stop_worker()
    if cfg.get('runtime') == 'rocm':
        require_rocm_headroom(cfg.get('min_free_vram_gib', 22.25))
    model_path = cfg.get('model_path', MODEL)
    launcher = cfg.get('launcher', '/opt/local-llm/sglang/start-qwen-rocm')
    args = [launcher, '--model-path', model_path,
            '--port', '30001', '--served-model-name', model,
            '--context-length', str(cfg['context']), '--max-total-tokens', str(cfg['context']),
            '--mem-fraction-static', str(cfg['memory_fraction'])]
    if cfg['mtp']:
        args += ['--speculative-algorithm', 'EAGLE', '--speculative-draft-model-path', model_path,
                 '--speculative-num-steps', str(cfg.get('mtp_steps', 3)), '--speculative-eagle-topk', '1',
                 '--speculative-num-draft-tokens', str(cfg.get('mtp_steps', 3) + 1)]
        if cfg.get('linear_replay', True):
            args += ['--enable-linear-replayssm-spec']
    args += cfg.get('extra_args', [])
    if cfg.get('scope_memory_max'):
        args = ['systemd-run', '--user', '--scope', '--quiet',
                '-p', 'MemoryMax=' + cfg['scope_memory_max'], *args]
    logfile = (ROOT / 'logs' / ('sglang-' + model + '.log')).open('a')
    worker = subprocess.Popen(args, stdout=logfile, stderr=subprocess.STDOUT,
                              env=env,
                              start_new_session=True)
    for _ in range(600):
        if worker.poll() is not None:
            stop_worker()
            raise RuntimeError('SGLang failed to load; see Desktop/local-llm/dsh/logs/sglang-' + model + '.log')
        try:
            get_worker('/health')
            info = get_worker('/server_info')
        except Exception:
            time.sleep(1)
            continue
        capacities = list(cache_capacities(info))
        if not capacities or min(capacities) < cfg['context']:
            stop_worker()
            raise RuntimeError('Insufficient actual KV cache for this profile: ' + str(capacities))
        active = model
        return
    stop_worker()
    raise RuntimeError('SGLang startup timed out')

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
                {'id': key, 'object': 'model', 'owned_by': 'local-sglang',
                 'context_length': cfg['context']} for key, cfg in PROFILES.items()
                if cfg.get('enabled', True)]})
        self.send_json(404, {'error': 'Unknown endpoint'})

    def do_POST(self):
        if self.path not in ('/v1/chat/completions', '/v1/completions', '/generate'):
            return self.send_json(404, {'error': 'Unknown endpoint'})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            model = data.get('model', DEFAULT)
            if model not in PROFILES:
                return self.send_json(400, {'error': 'Unknown model: ' + str(model)})
        except (ValueError, TypeError):
            return self.send_json(400, {'error': 'Invalid JSON request'})
        started = False
        connection = None
        try:
            with lock:
                ensure_worker(model)
                connection = http.client.HTTPConnection('127.0.0.1', 30001, timeout=86400)
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
    signal.signal(signal.SIGTERM, interrupted)
    server = ThreadingHTTPServer(('127.0.0.1', 30000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        stop_worker()
