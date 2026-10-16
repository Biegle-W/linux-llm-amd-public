#!/usr/bin/env python3
"""Sequential synthetic GPU-resident trials; never alter active launcher profiles."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/generated/gpu-resident-2026-10-16'
AMD = Path('/sys/bus/pci/devices/0000:03:00.0')
PORT = 18030
CASES = [
    ('qwen32-mtp', 'qwen3.8-27b-q4', 32768, 'Vulkan0', True),
    ('qwen64-mtp', 'qwen3.8-27b-q4', 65536, 'Vulkan0', True),
    ('qwen64-no-mtp', 'qwen3.8-27b-q4', 65536, 'Vulkan0', False),
    ('muse32', 'muse-glimmer-30b', 32768, 'Vulkan0', False),
    ('empero32-mtp', 'empero-qwen3.8-35b-a3b', 32768, 'Vulkan0', True),
    ('qwenmoe32-mtp', 'qwen3.6-35b-a3b', 32768, 'Vulkan0,Vulkan1', True),
    ('qwenmoe32-amd-mtp', 'qwen3.6-35b-a3b', 32768, 'Vulkan0', True),
    ('bolt64-amd', 'nemotron-3.5-bolt', 65536, 'Vulkan0', False),
]


def request(path, body=None, timeout=600):
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}' + path,
                                 None if body is None else json.dumps(body).encode(),
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def memory():
    mem = {line.split(':')[0]: int(line.split()[1]) * 1024
           for line in Path('/proc/meminfo').read_text().splitlines()}
    return {'amd_vram_bytes': int((AMD / 'mem_info_vram_used').read_text()),
            'amd_gtt_bytes': int((AMD / 'mem_info_gtt_used').read_text()),
            'mem_available_bytes': mem['MemAvailable'],
            'swap_used_bytes': mem['SwapTotal'] - mem['SwapFree']}


def terminate(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=30)
    except ProcessLookupError:
        pass
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


def amd_residency(pid):
    seen, total, resident = set(), 0, 0
    for path in (Path('/proc') / str(pid) / 'fdinfo').glob('*'):
        try:
            fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        except OSError:
            continue
        client = fields.get('drm-client-id')
        if fields.get('drm-driver', '').strip() != 'amdgpu' or client in seen:
            continue
        seen.add(client)
        total += int(fields.get('drm-total-vram', '0').split()[0]) * 1024
        resident += int(fields.get('drm-resident-vram', '0').split()[0]) * 1024
    return {'allocated_vram_bytes': total, 'resident_vram_bytes': resident,
            'nonresident_vram_bytes': max(0, total - resident)}


def run(case, long_only=False, no_host_visible=False, model_path=None, backend='vulkan'):
    name, model, context, devices, mtp = case
    if backend == 'hip':
        if ',' in devices:
            raise ValueError('Mixed AMD/NVIDIA tests require --backend vulkan')
        name += '-hip'
        devices = 'ROCm0'
    if long_only:
        name += '-long'
    if no_host_visible:
        name += '-no-host-visible'
    models = {m['id']: m for m in json.loads((ROOT / 'dsh/models.json').read_text())}
    cmd = [str(ROOT / f'llama.cpp/build-{backend}/bin/llama-server'),
           '--model', model_path or models[model]['path'], '--alias', model,
           '--host', '127.0.0.1', '--port', str(PORT), '--device', devices,
           '--n-gpu-layers', '99', '--fit', 'off', '--ctx-size', str(context),
           '--override-tensor', 'token_embd.*=' + devices.split(',')[0],
           '--parallel', '1', '--batch-size', '512', '--ubatch-size', '128',
           '--flash-attn', 'on', '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0',
           '--jinja', '--reasoning', 'off', '--log-colors', 'off', '-lv', '4',
           '--spec-type', 'draft-mtp' if mtp else 'none']
    if mtp:
        cmd += ['--spec-draft-n-max', '3', '--spec-draft-type-k', 'q8_0', '--spec-draft-type-v', 'q8_0']
    cmd += ['--cache-ram', '0', '--ctx-checkpoints', '0']
    cmd += ['--split-mode', 'layer', '--tensor-split', '2,1'] if ',' in devices else ['--split-mode', 'none']
    env = dict(os.environ)
    env.pop('GGML_VK_PREFER_HOST_MEMORY', None)
    env.pop('GGML_VK_ALLOW_SYSMEM_FALLBACK', None)
    env.pop('GGML_VK_DISABLE_HOST_VISIBLE_VIDMEM', None)
    if no_host_visible:
        env['GGML_VK_DISABLE_HOST_VISIBLE_VIDMEM'] = '1'
    env['LD_LIBRARY_PATH'] = ':'.join(str(ROOT / p) for p in
        ('llm-tools/vulkan-sdk/usr/lib/x86_64-linux-gnu', 'llm-tools/cuda-build/lib'))
    if backend == 'hip':
        loaded = subprocess.run(['bash', '-c', 'source "$1"; env -0', 'bash',
                                 str(ROOT / 'hardware/rocm-env.sh')],
                                capture_output=True, check=True, timeout=10)
        env = dict(item.decode().split('=', 1) for item in loaded.stdout.split(b'\0') if item)
        env['LD_LIBRARY_PATH'] += ':' + str(ROOT / 'llm-tools/cuda-build/lib')
        env.pop('GGML_CUDA_ENABLE_UNIFIED_MEMORY', None)
    else:
        sys.path.insert(0, str(ROOT / 'dsh'))
        from llama_runtime import select_vulkan_devices
        env = select_vulkan_devices(cmd[0], env, mixed=',' in devices)
    result = {'case': name, 'model': model, 'context': context, 'devices': devices,
              'mtp': mtp, 'kv': 'q8_0', 'command': cmd, 'before': memory()}
    result['disable_host_visible_vidmem'] = bool(env.get('GGML_VK_DISABLE_HOST_VISIBLE_VIDMEM'))
    result['started_unix'] = time.time()
    samples, alerts = [], []
    done = threading.Event()
    loaded = threading.Event()
    residency_samples = []
    path = OUT / (name + '.log')
    print('START', name, flush=True)
    with path.open('w') as logfile:
        proc = subprocess.Popen(cmd, env=env, stdout=logfile, stderr=subprocess.STDOUT,
                                start_new_session=True)
        def monitor():
            while not done.wait(1):
                sample = memory()
                samples.append(sample)
                if loaded.is_set():
                    residency = amd_residency(proc.pid)
                    residency_samples.append(residency)
                    if residency['nonresident_vram_bytes'] > 256 * 1024**2:
                        alerts.append('AMD model has over 256 MiB of nonresident VRAM; refusing host spill')
                if sample['mem_available_bytes'] < 2 * 1024**3:
                    alerts.append('Host available memory fell below 2 GiB')
                # Cold loading can transiently stage several GiB through GTT.
                # Enforce the paging limit after readiness, alongside DRM residency.
                if loaded.is_set() and sample['amd_gtt_bytes'] > result['before']['amd_gtt_bytes'] + 2 * 1024**3:
                    alerts.append('AMD GTT grew by over 2 GiB; refusing paging-heavy trial')
                if ',' not in devices and sample['amd_vram_bytes'] > 23 * 1024**3:
                    alerts.append('AMD VRAM exceeded 23 GiB; retaining about 1 GiB display headroom')
                if alerts:
                    terminate(proc)
                    return
        watch = threading.Thread(target=monitor, daemon=True)
        watch.start()
        try:
            started = time.monotonic()
            while time.monotonic() - started < 600:
                if proc.poll() is not None:
                    raise RuntimeError(f'server exited {proc.returncode}')
                try:
                    if request('/health', timeout=2).get('status') == 'ok':
                        break
                except (OSError, ValueError):
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('startup exceeded 600s')
            result['startup_seconds'] = round(time.monotonic()-started, 3)
            result['loaded_memory'] = memory()
            loaded.set()
            smoke = request('/v1/chat/completions', {'model': model,
                'messages': [{'role': 'user', 'content': 'What is 17 times 19? Answer with only the number.'}],
                'max_tokens': 128, 'temperature': 0, 'chat_template_kwargs': {'enable_thinking': False}})
            result['smoke'] = smoke
            result['smoke_answer_correct'] = '323' in str(smoke.get('choices', []))
            tool_reply = request('/v1/chat/completions', {'model': model,
                'messages': [{'role':'user', 'content':'Use lookup_inventory to check the stock for SKU BOLT-42. Do not guess the stock.'}],
                'tools': [{'type':'function', 'function':{'name':'lookup_inventory',
                    'description':'Look up current stock by SKU.', 'parameters':{
                        'type':'object', 'properties':{'sku':{'type':'string'}}, 'required':['sku']}}}],
                'tool_choice':'auto', 'temperature':0, 'max_tokens':256,
                'chat_template_kwargs':{'enable_thinking':False}})
            calls = tool_reply.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])
            result['tool_call_reply'] = tool_reply
            result['tool_call_valid'] = bool(calls) and calls[0]['function']['name'] == 'lookup_inventory' and json.loads(calls[0]['function']['arguments']).get('sku') == 'BOLT-42'
            prompt = ('Read the synthetic inventory and then write a detailed numbered explanation of '
                      'how to verify a shipment, including concrete examples.\n' +
                      '\n'.join(f'Bin {i}: blue bolts 12, steel washers 24, boxed sets 6.' for i in range(140)))
            formatted = request('/apply-template', {'messages': [{'role':'user','content':prompt}],
                                                   'chat_template_kwargs': {'enable_thinking':False}})['prompt']
            result['trials'] = []
            for _ in range(0 if long_only else 2):
                trial = request('/completion', {'prompt': formatted, 'n_predict':256,
                    'temperature':0, 'seed':123, 'cache_prompt':False, 'ignore_eos':True})
                result['trials'].append({key:trial.get(key) for key in
                    ('timings','tokens_predicted','tokens_evaluated','truncated','stop','content')})
            if long_only:
                # Binary-search the rendered token count; never fill beyond the context.
                low, high, chosen = 1, 4000, None
                codes = ['ALPHA-734', 'BRAVO-915', 'CHARLIE-268']
                while low <= high:
                    count = (low + high) // 2
                    lines = [f'Bin {i}: blue bolts 12, steel washers 24, boxed sets 6.' for i in range(count)]
                    text = ('Read the inventory and retain the three marked codes.\nSTART_CODE=' + codes[0] + '\n' +
                            '\n'.join(lines[:count//2]) + '\nMIDDLE_CODE=' + codes[1] + '\n' +
                            '\n'.join(lines[count//2:]) + '\nEND_CODE=' + codes[2] +
                            '\nReturn only START_CODE, MIDDLE_CODE and END_CODE values, in that order.')
                    rendered = request('/apply-template', {'messages':[{'role':'user','content':text}],
                        'chat_template_kwargs':{'enable_thinking':False}})['prompt']
                    n = len(request('/tokenize', {'content':rendered, 'add_special':False})['tokens'])
                    if n <= min(60000, context-512):
                        chosen = (rendered, n)
                        low = count + 1
                    else:
                        high = count - 1
                if chosen is None:
                    raise RuntimeError('Could not construct long-context prompt')
                reply = request('/completion', {'prompt':chosen[0], 'n_predict':128,
                    'temperature':0, 'cache_prompt':False})
                result['long_context'] = {'input_tokens':chosen[1],
                    'expected_codes':codes, 'content':reply.get('content'),
                    'all_codes_retrieved':all(code in reply.get('content','') for code in codes),
                    'timings':reply.get('timings'), 'truncated':reply.get('truncated')}
            result['status'] = 'passed' if result['smoke_answer_correct'] else 'generation_requires_review'
            if not result.get('tool_call_valid'):
                result['status'] = 'tool_call_requires_review'
            if long_only and not result['long_context']['all_codes_retrieved']:
                result['status'] = 'retrieval_requires_review'
        except Exception as error:
            result['status'], result['error'] = 'failed', str(error)
        finally:
            done.set()
            watch.join(timeout=35)
            terminate(proc)
    result['alerts'] = alerts
    if residency_samples:
        result['residency'] = {
            'samples': len(residency_samples),
            'max_nonresident_vram_bytes': max(s['nonresident_vram_bytes'] for s in residency_samples),
            'last': residency_samples[-1],
        }
    if samples:
        result['peaks'] = {key: max(s[key] for s in samples) for key in
                          ('amd_vram_bytes','amd_gtt_bytes','swap_used_bytes')}
        result['peaks']['min_mem_available_bytes'] = min(s['mem_available_bytes'] for s in samples)
    log = path.read_text(errors='replace')
    result['placement_log'] = [line for line in log.splitlines() if
        re.search(r'offloaded .*layers|model buffer size|KV buffer size|compute buffer size', line)]
    result['cpu_model_mib'] = sum(float(x) for x in re.findall(
        r'CPU(?:_Mapped)? model buffer size\s*=\s*([0-9.]+) MiB', log))
    result['gpu_layers'] = re.findall(r'offloaded (\d+)/(\d+) layers to GPU', log)
    result['gpu_weight_placement_confirmed'] = bool(result['gpu_layers']) and all(
        a == b for a, b in result['gpu_layers']) and result['cpu_model_mib'] < 1
    if result['status'] == 'passed' and not result['gpu_weight_placement_confirmed']:
        result['status'] = 'placement_requires_review'
    result['after_stop'] = memory()
    result['finished_unix'] = time.time()
    (OUT / (name + '.json')).write_text(json.dumps(result, indent=2)+'\n')
    print('RESULT', name, result['status'], result.get('error',''),
          [t.get('timings') for t in result.get('trials',[])], flush=True)
    return result


if __name__ == '__main__':
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    parser.add_argument('--backend', choices=['hip', 'vulkan'], default='vulkan')
    parser.add_argument('--cases', nargs='+', choices=[c[0] for c in CASES])
    parser.add_argument('--long-context', action='store_true', help='One near-window retrieval instead of short speed trials')
    parser.add_argument('--no-host-visible-vram', action='store_true', help='Test device-local VRAM without the host-visible mapping preference')
    parser.add_argument('--model-path', help='Override the weight file for one explicitly selected test case')
    args = parser.parse_args()
    OUT = args.output_dir
    if args.backend == 'hip' and (args.no_host_visible_vram or 'qwenmoe32-mtp' in (args.cases or [])):
        parser.error('Vulkan-only options require --backend vulkan')
    if args.model_path and (not args.cases or len(args.cases) != 1):
        parser.error('--model-path requires exactly one --cases entry')
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / 'dsh'))
    import backend_switch
    existing = [p.pid for p in backend_switch.processes().values() if
        backend_switch.is_inference(p) or (p.args and p.args[0] ==
        str(ROOT / 'llama.cpp/build-vulkan/bin/llama-server'))]
    if existing:
        parser.error('Stop the existing inference through its launcher first; running PIDs: ' +
                     ', '.join(map(str, existing)))
    # A busy test port is never replaced or killed.
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', PORT))
    # Mixed-GPU diagnostics are explicit-only; AMD is the default.
    preferred = {'qwen64-mtp', 'muse32', 'empero32-mtp',
                 'qwenmoe32-amd-mtp', 'bolt64-amd'}
    selected = [c for c in CASES if c[0] in (args.cases or preferred)]
    for case in selected:
        run(case, args.long_context, args.no_host_visible_vram, args.model_path, args.backend)
