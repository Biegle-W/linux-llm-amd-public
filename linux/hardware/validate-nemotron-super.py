#!/usr/bin/env python3
"""Isolated dual-HIP validation; never stop an existing inference workload."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import threading
import time

from nemotron_super import ROOT, GIB, server_args
sys.path.insert(0, str(ROOT/'dsh'))
from amd_device import amd_devices
from backend_switch import processes, is_inference, python_entrypoint
from moe_memory import host_memory, memory_reason, worker_memory

spec = importlib.util.spec_from_file_location('current_benchmark', ROOT/'hardware/benchmark-current-amd.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
PORT = 18183
bench.PORTS['llama'] = (PORT, PORT)
OUT = ROOT/'hardware/generated/nemotron-super'


def idle():
    for process in processes().values():
        if is_inference(process):
            raise RuntimeError(f'Inference PID {process.pid} is already running; no process was stopped')
        entry = python_entrypoint(process.args)
        if entry and entry[0] == 'script' and any(name in Path(entry[1]).name for name in ('benchmark-current-amd', 'bench-dual', 'bench-strata')):
            raise RuntimeError('Another benchmark is running; no process was stopped')
    for device in amd_devices():
        if int((device/'gpu_busy_percent').read_text()) > 10:
            raise RuntimeError('A GPU is busy; no process was stopped')


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def prompt_at_tokens(target, ending):
    def make(count):
        rows = [f'Record {n:05d}: value={n%97}; status=normal; location=archive.' for n in range(count)]
        return 'Review the reference records below.\n' + '\n'.join(rows) + '\n' + ending
    low, high = 0, target
    while low < high:
        mid = (low+high+1)//2
        size = len(bench.request(PORT, '/tokenize', {'content':make(mid),'add_special':False})['tokens'])
        if size <= target:
            low = mid
        else:
            high = mid-1
    return make(low)


def functional(profile, context):
    model = profile['id']
    def chat(messages, **kwargs):
        return bench.request(PORT, '/v1/chat/completions', {
            'model':model,'messages':messages,'temperature':0,'max_tokens':256,
            'cache_prompt':False,'chat_template_kwargs':{'enable_thinking':False},**kwargs})
    message = lambda text:[{'role':'user','content':text}]
    arithmetic = chat(message('What is 17 times 19? Answer only the integer.'))
    assert '323' in (arithmetic['choices'][0]['message'].get('content') or ''), arithmetic
    structured = chat(message('Return a JSON object with key answer and integer value 137.'),
                      response_format={'type':'json_object'})
    assert json.loads(structured['choices'][0]['message']['content'])['answer'] == 137
    tools = [{'type':'function','function':{'name':'lookup','description':'Look up a numeric value',
              'parameters':{'type':'object','properties':{'key':{'type':'string'}},'required':['key']}}}]
    history = message('Call lookup with key test-value, then report the returned number.')
    call = chat(history, tools=tools, tool_choice={'type':'function','function':{'name':'lookup'}})['choices'][0]['message']
    tool = call['tool_calls'][0]
    assert tool['function']['name'] == 'lookup'
    assert json.loads(tool['function']['arguments'])['key'] == 'test-value'
    reply = chat([*history,call,{'role':'tool','tool_call_id':tool['id'],'content':'{"value":137}'}],
                 tools=tools, tool_choice='none')['choices'][0]['message']
    assert '137' in (reply.get('content') or ''), reply
    record, text = bench.stream('llama',model,'Reply with the integer 137 only.',limit=32,sampled=False)
    assert '137' in text
    return {'arithmetic':True,'json':True,'tool_roundtrip':True,'streaming':True,'stream_usage':record['usage']}


def run(options):
    idle()
    profile = json.loads((ROOT/'dsh/candidates/nemotron-super.json').read_text())[options.model]
    reason = memory_reason(profile,*host_memory())
    if reason:
        raise RuntimeError(reason)
    for device in amd_devices():
        if int((device/'mem_info_vram_total').read_text())-int((device/'mem_info_vram_used').read_text()) < 21*GIB:
            raise RuntimeError('Need at least 21 GiB free VRAM per card before isolated testing')
    OUT.mkdir(parents=True,exist_ok=True)
    tag = options.tag
    result = {'model':profile['id'],'runtime_commit':subprocess.check_output(['git','-C',str(ROOT/'llama.cpp'),'rev-parse','HEAD'],text=True).strip(),
              'context':options.context,'split':options.split,'mtp':options.mtp,'phase':options.phase,
              'host_expert_bytes':profile['host_expert_bytes'],'cache_mib':profile['gpu_expert_cache_mib'],
              'trials':[],'status':'running','memory':{'min_available_bytes':host_memory()[1],
                'max_gpu_used_bytes':[0,0],'max_worker_swap_bytes':0,'max_worker_spill_bytes':0}}
    path = OUT/(tag+'.json')
    def save():
        path.write_text(json.dumps(result,indent=2)+'\n')
    save()
    env = dict(os.environ)
    env.pop('GGML_CUDA_ENABLE_UNIFIED_MEMORY',None)
    args = ['systemd-run','--user','--scope','--quiet','--property=MemorySwapMax=0',
            f'--property=MemoryMax={math.ceil(profile["host_expert_bytes"]/GIB+4)}G',
            *server_args(profile,options.context,options.split,options.mtp,PORT)]
    done = threading.Event()
    failure = []
    with (OUT/(tag+'.log')).open('w') as log:
        process = subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        def monitor():
            low = spill_count = 0
            while not done.wait(1) and process.poll() is None:
                available = host_memory()[1]
                used = [int((device/'mem_info_vram_used').read_text()) for device in amd_devices()]
                free = [int((device/'mem_info_vram_total').read_text())-value for device,value in zip(amd_devices(),used)]
                swap,spill = worker_memory(process.pid)
                memory = result['memory']
                memory['min_available_bytes'] = min(memory['min_available_bytes'],available)
                memory['max_gpu_used_bytes'] = [max(a,b) for a,b in zip(memory['max_gpu_used_bytes'],used)]
                memory['max_worker_swap_bytes'] = max(memory['max_worker_swap_bytes'],swap)
                memory['max_worker_spill_bytes'] = max(memory['max_worker_spill_bytes'],spill)
                low = low+1 if available < 3*GIB or min(free) < 3*GIB else 0
                spill_count = spill_count+1 if spill > 256*1024**2 else 0
                if low >= 3 or swap > 0 or spill_count >= 3:
                    failure.append('Owned-worker guard: insufficient RAM/VRAM headroom, swapping, or VRAM spill')
                    stop(process)
                    return
        thread = threading.Thread(target=monitor,daemon=True)
        thread.start()
        try:
            started = time.monotonic()
            while time.monotonic()-started < 900:
                if process.poll() is not None:
                    raise RuntimeError('Worker exited during startup; inspect the saved log')
                try:
                    if bench.request(PORT,'/health',timeout=2).get('status') == 'ok':
                        break
                except Exception:
                    pass
                time.sleep(2)
            else:
                raise RuntimeError('Startup exceeded 15 minutes')
            result['load_seconds'] = time.monotonic()-started
            properties = bench.request(PORT,'/props')
            result['allocated_context'] = properties['default_generation_settings']['n_ctx']
            assert result['allocated_context'] == options.context
            print(tag,'READY',round(result['load_seconds'],2),flush=True)
            result['functional'] = functional(profile,options.context)
            print(tag,'FUNCTIONAL PASS',flush=True)
            if options.phase == 'long':
                prompt = prompt_at_tokens(28500,'Ignore the reference records. Return the three secret markers in their original order.')
                lines = prompt.splitlines()
                for index,marker in reversed([(1,'ALPHA-719'),(len(lines)//2,'BETA-263'),(len(lines)-2,'GAMMA-451')]):
                    lines.insert(index,'Secret marker: '+marker)
                record,text = bench.stream('llama',profile['id'],'\n'.join(lines),limit=256,sampled=False)
                record['markers_passed'] = all(marker in text for marker in ('ALPHA-719','BETA-263','GAMMA-451'))
                result['long_context'] = record
                save()
                assert record['markers_passed'], 'Long-input marker retrieval failed'
                print(tag,'LONG PASS',record['usage'],flush=True)
            if options.phase in ('split','bench','long'):
                tasks = {'code':'Write a Python function that merges two sorted lists. Explain it in detail and provide several examples.',
                         'prose':'Write a detailed story about a lighthouse keeper finding a letter. Continue for at least 500 words.'}
                prompts = {task:prompt_at_tokens(8100,ending) for task,ending in tasks.items()}
                for task,prompt in prompts.items():
                    # The long probe already warms expert banks; exclude a short task warmup.
                    bench.stream('llama',profile['id'],tasks[task] if options.phase == 'long' else prompt,limit=32,sampled=True)
                    for index in range(3 if options.phase in ('bench','long') else 1):
                        record,text = bench.stream('llama',profile['id'],prompt,limit=256,sampled=True)
                        record.update(task=task,trial=index+1)
                        assert record['cached_tokens'] == 0
                        result['trials'].append(record)
                        save()
                        print(tag,task,index+1,'PP',record.get('prefill_native_tps'),'TTFT',round(record['ttft_seconds'],3),'DECODE',round(record['decode_tps_sse'],3),flush=True)
                result['medians'] = {task:{key:statistics.median(record[key] for record in result['trials'] if record['task']==task)
                    for key in ('prefill_native_tps','ttft_seconds','decode_tps_sse')} for task in tasks}
            done.set()
            stop(process)
            thread.join(timeout=5)
            log.flush()
            text = (OUT/(tag+'.log')).read_text(errors='replace')
            cache_lines = [line for line in text.splitlines() if 'moe_cache' in line or 'moe cache' in line.lower()]
            result['expert_cache_log'] = cache_lines
            if not cache_lines:
                raise RuntimeError('No evidence of native expert cache initialization')
            if failure:
                raise RuntimeError(failure[0])
            result['status'] = 'passed'
        except Exception as error:
            result['status'] = 'failed'
            result['error'] = str(error)
            raise
        finally:
            done.set()
            stop(process)
            thread.join(timeout=5)
            if failure:
                result['guard_failure'] = failure[0]
            save()
            print(tag,result['status'],result.get('error',''),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',default='nemotron-3.5-super-iq3')
    parser.add_argument('--context',type=int,default=16384)
    parser.add_argument('--split',default='1,1',choices=['1,1','21,19','19,21'])
    parser.add_argument('--mtp',action='store_true')
    parser.add_argument('--phase',choices=['smoke','split','bench','long'],default='smoke')
    parser.add_argument('--tag',required=True)
    run(parser.parse_args())
