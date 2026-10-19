#!/usr/bin/env python3
"""Benchmark already-running managed dual-AMD profiles without changing settings.

Run one backend group at a time with its normal launcher. Raw output is under
hardware/generated/; published records contain hashes/counts, never model text.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys
import threading
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from amd_device import amd_devices
from backend_switch import processes, is_inference
from moe_memory import host_memory, worker_memory
from strata_memory import vram_snapshot

PROMPTS = {
    'code': 'Write a Python function that merges two sorted lists. Explain its time and space complexity.',
    'prose': 'Write a short story about a lighthouse keeper finding a letter.'}
PORTS = {'llama': (8080, 8081), 'sglang': (30000, 30001),
         'vllm': (30010, 30011), 'strata': (30020, 30021)}


def request(port, path, body=None, timeout=900):
    req = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
          None if body is None else json.dumps(body).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.load(res)


def metrics(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/metrics', timeout=5) as res:
            lines = res.read().decode().splitlines()
        return {line.rsplit(' ',1)[0]: float(line.rsplit(' ',1)[1]) for line in lines
                if line and not line.startswith('#') and len(line.rsplit(' ',1)) == 2}
    except (OSError, ValueError):
        return {}


def stream(kind, model, prompt, limit=256, sampled=True):
    port, native = PORTS[kind]
    body = {'model':model, 'messages':[{'role':'user','content':prompt}],
            'temperature':.6 if sampled else 0, 'max_tokens':limit,
            'stream':True, 'stream_options':{'include_usage':True},
            'chat_template_kwargs':{'enable_thinking':False}}
    if sampled:
        body.update(top_p=.95, seed=42)
    if kind == 'llama':
        body['cache_prompt'] = False
    if kind == 'strata':
        body['strata_checkpoint'] = False
    before = metrics(native)
    req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
           json.dumps(body).encode(), {'Content-Type':'application/json'})
    first = last_content = usage = timing = None
    text = reasoning = ''
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=1200) as res:
        for line in res:
            line = line.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]':
                continue
            item = json.loads(line[6:])
            if item.get('error'):
                raise RuntimeError('Inference SSE error')
            usage = item.get('usage') or usage
            timing = item.get('timings') or timing
            for choice in item.get('choices', []):
                delta = choice.get('delta', {})
                content = delta.get('content') or ''
                thought = delta.get('reasoning_content') or delta.get('reasoning') or ''
                if content or thought:
                    last_content = time.monotonic()
                    if first is None:
                        first = last_content
                text += content
                reasoning += thought
    end = time.monotonic()
    assert first is not None and usage and usage['completion_tokens'] > 0, 'No output/usage'
    # Historical SSE method includes stream completion overhead after first output.
    record = {'usage':usage, 'ttft_seconds':first-started, 'total_seconds':end-started,
              'decode_tps_sse':(usage['completion_tokens']-1)/(end-first),
              'content_sha256':hashlib.sha256(text.encode()).hexdigest(),
              'reasoning_tokens_present':bool(reasoning), 'native_timings':timing}
    after = metrics(native)
    delta = {k: v-before.get(k,0) for k,v in after.items() if k in before and v-before[k] > 0}
    # Each request is sequential. Keep only numerical phase metrics, no label values.
    if kind == 'vllm':
        phase = [(k,v) for k,v in delta.items() if k.startswith('vllm:request_prefill_time_seconds_sum')]
        count = sum(v for k,v in delta.items() if k.startswith('vllm:request_prefill_time_seconds_count'))
        seconds = sum(v for k,v in phase)
        if seconds > 0 and count == 1:
            record['prefill_phase_seconds'] = seconds
            record['prefill_phase_observations'] = count
            record['prefill_phase_source'] = 'vllm:request_prefill_time_seconds_sum (scheduled to first engine token)'
    elif kind == 'sglang':
        # Per-rank copies can exist; stage time per rank is not additive across TP ranks.
        phase = [v for k,v in delta.items() if k.startswith('sglang:per_stage_req_latency_seconds_sum') and 'stage="prefill_forward"' in k]
        counts = [v for k,v in delta.items() if k.startswith('sglang:per_stage_req_latency_seconds_count') and 'stage="prefill_forward"' in k]
        if phase and counts and all(v == 1 for v in counts):
            record['prefill_phase_seconds'] = max(phase)
            record['prefill_phase_observations_per_rank'] = counts
            record['prefill_phase_source'] = 'sglang:per_stage_req_latency_seconds_sum stage=prefill_forward, maximum rank'
    if timing and timing.get('prompt_ms',0)>0:
        record['prefill_native_tps'] = timing.get('prompt_per_second')
        record['prefill_native_tokens'] = timing.get('prompt_n')
    # Always label this separately; includes API/tokenization/queueing/first decode.
    record['effective_input_per_ttft'] = usage['prompt_tokens']/record['ttft_seconds']
    cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens',0) or 0
    record['cached_tokens'] = cached
    if record.get('prefill_phase_seconds') and cached == 0:
        record['prefill_phase_tps'] = usage['prompt_tokens']/record['prefill_phase_seconds']
    return record, text


def profiles(kind):
    if kind == 'llama':
        return [(m['id'],m['context']) for m in json.loads((ROOT/'dsh/models.json').read_text())]
    return [(k,v['context']) for k,v in json.loads((ROOT/f'dsh/{kind}-profiles.json').read_text()).items()]


def prefill_prompt(index):
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(ROOT/'models/Qwen3.8-27B-W4A16-AutoRound-GPTQ/tokenizer.json'))
    salt = uuid.uuid4().hex
    def make(n):
        lines = [f'Record {i:05d}: bay {i%97}, blue bolts {i%31+1}, washers {i%43+2}, sets {i%19+1}.' for i in range(n)]
        for i, code in zip([5,n//2,n-5],['ALPHA-734','BRAVO-915','CHARLIE-268']):
            lines[i] += ' Secret marker: '+code
        return f'{salt}\nRead these records. Return the three secret markers in order, and nothing else.\n'+'\n'.join(lines)
    low,high=20,8192
    while low+1<high:
        mid=(low+high)//2
        if len(tokenizer.encode(make(mid)).ids)<=8192:low=mid
        else:high=mid
    return make(low)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',choices=PORTS,required=True)
    ap.add_argument('--date',default=date.today().isoformat(),help='Local ISO date for the result record')
    ap.add_argument('--model',action='append',help='Limit to a configured model ID')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--runs',type=int,default=3)
    ap.add_argument('--allow-marker-failure',action='store_true',help='Muse only: retain all timed probes and report retrieval failures explicitly')
    args=ap.parse_args()
    if args.allow_marker_failure:assert args.model==['muse-glimmer-30b'], 'Diagnostic allowance is limited to Muse'
    amd_devices()
    configs=profiles(args.kind)
    if args.model:
        configs=[(m,c) for m,c in configs if m in args.model]
        assert len(configs)==len(args.model)
    out={'date':args.date,'backend':args.kind,
         'method':{'short_prompts':PROMPTS,'short_output_cap':256,'runs':args.runs,
                   'sampling':{'temperature':.6,'top_p':.95,'seed':42,'thinking':False},
                   'prefill':'three fresh ~8192-token marker prompts, 64-output cap (Muse 1024), greedy; salt before content defeats prefix reuse',
                   'ttft':'monotonic request submission to first content or reasoning SSE delta',
                   'decode':'(completion_tokens-1)/(stream_end-first_output); native timing also retained',
                   'warmup':'excluded short warm-up for each workload; models loaded before timing',
                   'context':'production configured windows; no maximum-window claim from these probes'},
         'profiles':[]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save(): args.output.write_text(json.dumps(out,indent=2)+'\n')
    for model,context in configs:
        result={'model':model,'context':context,'status':'running','short':{},'prefill':[]}
        out['profiles'].append(result);save()
        print('LOAD',args.kind,model,flush=True)
        readings=[];done=threading.Event()
        def monitor():
            while not done.is_set():
                try:
                    tree=processes()
                    pids={p.pid for p in tree.values() if is_inference(p)}
                    for _ in range(8):pids.update(p.pid for p in tree.values() if p.parent in pids)
                    memory=[worker_memory(pid) for pid in pids]
                    readings.append({'available':host_memory()[1],'vram':vram_snapshot(),
                                     'swap':sum(x[0] for x in memory),'spill':sum(x[1] for x in memory)})
                except (OSError,RuntimeError):pass
                done.wait(1)
        try:
            # Loading/correctness occurs before the timed monitor; loading is not TTFT.
            _,text=stream(args.kind,model,'What is 17 times 19? Reply with only the integer.',limit=128,sampled=False)
            assert re.search(r'\b323\b',text), 'Arithmetic smoke failed'
            result['arithmetic']=True
            watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
            for task,prompt in PROMPTS.items():
                stream(args.kind,model,prompt) # excluded per-task warmup
                trials=[]
                for index in range(args.runs):
                    trial,_=stream(args.kind,model,prompt)
                    assert trial['usage']['completion_tokens']>=64,'Output too short for timing'
                    trials.append(trial)
                    result['short'][task]={'trials':trials}
                    save()
                    print('SHORT',model,task,index,round(trial['ttft_seconds'],3),round(trial['decode_tps_sse'],2),flush=True)
                result['short'][task]['median_decode_tps']=statistics.median(t['decode_tps_sse'] for t in trials)
                result['short'][task]['median_ttft_seconds']=statistics.median(t['ttft_seconds'] for t in trials)
            for index in range(args.runs):
                trial,text=stream(args.kind,model,prefill_prompt(index),limit=1024 if model=='muse-glimmer-30b' else 64,sampled=False)
                trial['markers_passed']=all(code in text for code in ['ALPHA-734','BRAVO-915','CHARLIE-268'])
                if not args.allow_marker_failure:assert trial['markers_passed'],'Marker retrieval failed'
                assert trial['cached_tokens']==0,'Fresh prefill reused cache'
                if trial.get('native_timings'):assert trial['native_timings'].get('cache_n',0)==0
                result['prefill'].append(trial);save()
                print('PREFILL',model,index,trial['usage']['prompt_tokens'],round(trial['ttft_seconds'],3),trial.get('prefill_native_tps'),round(trial.get('prefill_phase_tps',0),2),flush=True)
            assert readings,'No memory telemetry'
            result['memory']={'minimum_available_gib':round(min(r['available'] for r in readings)/1024**3,3),
                             'peak_vram_gib':[round(max(r['vram'][i]['used'] for r in readings)/1024**3,3) for i in range(2)],
                             'max_worker_swap_bytes':max(r['swap'] for r in readings),
                             'max_nonresident_vram_bytes':max(r['spill'] for r in readings)}
            assert min(result['memory']['peak_vram_gib'])>2,'Both GPU allocations not observed'
            assert result['memory']['max_nonresident_vram_bytes']==0,'Dedicated VRAM spill'
            result['marker_checks_passed']=sum(t['markers_passed'] for t in result['prefill'])
            result['status']='passed' if result['marker_checks_passed']==args.runs else 'measured_with_marker_failure'
        except Exception as error:
            result['status']='failed'
            result['error_type']=type(error).__name__
            print('FAILED',model,type(error).__name__,str(error)[:180],flush=True)
        finally:
            done.set()
            if 'watcher' in locals():watcher.join(timeout=3)
            save()
        print('PROFILE',model,result['status'],flush=True)
    if any(p['status'] not in ('passed','measured_with_marker_failure') for p in out['profiles']):raise SystemExit(1)


if __name__=='__main__':main()
