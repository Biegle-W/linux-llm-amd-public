# AMD native decode evidence — November 5, 2026

**All13 current routes now have short per-request native decoding statistics:** nine recovered from saved logs and four newly captured by owner-requested tests. A sustained, matched current-source benchmark across all13 remains missing. Native engine definitions, output lengths, reasoning, speculation and cache conditions differ, so this is not a performance ranking.

| Current route | First tool request native t/s | Follow-up native t/s | Evidence |
|---|---:|---:|---|
| `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | 20.32 | 15.84 | Recovered saved native statistic |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 3.39 | 1.21 | Recovered saved native statistic |
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | 5.76 | 14.19 | Recovered saved native statistic |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 1.80 | 6.72 | Recovered saved native statistic |
| `empero-qwen3.8-35b-a3b` | 157.16 | 153.85 | Recovered saved native statistic |
| `flint-40b-a2.5b` | 57.36 | 57.74 | Recovered saved native statistic |
| `glm-5.3-flash-maya` | 0.64 | 2.57 | Recovered saved native statistic |
| `nemotron-3.5-bolt-vllm` | 37.22 | 37.38 | New native capture |
| `ornith-1.5-122b` | 11.10 | 11.72 | Recovered saved native statistic |
| `qwen3.8-27b-sglang-dflash2` | 238.52 | 170.91 | New native capture |
| `qwen3.8-27b-vllm` | 145.60 | 124.81 | New native capture |
| `qwen3.8-flash-next-iq3_xxs` | 57.10 | 59.20 | Recovered saved native statistic |
| `sage-a1.5` | 136.53 | 136.69 | New native capture |

The first request emits a tool call and the second follows its result. GLM uses its engine-reported decode statistic; llama.cpp excludes the first generated token from its eval-rate denominator. Strata/Maya native generation records use their reported decode interval. New vLLM/SGLang records use native first/last-token or scheduler timestamps, not SSE/client throughput. The new tests also add three fixed128-token speed prompts per route; [methods, individual samples, guards and the SGLang collector correction](AMD-NATIVE-DECODE-TESTS-2026-11-05.md) remain explicit.

The recovered Maya rows match selectedc167004, llama.cpp rows match9c9074 and Strata rows matchffa80d7. The separate unselected Unsloth/Strata0.2.11 test retains its52.895tokens/s median; historical November4 Unsloth/Flint brackets retain their pinned source/workload limits. Failed CPU/startup-only cases produced no decode rate.

[All13 decode numeric evidence](results/AMD-DECODE-EVIDENCE-2026-11-05.json) · [New four-route native test results](results/AMD-NATIVE-DECODE-TESTS-2026-11-05.json) · [Current inventory and latency results](REALISTIC-LARGE-MODELS-2026-11-05.md)
