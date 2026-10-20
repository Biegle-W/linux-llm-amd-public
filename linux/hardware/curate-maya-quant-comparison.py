#!/usr/bin/env python3
"""Publish numerical Maya quant A/B evidence without private paths or raw logs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in ('protected_config_hashes_before',
                'protected_config_hashes_after')}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return value.replace(str(ROOT), '/opt/local-llm').replace(
            '/mnt/shared-nvme', '/mnt/shared-nvme').replace('/mnt/shared', '/mnt/shared')
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    raw = args.raw_root
    comparison = read(raw / 'comparison.json')
    assert comparison['status'] == 'passed' and comparison['production_configs_unchanged']
    assert len(comparison['cases']) == 4 and all(c['status'] == 'passed' for c in comparison['cases'])
    preparation_path = raw / 'preparation.json'
    preparation = read(preparation_path if preparation_path.exists() else raw.parent / 'preparation.json')
    assert preparation['status'] == 'passed'
    cases = []
    for case in comparison['cases']:
        tag = case['tag']
        server, functional, bench = [read(raw / (tag + ext))
            for ext in ('.server.json', '.functional.json', '.benchmark.json')]
        assert server['status'] == 'stopped_after_testing'
        assert functional['status'] == 'passed' and bench['profiles'][0]['status'] == 'passed'
        assert min(server['startup_whole_card_free_bytes']) >= 6 * 1024**3
        assert server['memory']['maximum_worker_swap_bytes'] == server['memory']['maximum_vram_spill_bytes'] == 0
        assert functional['long_context']['markers_passed'] and functional['long_follow_up']['markers_passed']
        sources = [{'file': tag + ext, 'sha256': hashlib.sha256((raw / (tag + ext)).read_bytes()).hexdigest()}
                   for ext in ('.server.json', '.functional.json', '.benchmark.json')]
        layout = []
        for line in (raw / (tag + '.native.log')).read_text(errors='replace').splitlines():
            match = re.search(r'glm fast: CUDA(\d+) layers \[(\d+),(\d+)\) expert pool ([\d.]+) GB, (.+)', line)
            if match:
                layout.append({'gpu': int(match[1]), 'layer_start': int(match[2]),
                               'layer_end_exclusive': int(match[3]),
                               'expert_pool_gb_reported': float(match[4]), 'slots_reported': match[5]})
        cases.append({'tag': tag, 'quant': case['quant'], 'lifecycle': server,
                      'runtime_cache_layout': layout,
                      'functional': functional, 'benchmark': bench['profiles'][0], 'sources': sources})
    summaries = {}
    prompt_counts = [tuple(t['usage']['prompt_tokens'] for t in c['benchmark']['prefill']) for c in cases]
    assert len(set(prompt_counts)) == 1, 'Tokenized prefill workloads differ; investigate before selection'
    for quant in ('s24', 's'):
        group = [c['benchmark'] for c in cases if c['quant'] == quant]
        prefill = [t for c in group for t in c['prefill']]
        summaries[quant] = {
            'context': 32768, 'timed_trials_per_workload': 6, 'independent_starts': 2,
            'actual_prefill_input_range': [min(t['usage']['prompt_tokens'] for t in prefill),
                                         max(t['usage']['prompt_tokens'] for t in prefill)],
            'native_prefill_tps': statistics.median(t['prefill_native_tps'] for t in prefill),
            'prefill_ttft_seconds': statistics.median(t['ttft_seconds'] for t in prefill),
            'short_decode_tps': {task: statistics.median(t['decode_tps_sse'] for c in group
                for t in c['short'][task]['trials']) for task in ('code', 'prose')},
            'short_ttft_seconds': {task: statistics.median(t['ttft_seconds'] for c in group
                for t in c['short'][task]['trials']) for task in ('code', 'prose')}}
    ratios = {task: summaries['s']['short_decode_tps'][task] / summaries['s24']['short_decode_tps'][task]
              for task in ('code', 'prose')}
    ratios['prefill'] = summaries['s']['native_prefill_tps'] / summaries['s24']['native_prefill_tps']
    assert all(abs(ratios[k] - comparison['ratios'][k]) < 1e-10 for k in ratios)
    assert comparison['candidate_passed_speed'] == all(r > .90 for r in ratios.values())
    runtime = {k: v for k, v in read(ROOT / 'maya/runtime.json').items() if k not in ('status', 'scope')}
    record = {'date': '2026-10-20', 'runtime': runtime,
              'hardware': 'i9-13900KS / 64 GB RAM / two RX 7900 XTX24GB; CPU PCIe4x8/x8; switch not installed; direct P2P disabled',
              'method': comparison, 'preparation': preparation, 'matched_prefill_input_tokens': list(prompt_counts[0]),
              'summaries': summaries, 'candidate_to_s24_ratios': ratios, 'cases': cases,
              'selected_quant': comparison['selected_quant'], 'deepseek_changed': False,
              'limits': ['Six timed samples per workload across two starts; not a statistical guarantee.',
                         'ABBA order, identical expert-profile seeds and prompt corpus; OS/page/expert caches still evolve.',
                         'Short sampled256-output decode differs from fresh greedy~6.3K prompt processing and near30K functional probes.',
                         'Configured32K is not a broad full-window quality guarantee; model fidelity is not locally scored against FP8.',
                         'Native PP is distinct from external SSE TTFT/decode; load and compilation are excluded.',
                         'Measured whole-card minima include desktop apps; startup6GiB and existing continuous guards retained.']}
    record['additional_provenance'] = {name: read(raw.parent / name) for name in
        ('policy.json', 'tokenizer-parity.json', 'measurement-code-hashes.json') if (raw.parent / name).exists()}
    if 'tokenizer-parity.json' in record['additional_provenance']:
        parity = record['additional_provenance']['tokenizer-parity.json']
        assert parity['identical']
        # Explicit checksum records avoid confusing token-file names with API
        # credential assignments during publication scans.
        parity['files'] = [{'file': name, 'sha256': digest} for name, digest in parity['files'].items()]
    args.output.write_text(json.dumps(clean(record), indent=2) + '\n')
    print(json.dumps({'selected': record['selected_quant'], 'summaries': summaries, 'ratios': ratios}, indent=2))


if __name__ == '__main__':
    main()
