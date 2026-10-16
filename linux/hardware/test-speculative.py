#!/usr/bin/env python3
"""Sequential GPU-only MTP/DFlash/n-gram comparison on retained Qwen weights."""
import argparse, importlib.util, json, os, signal, socket, subprocess, sys, threading, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/generated/speculative-2026-10-16'
sys.path.insert(0, str(ROOT / 'dsh'))
import backend_switch
from llama_runtime import launch_spec
spec = importlib.util.spec_from_file_location('gpu_checks', ROOT / 'hardware/test-gpu-resident.py')
gpu = importlib.util.module_from_spec(spec); spec.loader.exec_module(gpu)
PORT = 18042
MODEL = 'qwen-spec-test'
TARGET = '/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ'
DRAFT = '/opt/local-llm/models/drafts/Qwen3.8-27B-DFlash2-W4A16'


def request(path, body=None, stream=False):
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}'+path, None if body is None else json.dumps(body).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=900) as response:
        if path == '/flush_cache': return response.read().decode()
        if not stream: return json.load(response)
        first=None; usage=None; content=''; start=time.monotonic()
        for line in response:
            line=line.decode().strip()
            if not line.startswith('data: ') or line=='data: [DONE]': continue
            d=json.loads(line[6:]); usage=d.get('usage') or usage
            for choice in d.get('choices',[]):
                text=choice.get('delta',{}).get('content') or ''
                if text and first is None: first=time.monotonic()
                content+=text
        end=time.monotonic()
        if first is None or usage is None: raise RuntimeError('Missing streamed tokens/usage')
        return {'content':content,'usage':usage,'stream_seconds':end-start,
                'decode_tps_approx':(usage['completion_tokens']-1)/(end-first)}


def chat(messages, **kw):
    return request('/v1/chat/completions',dict(model=MODEL,messages=messages,max_tokens=256,temperature=0,chat_template_kwargs={'enable_thinking':False},**kw))


def launch(case):
    env=dict(os.environ)
    if case.startswith('sglang'):
        env['SGLANG_RDNA_VLLM_VERIFY']='1'
        # Pin this comparison's baseline instead of inheriting production context changes.
        cmd=[str(ROOT/'sglang/start-qwen-rocm'),'--port',str(PORT),'--served-model-name',MODEL,
             '--context-length','16384','--max-total-tokens','16384','--mem-fraction-static','0.85']
        if case.startswith('sglang-mtp'):
            steps = 1 if case == 'sglang-mtp1-jit' else 2
            cmd += ['--speculative-algorithm','EAGLE','--speculative-draft-model-path',TARGET,
                    '--speculative-num-steps',str(steps),'--speculative-eagle-topk','1','--speculative-num-draft-tokens',str(steps+1)]
        elif not case.startswith('sglang-plain'):
            cmd += ['--speculative-algorithm','DFLASH','--speculative-draft-model-path',DRAFT,
                    '--speculative-draft-model-quantization','compressed-tensors',
                    '--speculative-num-draft-tokens','8','--speculative-draft-window-size','2048']
        if case in ('sglang-dflash8-budget', 'sglang-dflash8-compact', 'sglang-dflash8-nocache', 'sglang-dflash8-standard-verify', 'sglang-dflash8-standard-nocache'):
            cmd += ['--mem-fraction-static','0.92']
        if case in ('sglang-dflash8-compact', 'sglang-dflash8-nocache', 'sglang-dflash8-standard-nocache'):
            cmd += ['--max-mamba-cache-size','2']
        if case in ('sglang-dflash8-nocache','sglang-dflash8-standard-nocache'):
            cmd += ['--disable-radix-cache']
        if case in ('sglang-mtp2-standard-verify','sglang-dflash8-standard-verify', 'sglang-dflash8-standard-nocache'):
            env['SGLANG_RDNA_VLLM_VERIFY']='0'
        if case == 'sglang-mtp2-no-graph':
            cmd += ['--disable-cuda-graph']
        return cmd,env,16384
    binary,_,env,_=launch_spec()
    model=next(m for m in json.loads((ROOT/'dsh/models.json').read_text()) if m['id']=='qwen3.8-27b-q4')
    cmd=[str(binary),'--model',model['path'],'--alias',MODEL,'--host','127.0.0.1','--port',str(PORT),
         '--device','Vulkan0','--n-gpu-layers','99','--override-tensor','token_embd.*=Vulkan0',
         '--split-mode','none','--fit','off','--ctx-size','65536','--parallel','1',
         '--batch-size','512','--ubatch-size','128','--flash-attn','on',
         '--cache-type-k','q8_0','--cache-type-v','q8_0','--cache-ram','0','--ctx-checkpoints','0',
         '--jinja','--reasoning','off','--spec-type','draft-mtp' if case=='llama-mtp' else 'ngram-map-k4v,draft-mtp',
         '--spec-draft-n-max','3','--spec-draft-type-k','q8_0','--spec-draft-type-v','q8_0']
    if case=='llama-ngram':
        cmd += ['--spec-ngram-map-k4v-size-n','32','--spec-ngram-map-k4v-size-m','48','--spec-ngram-map-k4v-min-hits','1']
    return cmd,env,65536


def validate():
    results={'arithmetic':True}
    for expression,answer in [('17 times 19','323'),('144 divided by 12','12'),('37 plus 48','85')]:
        d=chat([{'role':'user','content':f'What is {expression}? Reply with the number only.'}])
        text=d['choices'][0]['message'].get('content') or ''
        results['arithmetic'] &= text.strip().strip('.').strip()==answer
    d=chat([{'role':'user','content':'Return only a JSON array of the integers from 1 through 12 in order. No markdown.'}])
    text=d['choices'][0]['message'].get('content') or ''
    try: results['ordered_json'] = json.loads(text)==list(range(1,13))
    except ValueError: results['ordered_json'] = False
    results['ordered_json_answer'] = text
    tools=[{'type':'function','function':{'name':'lookup_inventory','description':'Look up stock by SKU.','parameters':{'type':'object','properties':{'sku':{'type':'string'}},'required':['sku']}}}]
    messages=[{'role':'user','content':'Use lookup_inventory for SKU QWEN-42. Do not guess stock.'}]
    a=chat(messages,tools=tools)['choices'][0]['message']; calls=a.get('tool_calls',[])
    assert len(calls)==1 and calls[0]['function']['name']=='lookup_inventory',a
    assert json.loads(calls[0]['function']['arguments'])['sku']=='QWEN-42'
    b=chat(messages+[a,{'role':'tool','tool_call_id':calls[0]['id'],'content':'{"sku":"QWEN-42","stock":137}'}],tools=tools,tool_choice='none')
    assert '137' in (b['choices'][0]['message'].get('content') or ''),b
    results['tool_roundtrip']=True
    return results


def run(case, stop_on_quality_failure=False):
    cmd,env,ctx=launch(case); done=threading.Event(); ready=threading.Event(); samples=[]; alerts=[]
    result={'case':case,'context':ctx,'command':cmd,'started_unix':time.time()}
    if case.startswith('sglang'):
        result['rdna_vllm_verify']=env['SGLANG_RDNA_VLLM_VERIFY']
    OUT.mkdir(parents=True,exist_ok=True)
    print('START',case,flush=True)
    with (OUT/(case+'.log')).open('w') as log:
        proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        def monitor():
            while not done.wait(.5):
                sample=gpu.memory()
                if ready.is_set():
                    tree=backend_switch.processes(); ids={proc.pid}
                    for _ in range(8): ids.update(p.pid for p in tree.values() if p.parent in ids)
                    sample['nonresident_vram_bytes']=sum(gpu.amd_residency(pid)['nonresident_vram_bytes'] for pid in ids)
                    if sample['nonresident_vram_bytes']>256*1024**2: alerts.append('VRAM spill exceeds 256 MiB')
                samples.append(sample)
                if sample['mem_available_bytes']<2*1024**3: alerts.append('Host available memory below 2 GiB')
                if sample['amd_vram_bytes']>23*1024**3: alerts.append('AMD VRAM exceeds 23 GiB headroom limit')
                if alerts:
                    os.killpg(proc.pid,signal.SIGTERM); return
        watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
        try:
            start=time.monotonic()
            while time.monotonic()-start<900:
                if proc.poll() is not None: raise RuntimeError(f'server exited {proc.returncode}')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/health',timeout=2) as r:
                        if r.status==200: break
                except OSError: pass
                time.sleep(1)
            else: raise TimeoutError('Startup timeout')
            ready.set();result['startup_seconds']=time.monotonic()-start
            result['validation']=validate();print('QUALITY',case,result['validation'],flush=True)
            if stop_on_quality_failure and not all(result['validation'][k] for k in ('arithmetic','ordered_json','tool_roundtrip')):
                raise RuntimeError('Structured-output check failed; skipping timed workloads')
            prompts={
                'inventory':'Read the inventory and write a detailed numbered guide to checking a shipment. Include examples.\n'+'\n'.join(f'Bin {n}: blue bolts 12, steel washers 24, boxed sets 6.' for n in range(140)),
                'code_edit':'Change only return value_20 + 1 to return value_20 + 2. Output the entire updated Python file without markdown.\n'+'\n\n'.join(f'def function_{n}(value_{n}):\n    """Process item {n} and return the incremented value."""\n    return value_{n} + 1' for n in range(40)),
                'prose':'Write an original literary scene about an astronomer discovering a handwritten letter inside an abandoned observatory. Use varied sentence structures, concrete sensory details, and no lists or repeated phrases.'}
            result['trials']=[]
            for repeat in range(2):
                for name,prompt in prompts.items():
                    if case.startswith('sglang'): request('/flush_cache',{})
                    body=dict(model=MODEL,messages=[{'role':'user','content':prompt}],temperature=0,max_tokens=512,ignore_eos=True,
                              stream=True,stream_options={'include_usage':True},chat_template_kwargs={'enable_thinking':False},cache_prompt=False)
                    t=time.monotonic();d=request('/v1/chat/completions',body,stream=True);d.update(workload=name,repeat=repeat,total_seconds=time.monotonic()-t)
                    result['trials'].append(d);print(case,name,repeat,round(d['decode_tps_approx'],2),flush=True)
            # Moderate-depth marker check shared by all four configurations.
            lines=[f'Record {n:05d}: blue bolts 12, washers 24, boxed sets 6.' for n in range(500)]
            for index,code in [(5,'ALPHA-734'),(250,'BRAVO-915'),(495,'CHARLIE-268')]:lines[index]+=' Secret marker: '+code
            d=chat([{'role':'user','content':'Return all three secret markers from these records.\n'+'\n'.join(lines)}])
            answer=d['choices'][0]['message'].get('content') or ''
            result['retrieval']={'usage':d['usage'],'passed':all(code in answer for code in ('ALPHA-734','BRAVO-915','CHARLIE-268')),'answer':answer}
            assert result['retrieval']['passed'],answer
            result['status']='passed' if all(result['validation'][k] for k in ('arithmetic','ordered_json','tool_roundtrip')) else 'quality_requires_review'
        except Exception as error:
            result.update(status='failed',error=str(error));print('FAILED',case,str(error),flush=True)
        finally:
            done.set();watcher.join(timeout=3);gpu.terminate(proc)
            # Stop only the process group created by this test, including ROCm workers.
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
    result['alerts']=alerts
    result['memory']={key:max((s.get(key,0) for s in samples),default=0) for key in ('amd_vram_bytes','amd_gtt_bytes','nonresident_vram_bytes')}
    result['finished_unix']=time.time()
    (OUT/(case+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',case,result['status'],result['memory'],flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',required=True,choices=['sglang-plain','sglang-plain-jit','sglang-mtp2-jit','sglang-mtp1-jit','sglang-mtp2-standard-verify','sglang-mtp2-no-graph','sglang-mtp2','sglang-mtp2-check','sglang-dflash8','sglang-dflash8-budget','sglang-dflash8-compact','sglang-dflash8-nocache','sglang-dflash8-standard-verify','sglang-dflash8-standard-nocache','llama-mtp','llama-ngram'])
    parser.add_argument('--stop-on-quality-failure',action='store_true')
    args=parser.parse_args()
    if any(backend_switch.is_inference(p) for p in backend_switch.processes().values()): parser.error('Stop existing configured inference first')
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1',PORT))
    def stop(*_): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGHUP,stop)
    for case in args.cases: run(case,args.stop_on_quality_failure)
