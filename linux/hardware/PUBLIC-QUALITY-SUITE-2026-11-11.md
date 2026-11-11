# Public-benchmark quality suite on all routes — November 10–11, 2026

**Result:** eleven of the twelve routes answered a frozen 216-item sample drawn from six public benchmarks. DeepSeek on Maya scored highest (168/216, 77.8%), level with Flash-Next and both Qwen3.8-27B routes; the test cannot separate those four. Flint is lowest (121, 56.0%). Ripple and Sage lose many answers to the token limit, not to wrong answers. DeepSeek on Strata was not measured: it returned NaN errors after four items.

This is a harder test than the [54- and 64-item suites](CURRENT-AMD-BENCHMARKS.md), where every route scores 112–117 of 118. It spreads the routes out, but the sample is small: read the intervals, not the order.

## What was run

- **Items:** 216 core items for every route, plus 84 extra items for the eight routes faster than about 28 tok/s. Sampled once with a fixed seed (20261110) from pinned public dataset revisions and frozen before any model was run (item file SHA-256 `9c7929bf…6117de`).

| Category | Source | Core | Extra |
|---|---|---:|---:|
| knowledge | MMLU-Pro | 60 | 20 |
| math | MATH-500, AIME 2024 and 2025 | 40 | 20 |
| code | BigCodeBench | 20 | 8 |
| instruction | IFEval | 32 | 12 |
| tools | BFCL v4 | 32 | 12 |
| reasoning | MuSR | 32 | 12 |

- **Settings:** through the hub, temperature 0, thinking off, one attempt per item, no retries. Answer budget 2,048 tokens (knowledge, reasoning, tools, instruction), 3,072 (most math, code) or 4,096 (AIME).
- **Scoring:** an answer cut off by the token limit counts as wrong ("capped"). Code answers run against the benchmark's tests in a `bwrap` sandbox with no network and no home directory. Graders and statistics were written and self-tested before the run and not changed after it.
- **Statistics:** Wilson 95% interval per route; exact McNemar test on each pair of routes with Holm correction over all 55 pairs.
- **Harness:** [quant-eval/pub/](quant-eval/pub/README.md) ([design](quant-eval/pub/DESIGN.md)). The item file is rebuilt from the pinned sources by `build_items.py`; it is not stored in this repository.

## Core set (216 items)

| Route | Correct | Score | 95% interval | Capped | Malformed | Request time |
|---|---:|---:|---|---:|---:|---:|
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 168 | 77.8% | 71.8 – 82.8 | 13 | 1 | 198 min |
| `qwen3.8-flash-next-iq3_xxs` | 164 | 75.9% | 69.8 – 81.1 | 20 | 1 | 55 min |
| `qwen3.8-27b-sglang-dflash2` | 163 | 75.5% | 69.3 – 80.7 | 21 | 0 | 24 min |
| `qwen3.8-27b-vllm` | 157 | 72.7% | 66.4 – 78.2 | 26 | 1 | 28 min |
| `empero-qwen3.8-35b-a3b` | 151 | 69.9% | 63.5 – 75.6 | 12 | 0 | 15 min |
| `ornith-1.5-122b` | 146 | 67.6% | 61.1 – 73.5 | 3 | 3 | 132 min |
| `nemotron-3.5-bolt-vllm` | 143 | 66.2% | 59.7 – 72.2 | 13 | 1 | 39 min |
| `sage-a1.5` | 142 | 65.7% | 59.2 – 71.7 | 34 | 0 | 21 min |
| `glm-5.3-flash-maya` | 136 | 63.0% | 56.3 – 69.1 | 0 | 3 | 41 min |
| `ripple-65b-vllm` | 134 | 62.0% | 55.4 – 68.2 | 65 | 0 | 155 min |
| `flint-40b-a2.5b` | 121 | 56.0% | 49.4 – 62.5 | 6 | 1 | 19 min |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | not measured | | | | | |

No request failed on the eleven measured routes. Request time excludes model loads.

By category (correct of 60 / 40 / 20 / 32 / 32 / 32):

| Route | knowledge | math | code | instruction | tools | reasoning |
|---|---:|---:|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 51 | 29 | 12 | 28 | 26 | 22 |
| `qwen3.8-flash-next-iq3_xxs` | 47 | 31 | 12 | 30 | 22 | 22 |
| `qwen3.8-27b-sglang-dflash2` | 47 | 32 | 8 | 31 | 27 | 18 |
| `qwen3.8-27b-vllm` | 45 | 31 | 10 | 28 | 24 | 19 |
| `empero-qwen3.8-35b-a3b` | 47 | 24 | 11 | 25 | 28 | 16 |
| `ornith-1.5-122b` | 45 | 22 | 10 | 23 | 25 | 21 |
| `nemotron-3.5-bolt-vllm` | 46 | 30 | 7 | 23 | 22 | 15 |
| `sage-a1.5` | 45 | 24 | 9 | 24 | 22 | 18 |
| `glm-5.3-flash-maya` | 43 | 11 | 10 | 25 | 26 | 21 |
| `ripple-65b-vllm` | 42 | 32 | 5 | 17 | 24 | 14 |
| `flint-40b-a2.5b` | 31 | 13 | 10 | 26 | 20 | 21 |

Per-category samples are 20–60 items, so a single category differs reliably only when the gap is large.

## Which differences are real

After Holm correction, 15 of the 55 pairs differ:

- **DeepSeek (Maya)** is above Flint, Ripple, Sage, GLM and Nemotron.
- **Flash-Next** is above Flint, Ripple, Sage and GLM.
- **Qwen3.8-27B on SGLang** is above Flint, Ripple and Sage; **on vLLM** above Flint and Ripple.
- **Empero** is above Flint.

Everything else is unresolved, including the order inside the top four and between the two engines serving the same Qwen3.8-27B weights (163 vs 157; 17 and 16 items differ each way on the 300-item set).

## Fast routes with the extras (300 items)

| Route | Correct | Score | 95% interval | Capped |
|---|---:|---:|---|---:|
| `qwen3.8-flash-next-iq3_xxs` | 234 | 78.0% | 73.0 – 82.3 | 28 |
| `qwen3.8-27b-sglang-dflash2` | 227 | 75.7% | 70.5 – 80.2 | 32 |
| `qwen3.8-27b-vllm` | 226 | 75.3% | 70.2 – 79.9 | 37 |
| `empero-qwen3.8-35b-a3b` | 217 | 72.3% | 67.0 – 77.1 | 15 |
| `nemotron-3.5-bolt-vllm` | 208 | 69.3% | 63.9 – 74.3 | 17 |
| `sage-a1.5` | 200 | 66.7% | 61.2 – 71.8 | 48 |
| `ripple-65b-vllm` | 189 | 63.0% | 57.4 – 68.3 | 91 |
| `flint-40b-a2.5b` | 167 | 55.7% | 50.0 – 61.2 | 6 |

Same order as the core set. With 300 items Flint is also below Nemotron and Sage, and Ripple below Empero.

## Findings by route

- **DeepSeek (Maya):** best on knowledge (51/60) and never capped outside math and knowledge. It is also the slowest: 8.9 tok/s over the run, 3.3 hours of request time.
- **Flash-Next and Qwen3.8-27B:** strong everywhere except code; 20–26 answers each capped, mostly knowledge and math.
- **GLM:** 11/40 on math with no capped answers; it answers briefly (19K completion tokens for the whole set, against 68K–264K for the others) and gets the hard math wrong.
- **Ripple:** 65 of 216 answers capped, in every category but tools. It keeps reasoning with thinking off and ran out of 2,048–4,096 tokens. Where it finished it did well (math 32/40). Its score here measures the budget more than the model, as on [November 9](FLINT-RIPPLE-BUDGET-RERUN-2026-11-10.md).
- **Sage:** 34 capped, 16 of them on math.
- **Flint:** genuinely wrong answers on knowledge (31/60) and math (13/40), with only 6 capped. This differs from the easy suites, where a larger budget brought Flint level with the fleet.
- **Nemotron:** weakest on code (7/20) and reasoning (15/32).

## Deviations and limits

- **DeepSeek on Strata was not measured.** It answered four items, then returned three NaN errors and the run stopped it. It was not retried. This is the second NaN event on this route.
- **Power loss.** The server lost power about 80 minutes into the run, during the DeepSeek (Maya) pass. The run was resumed after restart; answers already saved (first attempts) were kept and no item was asked twice.
- **DeepSeek (Maya) ran as a separate pass** after the other routes, with the run's 20-hour limit raised to 30 hours for it. Because the grader's own 20-hour window had then closed, the final grading was run on a copy of the answer files without the run clock. The ten routes graded inside the window received identical grades both times.
- **Requests** had an 1,800-second limit and each route got one warm-up request before its items. No request hit the limit.
- **One BFCL item** (`parallel_multiple_165`) was excluded before freezing because its reference could not be graded reliably.
- **Strict answer format.** Five answers held the right result in a form the frozen grader rejects (GLM 3, Nemotron 1, Flash-Next 1). They stay scored as wrong; counting them would give GLM 139, Nemotron 144, Flash-Next 165.
- **Sandbox** protects the host from ordinary model-written code. It was not hardened against deliberately hostile code.
- **Not the official scores.** These are small samples with local prompts and graders, so numbers are not comparable with published leaderboard results. Models may have seen these public items in training.
- **Not covered:** thinking mode, multi-turn agent work, long context, repeat-run variation.

Machine-readable: [results/public-quality-suite-2026-11-11.json](results/public-quality-suite-2026-11-11.json).

## How it was built

Designed and built by a council of agents with Claude as chair: Gemini 4 Argon (survey of public benchmarks), Kimi K3.1 Pro (verification, red-team and final review), GPT-6.1 Sol through two members (design, item builder, grader, analysis, self-tests, sandbox) and Claude Opus 5.5 (runner). The chair checked member work before use, ran the test, and read a sample of wrong, capped, malformed and tool-call answers from every route against the references before accepting the grades.
