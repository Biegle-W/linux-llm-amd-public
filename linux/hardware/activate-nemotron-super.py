#!/usr/bin/env python3
"""Register only a successfully validated Nemotron candidate; no worker launch."""
import argparse
import datetime
import json
from pathlib import Path
import sys

from nemotron_super import ROOT, GIB, overrides
sys.path.insert(0,str(ROOT/'dsh'))
from moe_memory import host_memory


def check_result(result, profile, total_ram):
    if result['model'] != profile['id'] or result.get('status') != 'passed':
        raise ValueError('A passed result for this exact candidate is required')
    if total_ram < profile['minimum_host_ram_gib']*GIB:
        raise ValueError('Physical RAM requirement is not met; candidate remains inactive')
    if (result.get('host_expert_bytes') != profile['host_expert_bytes'] or
            result.get('cache_mib') != profile['gpu_expert_cache_mib']):
        raise ValueError('Candidate CPU/cache allocation differs from the measured configuration')
    if not all(result.get('functional',{}).get(key) for key in ('arithmetic','json','tool_roundtrip','streaming')):
        raise ValueError('Functional checks are incomplete')
    if result['context'] >= 32768 and not result.get('long_context',{}).get('markers_passed'):
        raise ValueError('32K needs the near-28K actual-input retrieval test')
    for task in ('code','prose'):
        if len([row for row in result.get('trials',[]) if row.get('task') == task]) < 3:
            raise ValueError('Three fixed-input trials per workload are required')
    if not result.get('expert_cache_log'):
        raise ValueError('Expert-cache evidence is missing')
    if result.get('mtp') and not result.get('mtp_comparison_passed'):
        raise ValueError('MTP needs a passing baseline comparison before activation')
    if result.get('guard_failure') or result['memory']['max_worker_swap_bytes'] or result['memory']['max_worker_spill_bytes']:
        raise ValueError('A residency or guard failure blocks activation')


def activate(result_path):
    result = json.loads(Path(result_path).read_text())
    profile = json.loads((ROOT/'dsh/candidates/nemotron-super.json').read_text())[result['model']]
    check_result(result,profile,host_memory()[0])
    ident = profile['id']
    profile.update(context=result['context'],tensor_split=result['split'],mtp=result['mtp'],enabled=True,
                   validation='Passed arithmetic, JSON, tool round trip, streaming, residency and fixed ~8K timing trials'
                   + ('; near-28K input marker retrieval passed' if result['context'] >= 32768 else '; 16K fallback'))
    profile['name'] = profile['name'].replace('32K',str(result['context']//1024)+'K')
    if profile['mtp']:
        profile['name'] += ', MTP3'
    catalog_path = ROOT/'dsh/models.json'
    catalog = json.loads(catalog_path.read_text())
    catalog = [row for row in catalog if row['id'] != ident]
    catalog.append({key:value for key,value in profile.items() if key not in ('backend','expert_layer_bytes','all_weight_bytes','minimum_host_ram_gib')})
    catalog[-1].update(runtime='hip-amd',device='ROCm0,ROCm1',split_mode='layer',
                       cpu_moe_layers=len(profile['cpu_expert_layers']),batch_size=512,ubatch_size=128,flash_attention=True)
    memory_path = ROOT/'dsh/moe-offload.json'
    memory = json.loads(memory_path.read_text())
    memory['models'][ident] = {key:profile[key] for key in ('backend','context','minimum_host_ram_gib',
        'cpu_expert_layers','host_expert_bytes','gpu_expert_cache_mib','kv_cache','load_mode','min_free_vram_gib','min_start_vram_gib','validation','tensor_split')}
    memory['models'][ident]['mtp_draft_experts_on_gpu'] = profile['mtp']
    runtime_path = ROOT/'dsh/llama-runtime.json'
    runtime = json.loads(runtime_path.read_text())
    if ident not in runtime['models']:
        runtime['models'].append(ident)
    runtime.setdefault('runtime_overrides',{})[ident] = 'hip-amd'
    ini_path = ROOT/'dsh/models-hip.ini'
    ini = ini_path.read_text()
    marker = '\n[' + ident + ']\n'
    if marker in ini:
        raise ValueError('Preset already exists; explicit review is needed before replacing it')
    ini += marker + '\n'.join([
        'model = '+profile['path'], 'ctx-size = '+str(profile['context']),
        'device = ROCm0,ROCm1', 'split-mode = layer', 'tensor-split = '+profile['tensor_split'],
        'n-gpu-layers = 99','fit = off','override-tensor = '+overrides(profile),
        'n-cpu-moe = 0','moe-cache-mib = '+str(profile['gpu_expert_cache_mib']),
        'load-mode = none','threads = 6','threads-batch = 6','cache-ram = 0','ctx-checkpoints = 0',
        'spec-type = '+('draft-mtp' if profile['mtp'] else 'none'),
        'temp = 1.0','top-p = 0.95','top-k = 0','min-p = 0',
        *(['spec-draft-n-max = 3','spec-draft-type-k = q8_0','spec-draft-type-v = q8_0'] if profile['mtp'] else [])])+'\n'
    changes = [(catalog_path,json.dumps(catalog,indent=2)+'\n'),
               (memory_path,json.dumps(memory,indent=2)+'\n'),
               (runtime_path,json.dumps(runtime,indent=2)+'\n'),(ini_path,ini)]
    backup = ROOT/'.private-backups'/('nemotron-super-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    for path,content in changes:
        (backup/path.name).write_bytes(path.read_bytes())
    for path,content in changes:
        temp = path.with_name(path.name+'.tmp')
        temp.write_text(content)
        temp.replace(path)
    from configure_local import configure
    configure() # Preserve the current provider/model selection.
    print('Registered',ident,'without starting a worker or changing the default model')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result',type=Path)
    activate(parser.parse_args().result)
