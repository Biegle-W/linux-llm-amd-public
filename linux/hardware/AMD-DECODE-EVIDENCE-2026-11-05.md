# AMD native decode evidence — November 5, 2026

**Native decoding statistics were recovered for 9 of the 13 current routes from their saved AMD logs. Four routes have no recoverable native per-request figure. No inference was rerun.** The earlier current-route summaries exported load, TTFT, request wall time and token counts but omitted these available native timing lines; those latency fields are not decode throughput.

| Current setup | First request native t/s | Tool-result follow-up native t/s | Native generated tokens, first / follow-up |
|---|---:|---:|---:|
| DeepSeek Coder IQ2_XXS / Maya | 20.32 | 15.84 | 114 / 16 |
| DeepSeek Unsloth Q1 / Maya | 3.39 | 1.21 | 113 / 16 |
| DeepSeek Coder IQ2_XXS / Strata | 5.76 | 14.19 | 84 / 15 |
| DeepSeek Unsloth Q1 / Strata | 1.80 | 6.72 | 85 / 15 |
| Empero Qwen3.8 35B-A3B / llama.cpp | 157.16 | 153.85 | 64 / 20 |
| Flint 40B-A2.5B / llama.cpp | 57.36 | 57.74 | 176 / 106 |
| GLM 5.3 Flash / Maya | 0.64 | 2.57 | 60 / 15 |
| Nemotron Bolt / vLLM | Not captured | Not captured | — |
| Ornith 1.5 122B / llama.cpp | 11.10 | 11.72 | 92 / 19 |
| Qwen3.8 27B DFlash2 / SGLang | Not captured | Not captured | — |
| Qwen3.8 27B / vLLM | Not captured | Not captured | — |
| Qwen Flash Next GSQ IQ3_XXS / Strata | 57.10 | 59.20 | 63 / 20 |
| Sage A1.5 / vLLM | Not captured | Not captured | — |

These are two short functional tool requests per route, not sustained benchmarks or a matched performance ranking. The first request emits a tool call; the second follows its result and may reuse cache. Output lengths, reasoning, MTP and native timing definitions differ. Rates describe generated engine tokens, including reasoning where applicable, rather than visible prose alone. GLM reports its own decode-ms/token statistic; llama.cpp excludes the first generated token from its eval-rate denominator. Other native rates use generated tokens divided by logged decode duration. Keep these definitions with the numbers.

## Source binding and missing evidence

The recovered Maya rows match the selected `c1670044bbc0` checks; llama.cpp rows match `9c9074e14e02`; Strata rows match the retained `ffa80d73133e` route checks. First-request prompt/generated counts were checked against saved request results where the native log supplies them. GLM's final two request completion counts are 60/15 and match its two native decode-stat records. The exact model IDs, source revisions, engine definitions, generated counts and available native durations are recorded in the numeric evidence. Raw logs and private machine paths are not exported.

For Qwen/vLLM, Qwen/SGLang, Sage/vLLM and Bolt/vLLM, successful short requests exist but a trustworthy native per-request decode number was not captured or retained in the inspected evidence. A missing figure is not zero. Periodic average throughput, prefill throughput and `output_tokens / total_request_time` are not substituted for native decoding speed. A complete 13-route sustained decode benchmark remains missing.

## Existing separate speed probes

The previously published Strata 0.2.11/engine+Control 0.1.57 test with unselected Unsloth V3.1 already contains three native speed-probe rates: **52.895, 54.738 and 50.080 tokens/s**, with median **52.895 tokens/s**. They are explicitly present in `summary.median_native_decode_tokens_per_second` and `fixed_probe_rows` of [its numeric result](results/STRATA-0211-UNSLOTH-2026-11-05.json). The [November 4 Unsloth/Flint comparison](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md) also contains native rates, on its pinned historical sources and short bracket workloads. Neither replaces a sustained current-source benchmark across all routes.

The latest [Flint AWQ/PLE/Super candidate attempts](CANDIDATE-RETESTS-2026-11-05.md) completed zero inference requests; their lack of decode rates is an actual measurement gap, not an omitted timing export. CPU builds and startup-only failures likewise provide no decode result.

[Decode numeric evidence](results/AMD-DECODE-EVIDENCE-2026-11-05.json) · [Current route latency measurements](REALISTIC-LARGE-MODELS-2026-11-05.md)
