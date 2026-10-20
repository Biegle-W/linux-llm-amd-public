#!/usr/bin/env python3
"""Publish numeric Maya evidence, with source hashes and no local paths or answers."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'hardware/generated/maya-setup-2026-10-20'


def load(name):return json.loads((RAW/name).read_text())
def source(name):
    p=RAW/name
    return {'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def server(tag):
    r=load(tag+'.server.json')
    row={k:r[k] for k in ('source_commit','cpu','os_visible_ram_bytes','kernel','gpu_usable_vram_bytes','binary_sha256','measurement_started_utc','status','memory','load_seconds','startup_whole_card_free_bytes','startup_free_required_gib') if k in r}
    from datetime import datetime,timezone
    row['server_record_saved_utc']=datetime.fromtimestamp((RAW/(tag+'.server.json')).stat().st_mtime,timezone.utc).isoformat()
    cfg=r['config'];args=cfg['args']
    flags=('--max-context','--expert-cache','--prefill','--kv-streaming','--vram-reserve-mib','--vram-reserve-later-mib','--reserve-mib','--cpu-threads','--tp','--dspark')
    row['measured_settings']={'gpu':cfg['gpu'],'parallel':cfg.get('parallel',1),'layer_split':cfg.get('layer_split'),
        'engine':Path(cfg['exe']).name,'flags':{flag:args[args.index(flag)+1] for flag in flags if flag in args},
        'env':{k:v for k,v in cfg.get('env',{}).items() if k!='MAYA_HIPBLASLT_TUNING'},
        'expert_profile_seed_sha256':cfg.get('expert_profile_seed_sha256',cfg.get('upstream_expert_profile_seed_sha256'))}
    return row
def summarize(bench):
    p=bench['profiles'][0]
    assert p['status']=='passed'
    return {'model':p['model'],'context':p['context'],
        'actual_prefill_input_range':[min(t['usage']['prompt_tokens'] for t in p['prefill']),max(t['usage']['prompt_tokens'] for t in p['prefill'])],
        'median_native_prefill_tps':statistics.median(t['prefill_native_tps'] for t in p['prefill']),
        'median_prefill_ttft_seconds':statistics.median(t['ttft_seconds'] for t in p['prefill']),
        'short_decode_tps':{k:v['median_decode_tps'] for k,v in p['short'].items()},
        'short_ttft_seconds':{k:v['median_ttft_seconds'] for k,v in p['short'].items()}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--deepseek-tag',required=True)
    ap.add_argument('--glm-tag',default='glm-32k-desktop')
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    result={'schema':1,'date':'2026-10-20','runtime':json.loads((ROOT/'maya/runtime.json').read_text()),
        'hardware':'i9-13900KS / 64 GB / two RX 7900 XTX 24 GB; motherboard PCIe4 x8/x8; switch not installed',
        'kernel_parity':load('kernel-parity-summary.json'),
        'method_limits':['Configured windows are not a full-window quality guarantee.',
            'Native prefill is separate from external SSE TTFT and decode.',
            'Shared prefill corpus is sized with the Qwen tokenizer; actual Maya tokenizer counts are retained.',
            'No external model outputs or private paths are published; synthetic tool results only.',
            'Three trials per workload do not establish statistical significance. Stateful expert/page caches affect results.'],
        'models':[],'selection_cases':[],
        'normal_switchback':load('normal-switchback.json'),
        'dsh_registration':load('frontend-registration.json'),
        'gateway_auth_catalog':load('network-final.json'),
        'deepseek_selection':load('deepseek-selection.json'),
        'glm_ram_selection':load('glm-final-selection.json'),
        'glm_disk_seed_verification':{k:v for k,v in load('glm-profile-provenance.json').items() if k in ('status','files')},
        'screening_validation':[], 'glm_candidates':[]}
    for tag,fun in [(a.glm_tag,a.glm_tag+'.functional.json'),(a.deepseek_tag,a.deepseek_tag+'.functional.json')]:
        bench=load(tag+'.benchmark.json');functional=load(fun);normal=load(tag+'.normal.json')
        assert functional['status']==normal['status']=='passed'
        row={'summary':summarize(bench),'lifecycle':server(tag),'functional':functional,'benchmark':bench,'normal_integration':normal,
             'sources':[source(tag+'.server.json'),source(fun),source(tag+'.benchmark.json'),source(tag+'.normal.json')]}
        assert row['lifecycle']['status']=='stopped_after_testing'
        assert row['lifecycle']['memory']['maximum_worker_swap_bytes']==row['lifecycle']['memory']['maximum_vram_spill_bytes']==0
        result['models'].append(row)
    for p in sorted(RAW.glob('*.short.json')):
        r=json.loads(p.read_text());result['selection_cases'].append({'record':r,'source':source(p.name)})
    for tag in ('deepseek-8k','deepseek-8k-dspark-8','deepseek-8k-none-8'):
        name=tag+'.functional.json';result['screening_validation'].append({'tag':tag,'functional':load(name),'lifecycle':server(tag),'source':source(name)})
    for tag,fun in [('glm-32k','glm-32k.functional-a2.json'),('glm-32k-desktop','glm-32k-desktop.functional.json'),('glm-32k-ram40','glm-32k-ram40.functional.json')]:
        if (RAW/(tag+'.benchmark.json')).exists():
            result['glm_candidates'].append({'tag':tag,'benchmark':load(tag+'.benchmark.json'),'functional':load(fun),'lifecycle':server(tag),'source':source(tag+'.benchmark.json')})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    for m in result['models']:print(json.dumps(m['summary']))

if __name__=='__main__':main()
