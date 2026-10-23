#!/usr/bin/env python3
"""Check one normally launched 64 GB backend through the authenticated gateway.

Never starts/stops workers or executes a model-requested tool. All tool results
are synthetic. Output contains flags, counts and hashes, never keys or answers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from amd_device import amd_devices
from backend_switch import processes
from moe_memory import worker_memory,host_memory


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',choices=['llama','strata','maya'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--model',choices=['nemotron-3.5-super-iq3',
                                     'qwen3.8-flash-next-iq3_xxs','glm-5.3-flash-maya',
                                     'deepseek-v4.1-flash-1017-maya','deepseek-v4.1-flash-1017-maya-s'])
    ap.add_argument('--result',type=Path,help='Require exact measured Q4 placement, CPU/cache parameters and binary')
    a=ap.parse_args()
    ident=a.model or ('nemotron-3.5-super-iq3' if a.kind=='llama' else 'qwen3.8-flash-next-iq3_xxs')
    assert (a.kind=='llama' and ident.startswith('nemotron-3.5-super-')) or (a.kind=='strata' and ident=='qwen3.8-flash-next-iq3_xxs') or (a.kind=='maya' and ident in ('glm-5.3-flash-maya','deepseek-v4.1-flash-1017-maya','deepseek-v4.1-flash-1017-maya-s'))
    cfg=json.loads((ROOT/'dsh/data/network-access.json').read_text());key=Path(cfg['key_file']).read_text().strip()
    expected=next(m['context'] for m in json.loads((ROOT/'dsh/models.json').read_text()) if m['id']==ident) if a.kind=='llama' else json.loads((ROOT/f'dsh/{a.kind}-profiles.json').read_text())[ident]['context']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(path,body=None,address='127.0.0.1',port=None,stream=False):
        headers={'Content-Type':'application/json'}
        if port is None:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(f'http://{address}:{port or cfg["port"]}'+path,
            None if body is None else json.dumps(body).encode(),headers)
        with opener.open(req,timeout=1200) as response:
            if not stream:return json.load(response)
            text='';done=False
            for line in response:
                line=line.decode().strip()
                if line=='data: [DONE]':done=True
                elif line.startswith('data: '):
                    data=json.loads(line[6:]);assert not data.get('error')
                    text+=''.join(c.get('delta',{}).get('content') or '' for c in data.get('choices',[]))
            assert done
            return text
    rows={m['id']:m for m in api('/v1/models')['data']}
    assert rows[ident]['context_length']==expected and rows[ident]['backend_available']
    def chat(messages,**extra):
        return api('/v1/chat/completions',dict(model=ident,messages=messages,max_tokens=128,temperature=0,
            chat_template_kwargs={'enable_thinking':False},**extra))
    start=time.monotonic();addresses={}
    for address,label in zip(cfg['listen'],('loopback','lan','tailscale')):
        text=api('/v1/chat/completions',dict(model=ident,messages=[{'role':'user','content':'What is 17 times 19? Reply with only the integer.'}],
            max_tokens=32,temperature=0,stream=True,chat_template_kwargs={'enable_thinking':False}),address=address,stream=True)
        assert text.strip()=='323'
        addresses[label]={'authenticated_streaming':True,'answer_sha256':hashlib.sha256(text.encode()).hexdigest()}
    structured=chat([{'role':'user','content':'Return only a JSON object with key answer and integer value 137. No markdown.'}])
    assert json.loads(structured['choices'][0]['message']['content'])['answer']==137
    tools=[{'type':'function','function':{'name':'lookup_inventory','description':'Look up stock for a SKU',
        'parameters':{'type':'object','properties':{'sku':{'type':'string'}},'required':['sku']}}}]
    history=[{'role':'user','content':'Call lookup_inventory for SKU BOLT-42, then report the returned stock.'}]
    message=chat(history,tools=tools,tool_choice={'type':'function','function':{'name':'lookup_inventory'}})['choices'][0]['message']
    call=message['tool_calls'][0];assert call['function']['name']=='lookup_inventory'
    assert json.loads(call['function']['arguments'])=={'sku':'BOLT-42'}
    reply=chat(history+[message,{'role':'tool','tool_call_id':call['id'],'content':'{"sku":"BOLT-42","stock":137}'}],tools=tools,tool_choice='none')['choices'][0]['message']['content']
    assert '137' in reply
    tree=processes()
    binaries={'llama':{str(ROOT/'llama.cpp/build-hip/bin/llama-server')},'strata':{str(ROOT/'strata/build-hip/strata')},
              'maya':{str(ROOT/'maya/upstream/build-hip/maya'),str(ROOT/'maya/upstream/build-hip/maya-ds4')}}[a.kind]
    workers={p.pid for p in tree.values() if p.args and p.args[0] in binaries};assert workers
    runtime_proof = {}
    if a.kind == 'llama':
        sys.path.insert(0,str(ROOT/'hardware'))
        from nemotron_super import server_args
        profile=json.loads((ROOT/'dsh/candidates/nemotron-super.json').read_text())[ident]
        split='1,1' if ident.endswith('-q4') else '21,19'
        expected_args=server_args(profile,expected,split)
        selected=[tree[pid] for pid in workers if '--alias' in tree[pid].args and tree[pid].args[tree[pid].args.index('--alias')+1]==ident]
        assert len(selected)==1
        command=selected[0].args
        settings={}
        for flag in ('--ctx-size','--device','--split-mode','--tensor-split','--override-tensor',
                     '--threads','--threads-batch','--ubatch-size','--moe-cache-mib',
                     '--ctx-checkpoints','--load-mode','--spec-type','--cache-type-k','--cache-type-v'):
            actual='--swa-checkpoints' if flag=='--ctx-checkpoints' and flag not in command else flag
            assert actual in command and command[command.index(actual)+1]==expected_args[expected_args.index(flag)+1],flag
            settings[flag]=command[command.index(actual)+1]
        pin=json.loads((ROOT/'dsh/llama-runtime.json').read_text())['source_commit']
        assert subprocess.check_output(['git','-C',str(ROOT/'llama.cpp'),'rev-parse','HEAD'],text=True).strip()==pin
        version=subprocess.run([command[0],'--version'],capture_output=True,text=True,check=True,timeout=30)
        assert pin[:8] in version.stdout+version.stderr
        runtime_proof={'runtime_commit':pin,'compiled_revision':pin[:8],
            'production_binary_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
            'profile_arguments_match':True,'settings':settings,
            'binary_provenance':'Current production rebuild; this functional proof does not assert binary identity with a prior candidate benchmark.'}
    elif a.kind=='strata':
        cfg=json.loads((ROOT/'dsh/strata-iq3-profile.json').read_text())
        assert cfg['gpu']==[0,1] and not cfg['split_skip_if_fits']
        assert len(workers)==1
        command=tree[next(iter(workers))].args
        expected_args=cfg['args']
        for flag in ('--pack','--native','--ple-gguf','--mtp','--max-context',
                     '--resident-budget-gib','--pool-workers','--kv','--kv-resident',
                     '--prefill','--spec','--vram-reserve-mib','--vram-reserve-later-mib'):
            assert flag in command and command[command.index(flag)+1]==expected_args[expected_args.index(flag)+1],flag
        runtime_proof={'runtime_commit':subprocess.check_output(['git','-C',str(ROOT/'strata'),'rev-parse','HEAD'],text=True).strip(),
            'production_binary_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
            'profile_arguments_match':True,'both_gpus_configured':True,
            'layer_split':cfg['layer_split'],'expert_budget_gib':float(expected_args[expected_args.index('--resident-budget-gib')+1]),
            'asset_paths_match_active_configuration':True}
    else:
        from maya_runtime import profiles, config_fingerprint
        cfg=json.loads((ROOT/'dsh'/profiles()[ident]['config']).read_text())
        assert cfg['gpu']==[0,1] and not cfg['split_skip_if_fits'] and len(workers)==1
        command=tree[next(iter(workers))].args
        for flag in cfg['args'][::2]:
            assert flag in command and command[command.index(flag)+1]==cfg['args'][cfg['args'].index(flag)+1],flag
        binary_sha=hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()
        assert cfg['local_validation']['binary_sha256']==binary_sha
        assert cfg['local_validation']['config_sha256']==config_fingerprint(cfg)
        runtime_proof={'runtime_commit':subprocess.check_output(['git','-C',str(ROOT/'maya/upstream'),'rev-parse','HEAD'],text=True).strip(),
            'production_binary_sha256':binary_sha,'profile_arguments_match':True,
            'both_gpus_configured':True,'config_sha256':config_fingerprint(cfg)}
    measured_match = False
    if a.result:
        assert a.kind=='llama'
        measured=json.loads(a.result.read_text());assert measured['status']=='passed' and measured['model']==ident
        selected=[tree[pid] for pid in workers if '--alias' in tree[pid].args and tree[pid].args[tree[pid].args.index('--alias')+1]==ident]
        assert len(selected)==1
        command=selected[0].args
        flags=('--ctx-size','--device','--split-mode','--tensor-split','--override-tensor','--threads',
            '--threads-batch','--cpu-mask','--cpu-mask-batch','--ubatch-size','--moe-cache-mib',
            '--ctx-checkpoints','--load-mode','--spec-type','--cache-type-k','--cache-type-v',
            '--n-cpu-moe','--n-gpu-layers','--batch-size')
        for flag in flags:
            expected_args=measured['effective_args']
            if flag in ('--cpu-mask','--cpu-mask-batch') and flag not in expected_args:
                assert flag not in command,flag
                continue
            actual_flag = '--swa-checkpoints' if flag=='--ctx-checkpoints' and flag not in command else flag
            assert actual_flag in command and flag in expected_args,flag
            assert command[command.index(actual_flag)+1]==expected_args[expected_args.index(flag)+1],flag
        assert hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()==measured['binary_sha256']
        measured_match=True
    roots=set(workers)
    for pid in workers:
        parent=tree[pid].parent
        while parent in tree:
            if parent in workers:roots.discard(pid);break
            parent=tree[parent].parent
        group=next(line.split(':',2)[2] for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if line.startswith('0::'))
        assert (Path('/sys/fs/cgroup')/group.lstrip('/')/'memory.swap.max').read_text().strip()=='0'
    telemetry=[worker_memory(pid) for pid in roots]
    assert all(swap==spill==0 for swap,spill in telemetry)
    gpu=[int((d/'mem_info_vram_used').read_text()) for d in amd_devices()]
    assert len(gpu)==2 and min(gpu)>2*1024**3
    if a.kind=='llama':
        loaded=[m['id'] for m in api('/v1/models',port=8080)['data'] if m.get('status',{}).get('value')=='loaded']
        assert loaded==[ident],loaded
        props=api('/props?model='+ident,port=8080);assert props['default_generation_settings']['n_ctx']==expected
    else:
        health=api('/health',port=30030 if a.kind=='maya' else 30020);assert health['active_model']==ident and not health.get('memory_fault')
        if a.kind=='maya':
            free=health['startup_whole_card_free_bytes'];assert len(free)==2 and min(free)>=6*1024**3
            runtime_proof['startup_whole_card_free_bytes']=free
    result={'status':'passed','model':ident,'context':expected,'routes':addresses,'remote_peer_tested':False,
        'runtime_proof':runtime_proof,
        'json':True,'tool_roundtrip':True,'measured_arguments_and_binary_match':measured_match,
        'measured_q4_arguments_and_binary_match':measured_match and ident=='nemotron-3.5-super-q4',
        'owned_scope_swap_max_bytes':0,'worker_swap_bytes':0,
        'worker_vram_spill_bytes':0,'gpu_used_bytes':gpu,'available_host_bytes':host_memory()[1],
        'initial_model_check_and_functional_wall_seconds':round(time.monotonic()-start,3),
        'method':'Existing normal launcher; authenticated host self-access on loopback/LAN/Tailscale; functional check, not a throughput benchmark'}
    a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
