# Short tool-use test on all nine routes — November 24, 2026

**Owner, November 24:** "Use the short tool-use test as the ranking" (the NVIDIA server's test), then "Rebuild it on AMD". This page is the first AMD run on that standard. It replaces the 216-item public suite as the quality ranking; the 216-item results stay in [current results](CURRENT-AMD-BENCHMARKS.md) as the old standard.

## Ranking

| Rank | Route | Engine (at the run) | Score /100 | Single-turn /40 | Episodes /9 | Episodes /15 (large) | Load s | Items min | Coverage |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `qwen3.8-27b-sglang-dflash2` | SGLang TP2 `f84475ccf593` | 74.6 | 33 | 6 | — | 80 | 3.2 | complete |
| 2 | `glm-5.3-flash-maya` | Maya 1.1.73 | 72.1 | 31 | 6 | 9 (68.8) | 151 | 35.2 | complete |
| 3 | `qwen3.8-27b-vllm` | vLLM TP2 0.33.0rc1 | 71.5 | 35 | 5 | — | 45 | 3.5 | complete |
| 4 | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek `13eedf552417` | 64.0 | 29 | 5 | 5 of 11 run (52.9) | 72 | 56.0 | core complete; 4 extra episodes cut |
| 5 | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya 1.1.73 | 62.2 | 32 | 4 | 5 of 13 run (56.7) | 70 | 56.0 | core complete; 2 extra episodes cut |
| 5 | `ripple-65b-vllm` | vLLM TP2 0.33.0rc1 | 62.2 | 32 | 4 | 5 (56.7) | 121 | 35.3 | complete |
| 7 | `inkling-2-mini-sq-20-strata-2gpu` | Strata 0.2.20 `strata-inkling` | 60.4 | 35 | 3 | — | 58 | 10.0 | complete |
| 8 | `qwen3.8-flash-next-iq3_xxs` | Strata 0.2.20 | 52.9 | 29 | 3 | — | 149 | 9.1 | complete |
| 9 | `kolibri-1.1-iq4_xs` | llama.cpp PR 32891 `5f4d222898dd` | 45.6 | 32 | 1 | — | 85 | 2.7 | complete |

- **Score** = 50 × single-turn correct / 40 + 50 × core multi-turn episodes passed / 9. Every route ran all 40 single-turn items and all 9 core episodes, with no per-item timeout, so every score is complete and comparable.
- **Large group** (SSD-streamed models and Ripple) also ran six extra episodes; the figure in brackets is the 15-episode score (50 × single / 40 + 50 × episodes / 15, unrun episodes counted as not passed). Both DeepSeek routes reached the 56-minute item budget before the last extra episodes; that does not touch the ranking score.
- **How far apart:** one episode moves the score by 5.6 points and one single-turn item by 1.25. With 9 episodes, routes a few points apart are not separated; no significance test was run.
- The NVIDIA server's ranking uses the same method, seed and score, but these items were drawn again from BFCL v4 and none of the 55 matches NVIDIA's frozen list (checked November 26). Compare ranks within one machine only. **Since November 26 the test uses NVIDIA's items** ([shared benchmarks](../benchmarks/shared/README.md)); the scores on this page are from the old items until the routes are rerun.

## By pool

Correct / scored. Single-turn: parallel calls (15), irrelevance (15: the right answer is no call), simple (10). Multi-turn episodes: base, missing parameter, missing function (core 3 each; the large group runs 5 each).

| Route | Parallel | Irrelevance | Simple | MT base | MT miss param | MT miss func |
|---|---:|---:|---:|---:|---:|---:|
| `qwen3.8-27b-sglang-dflash2` | 13 | 11 | 9 | 3/3 | 2/3 | 1/3 |
| `glm-5.3-flash-maya` | 14 | 7 | 10 | 3/5 | 3/5 | 3/5 |
| `qwen3.8-27b-vllm` | 14 | 11 | 10 | 2/3 | 1/3 | 2/3 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 13 | 6 | 10 | 3/4 | 1/4 | 1/3 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 14 | 8 | 10 | 2/5 | 1/4 | 2/4 |
| `ripple-65b-vllm` | 14 | 8 | 10 | 3/5 | 1/5 | 1/5 |
| `inkling-2-mini-sq-20-strata-2gpu` | 13 | 12 | 10 | 1/3 | 2/3 | 0/3 |
| `qwen3.8-flash-next-iq3_xxs` | 12 | 7 | 10 | 1/3 | 2/3 | 0/3 |
| `kolibri-1.1-iq4_xs` | 11 | 13 | 8 | 1/3 | 0/3 | 0/3 |

- Simple calls are near the ceiling for every route. The spread comes from irrelevance (the large mixture-of-experts models call a tool when none fits) and from the multi-turn episodes.
- Kolibri declines irrelevant requests best (13/15) but passes one episode of nine; Inkling and Qwen3.8-27B vLLM have the most single-turn items right (35/40).
- **Added November 25:** Hy4-Flash SQ-64 ran the same test on a Strata 0.2.21.1 side server on November 24 (large group, same items and settings): 72.1 (31/40, 6/9; 7 of 15 episodes, 62.1). It became the hub route `hy4-flash-sq-64-strata` on November 25 and ranks second, tied with GLM ([report](HY4-FLASH-RETRY-2026-11-24.md)).

## Method

- **Items:** BFCL v4 (`ShishirPatil/gorilla` at `6ea57973c7a6`, Apache-2.0): parallel 15, irrelevance 15, simple_python 10, multi_turn_base / miss_param / miss_func 5 each. Each pool's eligible rows are ranked by sha256 of `20261122|pool|id` and the first N taken, never looking at results. Small group: 40 single-turn items and 9 core episodes; large group: 6 more episodes. Item ids and hashes: [manifest](quant-eval/tooluse/fast_amd/manifest.json).
- **Requests:** through the hub, one at a time, temperature 0.6, top_p 0.95, max_tokens 2,048, seed 20261122, no system prompt, thinking as each route serves it, tools in OpenAI function format.
- **Grading:** single-turn calls must match BFCL's answer exactly (names, arguments, count); an irrelevance item passes only with a plain text answer and no call. Episodes run BFCL's multi-turn FC loop (20-step limit, held-back functions added at their turn) against BFCL's own environment classes and are graded with BFCL's multi-turn checker, vendored unchanged.
- **Limits:** load cap 300 s (the NVIDIA method uses 180 s; the streamed models need more from a cold start), 120 s per single-turn item, 480 s per episode (a per-item timeout scores wrong; none happened), item budget 690 s small / 3,360 s large. An item cut by the budget is left out and recorded in the coverage column.
- **Guards:** no GPU hold, no build, no game, CPU at or below 60 °C before each route, and the hub serving nobody else.
- **Times:** load from a cold start; items minutes include the large models' streaming from SSD. These are not speed benchmarks.
- **Code and how to rerun:** [quant-eval/tooluse](quant-eval/tooluse/README.md). Machine-readable scores: [results/tooluse-short-2026-11-24.json](results/tooluse-short-2026-11-24.json). Per-item model replies stay in the private stage folder.

## What it does not show

Speed, long-context quality, coding or general knowledge. It is a short check of calling the right tool with the right arguments, declining when no tool fits, and finishing multi-step tool tasks. The scores stay tied to the engine in the second column; a later engine update does not rerun them (owner rule: existing routes are not retested).
