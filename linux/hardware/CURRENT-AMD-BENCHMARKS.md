# Current AMD results — November 8, 2026

One row per enabled route, with the latest measurement at the current settings. Every number comes from a short guarded check; none is a sustained or full-context benchmark. Older results are in the [benchmark history](BENCHMARK-HISTORY.md) and the [changelog](CHANGELOG.md).

| Route | Engine | Decode tok/s | Prompt read tok/s | Load s | Quality (graded suite) | Source |
|---|---|---:|---:|---:|---|---|
| `empero-qwen3.8-35b-a3b` | llama.cpp | 174.5 | 2,874 (7K) | 46.7 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `flint-40b-a2.5b` | llama.cpp | 64.8 | 4,980 (6.5K) | 50.7 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `ornith-1.5-122b` | llama.cpp | 11.3 | 651 (7K) | 151.9 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `qwen3.8-27b-vllm` | vLLM TP2 | 153.7 | 1,723 (7K) | 89.5 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | 218.6 | 1,741 (7.4K) | 34.4 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `nemotron-3.5-bolt-vllm` | vLLM | 29.6 | 2,092 (7.7K) | 224.4 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `sage-a1.5` | vLLM | 136.5 | 5,698 (7K) | 113.0 | — | [Nov 7](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| `ripple-65b-vllm` | vLLM TP2 | 28–29 | ~755 (8K) | — | 12/12 known-answer | [Nov 7](RIPPLE-65B-VLLM-2026-11-07.md) |
| `qwen3.8-flash-next-iq3_xxs` | Strata | 50.2–52.4 | 777–821 (5.5K) | 96.8 | 53/54; 62/64 harder | [Nov 8](QWEN-IQ3-UNSLOTH-VS-GSQ-2026-11-08.md) |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | 7.5–10.1 | 120 (4.8K) | 57–157 | 64/64 harder (one NaN event in an earlier run) | [Nov 8](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md) |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | 9.5–17.1 | 125 (4.8K) | 133 | 64/64 harder | [Nov 8](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md) |
| `glm-5.3-flash-maya` | Maya | 17.8–22.1 | 396 (4.9K) | 83 | 62/64 harder | [Nov 8](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md) |

How to read it:
- November 7 rows: one DSH read-tool round trip with about 7K prompt tokens and 25 tool definitions. Decode is measured on a short tool-call answer.
- November 8 rows: two 400-token answers (cold, then warm) and a 4.8–5.5K-token document prompt through the hub.
- Quality: the 54-item and harder 64-item suites from the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md), at temperature 0 with thinking off.
- Machine-readable results are in [results/](results/README.md).

Not measured yet: a sustained, matched benchmark across all 12 routes, and full-context quality.
