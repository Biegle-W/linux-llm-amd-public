#!/usr/bin/env python3
"""Load the saved vLLM profile through its real router and validate integration."""
import importlib.util
import argparse
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--long',action='store_true')
    parser.add_argument('--cache',action='store_true')
    options = parser.parse_args()
    bench = load('vllm_production_checks',ROOT/'hardware/bench-dual-tuning.py')
    if any(bench.base.backend_switch.is_inference(p) for p in bench.base.backend_switch.processes().values()):
        raise RuntimeError('Another configured inference worker is active')
    manager = load('vllm_production_router',ROOT/'dsh/vllm-router.py')
    model = manager.DEFAULT
    cfg = manager.PROFILES[model]
    bench.checks.PORT = manager.WORKER_PORT
    bench.checks.MODEL = model
    result = dict(model=model,status='running')
    try:
        manager.ensure_worker(model)
        args = Path(f'/proc/{manager.worker.pid}/cmdline').read_bytes().decode().split('\0')
        def last(flag):
            return args[max(i for i,value in enumerate(args) if value == flag)+1]
        effective = dict(context=int(last('--max-model-len')),tp=int(last('--tensor-parallel-size')),
                         kv=last('--kv-cache-dtype'),cache_bytes=int(last('--kv-cache-memory-bytes')),
                         dtype=last('--dtype'),chunk=int(last('--max-num-batched-tokens')),
                         compilation=json.loads(last('--compilation-config')),
                         speculation=json.loads(last('--speculative-config')))
        assert effective['context'] == cfg['context'] == 65536
        assert effective['tp'] == 2
        assert effective['kv'] == 'bfloat16'
        assert effective['chunk'] == 2048
        assert effective['compilation']['mode'] == 3
        assert effective['cache_bytes'] == cfg['kv_cache_bytes']
        assert effective['speculation']['method'] == 'mtp'
        assert effective['speculation']['num_speculative_tokens'] == cfg.get('mtp_steps',3)
        assert min(m['max_model_len'] for m in manager.get_worker('/v1/models')['data']) >= cfg['context']
        result['effective'] = effective
        selected = [value for value in Path(f'/proc/{manager.worker.pid}/environ').read_bytes().split(b'\0')
                    if value.startswith(b'VLLM_LOCAL_RDNA_PREFILL=')]
        assert selected == [b'VLLM_LOCAL_RDNA_PREFILL=1']
        result['rdna_prefill_enabled'] = True
        result['quality'] = bench.checks.validate()
        ordered = bench.stream('Return only a JSON array containing the integers 1 through 100 in ascending order. No markdown.',limit=1024,sampled=False)
        result['quality']['ordered_100'] = json.loads(ordered['content']) == list(range(1,101))
        assert all(result['quality'].values())
        if options.long:
            prompt,codes = bench.base.marker_prompt(cfg['context']-1500)
            trial = bench.stream(prompt,limit=128,sampled=False)
            assert all(code in trial['content'] for code in codes)
            result['long_retrieval'] = {k:v for k,v in trial.items() if k != 'content'}
            result['long_retrieval']['passed'] = True
        if options.cache:
            def counters():
                with urllib.request.urlopen(f'http://127.0.0.1:{manager.WORKER_PORT}/metrics',timeout=5) as response:
                    lines = response.read().decode().splitlines()
                return {line.rsplit(' ',1)[0]:float(line.rsplit(' ',1)[1]) for line in lines
                        if line.startswith('vllm:prefix_cache') and '_total{' in line}
            prompt,codes = bench.base.marker_prompt(8192)
            cold = bench.stream(prompt,limit=128,sampled=False)
            before = counters()
            warm = bench.stream(prompt,limit=128,sampled=False)
            after = counters()
            assert all(code in trial['content'] for trial in (cold,warm) for code in codes)
            delta = {key:value-before.get(key,0) for key,value in after.items()}
            result['prefix_cache'] = dict(initial_ttft_seconds=cold['ttft_seconds'],warm_ttft_seconds=warm['ttft_seconds'],counter_deltas=delta)
            assert sum(value for key,value in delta.items() if 'hits_total{' in key) > 0
        tree = bench.base.backend_switch.processes()
        owned = {manager.worker.pid}
        for _ in range(8):
            owned.update(p.pid for p in tree.values() if p.parent in owned)
        result['nonresident_vram_bytes'] = sum(bench.checks.gpu.amd_residency(pid)['nonresident_vram_bytes'] for pid in owned)
        assert result['nonresident_vram_bytes'] == 0
        result['gpu_vram_bytes'] = [int((d/'mem_info_vram_used').read_text()) for d in bench.base.amd_devices()]
        assert len(result['gpu_vram_bytes']) == 2 and min(result['gpu_vram_bytes']) > 2*1024**3
        result['status'] = 'passed'
    finally:
        manager.stop_worker()
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
