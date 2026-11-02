# Enabled AMD models: short DSH tool checks — November 2, 2026, repeat 2

**7/8 passed; 1/8 did not pass. Every tested managed backend was unloaded before the next model, and the final backend was also unloaded.**

The owner requested a fresh run of all eight currently enabled routes. Each received one attempt through installed DSH headless `0.2.1-rc.2`, **AMD server**, the model hub and its normal guarded backend. Four RAM-held routes remained excluded. Profiles, context caps, engine selections/pins and guard-source hashes are unchanged. The updater stayed paused.

The prompt names a tiny local file by its exact path. Success requires exactly one `read` call, its completed matching tool result, two completed model responses and the exact marker as final output. Each response is capped at 256 output tokens; normal harness tools/system prompt and model reasoning limits are retained. Router readiness is limited to 90 seconds and the harness to 240 seconds including cold loading when it occurs in that phase. There is no automatic retry, long context, throughput loop or soak.

## Functional results

| Model / route | Result | Tool calls | Initial input tokens | Generated tokens (both replies) | Marker | Verified unload |
|---|---|---:|---:|---:|---|---|
| Empero | failed | 1 | 5933 | 103 | not verified | yes |
| Super IQ3 | passed | 1 | 6475 | 94 | yes | yes |
| Flint | passed | 1 | 5450 | 184 | yes | yes |
| Qwen 27B / SGLang DFlash2 | passed | 1 | 6210 | 91 | yes | yes |
| Qwen 27B / vLLM | passed | 1 | 5925 | 90 | yes | yes |
| Bolt / vLLM | passed | 1 | 6475 | 92 | yes | yes |
| Sage / vLLM | passed | 1 | 5900 | 82 | yes | yes |
| GLM / Maya | passed | 1 | 5519 | 77 | yes | yes |

## Memory observations

All values are GiB. GPU figures are per card in observer order; they include whole-card desktop/other allocations. RSS is the sampled sum across owned processes and can double-count shared pages. Scope memory is the sampled simultaneous sum of `memory.current`, including accounted cache; JSON separately retains the maximum kernel `memory.peak` of any single owned scope. These metrics are not interchangeable. Sampling interval: 0.5 seconds from before launch through verified cleanup.

| Model / route | Min available RAM | Peak summed worker RSS | Peak summed scope memory.current | Peak used VRAM, GPU0 / GPU1 | Min free VRAM, GPU0 / GPU1 | Peak owned swap | Peak owned eviction/spill |
|---|---:|---:|---:|---|---|---:|---:|
| Empero | 25.497 | 1.813 | 1.669 | 11.957 / 13.300 | 12.028 / 10.685 | 0.000 | 0.000 |
| Super IQ3 | 6.799 | 20.354 | 24.602 | 20.355 / 19.277 | 3.629 / 4.707 | 0.000 | 0.000 |
| Flint | 25.947 | 1.394 | 1.252 | 14.333 / 12.778 | 9.651 / 11.206 | 0.000 | 0.000 |
| Qwen 27B / SGLang DFlash2 | 16.121 | 49.191 | 26.662 | 19.488 / 19.488 | 4.496 / 4.496 | 0.000 | 0.000 |
| Qwen 27B / vLLM | 19.702 | 15.644 | 13.277 | 16.767 / 16.767 | 7.217 / 7.217 | 0.000 | 0.000 |
| Bolt / vLLM | 19.752 | 26.577 | 27.120 | 22.828 / 22.828 | 1.157 / 1.157 | 0.156 | 0.000 |
| Sage / vLLM | 20.777 | 17.508 | 26.565 | 16.986 / 16.986 | 6.998 / 6.998 | 2.019 | 0.000 |
| GLM / Maya | 14.709 | 19.043 | 18.000 | 16.360 / 16.350 | 7.624 / 7.634 | 0.000 | 0.000 |

## Guardrails retained

RAM gates, worker high/max limits, per-card startup/runtime reserves, debounces, zero owned eviction/spill and `loading-swap-v4` remain as recorded in the [12-route guard catalog](FUTURE-MODEL-TEST-PLAN-2026-11-02.md#current-normal-route-guard-catalog). Each structured result embeds its exact normal-route RAM/VRAM/swap guard row and records before/after-unload RAM, VRAM and swap readings. No guard was relaxed to obtain a pass.

**Swap:** loading/parked paging is allowed; inference limits are 128 MiB/s writes and 160 MiB/s combined reads+writes over complete 30-second windows. The observer records system-wide lifecycle swap-in/out deltas and owned-worker occupancy, and does not infer exact inference-phase windows. This run therefore claims no independent sustained-swap-window qualification. The normal runtime guard remained active. No inference was extended for window coverage.

## Cleanup and thermal coverage

The managed stop path verified every observed owned worker cgroup empty or retired, all backend ports closed, launcher exited and owner file removed. Per-route cleanup took at most 60 seconds; a failure would have stopped the sequence. The campaign released its own GPU reservation. Post-unload memory snapshots and cleanup counts are retained in JSON. Unrelated DSH/services, held profiles and paused schedules were preserved.

| Model / route | Memory samples / errors | Thermal samples / errors | Peak junction C, GPU0 / GPU1 | Peak CPU package C | Cleanup s |
|---|---|---|---|---:|---:|
| Empero | 105 / 0 | 53 / 0 | 41.0 / 42.0 | 55.0 | 0.646 |
| Super IQ3 | 151 / 0 | 76 / 0 | 49.0 / 41.0 | 65.0 | 0.656 |
| Flint | 121 / 0 | 61 / 0 | 43.0 / 48.0 | 58.0 | 0.445 |
| Qwen 27B / SGLang DFlash2 | 159 / 0 | 81 / 0 | 63.0 / 65.0 | 83.0 | 0.875 |
| Qwen 27B / vLLM | 105 / 0 | 53 / 0 | 67.0 / 67.0 | 93.0 | 0.86 |
| Bolt / vLLM | 443 / 0 | 224 / 0 | 62.0 / 61.0 | 96.0 | 0.894 |
| Sage / vLLM | 255 / 0 | 129 / 0 | 58.0 / 58.0 | 97.0 | 0.856 |
| GLM / Maya | 203 / 0 | 107 / 0 | 53.0 / 57.0 | 84.0 | 1.066 |

Thermals were sampled every second through the lifecycle. Per-sensor coverage, power/clocks/fans and available raw SMU flag counts are retained in JSON. Flags are observed samples, not measured throttling duration or evidence of overheating; whole-card sensors include unrelated activity. No desktop display environment was available, so the launcher used its supported headless fallback and retained private logs.

## Failures and interpretation

The [first November 2 campaign](DSH-ENABLED-TOOL-CHECKS-2026-11-02.md) passed 8/8. This separately requested repeat passed 7/8 under the same check; Empero's final-answer formatting differed. A single earlier pass is not a reliability guarantee.

- **Empero:** Read tool succeeded, but the final answer added explanatory text and a code block instead of returning only the marker. No retry; unload verified.

Historical November 1 results remain **4/8 passed, 4/8 did not pass**, with their original fixture/deadlines, available-memory conditions and failures preserved. This is a new campaign with an exact fixture path and the ordinary harness catalog, not a controlled performance comparison or proof of why prior outcomes differed. Historical prefill, TTFT and code/prose decode rates are unchanged.

[Structured results](results/dsh-enabled-tool-checks-2026-11-02-repeat-2.json) · [Future-model test plan](FUTURE-MODEL-TEST-PLAN-2026-11-02.md) · [Previous campaign](DSH-ENABLED-TOOL-CHECKS-2026-11-01.md)
