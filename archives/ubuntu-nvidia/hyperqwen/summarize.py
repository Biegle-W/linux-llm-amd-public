"""Publish numeric test evidence while keeping generated responses out of Git."""
import json
import statistics
from pathlib import Path

root = Path(__file__).parent / 'research'
raw = root / 'raw'
raw.mkdir(exist_ok=True)
settings = {
    'baseline-32k': {'runtime': 'existing vLLM 0.30.0', 'context': 32768,
                     'speculation': 'MTP3', 'kv_bytes_per_gpu': 805306368,
                     'model_weights_gib_per_gpu': 8.34, 'mamba_state_dtype': 'bfloat16'},
    'mtp-64k': {'runtime': 'HyperQwen/vLLM 0.30.0', 'context': 65536,
                'speculation': 'MTP3', 'kv_bytes_per_gpu': 1610612736,
                'model_weights_gib_per_gpu': 7.21, 'mamba_state_dtype': 'float16',
                'allocated_kv_token_capacity': 129901},
    'dflash-64k': {'runtime': 'HyperQwen/vLLM 0.30.0', 'context': 65536,
                   'speculation': 'DFlash2, seven draft tokens', 'kv_bytes_per_gpu': 1610612736,
                   'model_weights_gib_per_gpu': 8.03, 'mamba_state_dtype': 'float16',
                   'allocated_kv_token_capacity': 105828},
}
result = {
    'date': '2026-10-05',
    'hardware': {'cpu': 'Intel i5-13600KF', 'ram_gb': 64,
                 'gpu0': 'RTX 4070 12GB, desktop display, PCIe4 x16',
                 'gpu1': 'RTX 3060 12GB, PCIe4 x4 via chipset', 'cuda_p2p': False},
    'hyperqwen_commit': '10bb488418064b50738c925b70c9510785c3c949',
    'common_settings': {'tensor_parallel_size': 2, 'custom_all_reduce': False,
                        'kv_cache_dtype': 'int4_per_token_head', 'attention': 'TRITON_ATTN',
                        'max_sequences': 1, 'prefill_chunk': 512, 'thinking': False,
                        'temperature': 0.6, 'top_p': 0.95, 'seed': 42},
    'method': 'Three warm 256-output-token code/prose runs. Decode=(completion_tokens-1)/(end-first_visible_output). TTFT includes frontend, prefill and first token. Long requests use temperature=0; MTP long replies originally requested codes only (22 output tokens), other profiles request codes and an explanation (256 outputs).',
    'limitations': ['Profiles differ in head/embedding quantization, draft model and Mamba precision.',
                    'No general quality benchmark; synthetic retrieval and tool checks only.',
                    '64K is the configured HyperQwen window, with approximately 59K input tested; larger contexts were not validated.',
                    'External streaming timing can be affected by speculative output bursts; short tool outputs are not sustained decode benchmarks.'],
    'profiles': {},
}
for label, config in settings.items():
    source = raw / (label + '.json')
    if not source.exists():
        source = root / (label + '.json')
    rows = json.loads(source.read_text())
    # Preserve the full local evidence, then export only metrics and pass flags.
    if source.parent != raw:
        source.rename(raw / source.name)
    public = []
    for row in rows:
        clean = {k: v for k, v in row.items() if k not in ('text', 'tool_calls')}
        if row['name'] == 'tool':
            calls = {}
            for piece in row['tool_calls']:
                call = calls.setdefault(piece['index'], {'name': '', 'arguments': ''})
                for k in call:
                    call[k] += piece.get('function', {}).get(k, '')
            clean['structured_tool_call_passed'] = any(
                c['name'] == 'get_test_value' and json.loads(c['arguments']) == {'key': 'alpha'}
                for c in calls.values())
        if row['name'] == 'tool-result':
            clean['tool_result_passed'] = 'HYPERQWEN_TOOL_OK_742' in row['text']
        if row['name'].startswith('context-'):
            clean['effective_input_tokens_per_ttft_second'] = row['usage']['prompt_tokens'] / row['ttft_s']
        public.append(clean)
    summary = {}
    for name in ('code', 'prose'):
        group = [r for r in rows if r['name'].startswith(name + '-')]
        summary[name] = {'runs': len(group),
                         'median_decode_tps_external': statistics.median(r['decode_tps_external'] for r in group),
                         'median_ttft_s': statistics.median(r['ttft_s'] for r in group)}
    result['profiles'][label] = {'settings': config, 'summary': summary, 'requests': public}
(root / 'results-2026-10-05.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({label: r['summary'] for label, r in result['profiles'].items()}, indent=2))
