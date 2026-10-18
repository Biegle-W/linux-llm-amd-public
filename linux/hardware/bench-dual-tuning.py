#!/usr/bin/env python3
"""Isolated TP2 protocol/speculation trials using saved NVIDIA benchmark prompts."""
import argparse
import importlib.util
import json
import os
import re
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


def stream(prompt, *, limit=256, sampled=True, timeout=180):
    body = dict(model=checks.MODEL, messages=[{'role':'user','content':prompt}],
                temperature=.6 if sampled else 0, max_tokens=limit,
                stream=True, stream_options={'include_usage':True},
                chat_template_kwargs={'enable_thinking':False})
    if sampled:
        body.update(top_p=.95, seed=42)
    swap_before = swap_io()
    request = urllib.request.Request(f'http://127.0.0.1:{checks.PORT}/v1/chat/completions',
                                    json.dumps(body).encode(), {'Content-Type':'application/json'})
    start = time.monotonic()
    first = usage = None
    text = ''
    with urllib.request.urlopen(request, timeout=timeout) as response:
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
    swap_after = swap_io()
    return dict(content=text, usage=usage, swap_io_pages={k:swap_after[k]-swap_before[k] for k in swap_before}, ttft_seconds=first-start,
                total_seconds=end-start, decode_tps_approx=(usage['completion_tokens']-1)/(end-first))


def swap_io():
    return {line.split()[0]:int(line.split()[1]) for line in Path('/proc/vmstat').read_text().splitlines() if line.startswith(('pswpin ', 'pswpout '))}


def memory_info():
    return {line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:', 'SwapTotal:', 'SwapFree:'))}


def process_swap_bytes(pids):
    total = 0
    for pid in pids:
        try:
            total += sum(int(line.split()[1])*1024 for line in Path(f'/proc/{pid}/status').read_text().splitlines() if line.startswith('VmSwap:'))
        except (FileNotFoundError,ProcessLookupError,PermissionError):
            pass
    return total


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
               '--served-model-name', checks.MODEL,
               '--kv-cache-dtype',args.vllm_kv,
               '--dtype',args.vllm_dtype,
               '--kv-cache-memory-bytes',str(args.vllm_kv_bytes),
               '--max-num-batched-tokens',str(args.chunk),
               '--compilation-config',json.dumps({'mode':args.compile_mode,'cudagraph_mode':'FULL_DECODE_ONLY'})]
        if args.mode == 'mtp':
            cmd += ['--speculative-config',json.dumps({'method':'mtp','num_speculative_tokens':args.steps}),
                    '--cudagraph-capture-sizes','1',str(args.steps+1)]
    env = dict(os.environ, SGLANG_RDNA_VLLM_VERIFY=str(args.verify),
               SGLANG_CUDA_COREDUMP_BEFORE_CRASH_WAIT_SECS='0')
    env['SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX'] = str(int(args.verify_walk_fix))
    env['LOCAL_LLM_NCCL_PROTO'] = args.protocol
    env['VLLM_LOCAL_RDNA_PREFILL'] = str(int(args.rdna_prefill))
    env.pop('NCCL_PROTO', None)
    if args.protocol != 'auto':
        env['NCCL_PROTO'] = args.protocol
    depth = args.steps if args.mode == 'mtp' else (8 if args.mode == 'dflash' else 0)
    case = f'{args.engine}-{args.mode}{depth}-{args.protocol}-verify{args.verify}'
    if args.verify_walk_fix:
        case += '-walkfix'
    if args.tag:
        case += '-' + args.tag
    if args.engine == 'vllm':
        case += f'-{args.vllm_dtype}-{args.vllm_kv}-chunk{args.chunk}-compile{args.compile_mode}'
        if args.rdna_prefill:
            case += '-rdna-prefill'
    OUT.mkdir(parents=True, exist_ok=True)
    result = dict(case=case, settings=vars(args), context=context, status='running', trials=[],
                  peak_vram_bytes=[0,0], peak_clock_mhz=[0,0], peak_power_watts=[0,0], peak_temp_celsius=[0,0], peak_junction_celsius=[0,0], peak_memory_celsius=[0,0], min_host_available_bytes=2**63,
                  max_nonresident_vram_bytes=0, max_swap_growth_bytes=0, max_owned_swap_growth_bytes=0,
                  max_startup_swap_growth_bytes=0, alerts=[])
    done = threading.Event()
    ready = threading.Event()
    ready_swap = [None]
    ready_owned_swap = [None]
    print('START',case,flush=True)
    with (OUT/(case+'.log')).open('w') as log:
        proc = subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        def monitor():
            while not done.wait(.5):
                used = [int((d/'mem_info_vram_used').read_text()) for d in devices]
                for index,device in enumerate(devices):
                    try:
                        clock = next(int(re.search(r'(\d+)Mhz',line).group(1)) for line in (device/'pp_dpm_sclk').read_text().splitlines() if '*' in line)
                        result['peak_clock_mhz'][index] = max(clock,result['peak_clock_mhz'][index])
                        hwmon = next((device/'hwmon').glob('hwmon*'))
                        power = int((hwmon/'power1_average').read_text())/1e6
                        temp = int((hwmon/'temp1_input').read_text())/1000
                        result['peak_power_watts'][index] = max(power,result['peak_power_watts'][index])
                        result['peak_temp_celsius'][index] = max(temp,result['peak_temp_celsius'][index])
                        for sensor,field in [('temp2_input','peak_junction_celsius'),('temp3_input','peak_memory_celsius')]:
                            reading = int((hwmon/sensor).read_text())/1000
                            result[field][index] = max(reading,result[field][index])
                    except (OSError,StopIteration,AttributeError,ValueError):
                        pass
                result['peak_vram_bytes'] = [max(a,b) for a,b in zip(used,result['peak_vram_bytes'])]
                memory = memory_info()
                available = memory['MemAvailable']
                swap_used = memory['SwapTotal']-memory['SwapFree']
                if ready.is_set():
                    if ready_swap[0] is None:
                        ready_swap[0] = swap_used
                    swap_growth = max(0,swap_used-ready_swap[0])
                    result['max_swap_growth_bytes'] = max(swap_growth,result['max_swap_growth_bytes'])
                else:
                    result['max_startup_swap_growth_bytes'] = max(result['max_startup_swap_growth_bytes'],swap_used-initial_swap)
                result['min_host_available_bytes'] = min(available,result['min_host_available_bytes'])
                if available < 2*1024**3:
                    result['alerts'].append('Host available memory below 2 GiB')
                if ready.is_set():
                    tree = base.backend_switch.processes()
                    ids = {proc.pid}
                    for _ in range(8):
                        ids.update(p.pid for p in tree.values() if p.parent in ids)
                    owned_swap = process_swap_bytes(ids)
                    if ready_owned_swap[0] is None:
                        ready_owned_swap[0] = owned_swap
                    result['max_owned_swap_growth_bytes'] = max(result['max_owned_swap_growth_bytes'],owned_swap-ready_owned_swap[0])
                    if result['max_owned_swap_growth_bytes'] > 1024**3:
                        result['alerts'].append('Backend-owned post-load swap use grew by more than 1 GiB')
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
            if args.verify_walk_fix or args.engine == 'vllm':
                count = stream('Return only a JSON array containing the integers 1 through 100 in ascending order. No markdown.',limit=1024,sampled=False)
                result['quality']['ordered_100'] = json.loads(count['content']) == list(range(1,101))
                assert result['quality']['ordered_100'], 'Long ordered-output check failed'
                reverse = stream('Return only this JSON array in reverse order: [17, -4, 88, 3, 51, 0, -29, 64, 9, 12, 37, -6]. No markdown.',limit=256,sampled=False)
                result['quality']['irregular_reverse'] = json.loads(reverse['content']) == [-6,37,12,9,64,-29,0,51,3,88,-4,17]
                assert result['quality']['irregular_reverse'], 'Irregular reversal check failed'
            print('QUALITY passed',case,flush=True)
            for prompt in PROMPTS.values():
                stream(prompt)  # Exclude warm-up from medians.
            for repeat in range(args.repeats):
                for name,prompt in PROMPTS.items():
                    before = vllm_spec_counters() if args.engine == 'vllm' else {}
                    trial = stream(prompt)
                    trial.update(workload=name,repeat=repeat)
                    if args.engine == 'vllm':
                        after = vllm_spec_counters()
                        trial['speculation_counter_deltas'] = {key:value-before.get(key,0) for key,value in after.items()}
                    if args.engine == 'sglang':
                        with urllib.request.urlopen(f'http://127.0.0.1:{checks.PORT}/metrics',timeout=5) as metrics:
                            lines = metrics.read().decode().splitlines()
                        trial['speculation_gauges'] = {key:[float(line.rsplit(' ',1)[1]) for line in lines if line.startswith('sglang:'+key+'{')] for key in ('spec_accept_length','spec_accept_rate')}
                    result['trials'].append(trial)
                    print('TRIAL',case,name,repeat,round(trial['decode_tps_approx'],2),round(trial['ttft_seconds'],3),flush=True)
            result['medians'] = {name:dict(decode_tps=statistics.median(t['decode_tps_approx'] for t in result['trials'] if t['workload']==name),
                                         ttft_seconds=statistics.median(t['ttft_seconds'] for t in result['trials'] if t['workload']==name)) for name in PROMPTS}
            if args.long:
                prompt,codes = base.marker_prompt(context-1500)
                if args.engine == 'sglang':
                    checks.request('/flush_cache',{})
                trial = stream(prompt,limit=128,sampled=False,timeout=600)
                result['long_retrieval'] = trial
                trial['passed'] = all(code in trial['content'] for code in codes)
                assert trial['passed'], 'Near-window retrieval failed'
            if args.benchy_depth is not None:
                benchy_python = ROOT/'llm-tools/llama-benchy-0.4.0/.venv/bin/python'
                output = OUT/(case+'-benchy.json')
                command = [str(benchy_python),str(ROOT/'hardware/benchy-seeded.py'),'--base-url',f'http://127.0.0.1:{checks.PORT}/v1',
                           '--model',checks.MODEL,'--tokenizer',checks.TARGET,'--pp','2048','--tg','128',
                           '--depth',*[str(d) for d in args.benchy_depth],'--runs','3',
                           '--concurrency','1','--no-cache','--latency-mode','generation',
                           '--extra-body','temperature=0','--extra-body','return_token_ids=false',
                           '--extra-body','chat_template_kwargs={"enable_thinking":false}',
                           '--save-result',str(output),'--format','json','--exit-on-first-fail']
                print('BENCHY begin',case,args.benchy_depth,flush=True)
                with (OUT/(case+'-benchy.log')).open('w') as benchlog:
                    subprocess.run(command,stdout=benchlog,stderr=subprocess.STDOUT,timeout=600,check=True)
                result['benchy_file'] = output.name
                result['benchy_seed'] = 42
                print('BENCHY passed',case,flush=True)
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


def vllm_spec_counters():
    with urllib.request.urlopen(f'http://127.0.0.1:{checks.PORT}/metrics',timeout=5) as response:
        lines = response.read().decode().splitlines()
    values = {}
    for line in lines:
        if line.startswith('vllm:spec_decode') and '_total{' in line:
            metric, value = line.rsplit(' ',1)
            values[metric] = float(value)
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=['sglang','vllm'],default='sglang')
    parser.add_argument('--mode',choices=['mtp','dflash','plain'],default='mtp')
    parser.add_argument('--steps',type=int,choices=[1,2,3,4],default=None)
    parser.add_argument('--vllm-kv',choices=['int4_per_token_head','int8_per_token_head','bfloat16'],default='int4_per_token_head')
    parser.add_argument('--vllm-dtype',choices=['bfloat16','float16'],default='bfloat16')
    parser.add_argument('--vllm-kv-bytes',type=int,default=1879048192)
    parser.add_argument('--chunk',type=int,default=512)
    parser.add_argument('--compile-mode',type=int,choices=[0,3],default=0)
    parser.add_argument('--rdna-prefill',action='store_true',help='Test the gated gfx1100 INT8 prefill tiles')
    parser.add_argument('--protocol',choices=['auto','Simple'],default='auto')
    parser.add_argument('--verify',type=int,choices=[0,1],default=0)
    parser.add_argument('--verify-walk-fix',action='store_true',help='Test the opt-in prefix+draft KV adapter repair')
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--long',action='store_true')
    parser.add_argument('--tag',default='',help='Separate a repeat batch from earlier measurements')
    parser.add_argument('--benchy-depth',type=int,nargs='+',default=None,help='Also run pinned llama-benchy 0.4.0 at these depths')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 3 if args.engine == 'vllm' else 2
    if (args.engine == 'sglang' and (args.mode == 'plain' or args.steps == 4)) or (args.engine == 'vllm' and args.mode == 'dflash'):
        parser.error('Unsupported engine/mode/steps combination')
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
