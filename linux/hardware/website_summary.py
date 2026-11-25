#!/usr/bin/env python3
"""Write docs/WEBSITE-SUMMARY.md in the public repo (owner, November 24: biegle.ca reads it every 6 hours).

Run after every change to the routes or the results, and commit its output in the same public commit:

    python3 hardware/website_summary.py            # writes ../local-llm-public/docs/WEBSITE-SUMMARY.md
    python3 hardware/website_summary.py --check    # exits 1 if the file is out of date or a route is missing

The data below is kept by hand from the dated reports. The script refuses to write if the enabled routes
here differ from the live registry (dsh/model_catalog.py) or a context differs, so the page cannot
silently miss a route.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'local-llm-public' / 'docs' / 'WEBSITE-SUMMARY.md'
UPDATED = '2026-11-24'
GH = 'https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/'

# 1. Enabled routes ---------------------------------------------------------------------------------------
ROUTES = [  # id, model and quant, engine and version, context, weights (size, drive), placement
    ('qwen3.8-27b-sglang-dflash2', 'Qwen3.8-27B AutoRound W4A16 (GPTQ) + DFlash2 W4A16 drafter',
     'SGLang TP2, gfx1100 build `f84475ccf593`', 163840, '19 GB + 1.2 GB drafter, shared SATA SSD', 'VRAM only (both cards)'),
    ('qwen3.8-27b-vllm', 'Qwen3.8-27B AutoRound W4A16 (GPTQ)',
     'vLLM TP2 `0.33.0rc1.dev229+g3966924d5.rocm72`', 163840, '19 GB, shared SATA SSD (same files as SGLang)', 'VRAM only (both cards)'),
    ('ripple-65b-vllm', 'Ripple-65B-Preview GPTQ W4A16',
     'vLLM TP2 `0.33.0rc1.dev229+g3966924d5.rocm72`', 65536, '33 GB, shared SATA SSD', 'VRAM only (both cards)'),
    ('kolibri-1.1-iq4_xs', 'Aleph Alpha Kolibri 1.1 (75B MoE, 3.4B active) IQ4_XS GGUF',
     'llama.cpp HIP, pull request 32891 at `5f4d222898dd` (unmerged, pinned for this route)', 262144, '40.2 GB, shared SATA SSD', 'VRAM only (both cards)'),
    ('inkling-2-mini-sq-20-strata-2gpu', 'Inkling 2 Mini SQ-20 `.strata` + vision',
     'Strata `v0.2.21.1` (`2af30ccaa072`) `strata-inkling`', 262144, '19 GB, shared NVMe SSD', 'VRAM only (both cards, expert parallel)'),
    ('qwen3.8-flash-next-iq3_xxs', 'Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS GGUF',
     'Strata `v0.2.21.1` (`2af30ccaa072`)', 262144, '71 GB + 2.3 GB pack and MTP head, system NVMe SSD', 'Partly in system memory (experts in RAM, streamed from SSD)'),
    ('deepseek-v4.1-flash-1017-maya-unsloth-q1', 'DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S GGUF',
     'Maya 1.1.78 (`1530120a124e`)', 32768, '217 GB, system NVMe SSD (shared with the Strata route)', 'Partly in system memory (RAM expert tier, streamed from SSD)'),
    ('deepseek-v4.1-flash-1017-strata-unsloth-q1', 'DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S GGUF',
     'Strata DeepSeek `13eedf552417` (frozen)', 32768, '217 GB, system NVMe SSD (shared with the Maya route)', 'Partly in system memory (streamed from SSD, RAM store off)'),
    ('glm-5.3-flash-maya', 'GLM-5.3-Flash Maya-S v2 IQ2_XXS GGUF',
     'Maya 1.1.78 (`1530120a124e`)', 32768, '91 GB, system NVMe SSD', 'Partly in system memory (40 GB RAM tier, streamed from SSD)'),
]

# 2. Speed rows: the standard short tool-call check (one DSH read-tool round trip, about 6.2-7.6K prompt tokens,
# 25 tool definitions, cold start). For each route: the run with the fastest decode since its current engine
# was installed. Decode = (answer tokens - 1) / (time after the first token); prefill = prompt / time to first token.
SPEED = {  # id: (prefill t/s, TTFT s, decode t/s or None, prompt tokens, answer tokens, date, evidence)
    'qwen3.8-27b-sglang-dflash2': (1736, 3.86, 208.5, 6705, 80, '2026-11-09', 'hardware/results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json'),
    'qwen3.8-27b-vllm': (1766, 3.64, 153.1, 6420, 77, '2026-11-09', 'hardware/results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json'),
    'ripple-65b-vllm': (764, 8.18, 27.6, 6244, 76, '2026-11-09', 'hardware/results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json'),
    'kolibri-1.1-iq4_xs': (2466, 2.58, 80.2, 6351, 82, '2026-11-24', 'hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md'),
    'inkling-2-mini-sq-20-strata-2gpu': (2115, 3.67, 96.6, 7761, 123, '2026-11-24', 'hardware/DAILY-UPDATES.md'),
    'qwen3.8-flash-next-iq3_xxs': (1548, 4.09, 173.4, 6332, 83, '2026-11-24', 'hardware/DAILY-UPDATES.md'),
    'deepseek-v4.1-flash-1017-maya-unsloth-q1': (92, 70.42, 6.6, 6448, 105, '2026-11-24', 'hardware/DAILY-UPDATES.md'),
    'deepseek-v4.1-flash-1017-strata-unsloth-q1': (108, 58.91, 4.4, 6338, 107, '2026-11-12', 'hardware/DAILY-UPDATES.md'),
    'glm-5.3-flash-maya': (170, 35.89, 11.1, 6104, 54, '2026-11-24', 'hardware/DAILY-UPDATES.md'),
}
SPEED_NOTES = [
    'Flash-Next and Inkling: checked after Strata 0.2.21.1 was installed on November 24 (one check each on the new engine). Flash-Next loaded from a cold file cache (178 s) after the Maya routes had run.',
    'DeepSeek on Maya and GLM: checked after Maya 1.1.78 was installed on November 24 (one check each on the new engine).',
    'DeepSeek on Strata: checked after its last engine update on November 12; the engine is frozen.',
    'The Qwen3.8-27B routes and Ripple: their engines have not changed since the November 9 check.',
    'Decode here is a short burst (54-123 answer tokens), not a sustained rate.',
    'Each evidence link is the page that records the check or the engine update it followed; the raw per-request timings stay in the private stage folders.',
]

# 3. Retired or removed routes -----------------------------------------------------------------------------
RETIRED = [
    ('inkling-2-mini-sq-20-strata', '2026-11-23', 'retired; replaced by the two-card entry (same weights)'),
    ('inkling-2-mini-q8', '2026-11-23', 'retired; weights kept'),
    ('empero-qwen3.8-35b-a3b', '2026-11-23', 'retired; weights kept'),
    ('nemotron-3.5-bolt-vllm', '2026-11-23', 'retired; weights kept'),
    ('qwen3.8-flash-next-iq3_xxs-upstream', '2026-11-23', 'merged into `qwen3.8-flash-next-iq3_xxs`'),
    ('ornith-1.5-122b', '2026-11-11', 'removed; weights deleted'),
    ('sage-a1.5', '2026-11-11', 'removed; weights deleted'),
    ('flint-40b-a2.5b', '2026-11-11', 'removed; weights deleted'),
    ('Flash-Next UD-IQ1_M, both DeepSeek Coder IQ2_XXS routes', '2026-11-08', 'removed; weights deleted'),
    ('nemotron-3.5-super-iq3, deepseek-v4.1-flash-1017-strata-xs, deepseek-v4.1-flash-1017-maya', '2026-11-02', 'removed; weights deleted'),
]

# 4. Quality ranking --------------------------------------------------------------------------------------
# Owner, November 24: the short tool-use test (the NVIDIA server's test) is the ranking on both machines.
# First AMD run: November 24 (hardware/TOOLUSE-SHORT-TEST-2026-11-24.md). The old 216-item results stay below as reference.
TOOLUSE = [  # route, model and quant, engine at the run, score, single/40, episodes/9, 15-episode score or None, coverage note
    ('qwen3.8-27b-sglang-dflash2', 'Qwen3.8-27B AutoRound W4A16 + DFlash2', 'SGLang TP2 `f84475ccf593`', 74.6, 33, 6, None, 'complete'),
    ('glm-5.3-flash-maya', 'GLM-5.3-Flash Maya-S v2 IQ2_XXS', 'Maya 1.1.73', 72.1, 31, 6, 68.8, 'complete'),
    ('qwen3.8-27b-vllm', 'Qwen3.8-27B AutoRound W4A16', 'vLLM TP2 0.33.0rc1', 71.5, 35, 5, None, 'complete'),
    ('deepseek-v4.1-flash-1017-strata-unsloth-q1', 'DeepSeek-V4.1-Flash-1017 UD-IQ1_S', 'Strata DeepSeek `13eedf552417`', 64.0, 29, 5, 52.9,
     'core complete; 4 of 6 extra episodes cut by the time budget'),
    ('deepseek-v4.1-flash-1017-maya-unsloth-q1', 'DeepSeek-V4.1-Flash-1017 UD-IQ1_S', 'Maya 1.1.73', 62.2, 32, 4, 56.7,
     'core complete; 2 of 6 extra episodes cut by the time budget'),
    ('ripple-65b-vllm', 'Ripple-65B-Preview GPTQ W4A16', 'vLLM TP2 0.33.0rc1', 62.2, 32, 4, 56.7, 'complete'),
    ('inkling-2-mini-sq-20-strata-2gpu', 'Inkling 2 Mini SQ-20', 'Strata 0.2.20 `strata-inkling`', 60.4, 35, 3, None, 'complete'),
    ('qwen3.8-flash-next-iq3_xxs', 'Qwen3.8-Flash-Next IQ3_XXS', 'Strata 0.2.20', 52.9, 29, 3, None, 'complete'),
    ('kolibri-1.1-iq4_xs', 'Kolibri 1.1 IQ4_XS', 'llama.cpp PR 32891 `5f4d222898dd`', 45.6, 32, 1, None, 'complete'),
]
RANKING_216 = [  # model, best route, correct/216, score, 95% interval, code/20, instr/32, knowledge/60, math/40, reasoning/32, tools/32, other engines
    ('Qwen3.8-Flash-Next IQ3_XXS', 'qwen3.8-flash-next-iq3_xxs', 169, '78.2%', '72.3-83.2%', 12, 30, 48, 33, 23, 23,
     'scored November 18 on the Strata RDNA3 fork (replaced by Strata 0.2.20 on November 23, same weights, not rerun)'),
    ('DeepSeek-V4.1-Flash-1017 UD-IQ1_S', 'deepseek-v4.1-flash-1017-maya-unsloth-q1', 168, '77.8%', '71.8-82.8%', 12, 28, 51, 29, 22, 26,
     'Strata DeepSeek 166 (76.9%, November 13)'),
    ('Qwen3.8-27B AutoRound W4A16', 'qwen3.8-27b-sglang-dflash2', 163, '75.5%', '69.3-80.7%', 8, 31, 47, 32, 18, 27,
     'vLLM 157 (72.7%)'),
    ('GLM-5.3-Flash Maya-S v2 IQ2_XXS', 'glm-5.3-flash-maya', 136, '63.0%', '56.3-69.1%', 10, 25, 43, 11, 21, 26, ''),
    ('Ripple-65B-Preview GPTQ W4A16', 'ripple-65b-vllm', 134, '62.0%', '55.4-68.2%', 5, 17, 42, 32, 14, 24,
     'lower bound: 65 answers cut off while still reasoning'),
]

# 5. Short quality test run here so far (AMD quick quality test; not the short tool-use test) -----------------
QUICK = [  # model, route, agent core/12, agent extra/8, tool calls/16, general/10, date, note
    ('Kolibri 1.1 IQ4_XS', 'kolibri-1.1-iq4_xs', 8, 7, 12, 7, '2026-11-24', 'llama.cpp; gBench Golden Set 14/14'),
    ('Inkling 2 Mini SQ-20', 'inkling-2-mini-sq-20-strata-2gpu', 12, 8, 11, 4, '2026-11-23',
     'tested on the retired one-card entry (Strata 0.2.19) with the same weights'),
]

# 6. Trials (not router entries) ---------------------------------------------------------------------------
TRIALS = [
    ('Hy4-Flash SQ-64', 'Strata 0.2.18 side install, one card, 32,768 context', '2026-11-22',
     'quick test: agent 12/12 and 8/8, tool calls 9/16, general 5/10; decode 26-30 t/s', 'hardware/HY4-FLASH-SQ64-2026-11-22.md'),
    ('Hy4-Flash Maya-M', 'Maya 1.1.73 side copy, both cards', '2026-11-22',
     'quick test: agent 11/12 and 8/8, tool calls 9/16, general 6/10; decode 13-32 t/s', 'hardware/HY4-FLASH-MAYA-M-2026-11-22.md'),
]

# 7. Hardware -----------------------------------------------------------------------------------------------
HARDWARE = [
    'Measured on: Intel Core i5-13600KF, 64 GB DDR5 (61.5 GiB visible), two Radeon RX 7900 XTX 24 GB (gfx1100) behind a Broadcom PEX88096 PCIe Gen4 switch (x16 uplink, x8 per card), Ubuntu with kernel `7.0.14-42-vmpt1`, ROCm 7.2.3.',
    'Last hardware change: the November 7 working layout (both cards behind the switch on its own power supply). Nothing changed since; every result above was measured on this layout.',
]


def live_routes():
    sys.path.insert(0, str(ROOT / 'dsh'))
    from model_catalog import catalog
    return {k: v.get('context_length') for k, v in catalog(ROOT).items()}


def fmt(n):
    return f'{n:,}'


def render():
    L = [f'# AMD server: website summary', '',
         f'Machine-readable summary for biegle.ca (read every 6 hours). AMD server only (two RX 7900 XTX); the NVIDIA server has its own repository. '
         f'Updated {UPDATED}, in the same commit as any change to the routes or the results. Generated by `linux/hardware/website_summary.py` from the dated reports; '
         f'links point at the evidence.', '']
    L += ['## 1. Enabled routes', '', '| Route | Model and quant | Engine and version | Context | Weights and disk | Placement |', '|---|---|---|---:|---|---|']
    for r in ROUTES:
        L.append(f'| `{r[0]}` | {r[1]} | {r[2]} | {fmt(r[3])} | {r[4]} | {r[5]} |')
    L += ['', 'One model is loaded at a time through one OpenAI-compatible API; an idle model unloads after 600 s.', '']
    L += ['## 2. Speed (standard short tool-call check)', '',
          'One DSH read-tool round trip through the hub from a cold start: about 6.2-7.6K prompt tokens and 25 tool definitions. '
          'For each route, the run with the fastest decode since its current engine was installed.', '',
          '| Route | Prefill t/s | Time to first token | Decode t/s | Prompt / answer tokens | Date | Evidence |', '|---|---:|---:|---:|---:|---|---|']
    for r in ROUTES:
        p, t, d, pt, at, date, ev = SPEED[r[0]]
        L.append(f'| `{r[0]}` | {fmt(p)} | {t:.2f} s | {"n/a" if d is None else f"{d:.1f}"} | {fmt(pt)} / {at} | {date} | [{Path(ev).name}]({GH}{ev}) |')
    L += [''] + [f'- {n}' for n in SPEED_NOTES] + ['']
    L += ['## 3. Retired or removed routes', '', '| Route | Date | What happened |', '|---|---|---|']
    L += [f'| {r[0] if "," in r[0] or " " in r[0] else "`" + r[0] + "`"} | {r[1]} | {r[2]} |' for r in RETIRED]
    L += ['', '## 4. Quality ranking', '',
          '**Standard (owner, November 24): the short tool-use test, the same test the NVIDIA server ranks by.** 40 single-turn BFCL v4 tool-calling items '
          '(parallel calls, irrelevance, simple calls) and 9 multi-turn episodes; score = 50 x single-turn correct / 40 + 50 x episodes passed / 9, out of 100. '
          'Larger models (the large group) also ran 6 extra episodes, shown as a 15-episode score. Run on all nine routes on November 24, one route at a time through the hub, '
          'temperature 0.6. Items were drawn from BFCL v4 by the NVIDIA rule (seed 20261122) but need not match its frozen list, so compare ranks within one machine.', '',
          '| Rank | Route | Model and quant | Engine at the run | Score /100 | Single-turn /40 | Episodes /9 | 15-episode score | Coverage |',
          '|---:|---|---|---|---:|---:|---:|---:|---|']
    prev, rank = None, 0
    for i, r in enumerate(sorted(TOOLUSE, key=lambda r: -r[3]), 1):
        rank = rank if r[3] == prev else i
        prev = r[3]
        L.append(f'| {rank} | `{r[0]}` | {r[1]} | {r[2]} | {r[3]:.1f} | {r[4]} | {r[5]} | {"—" if r[6] is None else f"{r[6]:.1f}"} | {r[7]} |')
    L += ['', '- One episode moves the score by 5.6 points and one single-turn item by 1.25; routes a few points apart are not separated (no significance test).',
          '- Every route ran all 40 single-turn items and all 9 core episodes with no timeout, so every score is complete.',
          f'- Source: [report]({GH}hardware/TOOLUSE-SHORT-TEST-2026-11-24.md), [results JSON]({GH}hardware/results/tooluse-short-2026-11-24.json), [test code]({GH}hardware/quant-eval/tooluse/README.md).', '',
          '### Reference: old standard (216-item public suite)', '',
          'Not comparable with the ranking above or with the NVIDIA ranking: 216-item public suite (MMLU-Pro, MATH-500, AIME, BigCodeBench, IFEval, BFCL, MuSR), '
          'one attempt, temperature 0, thinking off, November 10-18. One row per model, best engine first.', '',
          '| Rank | Model and quant | Route | Correct / 216 | Score | 95% interval | Code /20 | Instructions /32 | Knowledge /60 | Math /40 | Reasoning /32 | Tools /32 | Other engines and notes |',
          '|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|']
    for i, r in enumerate(RANKING_216, 1):
        L.append(f'| {i} | {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} | ' + ' | '.join(str(x) for x in r[5:11]) + f' | {r[11]} |')
    L += ['', '- Old-standard ties: ranks 1-3 are not statistically separated, nor are ranks 4-5 (exact McNemar, Holm-corrected).',
          '- Not on the old standard: `kolibri-1.1-iq4_xs` and `inkling-2-mini-sq-20-strata-2gpu` (no 216-item run).',
          f'- Source: [current results]({GH}hardware/CURRENT-AMD-BENCHMARKS.md#old-quality-ranking-216-item-public-suite).', '']
    L += ['## 5. Short quality test', '',
          'The AMD quick quality test for new models (run once per new model or new weights since November 22). It is not the short tool-use test and is too small to rank models.', '',
          '| Model and quant | Route | Agent core /12 | Agent extra /8 | Tool calls /16 | General /10 | Date | Note |', '|---|---|---:|---:|---:|---:|---|---|']
    L += [f'| {q[0]} | `{q[1]}` | {q[2]} | {q[3]} | {q[4]} | {q[5]} | {q[6]} | {q[7]} |' for q in QUICK]
    L += ['', 'Other engines: none of these models runs on a second engine here.', '']
    L += ['## 6. Trials (not router entries)', '']
    L += [f'- **{t[0]}** ({t[1]}, {t[2]}): {t[3]}. [Report]({GH}{t[4]}) **Trial, not for the website.**' for t in TRIALS]
    L += ['', '## 7. Hardware', ''] + [f'- {h}' for h in HARDWARE] + ['']
    return '\n'.join(L)


def main():
    live = live_routes()
    mine = {r[0]: r[3] for r in ROUTES}
    if live != mine:
        sys.exit(f'Route list differs from the live registry: missing {sorted(set(live) - set(mine))}, extra {sorted(set(mine) - set(live))}, '
                 f'context {[k for k in live if k in mine and live[k] != mine[k]]}')
    assert set(SPEED) == set(mine)
    assert {r[0] for r in TOOLUSE} == set(mine), 'every enabled route needs a short tool-use row'
    text = render()
    if '--check' in sys.argv:
        sys.exit(0 if OUT.exists() and OUT.read_text() == text else 'docs/WEBSITE-SUMMARY.md is out of date')
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(text)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
