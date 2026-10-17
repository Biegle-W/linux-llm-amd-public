#!/usr/bin/env python3
"""Isolated TP2 protocol/speculation trials using saved NVIDIA benchmark prompts."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import statistics
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('context_checks', ROOT/'hardware/test-sglang-dual-context.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
checks = base.checks
OUT = ROOT/'hardware/generated/dual-tuning-2026-10-17'
PROMPTS = {
    'code': 'Write a Python function that merges two sorted lists. Explain its time and space complexity.',
    'prose': 'Write a short story about a lighthouse keeper finding a letter.'}


def stream(prompt, *, limit=256, sampled=True):
    body = dict(model=checks.MODEL, messages=[{'role':'user','content':prompt}],
                temperature=.6 if sampled else 0, max_tokens=limit,
                stream=True, stream_options={'include_usage':True},
                chat_template_kwargs={'enable_thinking':False})
    if sampled:
        body.update(top_p=.95, seed=42)
    request = urllib.request.Request(f'http://127.0.0.1:{checks.PORT}/v1/chat/completions',
                                    json.dumps(body).encode(), {'Content-Type':'application/json'})
    start = time.monotonic()
    first = usage = None
    text = ''
    with urllib.request.urlopen(request, timeout=180) as response:
        for line in response:
            line = line.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]':
                continue
            item = json.loads(line[6:])
            usage = item.get('usage') or usage
            for choice in item.get('choices', []):
                delta = choice.get('delta', {})
                content = delta.get('content') or delta.get('reasoning_content') or ''
                if content and first is None:
                    first = time.monotonic()
                text += content
    end = time.monotonic()
    assert first is not None and usage
    return dict(content=text, usage=usage, ttft_seconds=first-start,
                total_seconds=end-start, decode_tps_approx=(usage['completion_tokens']-1)/(end-first))


def memory_info():
    return {line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:', 'SwapTotal:', 'SwapFree:'))}


def run(args):
    initial_memory = memory_info()
    if initial_memory['MemAvailable'] < 12*1024**3:
        raise RuntimeError('Need at least 12 GiB available host RAM before loading a test model')
    initial_swap = initial_memory['SwapTotal']-initial_memory['SwapFree']
    devices = base.amd_devices()
    if args.engine == 'sglang':
        profiles = json.loads((ROOT/'dsh/sglang-profiles.json').read_text())
        cfg = profiles['qwen3.8-27b-sglang' + ('-dflash2' if args.mode == 'dflash' else '')]
        cmd = [str(ROOT/'sglang/start-qwen-rocm'), '--port', str(checks.PORT),
               '--served-model-name', checks.MODEL]
        if args.mode == 'mtp':
            cmd += ['--speculative-algorithm','EAGLE','--speculative-draft-model-path',cfg['model_path'],
                    '--speculative-num-steps',str(args.steps),'--speculative-eagle-topk','1',
                    '--speculative-num-draft-tokens',str(args.steps+1)]
        cmd += cfg['extra_args']
        if args.mode == 'dflash':
            cmd += ['--context-length','65536','--max-total-tokens','65536']
        context = cfg['context']
    else:
        context = 65536
        cmd = [str(ROOT/'vllm/start-qwen-rocm'),'--port',str(checks.PORT),
               '--served-model-name', checks.MODEL, '--speculative-config',
               json.dumps({'method':'mtp','num_speculative_tokens':3})]
    env = dict(os.environ, SGLANG_RDNA_VLLM_VERIFY=str(args.verify),
               SGLANG_CUDA_COREDUMP_BEFORE_CRASH_WAIT_SECS='0')
    env.pop('NCCL_PROTO', None)
    if args.protocol != 'auto':
        env['NCCL_PROTO'] = args.protocol
    case = f'{args.engine}-{args.mode}{args.steps if args.mode == "mtp" else 8}-{args.protocol}-verify{args.verify}'
    OUT.mkdir(parents=True, exist_ok=True)
    result = dict(case=case, settings=vars(args), context=context, status='running', trials=[],
                  peak_vram_bytes=[0,0], min_host_available_bytes=2**63,
                  max_nonresident_vram_bytes=0, max_swap_growth_bytes=0, alerts=[])
    done = threading.Event()
    ready = threading.Event()
    print('START',case,flush=True)
    with (OUT/(case+'.log')).open('w') as log:
        proc = subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        def monitor():
            while not done.wait(.5):
                used = [int((d/'mem_info_vram_used').read_text()) for d in devices]
                result['peak_vram_bytes'] = [max(a,b) for a,b in zip(used,result['peak_vram_bytes'])]
                memory = memory_info()
                available = memory['MemAvailable']
                swap_growth = max(0,memory['SwapTotal']-memory['SwapFree']-initial_swap)
                result['max_swap_growth_bytes'] = max(swap_growth,result['max_swap_growth_bytes'])
                if swap_growth > 1024**3:
                    result['alerts'].append('Swap use grew by more than 1 GiB; close competing memory workloads')
                result['min_host_available_bytes'] = min(available,result['min_host_available_bytes'])
                if available < 2*1024**3:
                    result['alerts'].append('Host available memory below 2 GiB')
                if ready.is_set():
                    tree = base.backend_switch.processes()
                    ids = {proc.pid}
                    for _ in range(8):
                        ids.update(p.pid for p in tree.values() if p.parent in ids)
                    spill = sum(checks.gpu.amd_residency(pid)['nonresident_vram_bytes'] for pid in ids)
                    result['max_nonresident_vram_bytes'] = max(spill,result['max_nonresident_vram_bytes'])
                    if spill > 256*1024**2:
                        result['alerts'].append('VRAM spill above 256 MiB')
                if result['alerts']:
                    try:
                        os.killpg(proc.pid,signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    return
        watcher = threading.Thread(target=monitor,daemon=True)
        watcher.start()
        try:
            start = time.monotonic()
            while time.monotonic()-start < 600:
                if proc.poll() is not None:
                    raise RuntimeError(f'Worker exited {proc.returncode}')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{checks.PORT}/health',timeout=2) as response:
                        if response.status == 200:
                            break
                except OSError:
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('Startup timeout')
            ready.set()
            result['startup_seconds'] = time.monotonic()-start
            result['quality'] = checks.validate()
            assert all(result['quality'][k] for k in ('arithmetic','ordered_json','tool_roundtrip')), 'Quality check failed'
            # A second structured probe catches the historical verify-kernel ordering defect.
            ordered = stream('Return only a JSON array counting down from 20 to 1, in order. No markdown.',sampled=False)
            result['quality']['reverse_json'] = json.loads(ordered['content']) == list(range(20,0,-1))
            assert result['quality']['reverse_json'], 'Reverse ordering failed'
            print('QUALITY passed',case,flush=True)
            for prompt in PROMPTS.values():
                stream(prompt)  # Exclude warm-up from medians.
            for repeat in range(args.repeats):
                for name,prompt in PROMPTS.items():
                    trial = stream(prompt)
                    trial.update(workload=name,repeat=repeat)
                    result['trials'].append(trial)
                    print('TRIAL',case,name,repeat,round(trial['decode_tps_approx'],2),round(trial['ttft_seconds'],3),flush=True)
            result['medians'] = {name:dict(decode_tps=statistics.median(t['decode_tps_approx'] for t in result['trials'] if t['workload']==name),
                                         ttft_seconds=statistics.median(t['ttft_seconds'] for t in result['trials'] if t['workload']==name)) for name in PROMPTS}
            if args.long:
                prompt,codes = base.marker_prompt(context-1500)
                if args.engine == 'sglang':
                    checks.request('/flush_cache',{})
                trial = stream(prompt,limit=128,sampled=False)
                result['long_retrieval'] = trial
                trial['passed'] = all(code in trial['content'] for code in codes)
                assert trial['passed'], 'Near-window retrieval failed'
            assert not result['alerts']
            assert min(result['peak_vram_bytes']) > 2*1024**3
            result['status'] = 'passed'
        except Exception as error:
            result.update(status='failed',error=f'{type(error).__name__}: {error}')
        finally:
            done.set()
            watcher.join(timeout=3)
            checks.gpu.terminate(proc)
            try:
                os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
    (OUT/(case+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',case,result['status'],result.get('error'),result.get('medians'),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=['sglang','vllm'],default='sglang')
    parser.add_argument('--mode',choices=['mtp','dflash'],default='mtp')
    parser.add_argument('--steps',type=int,choices=[1,2,3],default=2)
    parser.add_argument('--protocol',choices=['auto','Simple'],default='auto')
    parser.add_argument('--verify',type=int,choices=[0,1],default=0)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--long',action='store_true')
    args = parser.parse_args()
    if any(base.backend_switch.is_inference(p) for p in base.backend_switch.processes().values()):
        parser.error('Another configured inference worker is active')
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        probe.bind(('127.0.0.1',checks.PORT))
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGHUP,interrupted)
    raise SystemExit(0 if run(args)['status']=='passed' else 1)
