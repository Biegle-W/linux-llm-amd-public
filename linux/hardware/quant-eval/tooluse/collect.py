#!/usr/bin/env python3
"""Collect the November 24 short tool-use runs into hardware/results/tooluse-short-2026-11-24.json (scores only, no item text)."""
import json, sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]  # repository root (this file: hardware/quant-eval/tooluse/collect.py)
RUNS = R / 'hardware/generated/fast-tooluse-2026-11-24'
OUT = R / 'hardware/results/tooluse-short-2026-11-24.json'
ENGINE = {
    'qwen3.8-27b-sglang-dflash2': 'SGLang TP2 f84475ccf593',
    'qwen3.8-27b-vllm': 'vLLM TP2 0.33.0rc1.dev229+g3966924d5.rocm72',
    'ripple-65b-vllm': 'vLLM TP2 0.33.0rc1.dev229+g3966924d5.rocm72',
    'kolibri-1.1-iq4_xs': 'llama.cpp PR 32891 5f4d222898dd',
    'inkling-2-mini-sq-20-strata-2gpu': 'Strata v0.2.20 a34979fc94f3 (strata-inkling)',
    'qwen3.8-flash-next-iq3_xxs': 'Strata v0.2.20 a34979fc94f3',
    'deepseek-v4.1-flash-1017-maya-unsloth-q1': 'Maya 1.1.73 f9a053dcb5a9',
    'deepseek-v4.1-flash-1017-strata-unsloth-q1': 'Strata DeepSeek 13eedf552417 (frozen)',
    'glm-5.3-flash-maya': 'Maya 1.1.73 f9a053dcb5a9',
}
KEEP = ['model', 'group', 'manifest_hash', 'start_utc', 'end_utc', 'load_seconds', 'item_seconds', 'status', 'single_correct',
        'episodes_passed', 'episodes15_passed', 'coverage', 'complete', 'score_meaningful', 'score', 'score15', 'covered_score', 'timeouts', 'pools']
rows = []
for d in sorted(RUNS.iterdir()):
    f = d / 'fast-result.json'
    if not f.exists():
        continue
    r = json.loads(f.read_text())
    row = {k: r.get(k) for k in KEEP if k in r}
    row['engine'] = ENGINE[r['model']]
    rows.append(row)
missing = set(ENGINE) - {r['model'] for r in rows}
if missing:
    sys.exit(f'missing runs: {sorted(missing)}')
rows.sort(key=lambda r: -r['score'])
doc = {
    'test': 'short tool-use test (AMD rebuild of the NVIDIA method)',
    'date': '2026-11-24',
    'source': 'BFCL v4 (ShishirPatil/gorilla, Apache-2.0), ranking seed 20261122; items are listed by id in hardware/quant-eval/tooluse/fast_amd/manifest.json',
    'score': '50 x single-turn correct / 40 + 50 x core multi-turn episodes passed / 9; large group also score15 with all 15 episodes',
    'settings': 'temperature 0.6, top_p 0.95, max_tokens 2048, seed 20261122, no system prompt, thinking as served; one request at a time through the hub',
    'limits_seconds': {'load_cap': 300, 'item_budget_small': 690, 'item_budget_large': 3360, 'hard_limit_small': 1020, 'hard_limit_large': 3720,
                       'per_item': 120, 'per_episode': 480},
    'runs': rows,
}
OUT.write_text(json.dumps(doc, indent=2) + '\n')
for r in rows:
    print(f"{r['score']:5.1f} {r.get('score15')} {r['single_correct']}/40 {r['episodes_passed']}/9 {r['coverage']} {r['status']} load {r['load_seconds']:.0f} items {r['item_seconds']:.0f} {r['model']}")
print('wrote', OUT)
