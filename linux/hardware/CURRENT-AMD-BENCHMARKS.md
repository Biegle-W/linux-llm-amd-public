# Current AMD results — November 11, 2026

One row per enabled route, from the [November 9 rerun](AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.md) and the [November 10–11 public-benchmark suite](PUBLIC-QUALITY-SUITE-2026-11-11.md). Every number comes from a short guarded check or the graded quality suites; none is a sustained or full-context benchmark. Older results are in the [benchmark history](BENCHMARK-HISTORY.md) and the [changelog](CHANGELOG.md).

| Route | Engine | Tool call | Decode tok/s | Prompt read tok/s | Load s | 54-item suite | 64-item suite | Public suite (216) | Quality rank |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | llama.cpp | passed | 173.3 | 2,893 | 47.7 | 53 | 62 | 151 | 6 |
| `qwen3.8-27b-vllm` | vLLM TP2 | passed | 155.1 | 1,766 | 89.5 | 52 | 62 | 157 | 5 |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | passed | 211.2 | 1,736 | 34.4 | 52 | 62 | 163 | 4 |
| `nemotron-3.5-bolt-vllm` | vLLM | passed | 40.1 | 1,963 | 219.4 | 52 | 61 | 143 | 7 |
| `ripple-65b-vllm` | vLLM TP2 | passed | 28.0 | 764 | 117.6 | 53* | 63* | 134§ | 9 |
| `qwen3.8-flash-next-iq3_xxs` | Strata | passed | 66.3 | 710 | 69.5 | 51 | 62 | 164 | 3 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | passed | 5.6 (7.5–10.1†) | 111 | 140.1 | 54 | 62 | 169¶ | 1 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | passed | 6.8 (9.5–17.1†) | 35 | 72.7 | 54 | 63 | 168 | 2 |
| `glm-5.3-flash-maya` | Maya | passed‡ | 5.2 (17.8–22.1†) | 57 | 119.0 | 53 | 62 | 136 | 8 |

How to read it:
- **Tool call:** one DSH read-tool round trip with about 6.4K prompt tokens and 25 tool definitions, under the guarded harness ([standard](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md)).
- **Decode** is measured on that short tool-call answer (54–171 tokens). **Prompt read** is that prompt divided by time to first token, from a cold start.
- **Suites:** the 54-item suite and the harder 64-item suite from the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md), through the hub at temperature 0 with thinking off.
- \* Ripple's scores are from the [November 10 rerun](FLINT-RIPPLE-BUDGET-RERUN-2026-11-10.md) with every answer budget raised to at least 4,096 tokens. It keeps reasoning with thinking off, so under the suites' 60-token short-answer limit it returned empty answers and scored 50 and 56 on November 9. Give this route about a thousand answer tokens.
- **Quality rank:** position by public-suite score; see [Quality ranking](#quality-ranking) for which differences are real.
- **Public suite:** correct answers out of 216 items sampled from MMLU-Pro, MATH-500, AIME, BigCodeBench, IFEval, BFCL and MuSR ([report](PUBLIC-QUALITY-SUITE-2026-11-11.md)). The 95% interval is about ±6 points (±13 items); the top four routes are not separated.
- § 65 of Ripple's 216 answers were cut off by the 2,048–4,096-token limit while still reasoning.
- ¶ DeepSeek on Strata, measured November 12 with its RAM store turned off (`--ssd-cache 0`): all 216 items answered, no NaN error ([report](STRATA-DEEPSEEK-NO-RAM-STORE-2026-11-12.md)). With the 36 GB RAM store on, three earlier attempts stopped on NaN errors (after 4 items, after 88 with 5 errors, and after 17 when the server's kernel crashed). The decode, prompt-read and load figures in this row were measured with the store on and have not been re-measured; the suite ran at 8.6 tok/s end to end with the store off, against 7.4 with it on.
- † 400-token answers through the hub on November 8 ([report](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md)). Strata DeepSeek measured the same way after the November 11 engine update: 4.2 for the first answer after load, then 8.0–10.2; prompt read 119–132 tok/s with one sample at 63 ([results](results/strata-dsv41-speed-2026-11-11.json)).
- ‡ GLM ran with a 30 s watchdog heartbeat instead of 6 s (owner choice), because its expert warm-up stalls disk writes on the system drive.
- Machine-readable results: [results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json](results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json), [results/public-quality-suite-2026-11-11.json](results/public-quality-suite-2026-11-11.json).

## Quality ranking

Ranked by correct answers on the 216-item public suite, the only quality test here that spreads the routes out. The 54- and 64-item suites do not rank them: all nine routes score 51–54 and 61–63.

| Rank | Route | Correct / 216 | Score | 95% interval | Cut off | Code /20 | Instructions /32 | Knowledge /60 | Math /40 | Reasoning /32 | Tools /32 | Measurably better than |
|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 169 | 78.2% | 72.3–83.2% | 13 | 13 | 29 | 49 | 32 | 19 | 27 | not tested |
| 2 | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 168 | 77.8% | 71.8–82.8% | 13 | 12 | 28 | 51 | 29 | 22 | 26 | Nemotron, GLM, Ripple |
| 3 | `qwen3.8-flash-next-iq3_xxs` | 164 | 75.9% | 69.8–81.1% | 20 | 12 | 30 | 47 | 31 | 22 | 22 | GLM, Ripple |
| 4 | `qwen3.8-27b-sglang-dflash2` | 163 | 75.5% | 69.3–80.7% | 21 | 8 | 31 | 47 | 32 | 18 | 27 | Ripple |
| 5 | `qwen3.8-27b-vllm` | 157 | 72.7% | 66.4–78.2% | 26 | 10 | 28 | 45 | 31 | 19 | 24 | Ripple |
| 6 | `empero-qwen3.8-35b-a3b` | 151 | 69.9% | 63.5–75.6% | 12 | 11 | 25 | 47 | 24 | 16 | 28 | — |
| 7 | `nemotron-3.5-bolt-vllm` | 143 | 66.2% | 59.7–72.2% | 13 | 7 | 23 | 46 | 30 | 15 | 22 | — |
| 8 | `glm-5.3-flash-maya` | 136 | 63.0% | 56.3–69.1% | 0 | 10 | 25 | 43 | 11 | 21 | 26 | — |
| 9 | `ripple-65b-vllm` | 134 | 62.0% | 55.4–68.2% | 65 | 5 | 17 | 42 | 32 | 14 | 24 | — |

- **Ranks 1–5 are a tie.** No difference among DeepSeek on Strata, DeepSeek on Maya, Flash-Next and the two Qwen3.8-27B routes is statistically detected. The same holds among ranks 6–9.
- **Measurably better than** lists the routes a route beats on the paired test (exact McNemar, Holm-corrected over the 55 pairs of the eleven routes scored on November 11, before three were removed). An empty cell means the suite cannot tell the route from any route below it.
- **Cut off** counts answers that hit the 2,048–4,096-token limit and were scored wrong. Ripple (65) is held down by this; its rank is a lower bound.
- DeepSeek on Strata uses the same weights as DeepSeek on Maya and scores the same: 169 against 168, with 158 items right on both, 11 only on Strata and 10 only on Maya. It was scored on November 12, after the other routes, so it is not in the paired test behind the last column.
- **Removed November 11 (owner request):** `ornith-1.5-122b` (146, rank 6 of 11), `sage-a1.5` (142, rank 8) and `flint-40b-a2.5b` (121, rank 11). Ranks here are renumbered among the remaining routes; the removed routes' results stay in the report.
- One attempt per item, temperature 0, thinking off. Details and per-pair numbers: [report](PUBLIC-QUALITY-SUITE-2026-11-11.md).
Not measured yet: a sustained, matched benchmark across all 9 routes, thinking mode, and full-context quality.
