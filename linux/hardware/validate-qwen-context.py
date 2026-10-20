#!/usr/bin/env python3
"""Check a normally launched Qwen router; never starts or stops a backend."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from backend_switch import processes
from moe_memory import worker_memory
from strata_memory import vram_snapshot


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',choices=['sglang','vllm'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    model='qwen3.8-27b-sglang-dflash2' if a.kind=='sglang' else 'qwen3.8-27b-vllm'
    cfg=json.loads((ROOT/f'dsh/{a.kind}-profiles.json').read_text())[model]
    public,native=(30000,30001) if a.kind=='sglang' else (30010,30011)
    checks=load('normal_checks',ROOT/'hardware/test-speculative.py')
    checks.PORT,checks.MODEL=public,model
    result={'kind':a.kind,'model':model,'context':cfg['context'],'status':'running'}
    checks.chat([{'role':'user','content':'What is 17 times 19? Reply only with the integer.'}])
    quality=checks.validate()
    assert all(quality[x] for x in ('arithmetic','ordered_json','tool_roundtrip'))
    result['quality']={x:quality[x] for x in ('arithmetic','ordered_json','tool_roundtrip')}
    bench=load('normal_bench',ROOT/'hardware/benchmark-current-amd.py')
    streamed,text=bench.stream(a.kind,model,'What is 17 times 19? Reply only with the integer.',limit=64,sampled=False)
    assert '323' in text and streamed['usage']['completion_tokens']>0
    result['streaming']=True
    tree=processes()
    parents=[p for p in tree.values() if model in p.args and '--served-model-name' in p.args]
    assert len(parents)==1,'Expected exactly one owned worker API process'
    proc=parents[0];args=proc.args
    env={x.split(b'=',1)[0].decode():x.split(b'=',1)[1].decode()
         for x in Path(f'/proc/{proc.pid}/environ').read_bytes().split(b'\0') if b'=' in x}
    wanted={'SGLANG_RDNA_VLLM_VERIFY':'1','SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX':'1'} if a.kind=='sglang' else {'VLLM_LOCAL_RDNA_PREFILL':'1'}
    assert all(env.get(k)==v for k,v in wanted.items())
    result['selected_environment_flags']={k:env[k] for k in wanted}
    def last(flag):return args[max(i for i,x in enumerate(args) if x==flag)+1]
    assert int(last('--context-length' if a.kind=='sglang' else '--max-model-len'))==cfg['context']
    assert int(last('--tp-size' if a.kind=='sglang' else '--tensor-parallel-size'))==2
    assert last('--kv-cache-dtype')==cfg.get('kv_cache_dtype','bfloat16')
    if a.kind=='sglang':
        assert last('--speculative-algorithm')=='DFLASH'
        assert int(last('--max-total-tokens'))==cfg['context']
        router=load('normal_sglang',ROOT/'dsh/sglang-router.py')
        info=router.get_worker('/server_info')
        result['cache_capacities']=list(router.cache_capacities(info))
        assert min(result['cache_capacities'])>=cfg['context']
    else:
        assert int(last('--kv-cache-memory-bytes'))==cfg['kv_cache_bytes']
        assert json.loads(last('--speculative-config'))=={'method':'mtp','num_speculative_tokens':3}
    result['worker_args']=args
    swap,spill=worker_memory(proc.pid)
    result['owned_memory']={'swap':swap,'spill':spill}
    result['vram']=vram_snapshot()
    assert swap==spill==0 and len(result['vram'])==2 and all(x['used']>2*1024**3 for x in result['vram'])
    network=json.loads((ROOT/'dsh/data/network-access.json').read_text())
    key=Path(network['key_file']).read_text().strip()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def gateway(path,body=None,auth=True):
        headers={'Content-Type':'application/json'}
        if auth:headers['Authorization']='Bearer '+key
        req=urllib.request.Request('http://127.0.0.1:10000'+path,None if body is None else json.dumps(body).encode(),headers)
        with opener.open(req,timeout=1200) as response:return json.load(response)
    rows=gateway('/v1/models')['data']
    ids={x['id'] for x in rows}
    assert len(ids)==10 and model in ids
    assert not ids & {'muse-glimmer-30b','nemotron-3.5-super-q4','qwen3.8-27b-sglang'}
    assert next(x for x in rows if x['id']==model)['context_length']==cfg['context']
    for auth in (False,):
        try:gateway('/v1/models',auth=auth)
        except urllib.error.HTTPError as e:assert e.code==401
        else:raise AssertionError('Missing authentication accepted')
    answer=gateway('/v1/chat/completions',{'model':model,'messages':[{'role':'user','content':'What is 17 times 19? Reply only with the integer.'}], 'max_tokens':64,'temperature':0,'chat_template_kwargs':{'enable_thinking':False}})
    assert '323' in answer['choices'][0]['message']['content']
    result['gateway']={'authenticated_generation':True,'missing_key_401':True,'catalog_count':len(ids),'retired_ids_absent':True}
    result['status']='passed'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(a.kind,'normal router/source flags/functional/TP2/zero swap-spill/gateway catalog: PASS')


if __name__=='__main__':main()
