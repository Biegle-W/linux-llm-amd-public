# Qwen27B SGLang: VRAM guard correction and ROCm multicast fix — October 29, 2026

**Qualified and enabled.** Qwen27B/SGLang now passes on the actual 30.56 GiB host with both RX 7900 XTX cards. The original graph-enabled 163,840-token DFlash2 profile is retained. The fix chooses SGLang's existing NCCL fallback before an unsupported CUDA/NVLink multicast allocation on ROCm. Actual driver-reported eviction still has a **zero-byte threshold**. Ornith, DeepSeek XS/Maya, DeepSeek XS/Strata and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Eight working profiles are exposed by the hub and authenticated API.

## Diagnosis and correction

The previous guard inferred spill from `drm-total-vram - drm-resident-vram`. The [kernel definitions](https://docs.kernel.org/gpu/drm-usage-stats.html#memory) allow total to include unbacked requests. Linux 7.0 AMDGPU also exposes `amd-evicted-vram`; [its implementation](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/amdgpu/amdgpu_vm.c) counts buffers whose actual placement is outside their preferred domains. The installed driver exposes this counter. The shared reader now uses valid explicit eviction counters, records the old requested/resident gap separately, and preserves the conservative original fallback on older drivers. Invalid counters fail closed. Any nonzero explicit eviction still stops the owned worker; no grace period or positive spill allowance was added.

Fresh retries showed that SGLang's stop was **not merely the old subtraction ambiguity**: both the original profile and a graph-disabled diagnostic reproduced **63,582,208 bytes (60.637 MiB)** of explicit eviction during startup/warmup. Available GPU memory had been reported as 6.00 GB per rank. More system RAM was not an established fix.

Source inspection found that the lazy logits gatherer attempted a CUDA/NVLink `multimem.st` optimization on ROCm, allocated symmetric memory, then discovered no multicast support and fell back to NCCL. Its 128 × 248,320 BF16 logits buffer is **63,569,920 bytes (60.625 MiB)**, only **12 KiB** below the driver-observed amount. The targeted ROCm dispatch fix selects that same NCCL fallback before creating the unsupported probe buffer. This avoids the problematic allocation rather than tolerating it. Weights, quantization, DFlash2, context, prefill buffers, Mamba cache, graph settings, RAM limits and runtime revision are unchanged.

The upstream revision remains `f84475ccf593`. The strict, replayable [AMD patch script](../sglang/apply-rocm-fixes.py) carries the correction; all five earlier local AMD source fixes were byte-preserved. [Guard reader](../dsh/amd_memory.py), lifecycle collector, owned-worker guard and native watchdogs use consistent eviction semantics. Fault diagnostics retain only bounded counter/phase/time data. Historical failure records keep their original flags and are not retrospectively marked passed.

## Verification

**118 affected CPU checks pass in each maintained checkout**, including 14 eviction/accounting/owned-shutdown cases and four multicast-dispatch cases. Tests prove that unbacked requests with zero eviction pass; one byte of actual eviction still stops a worker; malformed data fails closed; legacy handling stays conservative; duplicate GPU clients count once per device; and ROCm uses the existing fallback while the CUDA branch stays unchanged. Older router fixtures now declare their test-only enabled profiles rather than depending on owner-paused production catalogs.

The full isolated run passed arithmetic, logic, record lookup, JSON, tool round-trip and generated-code execution against four unit cases. Each timed task used one excluded warmup followed by three trials; prefill used three fresh salted ~8K prompts with all three markers and no prefix-cache reuse.

| Fresh measurement | Result |
|---|---:|
| Code median SSE decode | 193.32 tokens/s |
| Prose median SSE decode | 73.91 tokens/s |
| ~8K engine-phase prefill median | 1473.83 tokens/s |
| ~8K fresh request TTFT median | 5.620 s |
| Fresh long input / TTFT | 159,986 tokens / 246.223 s |
| Full-history follow-up input / TTFT | 160,033 tokens / 0.820 s |
| Cached tokens in history follow-up | 160,000 |
| Observed actual KV capacity | 163,840 tokens |
| Continuous inference loop | 35.123 s / 8 requests |

The long fresh request and history follow-up both returned all three markers. These are bounded synthetic checks, not exhaustive quality or vision qualification. The short-performance results are fresh measurements, not a matched historical comparison or claimed speedup. No engine version or 95% performance-comparator threshold changed.

Lifecycle evidence: **756 worker samples, zero sampling errors, zero eviction, zero requested/resident gap**, and 754 explicit-counter samples with no legacy fallback. Peak owned worker swap was **22.034 GiB**. Lifecycle-sampled available host RAM stayed at least **17.658 GiB**; the benchmark observer's sampled free VRAM minima were **4.440 / 4.471 GiB**. The v4 128 MiB/s write / 160 MiB/s combined ceilings over complete 30-second inference windows remain, with independent RAM, VRAM, ownership and thermal protections. Benchmark shutdown was verified and its GPU reservation released.

The normal authenticated API separately passed JSON arithmetic, SSE arithmetic with completion, tool round-trip, and ordered ~8K markers plus full-history follow-up. Both live catalogs expose exactly eight profiles and exclude all four held routes. Hub/gateway processes were preserved. The normal hub-managed SGLang worker retains the existing 600-second inference-aware idle release; it is distinct from the cleaned-up benchmark job. No new schedule or service pause was introduced.

## Retained failed attempts and limits

The original profile first hit the owned guard too briefly for the slower timeline; an instrumented repeat and the graph-disabled diagnostic captured explicit eviction. After the platform fix, startup and the first request succeeded without eviction, but an obsolete private benchmark TTFT rewrite failed. The final run used the maintained benchmark unchanged. A normal API marker check initially used an interpreter without the existing tokenizer package; its script safely restored the SGLang pause, then the complete check passed in the already-installed benchmark environment. No package install or guard relaxation was used to bypass these failures.

Read-only refreshed SSD health: **3% endurance used, 0 media errors, no critical warning**, controller error count **66,051** unchanged, and **41.9°C**. This finite observation is not an SSD lifetime guarantee. Other runtime selections, manual pins, holds, timer/recovery and unrelated schedules remain.

[Curated measurements and verification](results/sglang-vram-guard-fix-2026-10-29.json). Raw logs, responses, driver-client timelines and checkpoints remain private.
