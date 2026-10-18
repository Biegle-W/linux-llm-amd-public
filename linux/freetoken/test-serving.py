#!/usr/bin/env python3
"""Bounded single-card serving test, authorized only for the FreeToken experiment."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from backend_switch import startup_handover
from moe_memory import host_memory, worker_memory
from amd_device import amd_devices


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def api(path, data=None, timeout=10):
    request = urllib.request.Request('http://127.0.0.1:1919'+path,
        None if data is None else json.dumps(data).encode(), {'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'HTTP {error.code}: '+error.read().decode()[:1500]) from error


def main():
    output=ROOT/'freetoken/generated';output.mkdir(exist_ok=True)
    models=json.loads((ROOT/'dsh/models.json').read_text())
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',default='qwen3.8-27b-q4')
    args=parser.parse_args()
    model=next(m for m in models if m['id']==args.model)
    moe=bool(model.get('expert_count',0))
    alias=model['id']+'-freetoken'
    command=[str(ROOT/'freetoken/.venv-rocm/bin/ft'),'serve','--model',model['path'],
        '--gpu','1','--tensor-parallel-size','1','--disable-pynccl','--attn','triton',
        '--host','127.0.0.1','--port','1919','--served-model-name',alias,
        '--text-model-only','--max-running-requests','1','--max-seq-len-override','8192',
        '--num-tokens','8192','--max-prefill-length','128','--memory-ratio','0.75',
        '--cache-type','naive','--cuda-graph-max-bs','0']
    if moe:
        command += ['--moe-strategy','offload','--moe-cache-mem','6GiB','--expert-load','serial',
            '--disable-moe-prefill-overlap']
    record={'model':alias,'gpu':1,'context':8192,'prefill_chunk':128,'expert_cache_gib':6 if moe else 0,'checks':{},'passed':False}
    with startup_handover('llama'):
        pass
    required_ram_gib=22 if moe else 10
    if host_memory()[1]<required_ram_gib*1024**3:
        raise RuntimeError(f'Need {required_ram_gib} GiB available RAM before loading; no model started')
    samples=[];alerts=[];done=threading.Event();ready_swap=[None]
    with (output/'serving.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        def monitor():
            low=0
            while not done.wait(1):
                available=host_memory()[1];swap,spill=worker_memory(process.pid)
                vram=[int((d/'mem_info_vram_used').read_text()) for d in amd_devices()]
                samples.append((available,swap,spill,vram))
                low=low+1 if available<3*1024**3 else 0
                swap_limit=1024**3 if ready_swap[0] is None else max(1024**3,ready_swap[0]+256*1024**2)
                if low>=3 or swap>swap_limit or spill>256*1024**2 or max(vram)>23*1024**3:
                    alerts.append({'available_gib':available/1024**3,'swap_mib':swap/1024**2,'spill_mib':spill/1024**2})
                    stop(process);return
        threading.Thread(target=monitor,daemon=True).start()
        try:
            started=time.monotonic()
            for _ in range(900):
                if process.poll() is not None:raise RuntimeError('FreeToken exited '+str(process.returncode))
                try:
                    health=api('/health',timeout=1)
                    if health.get('status')=='ok' or health.get('ready') is True:break
                except Exception:pass
                time.sleep(1)
            else:raise TimeoutError('FreeToken model startup exceeded 15 minutes')
            record['ready_seconds']=round(time.monotonic()-started,3)
            ready_swap[0]=worker_memory(process.pid)[0]
            record['startup_worker_swap_mib']=round(ready_swap[0]/1024**2,3)
            print('FreeToken model ready; checking actual generation.',flush=True)
            def chat(messages,**extra):
                return api('/v1/chat/completions',{'model':alias,'messages':messages,
                    'max_tokens':96,'temperature':0,'chat_template_kwargs':{'enable_thinking':False},**extra},timeout=180)
            result=chat([{'role':'user','content':'Calculate 37 + 48. Reply with only the integer.'}])
            assert result['choices'][0]['message']['content'].strip()=='85',result
            record['checks']['arithmetic']=True
            result=chat([{'role':'user','content':'Return only valid JSON: an object with key numbers and the integers 1 through 8 in order as its array.'}])
            text=result['choices'][0]['message']['content'].strip()
            if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
            assert json.loads(text)['numbers']==list(range(1,9)),text
            record['checks']['json']=True
            tool={'type':'function','function':{'name':'get_inventory','description':'Look up product stock.','parameters':{'type':'object','properties':{'sku':{'type':'string'}},'required':['sku']}}}
            messages=[{'role':'user','content':'Use get_inventory to check stock for SKU ABC-123.'}]
            result=chat(messages,tools=[tool],tool_choice='required')
            message=result['choices'][0]['message'];call=message['tool_calls'][0]
            assert call['function']['name']=='get_inventory'
            assert json.loads(call['function']['arguments'])['sku']=='ABC-123'
            messages += [message,{'role':'tool','tool_call_id':call['id'],'content':'{"sku":"ABC-123","quantity":17}'}]
            result=chat(messages,tools=[tool]);assert '17' in result['choices'][0]['message']['content']
            record['checks']['tools_roundtrip']=True
            start=time.monotonic()
            result=chat([{'role':'user','content':'Write a short Python function that returns the sum of squares of the integers in a list, with a short explanation.'}],max_tokens=128)
            record['code_probe']={'usage':result.get('usage'),'elapsed_seconds':round(time.monotonic()-start,3),'timings':result.get('timings')}
            record['passed']=True
        except Exception as error:
            record['error']=str(error)
        finally:
            done.set();stop(process)
    if samples:
        record['telemetry']={'min_available_ram_gib':round(min(s[0] for s in samples)/1024**3,3),
            'max_worker_swap_mib':round(max(s[1] for s in samples)/1024**2,3),
            'max_vram_spill_mib':round(max(s[2] for s in samples)/1024**2,3),
            'peak_vram_gib':[round(max(s[3][i] for s in samples)/1024**3,3) for i in range(2)]}
    record['alerts']=alerts
    record['passed']=record['passed'] and not alerts
    (output/'serving-result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
    return 0 if record['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
