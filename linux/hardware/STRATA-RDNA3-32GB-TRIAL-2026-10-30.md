# Strata RDNA3 fork: isolated 32 GB trial — October 30, 2026

**The fork loads and short replies work; conservative 8K recall passes, but its history follow-up stalls. This tested 32 GB configuration is not qualified.** Production Strata remains paused and its selected source/build is preserved. This records the owner's explicit instruction to try the fork now with 32 GB; it does not resume the other RAM-held models or create an ongoing test queue.

## Source, build and bounded profile

Candidate: [nicejunjie/Strata-rdna3](https://github.com/nicejunjie/Strata-rdna3), branch `rdna3`, commit `fc8f82334239199cd3cfcfa5ab5b8ac09827d19b`, engine 0.1.43. Applied the source-only [PR #1 AVX2 startup fix](https://github.com/nicejunjie/Strata-rdna3/pull/1), needed for this AVX2-only CPU. The isolated HIP build and CPU help/startup check pass. Build uses the existing ROCm 7.2.3 SDK, GCC 14.4, rocWMMA 7.2.3 and pinned ggml `3cf03257`; no installer, driver replacement, model download or model-file move.

Host: nominal 32 GB / 30.56 GiB OS-visible, i9-13900KS and two RX 7900 XTX 24 GB cards. Reused the existing IQ3_XXS weights with the previously qualified small memory tier: 8 GiB configured expert budget, 18/20 GiB cgroup MemoryHigh/MemoryMax, 256K configured context, 32K INT8 resident KV, dual-GPU split 26 and one request. Actual native resident expert storage is clamped further by its own headroom check. The native expert-cache mode continues to read misses from the model files. Build dependencies differ from the fork's published pinned SDK setup, so these outcomes apply to this tested build and configuration.

The retained stage-trim layout saves GPU memory but disables this fork's dual-GPU data-parallel prefill path. An environment request alone does not activate that path. The author's [128 GB benchmark setup](https://github.com/nicejunjie/Strata-rdna3/blob/rdna3/rdna3/README.md) uses a different resource envelope; no matching speed claim is made here.

## Attempts and retained failures

1. Fork's tuned switch group with the small tier: the model loaded, but readiness had 4.682/6.145 GiB free VRAM against the unchanged 5 GiB floor. The worker was stopped and owned cleanup/reservation release were verified.
2. Increased GPU 0's configured reserve from 7168 to 8192 MiB, retaining GPU 1's 8192 MiB. Readiness passed. Code generation passed four semantic unit cases; native short code/prose decode measured 28.8/43.6 tokens/s in single samples. The 8,168-token retrieval prompt then stalled at layer 39 and the native 60-second no-progress watchdog aborted the engine. No OOM, sampled VRAM spill, telemetry error or outer swap-guard fault was recorded. All expert workers were parked and the stall report found no threads in disk-wait state. This is a failed long-prompt result, with no claim that RAM exhaustion caused it.
3. Removed the opt-in prefill/fusion group, retaining the original memory-saving environment and four basic RDNA decode switches. The same 8/8 GiB GPU reserves, 18/20 GiB RAM limits, context and all independent guards remain. Final status: **failed**. The initial 8,168-token recall passed in 335.94 seconds (324.95 seconds to first token, 25.2 native prefill tokens/s and 1.8 native decode tokens/s). The 8,214-token history follow-up then stalled at layer 44 of the first prompt chunk and the native watchdog stopped it. No OOM, sampled VRAM spill or outer monitor fault was recorded; full-profile qualification is not established.

Final conservative attempt; individual native timings, not medians:

| Request | Input tokens | Output tokens | First token seconds | Total seconds | Prefill tokens/s | Decode tokens/s |
|---|---:|---:|---:|---:|---:|---:|
| warmup | 23 | 64 | 1.02 | 3.13 | 24.0 | 29.9 |
| 8k_retrieval | 8168 | 22 | 324.95 | 335.94 | 25.2 | 1.8 |

These inputs do not establish full-window or general model-quality equivalence. The failures do not identify a single faulty kernel or establish RAM exhaustion as their cause. Code/prose timings above belong to attempt 2 and must not be relabelled conservative-mode timings.

## Protection, cleanup and current state

Final sampled minimum host-available RAM: 16.11 GiB; peak scope memory.current: 18.29 GiB. Sampled owned VRAM spill: 0 bytes; sampler/outer-monitor errors: 0. Cgroup OOM/kill counters and per-attempt swap/VRAM peaks are in the [curated results](results/strata-rdna3-32gb-trial-2026-10-30.json). Nonzero permitted worker swap is retained in the evidence.

The current loading-swap-v4 ceilings, physical-RAM checks, sealed RAM limits, startup/runtime desktop VRAM floors, zero-eviction requirement, worker ownership and native liveness watchdog remain. Increasing the configured GPU reserve reduced expert-cache space; no guard threshold was lowered. Both failed and completed scopes are verified stopped, and the task GPU reservation is released. The active client reply finished before idle production inference was unloaded for the trial; API/hub/DSH services, profiles, production source/build, pins and schedules are preserved. Normal API routes retain on-demand launch.

The candidate is retained separately for review. No automatic promotion or resumed held-model queue. Production adoption needs an explicit scope and the existing qualification gates, including the unresolved tuned-mode stall.

After cleanup, the previously selected `qwen3.8-27b-vllm` was restored through the normal authenticated API: HTTP 200, finish reason `stop`, nonempty output. No trial scope or GPU reservation remains.
