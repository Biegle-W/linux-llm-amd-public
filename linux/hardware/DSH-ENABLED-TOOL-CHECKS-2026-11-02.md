# Enabled AMD models: short DSH tool checks — November 2, 2026

**8/8 passed; 0/8 did not pass. Every tested managed backend was unloaded before the next model, and the final backend was also unloaded.**

The owner requested a fresh run of all eight currently enabled routes. Each received one attempt through installed DSH headless `0.2.1-rc.2`, **AMD server**, the model hub and its normal guarded backend. Four RAM-held routes remained excluded. Profiles, context caps, engine selections/pins and guard-source hashes are unchanged. The updater stayed paused.

The prompt names a tiny local file by its exact path. Success requires exactly one `read` call, its completed matching tool result, two completed model responses and the exact marker as final output. Each response is capped at 256 output tokens; normal harness tools/system prompt and model reasoning limits are retained. Router readiness is limited to 90 seconds and the harness to 240 seconds including cold loading when it occurs in that phase. There is no automatic retry, long context, throughput loop or soak.

## Functional results

| Model / route | Result | Tool calls | Initial input tokens | Generated tokens (both replies) | Marker | Verified unload |
|---|---|---:|---:|---:|---|---|
| Empero | passed | 1 | 5924 | 88 | yes | yes |
| Super IQ3 | passed | 1 | 6466 | 89 | yes | yes |
| Flint | passed | 1 | 5441 | 165 | yes | yes |
| Qwen 27B / SGLang DFlash2 | passed | 1 | 6201 | 87 | yes | yes |
| Qwen 27B / vLLM | passed | 1 | 5916 | 86 | yes | yes |
| Bolt / vLLM | passed | 1 | 6466 | 90 | yes | yes |
| Sage / vLLM | passed | 1 | 5891 | 79 | yes | yes |
| GLM / Maya | passed | 1 | 5510 | 68 | yes | yes |

## Memory observations

All values are GiB. GPU figures are per card in observer order; they include whole-card desktop/other allocations. RSS is the sampled sum across owned processes and can double-count shared pages. Scope memory is the sampled simultaneous sum of `memory.current`, including accounted cache; JSON separately retains the maximum kernel `memory.peak` of any single owned scope. These metrics are not interchangeable. Sampling interval: 0.5 seconds from before launch through verified cleanup.

| Model / route | Min available RAM | Peak summed worker RSS | Peak summed scope memory.current | Peak used VRAM, GPU0 / GPU1 | Min free VRAM, GPU0 / GPU1 | Peak owned swap | Peak owned eviction/spill |
|---|---:|---:|---:|---|---|---:|---:|
| Empero | 25.062 | 1.811 | 1.709 | 11.956 / 13.299 | 12.028 / 10.685 | 0.000 | 0.000 |
| Super IQ3 | 6.442 | 20.374 | 24.271 | 20.355 / 19.277 | 3.629 / 4.707 | 0.000 | 0.000 |
| Flint | 25.557 | 1.394 | 1.240 | 14.334 / 12.779 | 9.651 / 11.205 | 0.000 | 0.000 |
| Qwen 27B / SGLang DFlash2 | 15.291 | 49.225 | 25.023 | 19.488 / 19.488 | 4.496 / 4.496 | 0.000 | 0.000 |
| Qwen 27B / vLLM | 20.262 | 16.107 | 25.874 | 16.767 / 16.768 | 7.217 / 7.217 | 1.816 | 0.000 |
| Bolt / vLLM | 19.995 | 27.679 | 27.055 | 22.672 / 22.672 | 1.313 / 1.313 | 0.000 | 0.000 |
| Sage / vLLM | 20.946 | 17.779 | 26.079 | 16.986 / 16.986 | 6.998 / 6.998 | 2.446 | 0.000 |
| GLM / Maya | 14.538 | 19.032 | 18.000 | 16.360 / 16.350 | 7.624 / 7.634 | 0.000 | 0.000 |

The Qwen/vLLM and Sage/vLLM runs recorded peak owned swap occupancy of 1.816 and 2.446 GiB respectively. Occupancy is allowed by the current phase-aware policy and is not a failed rate-window verdict. Bolt reached 1.313 GiB free per card; its framework route retains its own startup gate/allocation and does not inherit the native worker's 1.5 GiB hard floor. These observations are retained without changing guard settings.

## Guardrails retained

RAM gates, worker high/max limits, per-card startup/runtime reserves, debounces, zero owned eviction/spill and `loading-swap-v4` remain as recorded in the [12-route guard catalog](FUTURE-MODEL-TEST-PLAN-2026-11-02.md#current-normal-route-guard-catalog). Each structured result embeds its exact normal-route RAM/VRAM/swap guard row and records before/after-unload RAM, VRAM and swap readings. No guard was relaxed to obtain a pass.

**Swap:** loading/parked paging is allowed; inference limits are 128 MiB/s writes and 160 MiB/s combined reads+writes over complete 30-second windows. The observer records system-wide lifecycle swap-in/out deltas and owned-worker occupancy, and does not infer exact inference-phase windows. This run therefore claims no independent sustained-swap-window qualification. The normal runtime guard remained active. No inference was extended for window coverage.

## Cleanup and thermal coverage

The managed stop path verified every observed owned worker cgroup empty or retired, all backend ports closed, launcher exited and owner file removed. Per-route cleanup took at most 60 seconds; a failure would have stopped the sequence. The campaign released its own GPU reservation. Post-unload memory snapshots and cleanup counts are retained in JSON. Unrelated DSH/services, held profiles and paused schedules were preserved.

| Model / route | Memory samples / errors | Thermal samples / errors | Peak junction C, GPU0 / GPU1 | Peak CPU package C | Cleanup s |
|---|---|---|---|---:|---:|
| Empero | 113 / 0 | 57 / 0 | 40.0 / 41.0 | 57.0 | 0.652 |
| Super IQ3 | 144 / 0 | 73 / 0 | 48.0 / 41.0 | 63.0 | 0.646 |
| Flint | 118 / 0 | 60 / 0 | 40.0 / 52.0 | 53.0 | 0.442 |
| Qwen 27B / SGLang DFlash2 | 149 / 0 | 76 / 0 | 62.0 / 64.0 | 79.0 | 0.877 |
| Qwen 27B / vLLM | 143 / 0 | 73 / 0 | 64.0 / 65.0 | 94.0 | 0.868 |
| Bolt / vLLM | 338 / 0 | 171 / 0 | 62.0 / 62.0 | 92.0 | 0.864 |
| Sage / vLLM | 210 / 0 | 106 / 0 | 53.0 / 53.0 | 89.0 | 0.861 |
| GLM / Maya | 201 / 0 | 106 / 0 | 58.0 / 47.0 | 90.0 | 1.244 |

Thermals were sampled every second through the lifecycle. Per-sensor coverage, power/clocks/fans and available raw SMU flag counts are retained in JSON. Flags are observed samples, not measured throttling duration or evidence of overheating; whole-card sensors include unrelated activity. No desktop display environment was available, so the launcher used its supported headless fallback and retained private logs.

## Failures and interpretation

All eight routes passed this one short tool round trip. This does not establish arbitrary-tool compatibility, intermittent reliability, full-window recall or other harness behavior.

Historical November 1 results remain **4/8 passed, 4/8 did not pass**, with their original fixture/deadlines, available-memory conditions and failures preserved. This is a new campaign with an exact fixture path and the ordinary harness catalog, not a controlled performance comparison or proof of why prior outcomes differed. Historical prefill, TTFT and code/prose decode rates are unchanged.

[Structured results](results/dsh-enabled-tool-checks-2026-11-02.json) · [Future-model test plan](FUTURE-MODEL-TEST-PLAN-2026-11-02.md) · [Previous campaign](DSH-ENABLED-TOOL-CHECKS-2026-11-01.md)
