#!/usr/bin/env python3
"""Isolated dual-AMD context/cache/prefill comparison; does not edit profiles."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from amd_device import amd_devices
import backend_switch

spec = importlib.util.spec_from_file_location('dual_checks', ROOT / 'hardware/test-dual-amd.py')
dual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dual)
checks = dual.checks
OUT = ROOT / 'hardware/generated/sglang-dual-context-2026-10-17'


def stream(messages, limit=256):
    body = dict(model=checks.MODEL, messages=messages, temperature=0, max_tokens=limit,
                stream=True, stream_options={'include_usage': True},
                chat_template_kwargs={'enable_thinking': False})
    req = urllib.request.Request(f'http://127.0.0.1:{checks.PORT}/v1/chat/completions',
                                 json.dumps(body).encode(), {'Content-Type': 'application/json'})
    start = time.monotonic()
    first = usage = None
    text = reasoning = ''
    with urllib.request.urlopen(req, timeout=900) as response:
        for line in response:
            line = line.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]':
                continue
            item = json.loads(line[6:])
            usage = item.get('usage') or usage
            for choice in item.get('choices', []):
                delta = choice.get('delta', {})
                content = delta.get('content') or ''
                thought = delta.get('reasoning_content') or delta.get('reasoning') or ''
                if (content or thought) and first is None:
                    first = time.monotonic()
                text += content
                reasoning += thought
    end = time.monotonic()
    assert first is not None and usage, 'Missing output/usage'
    return dict(content=text, reasoning=reasoning, usage=usage, ttft_seconds=first-start,
                total_seconds=end-start, decode_tps_approx=(usage['completion_tokens']-1)/(end-first),
                input_tokens_per_ttft=usage['prompt_tokens']/(first-start))


def marker_prompt(budget):
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(Path(checks.TARGET) / 'tokenizer.json'))
    codes = ['ALPHA-734', 'BRAVO-915', 'CHARLIE-268']
    def make(n):
        lines = [f'Record {i:05d}: location bay {i%97}, blue bolts {i%31+1}, washers {i%43+2}, boxed sets {i%19+1}.' for i in range(n)]
        for i, code in zip([5, n//2, n-5], codes):
            lines[i] += ' Secret marker: ' + code
        return 'Read the records. Return all three secret markers exactly, in record order, and nothing else.\n' + '\n'.join(lines)
    low, high = 20, budget
    while low + 1 < high:
        mid = (low + high)//2
        if len(tokenizer.encode(make(mid)).ids) <= budget:
            low = mid
        else:
            high = mid
    return make(low), codes


def capacities(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == 'max_total_num_tokens' and isinstance(v, int):
                yield v
            yield from capacities(v)
    elif isinstance(value, list):
        for v in value:
            yield from capacities(v)


def run(args):
    devices = amd_devices()
    profiles = json.loads((ROOT / 'dsh/sglang-profiles.json').read_text())
    cfg = profiles['qwen3.8-27b-sglang' + ('-dflash2' if args.mode == 'dflash' else '')]
    extra = [x for x in cfg.get('extra_args', []) if x != '--disable-radix-cache']
    cmd = [str(ROOT / 'sglang/start-qwen-rocm'), '--port', str(checks.PORT),
           '--served-model-name', checks.MODEL, '--context-length', str(args.context),
           '--max-total-tokens', str(args.context), '--mem-fraction-static', str(args.memory)]
    if cfg['mtp']:
        cmd += ['--speculative-algorithm', 'EAGLE', '--speculative-draft-model-path', cfg['model_path'],
                '--speculative-num-steps', '2', '--speculative-eagle-topk', '1', '--speculative-num-draft-tokens', '3']
    cmd += extra + ['--max-mamba-cache-size', str(args.mamba), '--chunked-prefill-size', str(args.chunk),
                    '--max-prefill-tokens', str(max(1024, args.chunk)), '--enable-cache-report']
    if not args.cache:
        cmd += ['--disable-radix-cache']
    case = f'{args.mode}-ctx{args.context}-cache{int(args.cache)}-chunk{args.chunk}-states{args.mamba}'
    OUT.mkdir(parents=True, exist_ok=True)
    result = dict(case=case, settings=vars(args), command=cmd, status='running',
                  peak_vram_bytes=[0, 0], min_host_available_bytes=2**63,
                  max_nonresident_vram_bytes=0, alerts=[], trials=[])
    done = threading.Event()
    ready = threading.Event()
    print('START', case, flush=True)
    with (OUT / (case + '.log')).open('w') as log:
        proc = subprocess.Popen(cmd, env={**os.environ, 'SGLANG_CUDA_COREDUMP_BEFORE_CRASH_WAIT_SECS': '0'},
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        def monitor():
            while not done.wait(1):
                used = [int((d / 'mem_info_vram_used').read_text()) for d in devices]
                result['peak_vram_bytes'] = [max(a, b) for a, b in zip(result['peak_vram_bytes'], used)]
                available = next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
                result['min_host_available_bytes'] = min(available, result['min_host_available_bytes'])
                if available < 2*1024**3:
                    result['alerts'].append('Host available RAM below 2 GiB')
                if ready.is_set():
                    tree = backend_switch.processes()
                    ids = {proc.pid}
                    for _ in range(8):
                        ids.update(p.pid for p in tree.values() if p.parent in ids)
                    spill = sum(checks.gpu.amd_residency(pid)['nonresident_vram_bytes'] for pid in ids)
                    result['max_nonresident_vram_bytes'] = max(spill, result['max_nonresident_vram_bytes'])
                    if spill > 256*1024**2:
                        result['alerts'].append('VRAM spill exceeds 256 MiB')
                if result['alerts']:
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    return
        watcher = threading.Thread(target=monitor, daemon=True)
        watcher.start()
        try:
            start = time.monotonic()
            while time.monotonic()-start < 900:
                if proc.poll() is not None:
                    raise RuntimeError(f'Worker exited {proc.returncode}')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{checks.PORT}/health', timeout=2) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('Startup timed out')
            ready.set()
            result['reported_cache_capacities'] = list(capacities(checks.request('/server_info')))
            assert result['reported_cache_capacities'] and min(result['reported_cache_capacities']) >= args.context
            result['quality'] = checks.validate()
            assert all(result['quality'][k] for k in ('arithmetic', 'ordered_json', 'tool_roundtrip'))
            print('QUALITY passed', case, flush=True)
            prompts = {
                'inventory': 'Write a detailed numbered shipment-checking guide with examples.\n' + '\n'.join(f'Bin {n}: blue bolts 12, washers 24, boxed sets 6.' for n in range(140)),
                'code': 'Change only return value_20 + 1 to return value_20 + 2. Output the entire updated Python file without markdown.\n' + '\n\n'.join(f'def function_{n}(value_{n}):\n    """Process item {n} and increment it."""\n    return value_{n} + 1' for n in range(40)),
                'prose': 'Write an original literary scene about an astronomer discovering a handwritten letter inside an abandoned observatory. Use varied sentences and concrete sensory details.'}
            for repeat in range(args.repeats):
                for name, prompt in prompts.items():
                    checks.request('/flush_cache', {})
                    trial = stream([{'role': 'user', 'content': prompt}])
                    trial.update(workload=name, repeat=repeat)
                    result['trials'].append(trial)
                    print('TRIAL', name, repeat, round(trial['decode_tps_approx'], 2), 'ttft', round(trial['ttft_seconds'], 3), flush=True)
            prompt, codes = marker_prompt(8000)
            messages = [{'role': 'user', 'content': prompt}]
            checks.request('/flush_cache', {})
            result['prefix'] = []
            for name, ms in [('cold', messages), ('repeat', messages)]:
                trial = stream(ms, 96)
                trial['phase'] = name
                assert all(code in trial['content'] for code in codes), trial['content']
                result['prefix'].append(trial)
                print('PREFIX', name, round(trial['ttft_seconds'], 3), trial['usage'], flush=True)
            continuation = messages + [{'role': 'assistant', 'content': result['prefix'][0]['content']},
                                        {'role': 'user', 'content': 'Repeat those same three secret markers in record order, exactly.'}]
            trial = stream(continuation, 96)
            trial['phase'] = 'continuation'
            assert all(code in trial['content'] for code in codes), trial['content']
            result['prefix'].append(trial)
            print('PREFIX continuation', round(trial['ttft_seconds'], 3), trial['usage'], flush=True)
            if args.cache:
                assert any((t['usage'].get('prompt_tokens_details') or {}).get('cached_tokens', 0) > 4000 for t in result['prefix'][1:]), 'No confirmed substantial prefix-cache hit'
            if args.long:
                prompt, codes = marker_prompt(args.context-1500)
                checks.request('/flush_cache', {})
                print('LONG begin', case, flush=True)
                trial = stream([{'role': 'user', 'content': prompt}], 128)
                trial['passed'] = all(code in trial['content'] for code in codes)
                result['long_retrieval'] = trial
                print('LONG', trial['passed'], trial['usage'], round(trial['ttft_seconds'], 3), flush=True)
                assert trial['passed'], trial['content']
            assert min(result['peak_vram_bytes']) > 2*1024**3
            assert not result['alerts']
            result['status'] = 'passed'
        except Exception as error:
            result.update(status='failed', error=str(error))
        finally:
            done.set()
            watcher.join(timeout=3)
            checks.gpu.terminate(proc)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    (OUT / (case + '.json')).write_text(json.dumps(result, indent=2)+'\n')
    print('RESULT', case, result['status'], result.get('error'), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['mtp', 'dflash'], default='dflash')
    parser.add_argument('--context', type=int, required=True)
    parser.add_argument('--chunk', type=int, required=True)
    parser.add_argument('--cache', action='store_true')
    parser.add_argument('--mamba', type=int, default=8)
    parser.add_argument('--memory', type=float, default=.85)
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--long', action='store_true')
    args = parser.parse_args()
    if any(backend_switch.is_inference(p) for p in backend_switch.processes().values()):
        parser.error('Another configured inference is active; use scoped handover first')
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(('127.0.0.1', checks.PORT))
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    sys.exit(0 if run(args)['status'] == 'passed' else 1)
