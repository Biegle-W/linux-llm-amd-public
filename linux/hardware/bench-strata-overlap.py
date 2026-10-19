#!/usr/bin/env python3
"""Measure an already-running dual-AMD Strata profile; no handover or GPU kernels."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from amd_device import amd_devices
from backend_switch import processes
from moe_memory import host_memory, worker_memory
from strata_memory import vram_snapshot

PROMPTS = {
    'code': 'Write a Python function that merges two sorted lists. Explain its time and space complexity.',
    'prose': 'Write a short story about a lighthouse keeper finding a letter.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--port', type=int, default=30020)
    args = parser.parse_args()
    cfg = json.loads((ROOT/'dsh/strata-iq3-profile.json').read_text())
    model = cfg['model_name']
    for _ in range(180):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/health',timeout=2) as response:
                health=json.load(response)
            if health.get('memory_fault'):
                raise RuntimeError(health['memory_fault'])
            if health.get('active_model')==model:
                break
        except (OSError,TimeoutError):
            pass
        time.sleep(1)
    else:
        raise RuntimeError('Managed Strata did not become ready')
    engines = [p for p in processes().values() if p.args and p.args[0] == cfg['exe']]
    assert len(engines) == 1, 'Expected one managed Strata engine'
    engine = engines[0]
    amd_devices()
    env = dict(item.split('=',1) for item in Path(f'/proc/{engine.pid}/environ').read_text().split('\0') if '=' in item)
    assert env.get('STRATA_SPLIT_OVERLAP', '0') == cfg['env']['STRATA_SPLIT_OVERLAP']
    assert '--layer-split' in engine.args and '26' == engine.args[engine.args.index('--layer-split')+1]
    assert '--trim-stage-weights' in engine.args
    reserve = int(engine.args[engine.args.index('--vram-reserve-mib')+1])
    assert reserve >= 6144
    out = ROOT/'hardware/generated/strata-optimization-2026-10-19'/f'{args.tag}.json'
    result = {'tag': args.tag, 'context':32768, 'overlap':env.get('STRATA_SPLIT_OVERLAP'),
              'prefill_chunk':int(engine.args[engine.args.index('--prefill')+1]),
              'reserve_mib':reserve, 'split':26, 'trim_stage_weights':True,
              'resident_budget_gib':int(engine.args[engine.args.index('--resident-budget-gib')+1]),
              'runs':[], 'functional':{}, 'method':'native timing, greedy, 512 output cap, thinking off; one excluded warmup per task'}
    def save():
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2)+'\n')
    def api(messages, **extra):
        body={'model':model,'messages':messages,'temperature':0,'max_tokens':512,
              'strata_checkpoint':False,'chat_template_kwargs':{'enable_thinking':False},**extra}
        request=urllib.request.Request(f'http://127.0.0.1:{args.port}/v1/chat/completions',
                                      json.dumps(body).encode(),{'Content-Type':'application/json'})
        start=time.monotonic()
        with urllib.request.urlopen(request,timeout=600) as response:data=json.load(response)
        return data,round(time.monotonic()-start,4)
    def ask(prompt, **extra):return api([{'role':'user','content':prompt}],**extra)
    readings=[];done=threading.Event()
    def monitor():
        while not done.is_set():
            swap,spill=worker_memory(engine.pid)
            readings.append({'available':host_memory()[1],'swap':swap,'spill':spill,'vram':vram_snapshot()})
            done.wait(.5)
    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
    try:
        data,_=ask('What is 37 multiplied by 19? Reply with only the integer.',max_tokens=32)
        assert data['choices'][0]['message']['content'].strip()=='703'
        data,_=ask('Return only a JSON array of the integers from 1 through 12 in order. No markdown.',max_tokens=128)
        assert json.loads(data['choices'][0]['message']['content'])==list(range(1,13))
        result['functional'].update(arithmetic=True,ordered_json=True)
        for name,prompt in PROMPTS.items():
            ask(prompt)
            for i in range(args.runs):
                data,wall=ask(prompt)
                content=data['choices'][0]['message'].get('content') or ''
                trial={'task':name,'trial':i,'usage':data['usage'],'timings':data['timings'],
                       'wall_seconds':wall,'content_sha256':hashlib.sha256(content.encode()).hexdigest()}
                assert trial['usage']['completion_tokens']>=128
                result['runs'].append(trial);save()
                print(args.tag,name,i,trial['timings']['predicted_per_second'],flush=True)
        prompt='Read this inventory.\n'+('The ledger entry lists a routine inventory check.\n'*800)+'\nReply with only READY.'
        data,wall=ask(prompt,max_tokens=32)
        assert 'READY' in data['choices'][0]['message']['content']
        result['prefill_probe']={'usage':data['usage'],'timings':data['timings'],'wall_seconds':wall}
        result['medians']={name:statistics.median(t['timings']['predicted_per_second'] for t in result['runs'] if t['task']==name) for name in PROMPTS}
        result['status']='passed'
    except Exception as error:
        result['status']='failed'
        result['error_type']=type(error).__name__
        raise
    finally:
        done.set();watcher.join(timeout=4)
        if readings:
            result['memory']={'min_available_gib':round(min(r['available'] for r in readings)/1024**3,3),
                              'max_worker_swap_bytes':max(r['swap'] for r in readings),
                              'max_nonresident_vram_bytes':max(r['spill'] for r in readings),
                              'min_free_vram_gib':[round(min(r['vram'][i]['free'] for r in readings)/1024**3,3) for i in range(2)]}
        save()
    assert result['memory']['max_worker_swap_bytes']==0
    assert result['memory']['max_nonresident_vram_bytes']==0
    assert min(result['memory']['min_free_vram_gib'])>=3
    print(json.dumps({'tag':args.tag,'medians':result['medians'],'memory':result['memory']}),flush=True)


if __name__=='__main__':main()
