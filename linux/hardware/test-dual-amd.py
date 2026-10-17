#!/usr/bin/env python3
"""Sequential dual AMD profile validation, with owned-process cleanup."""
import argparse, configparser, importlib.util, json, os, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from amd_device import amd_devices
from llama_runtime import launch_spec
import backend_switch
spec = importlib.util.spec_from_file_location('checks', ROOT / 'hardware/test-speculative.py')
checks = importlib.util.module_from_spec(spec); spec.loader.exec_module(checks)
OUT = ROOT / 'hardware/generated/dual-amd-2026-10-16'

def stream_trial(body):
    request = urllib.request.Request(f'http://127.0.0.1:{checks.PORT}/v1/chat/completions',
                                     json.dumps(body).encode(), {'Content-Type': 'application/json'})
    first = None
    usage = None
    content = ''
    reasoning = ''
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=600) as response:
        for line in response:
            line = line.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]': continue
            item = json.loads(line[6:]); usage = item.get('usage') or usage
            for choice in item.get('choices', []):
                delta = choice.get('delta', {})
                text = delta.get('content') or ''
                thought = delta.get('reasoning_content') or delta.get('reasoning') or ''
                if (text or thought) and first is None: first = time.monotonic()
                content += text; reasoning += thought
    end = time.monotonic()
    assert first is not None and usage, 'Missing streamed output or usage'
    return {'content': content, 'reasoning': reasoning, 'usage': usage,
            'total_seconds': end-start, 'decode_tps_approx': (usage['completion_tokens']-1)/(end-first)}

def run(case):
    devices = amd_devices()
    env = dict(os.environ)
    port = str(checks.PORT)
    model = checks.MODEL
    if case.startswith('sglang'):
        profiles = json.loads((ROOT / 'dsh/sglang-profiles.json').read_text())
        cfg = profiles['qwen3.8-27b-sglang' + ('-dflash2' if case.endswith('dflash2') else '')]
        cmd = [str(ROOT / 'sglang/start-qwen-rocm'), '--port', port, '--served-model-name', model,
               '--context-length', str(cfg['context']), '--max-total-tokens', str(cfg['context']),
               '--mem-fraction-static', str(cfg['memory_fraction'])]
        if cfg['mtp']:
            cmd += ['--speculative-algorithm', 'EAGLE', '--speculative-draft-model-path', cfg['model_path'],
                    '--speculative-num-steps', '2', '--speculative-eagle-topk', '1', '--speculative-num-draft-tokens', '3']
        cmd += cfg.get('extra_args', [])
    elif case == 'vllm':
        cmd = [str(ROOT / 'vllm/start-qwen-rocm'), '--port', port, '--served-model-name', model,
               '--speculative-config', '{"method":"mtp","num_speculative_tokens":3}']
    else:
        binary, preset, env, _ = launch_spec()
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(preset.read_text().split('version = 1', 1)[1])
        cfg = {**dict(parser['*']), **dict(parser[case])}
        cmd = [str(binary), '--host', '127.0.0.1', '--port', port, '--alias', model]
        for key, value in cfg.items():
            if value == 'true': cmd += ['--' + key]
            else: cmd += ['--' + key, value]
    OUT.mkdir(parents=True, exist_ok=True)
    result = {'case': case, 'command': cmd, 'status': 'running', 'peak_vram_bytes': [0, 0]}
    print('START', case, flush=True)
    with (OUT / (case + '.log')).open('w') as log:
        proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            start = time.monotonic()
            while time.monotonic() - start < 1200:
                if proc.poll() is not None: raise RuntimeError(f'worker exited {proc.returncode}')
                used = [int((d / 'mem_info_vram_used').read_text()) for d in devices]
                result['peak_vram_bytes'] = [max(a, b) for a, b in zip(result['peak_vram_bytes'], used)]
                available = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
                if available < 2 * 1024**3: raise RuntimeError('Host available memory below 2 GiB')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as response:
                        assert response.status == 200
                    break
                except Exception: time.sleep(2)
            else: raise RuntimeError('Startup timed out')
            result['startup_seconds'] = time.monotonic() - start
            if case.startswith('sglang'):
                info = checks.request('/server_info')
                def capacities(value):
                    if isinstance(value, dict):
                        for key, item in value.items():
                            if key == 'max_total_num_tokens' and isinstance(item, int): yield item
                            yield from capacities(item)
                    elif isinstance(value, list):
                        for item in value: yield from capacities(item)
                result['cache_capacities'] = list(capacities(info))
                assert result['cache_capacities'] and min(result['cache_capacities']) >= cfg['context']
            elif case == 'vllm':
                result['model_info'] = checks.request('/v1/models')
            else:
                result['props'] = checks.request('/props')

            result['validation'] = checks.validate()
            if not all(result['validation'][k] for k in ('arithmetic', 'ordered_json', 'tool_roundtrip')):
                raise RuntimeError('Output quality check failed')
            result['trial'] = stream_trial({
                'model': model, 'messages': [{'role': 'user', 'content': 'Write a detailed numbered guide to checking a shipment of bolts, washers and boxed sets.'}],
                'max_tokens': 256, 'temperature': 0, 'stream': True,
                'stream_options': {'include_usage': True}, 'chat_template_kwargs': {'enable_thinking': False}})
            used = [int((d / 'mem_info_vram_used').read_text()) for d in devices]
            result['peak_vram_bytes'] = [max(a, b) for a, b in zip(result['peak_vram_bytes'], used)]
            assert min(used) > 2 * 1024**3, 'Both cards must hold model allocations'
            result['status'] = 'passed'
        except Exception as error:
            result['error'] = str(error); result['status'] = 'failed'
        finally:
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=20)
            except subprocess.TimeoutExpired: pass
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
    (OUT / (case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('RESULT', case, result['status'], result.get('error'), result['peak_vram_bytes'], flush=True)
    return result

if __name__ == '__main__':
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    parser = argparse.ArgumentParser()
    parser.add_argument('cases', nargs='+')
    args = parser.parse_args()
    if any(backend_switch.is_inference(p) for p in backend_switch.processes().values()):
        parser.error('Another configured inference is running')
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(('127.0.0.1', checks.PORT))
    results = [run(case) for case in args.cases]
    sys.exit(0 if all(result['status'] == 'passed' for result in results) else 1)
