#!/usr/bin/env python3
"""Publish reviewed numeric validation records; exclude paths and generated text."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from amd_device import amd_devices
TRIAL_KEYS = ('usage','ttft_seconds','total_seconds','decode_tps_sse','content_sha256',
              'reasoning_tokens_present','native_timings','prefill_native_tps','prefill_native_tokens',
              'prefill_phase_seconds','prefill_phase_tps','cached_tokens','effective_input_per_ttft',
              'markers_passed','prefix_reuse_passed','task','trial')


def trial(row):
    out = {key:row[key] for key in TRIAL_KEYS if key in row}
    if 'follow_up' in row:out['follow_up'] = trial(row['follow_up'])
    return out


def nemotron(data):
    keys = ('model','runtime_commit','compiled_revision','binary_sha256','context','split','mtp',
            'phase','status','threads','threads_batch','cpu_mask','cpu_mask_batch','ctx_checkpoints',
            'cpu_expert_layers','host_expert_bytes','cache_mib','ubatch_size','load_seconds','allocated_context',
            'cpu','os_visible_ram_bytes','measurement_time_utc','measurement_time_source',
            'source_raw_sha256','effective_args_provenance','binary_sha256_verified_utc',
            'memory','medians','long_input_target')
    out = {key:data[key] for key in keys if key in data}
    out['functional'] = {key:data['functional'][key] for key in ('arithmetic','json','tool_roundtrip','streaming')
                         if key in data.get('functional',{})}
    out['trials'] = [trial(row) for row in data.get('trials',[])]
    if 'long_context' in data:out['long_context'] = trial(data['long_context'])
    if 'standard_short' in data.get('functional',{}):
        out['standard_short'] = {task:dict(median_ttft_seconds=row['median_ttft_seconds'],
             median_decode_tps=row['median_decode_tps'],trials=[trial(t) for t in row['trials']])
             for task,row in data['functional']['standard_short'].items()}
    out['expert_cache_observed'] = bool(data.get('expert_cache_log'))
    if data.get('guard_failure'):out['guard_stopped_owned_worker'] = True
    return out


def benchmark(data):
    out = {key:data[key] for key in ('date','backend','method') if key in data}
    out['profiles'] = []
    for row in data['profiles']:
        item = {key:row[key] for key in ('model','context','status','arithmetic','memory','marker_checks_passed') if key in row}
        item['prefill'] = [trial(t) for t in row['prefill']]
        item['short'] = {task:dict(median_ttft_seconds=v['median_ttft_seconds'],
             median_decode_tps=v['median_decode_tps'],trials=[trial(t) for t in v['trials']]) for task,v in row['short'].items()}
        out['profiles'].append(item)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('nemotron','strata-benchmark','strata-functional','strata-long','strata-server','output'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--control',type=Path,action='append',default=[])
    a = ap.parse_args()
    read = lambda p:json.loads(p.read_text())
    q,s,f,long,server = map(read,(a.nemotron,a.strata_benchmark,a.strata_functional,a.strata_long,a.strata_server))
    assert q['status']=='passed' and q['long_context']['markers_passed']
    assert q['memory']['max_worker_swap_bytes']==q['memory']['max_worker_spill_bytes']==0
    totals = [int((device/'mem_info_vram_total').read_text()) for device in amd_devices()]
    assert len(totals)==2 and len(q['memory']['max_gpu_used_bytes'])==2
    assert min(total-used for total,used in zip(totals,q['memory']['max_gpu_used_bytes'])) >= 3*1024**3
    assert q['memory']['min_available_bytes'] >= 3*1024**3
    assert len(q['trials'])>=6 and all(t['usage']['completion_tokens']>=128 for t in q['trials'])
    assert s['profiles'][0]['status']=='passed' and len(s['profiles'][0]['prefill'])==3
    assert f['status']=='passed' and f['stream_passed']
    assert long['status']=='passed' and all(long['markers_found']) and all(long['follow_up']['markers_found'])
    assert server['status']=='stopped_after_testing'
    memory=server['memory']
    assert memory['maximum_worker_swap_bytes']==memory['maximum_vram_spill_bytes']==0
    assert min(memory['minimum_free_vram_bytes'])>=3*1024**3 and memory['minimum_available_bytes']>=3*1024**3
    cfg=server['config'];args=cfg['args']
    assert cfg['gpu']==[0,1] and not cfg['split_skip_if_fits']
    config={flag:args[args.index(flag)+1] for flag in ('--max-context','--kv','--kv-resident',
        '--resident-budget-gib','--prefill','--pool-workers','--spec','--vram-reserve-mib','--vram-reserve-later-mib')}
    if '--pool-affinity' in args:config['--pool-affinity']=args[args.index('--pool-affinity')+1]
    functional=dict(runtime=f['runtime'],context=f['context'],status=f['status'],stream_passed=f['stream_passed'],
        memory=f['memory'],tests=[{key:t[key] for key in ('name','usage','timings','wall_seconds') if key in t}
        | {'message_sha256':hashlib.sha256(json.dumps(t['message'],sort_keys=True).encode()).hexdigest()} for t in f['tests']])
    out={'schema':1,'published_utc':datetime.now(timezone.utc).isoformat(),'local_timezone':'America/Toronto',
        'hardware':{'cpu':'Intel Core i9-13900KS','cores':24,'logical_cpus':32,'installed_ram_gb':64,
            'os_visible_ram_bytes':server.get('os_visible_ram_bytes') or q.get('os_visible_ram_bytes'),'gpu_usable_vram_bytes':totals,'gpus':['RX 7900 XTX 24 GB','RX 7900 XTX 24 GB'],
            'uplinks':'CPU PCIe4 x8/x8; switch not installed','transport':'llama.cpp/Strata layer splitting, direct P2P not enabled'},
        'nemotron':nemotron(q),'strata':{'source_commit':server['source_commit'],'binary_sha256':server['binary_sha256'],
            'measurement_started_utc':server['measurement_started_utc'],
            'os_visible_ram_bytes':server.get('os_visible_ram_bytes'), 'kernel':server.get('kernel'),
            'config':config,'layer_split':cfg['layer_split'],'env':{key:cfg['env'][key] for key in ('STRATA_PREFILL_MMQ','STRATA_NO_ARENA_THP','STRATA_IO_STATS','STRATA_SPLIT_OVERLAP') if key in cfg['env']},'memory':memory,
            'load_seconds':server['load_seconds'],'benchmark':benchmark(s),'functional':functional,'long_context':long},
        'method':{'sampling':'temperature 0.6, top_p 0.95, seed 42, thinking off; 256 output cap',
            'nemotron_fixed_input':'three ~8K-input trials per code/prose task; native prefill and external SSE TTFT/decode',
            'nemotron_short':('three trials/task on canonical short code/prose prompts; actual counts retained; excluded task warmup'
                              if q.get('functional',{}).get('standard_short') else
                              'Not measured for this selected profile; fixed ~8K-input TTFT is not short TTFT.'),
            'controls':'split-phase controls have one timed trial/task after full-input warmup; final long phase uses short task warmups after long retrieval',
            'long_context':'greedy three-marker retrieval; actual counts and full-history follow-up separate from allocated context'},
        'controls':[],'interpretation':'Complete-profile comparisons. Old i5/32GB and NVIDIA measurements retain their original hardware. Fixed ~8K Nemotron TTFT differs from short-prompt TTFT. Allocated context is distinct from actual input tested.'}
    # The probe holds hashes, counts and timing, not model text; keep its numeric schema only.
    out['strata']['long_context']={key:long[key] for key in ('context','target_raw_tokens','raw_tokens','kv','kv_resident','kind',
        'production_checkpoints','status','usage','timings','finish_reason','content_sha256','markers_found','follow_up','wall_seconds','memory') if key in long}
    for path in a.control:
        data=read(path)
        out['controls'].append({'tag':path.stem,'data':benchmark(data) if 'profiles' in data else nemotron(data)})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print('Curated numeric result:',a.output)


if __name__ == '__main__':main()
