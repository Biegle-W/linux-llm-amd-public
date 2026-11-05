# AMD native decode evidence — November 5, 2026

**All14 current routes now have short per-request native decoding statistics:** nine recovered from saved logs and five newly captured by owner-requested tests. A sustained, matched current-source benchmark across all14 remains missing. Native engine definitions, output lengths, reasoning, speculation and cache conditions differ, so this is not a performance ranking.

| Execution mode | Engine | Exact weights / API route | First native t/s | Follow-up native t/s |
|---|---|---|---:|---:|
| VRAM only | llama.cpp | Empero Qwen3.8-35B-A3B IQ4_XS / `empero-qwen3.8-35b-a3b` | 157.16 | 153.85 |
| VRAM only | llama.cpp | Flint-40B-A2.5B Unsloth UD-Q4_K_XL / `flint-40b-a2.5b` | 57.36 | 57.74 |
| VRAM only | SGLang | Qwen3.8-27B AutoRound W4A16 GPTQ; DFlash2 auxiliary / `qwen3.8-27b-sglang-dflash2` | 238.52 | 170.91 |
| VRAM only | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 / `nemotron-3.5-bolt-vllm` | 37.22 | 37.38 |
| VRAM only | vLLM | Qwen3.8-27B AutoRound W4A16 GPTQ; shared main weights / `qwen3.8-27b-vllm` | 145.60 | 124.81 |
| VRAM only | vLLM | Sage-A1.5 AutoRound W4A16 / `sage-a1.5` | 136.53 | 136.69 |
| CPU RAM offload | llama.cpp | Ornith-1.5-122B Q4_K_M; CPU experts + VRAM cache / `ornith-1.5-122b` | 11.10 | 11.72 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing / `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | 20.32 | 15.84 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing / `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 3.39 | 1.21 |
| SSD streaming | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS; RAM/VRAM tiers / `glm-5.3-flash-maya` | 0.64 | 2.57 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing + RAM store / `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | 5.76 | 14.19 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing +36GB store / `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 1.80 | 6.72 |
| SSD streaming | Strata | Qwen3.8-Flash-Next GSQ IQ3_XXS; RAM/VRAM expert caches / `qwen3.8-flash-next-iq3_xxs` | 57.10 | 59.20 |
| SSD streaming | Strata | Qwen3.8-Flash-Next Unsloth UD-IQ1_M Dynamicv3.1; RAM/VRAM caches / `qwen3.8-flash-next-unsloth-iq1_m` | 59.10 | 63.60 |

The first request emits a tool call and the second follows its result. GLM uses its engine-reported decode statistic; llama.cpp excludes the first generated token from its eval-rate denominator. Strata/Maya native generation records use their reported decode interval. New vLLM/SGLang records use native first/last-token or scheduler timestamps, not SSE/client throughput. The new tests also add three fixed128-token speed prompts per route; [methods, individual samples, guards and the SGLang collector correction](AMD-NATIVE-DECODE-TESTS-2026-11-05.md) remain explicit.

The recovered Maya rows match selectedc167004, llama.cpp rows match9c9074 and Strata rows matchffa80d7. The separate unselected Unsloth/Strata0.2.11 test retains its52.895tokens/s median; historical November4 Unsloth/Flint brackets retain their pinned source/workload limits. Failed CPU/startup-only cases produced no decode rate.

[All13 decode numeric evidence](results/AMD-DECODE-EVIDENCE-2026-11-05.json) · [New four-route native test results](results/AMD-NATIVE-DECODE-TESTS-2026-11-05.json) · [Current inventory and latency results](REALISTIC-LARGE-MODELS-2026-11-05.md)

[New IQ1_M qualification](STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md): three short speed probes median57.140native tokens/s; all prior13routes retained.
