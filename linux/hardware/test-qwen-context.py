#!/usr/bin/env python3
"""Bounded dual-AMD context candidates; never edits production profiles."""
import argparse
import copy
import datetime
import importlib.util
import json
import os
from pathlib import Path
import signal
import statistics
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from amd_device import amd_devices
from moe_memory import host_memory, worker_memory
from strata_memory import vram_snapshot


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind', choices=['sglang', 'vllm'], required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--context', type=int, required=True)
    p.add_argument('--kv', choices=['bfloat16', 'int8_per_token_head'], default='bfloat16')
    p.add_argument('--kv-gib', type=float)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--long', action='store_true')
    a = p.parse_args()
    router = load('context_router', ROOT/f'dsh/{a.kind}-router.py')
    cfg = copy.deepcopy(router.PROFILES[a.model])
    cfg['context'] = a.context
    cfg.setdefault('extra_args', []).extend(['--kv-cache-dtype', a.kv])
    if a.kv_gib is not None:
        cfg['kv_cache_bytes'] = int(a.kv_gib*1024**3)
    router.PROFILES = {a.model: cfg}
    bench = load('context_bench', ROOT/'hardware/benchmark-current-amd.py')
    native = 30001 if a.kind == 'sglang' else 30011
    bench.PORTS[a.kind] = (native, native)
    checks = load('context_checks', ROOT/'hardware/test-speculative.py')
    checks.PORT, checks.MODEL = native, a.model
    base = load('context_base', ROOT/'hardware/test-sglang-dual-context.py')
    base.checks = checks
    r = {'date': datetime.datetime.now().astimezone().isoformat(),
         'kind': a.kind, 'model': a.model, 'context': a.context, 'profile': cfg,
         'kv': a.kv, 'status': 'running', 'short': {}, 'prefill': [],
         'memory': {'minimum_available_gib': 1000, 'minimum_free_vram_gib': [24,24],
                    'max_worker_swap_bytes': 0, 'max_nonresident_vram_bytes': 0},
         'method': 'Existing shared-method prompts; one excluded warmup then three 256-cap trials per short task, three salted fresh ~8K probes. Long greedy marker/history probes are separate; caches not globally flushed.'}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    def save(): a.output.write_text(json.dumps(r, indent=2)+'\n')
    done = threading.Event()
    fault = []
    def monitor():
        low = 0
        while not done.wait(1):
            proc = router.worker
            if proc is None or proc.poll() is not None:
                continue
            available = host_memory()[1]
            free = [x['free']/1024**3 for x in vram_snapshot()]
            swap, spill = worker_memory(proc.pid)
            mem = r['memory']
            mem['minimum_available_gib'] = min(mem['minimum_available_gib'], available/1024**3)
            mem['minimum_free_vram_gib'] = [min(x,y) for x,y in zip(mem['minimum_free_vram_gib'],free)]
            mem['max_worker_swap_bytes'] = max(mem['max_worker_swap_bytes'],swap)
            mem['max_nonresident_vram_bytes'] = max(mem['max_nonresident_vram_bytes'],spill)
            low = low+1 if min(free)<3 or available<3*1024**3 else 0
            if swap or spill or low>=4:
                fault.append('Owned swap/spill or sustained whole-card/RAM headroom below 3 GiB')
                os.killpg(proc.pid,signal.SIGTERM)
                return
    def stop(*_): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGHUP,stop)
    watcher = threading.Thread(target=monitor,daemon=True)
    try:
        save();watcher.start()
        t=time.monotonic();router.ensure_worker(a.model)
        r['startup_seconds']=time.monotonic()-t
        proc=router.worker
        r['worker_args']=Path(f'/proc/{proc.pid}/cmdline').read_bytes().decode().strip('\0').split('\0')
        if a.kind=='sglang':
            r['cache_capacities']=list(router.cache_capacities(router.get_worker('/server_info')))
            assert min(r['cache_capacities'])>=a.context
        else:
            r['model_info']=router.get_worker('/v1/models')
        print('READY',a.model,a.context,flush=True);save()
        r['quality']=checks.validate()
        assert all(r['quality'][key] for key in ('arithmetic','ordered_json','tool_roundtrip'))
        for name,prompt in bench.PROMPTS.items():
            bench.stream(a.kind,a.model,prompt)
            trials=[]
            for i in range(3):
                trial,_=bench.stream(a.kind,a.model,prompt)
                assert trial['usage']['completion_tokens']>=64
                trials.append(trial)
                print('SHORT',name,i,round(trial['decode_tps_sse'],2),flush=True)
            r['short'][name]={'trials':trials,
                'median_decode_tps':statistics.median(x['decode_tps_sse'] for x in trials),
                'median_ttft_seconds':statistics.median(x['ttft_seconds'] for x in trials)}
            save()
        for i in range(3):
            trial,text=bench.stream(a.kind,a.model,bench.prefill_prompt(i),limit=64,sampled=False)
            trial['markers_passed']=all(x in text for x in ['ALPHA-734','BRAVO-915','CHARLIE-268'])
            assert trial['markers_passed'] and trial['cached_tokens']==0
            r['prefill'].append(trial);save()
            print('PREFILL',i,trial['usage']['prompt_tokens'],round(trial.get('prefill_phase_tps',0),1),flush=True)
        if a.long:
            prompt,codes=base.marker_prompt(a.context-3000)
            # Leading random salt guarantees this is a fresh long prefill.
            prompt=os.urandom(16).hex()+'\n'+prompt
            print('LONG begin',a.context,flush=True)
            trial,text=bench.stream(a.kind,a.model,prompt,limit=256,sampled=False,timeout=1800)
            trial['markers_passed']=all(x in text for x in codes)
            assert trial['markers_passed'] and trial['cached_tokens']==0,text[:250]
            r['long_retrieval']=trial;save()
            messages=[{'role':'user','content':prompt},{'role':'assistant','content':text},
                      {'role':'user','content':'Repeat the same three secret markers exactly, in record order.'}]
            follow,text=bench.stream(a.kind,a.model,'',limit=256,sampled=False,timeout=1800,messages=messages)
            follow['markers_passed']=all(x in text for x in codes)
            assert follow['markers_passed']
            r['cached_history_followup']=follow;save()
            print('LONG passed',trial['usage'],flush=True)
        assert not fault,fault
        assert len(amd_devices())==2 and all(x['used']>2*1024**3 for x in vram_snapshot())
        r['status']='passed'
    except (Exception,KeyboardInterrupt) as e:
        r.update(status='failed',error=type(e).__name__+': '+str(e),guard_faults=fault)
        print('FAILED',r['error'],flush=True)
    finally:
        # systemd can signal both the unit parent and child during cleanup.
        # Preserve the result even when another stop arrives while waiting.
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        signal.signal(signal.SIGHUP,signal.SIG_IGN)
        done.set();watcher.join(timeout=5)
        try:router.stop_worker()
        finally:save()
    return 0 if r['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
