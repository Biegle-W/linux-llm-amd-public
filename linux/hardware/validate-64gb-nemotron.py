#!/usr/bin/env python3
"""Validate isolated Nemotron CPU-thread candidates without changing production.

Reuse the guarded dual-GPU validator and its fixed ~8K benchmark corpus. Results
record the CPU/RAM, exact effective arguments and output hashes, not answer text.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import statistics
import hashlib
import re
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--threads-batch', type=int)
    parser.add_argument('--split', choices=['1,1','21,19','19,21'], default='21,19')
    parser.add_argument('--phase', choices=['smoke','split','bench','long'], default='split')
    parser.add_argument('--tag', required=True)
    parser.add_argument('--context', type=int, default=32768)
    parser.add_argument('--physical-cores', action='store_true',
                        help='Pin decode to physical P-cores and prefill to physical cores, excluding SMT siblings')
    parser.add_argument('--long-input-tokens', type=int, default=28500,
                        help='Uncached marker-probe target for --phase long; prompt/chat overhead is recorded separately')
    parser.add_argument('--standard-short', action='store_true',
                        help='Also measure the saved nine-profile batch short prompts, three trials/task')
    parser.add_argument('--cache-mib', type=int,
                        help='Isolated GPU expert-cache ceiling; production/candidate files are not changed')
    parser.add_argument('--extra-cpu-layers', default='',
                        help='Comma-separated existing MoE layers to add to bounded CPU storage')
    parser.add_argument('--checkpoints', type=int, choices=range(5), default=0,
                        help='Bounded hybrid-state checkpoint count; default preserves the baseline')
    parser.add_argument('--prefix-followup', action='store_true',
                        help='Validate marker retrieval and over 90 percent prefix reuse on a full-history follow-up')
    parser.add_argument('--ubatch',type=int,choices=(128,192,256),default=128)
    options = parser.parse_args()
    assert 1 <= options.threads <= 32
    batch = options.threads_batch or options.threads
    assert 1 <= batch <= 32
    spec = importlib.util.spec_from_file_location('nemotron_validator', ROOT/'hardware/validate-nemotron-super.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    original_stream = validator.bench.stream
    follow_up_evidence = {}
    progress_path = ROOT/'hardware/generated/cpu-ram-validation-2026-10-19/nemotron'/(options.tag+'.progress.jsonl')
    assert not progress_path.exists(), 'Do not overwrite recorded request progress'
    def progress(stage, record):
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        with progress_path.open('a') as output:
            output.write(json.dumps({'stage':stage,'completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'record':record})+'\n')
            output.flush()
            os.fsync(output.fileno())
    def stream(kind, model, prompt, **kwargs):
        if len(prompt) > 200000:kwargs.setdefault('timeout',3600)
        record,text = original_stream(kind, model, prompt, **kwargs)
        progress('request', record)
        if options.prefix_followup and 'Secret marker:' in prompt and kwargs.get('sampled') is False:
            messages = [{'role':'user','content':prompt},{'role':'assistant','content':text},
                        {'role':'user','content':'Repeat the three secret markers, in their original order. Nothing else.'}]
            follow,answer = original_stream(kind,model,'',messages=messages,cache_prompt=True,
                                            limit=96,sampled=False,timeout=3600)
            follow['markers_passed'] = all(m in answer for m in ('ALPHA-719','BETA-263','GAMMA-451'))
            follow['prefix_reuse_passed'] = follow['cached_tokens'] > .9*record['usage']['prompt_tokens']
            progress('prefix_followup', follow)
            record['follow_up'] = follow
            follow_up_evidence.update(record)
            assert follow['markers_passed'] and follow['prefix_reuse_passed'], 'Long-history follow-up failed retrieval or prefix reuse'
        return record,text
    validator.bench.stream = stream
    if options.cache_mib is not None:assert 512 <= options.cache_mib <= 9216
    measured_profile = {}
    original_admission = validator.memory_reason
    def admission(profile, total, available):
        if options.cache_mib is not None:
            profile['gpu_expert_cache_mib'] = options.cache_mib
        extra = [int(value) for value in options.extra_cpu_layers.split(',') if value]
        assert all(str(layer) in profile['expert_layer_bytes'] and layer != 88 for layer in extra)
        profile['cpu_expert_layers'] = sorted(set(profile['cpu_expert_layers'] + extra))
        profile['host_expert_bytes'] = sum(profile['expert_layer_bytes'][str(layer)] for layer in profile['cpu_expert_layers'])
        measured_profile.update(profile)
        return original_admission(profile, total, available)
    validator.memory_reason = admission
    original = validator.server_args
    effective = []
    binary_hash = None
    masks = {}
    if options.physical_cores:
        topology = {}
        for cpu in sorted(os.sched_getaffinity(0)):
            base = Path(f'/sys/devices/system/cpu/cpu{cpu}')
            core = ((base/'topology/physical_package_id').read_text(), (base/'topology/core_id').read_text())
            topology.setdefault(core, cpu)
        physical = sorted(topology.values())
        # An SMT pair identifies the P-cores on this checked Intel hybrid CPU.
        pcores = [cpu for cpu in physical if len((Path(f'/sys/devices/system/cpu/cpu{cpu}')/'topology/thread_siblings_list').read_text().strip().replace('-', ',').split(',')) > 1]
        assert options.threads <= len(pcores) and batch <= len(physical), 'Thread count exceeds detected physical core set'
        masks = dict(cpu_mask=format(sum(1<<cpu for cpu in pcores),'x'),
                     cpu_mask_batch=format(sum(1<<cpu for cpu in physical),'x'))
    def configured(*args, **kwargs):
        nonlocal binary_hash
        cmd = original(*args, **kwargs)
        cmd[cmd.index('--threads')+1] = str(options.threads)
        cmd[cmd.index('--threads-batch')+1] = str(batch)
        cmd[cmd.index('--ctx-checkpoints')+1] = str(options.checkpoints)
        cmd[cmd.index('--ubatch-size')+1] = str(options.ubatch)
        if masks:
            cmd += ['--cpu-mask',masks['cpu_mask'],'--cpu-strict','1',
                    '--cpu-mask-batch',masks['cpu_mask_batch'],'--cpu-strict-batch','1']
        effective[:] = cmd
        binary_hash = hashlib.sha256(Path(cmd[0]).read_bytes()).hexdigest()
        progress('candidate', dict(effective_args=cmd,binary_sha256=binary_hash,
            threads=options.threads,threads_batch=batch,context=options.context,
            cpu_expert_layers=measured_profile.get('cpu_expert_layers',[]),
            host_expert_bytes=measured_profile.get('host_expert_bytes'),
            cache_mib=measured_profile.get('gpu_expert_cache_mib'),
            ctx_checkpoints=options.checkpoints,ubatch_size=options.ubatch,**masks))
        return cmd
    validator.server_args = configured
    original_prompt = validator.prompt_at_tokens
    def sized_prompt(target, ending):
        return original_prompt(options.long_input_tokens if target == 28500 else target, ending)
    if options.phase == 'long':assert 1000 <= options.long_input_tokens < options.context - 1024
    assert not options.prefix_followup or options.phase == 'long'
    validator.prompt_at_tokens = sized_prompt
    if options.standard_short or options.prefix_followup:
        original_functional = validator.functional
        def functional(profile, context):
            result = original_functional(profile, context)
            if options.prefix_followup:
                prefix = ('Read the ledger and return its three secret markers in order.\n'
                    'Secret marker: ALPHA-719\n'+'Routine inventory record.\n'*100+
                    'Secret marker: BETA-263\n'+'Routine inventory record.\n'*100+
                    'Secret marker: GAMMA-451\nReturn only the markers, in order.')
                smoke,text = stream('llama',profile['id'],prefix,limit=96,sampled=False)
                assert all(m in text for m in ('ALPHA-719','BETA-263','GAMMA-451'))
                result['prefix_smoke'] = smoke
                print(options.tag,'PREFIX SMOKE PASS',smoke['follow_up']['cached_tokens'],flush=True)
            if not options.standard_short:
                progress('functional', result)
                return result
            short = {}
            for task, prompt in validator.bench.PROMPTS.items():
                validator.bench.stream('llama',profile['id'],prompt)
                trials = []
                for index in range(3):
                    record, _ = validator.bench.stream('llama',profile['id'],prompt)
                    assert record['usage']['completion_tokens'] >= 64
                    record['trial'] = index+1
                    trials.append(record)
                    print(options.tag,'SHORT',task,index+1,round(record['ttft_seconds'],3),round(record['decode_tps_sse'],3),flush=True)
                short[task] = dict(trials=trials,
                    median_ttft_seconds=statistics.median(t['ttft_seconds'] for t in trials),
                    median_decode_tps=statistics.median(t['decode_tps_sse'] for t in trials))
            result['standard_short'] = short
            progress('functional', result)
            return result
        validator.functional = functional
    validator.OUT = ROOT/'hardware/generated/cpu-ram-validation-2026-10-19/nemotron'
    target = validator.OUT/(options.tag+'.json')
    assert not target.exists(), 'Do not overwrite a measured trial'
    cpu = next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name'))
    total = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:'))
    # The driver's utilization sample can briefly outlive a stopped worker.
    for _ in range(10):
        if all(int((d/'gpu_busy_percent').read_text()) <= 10 for d in validator.amd_devices()):break
        time.sleep(1)
    try:
        validator.run(SimpleNamespace(model='nemotron-3.5-super-q4',context=options.context,
            split=options.split,mtp=False,phase=options.phase,tag=options.tag,max_gpu_busy=10))
    finally:
        if target.exists():
            data = json.loads(target.read_text())
            data.update(cpu=cpu,os_visible_ram_bytes=total,threads=options.threads,threads_batch=batch,
                        effective_args=effective,measurement_time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
            data.update(masks)
            data['cpu_expert_layers'] = measured_profile.get('cpu_expert_layers', [])
            data['ctx_checkpoints'] = options.checkpoints
            data['ubatch_size'] = options.ubatch
            if follow_up_evidence:data['follow_up_probe'] = follow_up_evidence
            data['binary_sha256'] = binary_hash
            log = target.with_suffix('.log').read_text(errors='replace')
            build = re.search(r'common_params_print_info: build \d+ \(([0-9a-f]+)\)',log)
            data['compiled_revision'] = build.group(1) if build else None
            if data['status']=='passed' and (not build or not data['runtime_commit'].startswith(build.group(1))):
                data.update(status='failed',error='Compiled revision did not match recorded runtime source')
            if options.phase == 'long':data['long_input_target'] = options.long_input_tokens
            target.write_text(json.dumps(data,indent=2)+'\n')
            if data['status']=='failed':raise RuntimeError(data.get('error','Candidate validation failed'))


if __name__ == '__main__':
    main()
