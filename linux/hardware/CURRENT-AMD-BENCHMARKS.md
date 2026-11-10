# Current AMD results — November 9, 2026

One row per enabled route, all from the [November 9 rerun](AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.md). Every number comes from a short guarded check or the graded quality suites; none is a sustained or full-context benchmark. Older results are in the [benchmark history](BENCHMARK-HISTORY.md) and the [changelog](CHANGELOG.md).

| Route | Engine | Tool call | Decode tok/s | Prompt read tok/s | Load s | 54-item suite | 64-item suite |
|---|---|---|---:|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | llama.cpp | passed | 173.3 | 2,893 | 47.7 | 53 | 62 |
| `flint-40b-a2.5b` | llama.cpp | passed | 64.0 | 4,653 | 50.7 | 51* | 62* |
| `ornith-1.5-122b` | llama.cpp | passed | 11.6 | 602 | 167.9 | 53 | 62 |
| `qwen3.8-27b-vllm` | vLLM TP2 | passed | 155.1 | 1,766 | 89.5 | 52 | 62 |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | passed | 211.2 | 1,736 | 34.4 | 52 | 62 |
| `nemotron-3.5-bolt-vllm` | vLLM | passed | 40.1 | 1,963 | 219.4 | 52 | 61 |
| `sage-a1.5` | vLLM | passed | 140.0 | 5,619 | 88.5 | 51 | 61 |
| `ripple-65b-vllm` | vLLM TP2 | passed | 28.0 | 764 | 117.6 | 53* | 63* |
| `qwen3.8-flash-next-iq3_xxs` | Strata | passed | 66.3 | 710 | 69.5 | 51 | 62 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | passed | 5.6 (7.5–10.1†) | 111 | 140.1 | 54 | 62 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | passed | 6.8 (9.5–17.1†) | 35 | 72.7 | 54 | 63 |
| `glm-5.3-flash-maya` | Maya | passed‡ | 5.2 (17.8–22.1†) | 57 | 119.0 | 53 | 62 |

How to read it:
- **Tool call:** one DSH read-tool round trip with about 6.4K prompt tokens and 25 tool definitions, under the guarded harness ([standard](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md)).
- **Decode** is measured on that short tool-call answer (54–171 tokens). **Prompt read** is that prompt divided by time to first token, from a cold start.
- **Suites:** the 54-item suite and the harder 64-item suite from the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md), through the hub at temperature 0 with thinking off.
- \* Flint and Ripple scores are from the [November 10 rerun](FLINT-RIPPLE-BUDGET-RERUN-2026-11-10.md) with every answer budget raised to at least 4,096 tokens. Both keep reasoning with thinking off, so under the suites' 60-token short-answer limit they returned empty answers and scored 43 and 36 (Flint) and 50 and 56 (Ripple) on November 9. Give these two routes about a thousand answer tokens.
- † 400-token answers through the hub on November 8 ([report](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md)).
- ‡ GLM ran with a 30 s watchdog heartbeat instead of 6 s (owner choice), because its expert warm-up stalls disk writes on the system drive.
- Machine-readable results: [results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json](results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json).

Not measured yet: a sustained, matched benchmark across all 12 routes, thinking mode, and full-context quality.
