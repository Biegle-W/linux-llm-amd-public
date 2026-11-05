# AMD native per-request decode tests — November 5, 2026

All four previously missing selected routes now have native timing records. Each route completed a strict two-step read-tool check and three fixed128-token speed prompts. Every native record was paired with its completed API request and checked for matching input/generated token counts. **These are short probe measurements, not a sustained or full-context benchmark.** No selected profile, model, engine, Torch/ROCm, guard, boot default or schedule was changed.

| Selected route | Context | First tool request native t/s | Follow-up native t/s | Three speed prompts: median native t/s | Speed range |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 27B / vLLM | 163,840 | 145.60 | 124.81 | 102.45 | 98.41–111.33 |
| Qwen3.8 27B DFlash2 / SGLang | 163,840 | 238.52 | 170.91 | 103.29 | 95.68–130.50 |
| Sage A1.5 / vLLM | 65,536 | 136.53 | 136.69 | 157.39 | 150.45–157.53 |
| Nemotron Bolt / vLLM | 262,144 | 37.22 | 37.38 | 37.63 | 37.58–37.74 |

## Native measurement method and limits

vLLM uses its existing `FinishedRequestStats`: decode time is the monotonic engine-core interval from the first NEW_TOKEN event to the last NEW_TOKEN event; throughput is `(generated_tokens−1)/decode_time`, matching its native mean-time-per-output-token definition. SGLang uses TP0 scheduler `prefill_finished_time` through `last_decode_finish_time` with the same token denominator. SGLang's selected DFlash2, Qwen/Sage MTP3, native KV/context sizes and Bolt's selected global runtime were retained. Speculative multi-token steps, caches and engine definitions affect interpretation; these rates are not pure GPU-kernel timing or a controlled cross-model ranking.

Timing observers were isolated import-time wrappers that recorded already-computed native fields after the original methods ran and preserved their return values. Installed engine source was not edited. CPU contracts checked arithmetic and wrapper behavior before GPU use. Three identical synthetic speed-message fixtures were reused from the completed Strata test, with temperature0, seed7 and a128-token cap. Loading is separate from request TTFT. Prompt-message hashes, native durations, tokens, client latencies and resource maxima are in the numeric results. No private log path or client data is exported.

The first SGLang attempt completed both strict tool steps, then a collector bug concatenated a nullable SSE text field during the first speed prompt. Its failed record and clean owned teardown were retained. The collector fix passed a nullable-field CPU regression check. A separate guarded speed-only continuation completed the three prompts; the passed strict tool steps were not repeated. Native startup warmups and the cancelled14-token partial prompt were excluded, using exact per-request input/output counts. The final SGLang speed stage passed; the original harness-failure guard status remains explicit in the numeric evidence.

The current six-second heartbeat,15-second cleanup,100°C thermal/storage policy,1GiB host and128MiB per-card live floors, zero-spill protection, physical-RAM hard caps and phase-aware swap stayed active. The three-second decode cutoff remains removed. Actual owned swap/spill maxima and cleanup results are recorded per case; no guard was relaxed for a pass. Requests were serialized under owned GPU/heavy-I/O/queue locks. No passed prior model or graphics case was replayed for documentation.

Bolt logged inference-time Triton JIT compilation for checkpoint-store and fused-MoE kernels. All measured samples were retained; the short probes do not establish controlled warm-cache or steady-state throughput.

## Individual native records

### Qwen3.8 27B / vLLM

| Request | Input tokens | Generated tokens | Native decode seconds | Native tokens/s | Client TTFT seconds |
|---|---:|---:|---:|---:|---:|
| tool-1 | 5901 | 61 | 0.412085 | 145.601 | 3.387 |
| tool-2 | 6069 | 19 | 0.144214 | 124.814 | 0.234 |
| speed-1 | 31 | 128 | 1.290471 | 98.414 | 0.109 |
| speed-2 | 34 | 128 | 1.140717 | 111.334 | 0.121 |
| speed-3 | 33 | 128 | 1.239674 | 102.446 | 0.125 |

### Qwen3.8 27B DFlash2 / SGLang

| Request | Input tokens | Generated tokens | Native decode seconds | Native tokens/s | Client TTFT seconds |
|---|---:|---:|---:|---:|---:|
| tool-1 | 6177 | 61 | 0.251548 | 238.523 | 3.592 |
| tool-2 | 6345 | 19 | 0.105316 | 170.914 | 0.282 |
| speed-1 | 31 | 128 | 1.229491 | 103.295 | 0.134 |
| speed-2 | 34 | 128 | 0.973205 | 130.497 | 0.141 |
| speed-3 | 33 | 128 | 1.327385 | 95.677 | 0.129 |

### Sage A1.5 / vLLM

| Request | Input tokens | Generated tokens | Native decode seconds | Native tokens/s | Client TTFT seconds |
|---|---:|---:|---:|---:|---:|
| tool-1 | 5894 | 61 | 0.439463 | 136.530 | 1.064 |
| tool-2 | 6063 | 20 | 0.139004 | 136.687 | 0.212 |
| speed-1 | 31 | 128 | 0.806186 | 157.532 | 0.104 |
| speed-2 | 34 | 128 | 0.806938 | 157.385 | 0.106 |
| speed-3 | 33 | 128 | 0.844117 | 150.453 | 0.490 |

### Nemotron Bolt / vLLM

| Request | Input tokens | Generated tokens | Native decode seconds | Native tokens/s | Client TTFT seconds |
|---|---:|---:|---:|---:|---:|
| tool-1 | 6454 | 65 | 1.719352 | 37.223 | 3.450 |
| tool-2 | 6624 | 18 | 0.454734 | 37.384 | 0.238 |
| speed-1 | 35 | 128 | 3.379377 | 37.581 | 3.332 |
| speed-2 | 38 | 128 | 3.374841 | 37.631 | 0.114 |
| speed-3 | 37 | 128 | 3.365269 | 37.738 | 0.114 |

## Owner-requested candidate removal

Only these failed, unselected candidate download directories were removed after fresh tree-identity, current-dependency, alias and open-file review: **Flint-AWQ (20.875 GiB); Qwen-Flash-Next-W4A16-FP8PLE-20261103 (116.253 GiB); Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin (67.912 GiB)**. Total: **220,160,068,019 logical bytes (205.040 GiB)**. This is not a filesystem free-space-delta claim. The selected Qwen27B checkpoint, selected Flint GGUF, Sage, Bolt, normal Strata/Maya backing, SGLang drafter, Unsloth/Flint Mix alternatives and graphics assets were preserved. No model was downloaded again. Small model provenance and prior failure evidence remain retained privately.

The earlier unused Strata DFlash2 removal remains separate. Current inventory disposition records all four explicitly removed groups; historical benchmark outcomes are retained.

[Native test numeric results](results/AMD-NATIVE-DECODE-TESTS-2026-11-05.json) · [All13 native decode coverage](AMD-DECODE-EVIDENCE-2026-11-05.md) · [Current inventory/route measurements](REALISTIC-LARGE-MODELS-2026-11-05.md)
