# Daily engine updates

The configured updater checks candidate engine builds in isolation. Its timer/hold
status is recorded in the canonical runtime handoff; this text does not enable it.
Promotion retains fixed performance/marker/quality gates and valid lifecycle
memory evidence under loading-swap-v4: loading/parked swap is allowed. Sustained
inference swap writes are limited to 128 MiB/s and combined reads+writes to 160 MiB/s
over 30-second windows. Pressure alone does not stop work. These are operational
ceilings, not SSD endurance guarantees. Dedicated-VRAM spill remains guarded. Independent RAM,
GPU headroom, ownership and thermal protections remain. Manually pinned model
runtimes are excluded from global update comparisons and reported separately.
Anything else is rolled back. Newest entries first. Method: [daily-update/README.md](daily-update/README.md).

## 2026-10-29

- **Strata** `7dd5cf18e68c` → `46c152a1310f`: **rejected**. Step: launcher exited (1) before port 30020 answered; rollback NEEDS ATTENTION

## 2026-10-29

- **Strata** `7dd5cf18e68c` → `46c152a1310f`: **skipped (production baseline failed)**. Isolated build passed; normal 32 GB Strata loader needs 25 GiB available RAM, latest observed 24.849 GiB. Baseline stopped before loading; no candidate installation. Original source remains 7dd5cf18e68c. Performance tolerance unchanged. See hardware/STRATA-RETRY-SAMPLER-2026-10-29.md.

## 2026-10-29

- **llama.cpp** `2280f0fd163b` → `eb4e244be77a`: **promoted**. all gates passed

llama.cpp gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| policy | swap_policy | | loading-swap-v3 | |
| policy | worker_swap_limit_bytes | | uncapped | |
| lifecycle | max_worker_swap_bytes | | 5948850176 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | pass |
| empero-qwen3.8-35b-a3b | prefill_tps | 3421.426 | 3409.690 | -0.3% |
| empero-qwen3.8-35b-a3b | code_decode_tps | 135.455 | 135.640 | +0.1% |
| empero-qwen3.8-35b-a3b | prose_decode_tps | 86.061 | 85.392 | -0.8% |
| empero-qwen3.8-35b-a3b | code_ttft_s | 0.059 | 0.058 | -2.3% |
| empero-qwen3.8-35b-a3b | prose_ttft_s | 0.058 | 0.057 | -2.7% |
| empero-qwen3.8-35b-a3b | markers | 3.000 | 3.000 |  |
| empero-qwen3.8-35b-a3b | max_worker_swap_bytes | | 0 | |
| empero-qwen3.8-35b-a3b | max_nonresident_vram_bytes | | 0 | |
| empero-qwen3.8-35b-a3b | verdict | | | pass |
| nemotron-3.5-super-iq3 | prefill_tps | 428.006 | 425.815 | -0.5% |
| nemotron-3.5-super-iq3 | code_decode_tps | 15.654 | 15.483 | -1.1% |
| nemotron-3.5-super-iq3 | prose_decode_tps | 17.175 | 16.941 | -1.4% |
| nemotron-3.5-super-iq3 | code_ttft_s | 0.951 | 0.962 | +1.1% |
| nemotron-3.5-super-iq3 | prose_ttft_s | 0.632 | 0.636 | +0.7% |
| nemotron-3.5-super-iq3 | markers | 3.000 | 3.000 |  |
| nemotron-3.5-super-iq3 | max_worker_swap_bytes | | 134729728 | |
| nemotron-3.5-super-iq3 | max_nonresident_vram_bytes | | 0 | |
| nemotron-3.5-super-iq3 | verdict | | | pass |
| flint-40b-a2.5b | prefill_tps | 5688.457 | 5726.102 | +0.7% |
| flint-40b-a2.5b | code_decode_tps | 46.966 | 46.915 | -0.1% |
| flint-40b-a2.5b | prose_decode_tps | 46.950 | 46.856 | -0.2% |
| flint-40b-a2.5b | code_ttft_s | 0.081 | 0.082 | +1.2% |
| flint-40b-a2.5b | prose_ttft_s | 0.072 | 0.071 | -1.7% |
| flint-40b-a2.5b | markers | 3.000 | 3.000 |  |
| flint-40b-a2.5b | max_worker_swap_bytes | | 9670656 | |
| flint-40b-a2.5b | max_nonresident_vram_bytes | | 0 | |
| flint-40b-a2.5b | verdict | | | pass |

## 2026-10-29

- **vLLM** `0.32.1rc1.dev602+g5d35ce393.rocm72` → `0.33.0rc1.dev229+g3966924d5.rocm72`: **promoted**. all gates passed

vLLM gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| policy | swap_policy | | loading-swap-v3 | |
| policy | worker_swap_limit_bytes | | uncapped | |
| lifecycle | max_worker_swap_bytes | | 3232501760 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | pass |
| qwen3.8-27b-vllm | prefill_tps | 1457.002 | 1471.737 | +1.0% |
| qwen3.8-27b-vllm | code_decode_tps | 142.751 | 142.510 | -0.2% |
| qwen3.8-27b-vllm | prose_decode_tps | 78.444 | 75.836 | -3.3% |
| qwen3.8-27b-vllm | code_ttft_s | 0.078 | 0.076 | -2.1% |
| qwen3.8-27b-vllm | prose_ttft_s | 0.071 | 0.074 | +4.9% |
| qwen3.8-27b-vllm | markers | 3.000 | 3.000 |  |
| qwen3.8-27b-vllm | max_worker_swap_bytes | | 2326487040 | |
| qwen3.8-27b-vllm | max_nonresident_vram_bytes | | 0 | |
| qwen3.8-27b-vllm | verdict | | | pass |
| sage-a1.5 | prefill_tps | 5276.474 | 5324.545 | +0.9% |
| sage-a1.5 | code_decode_tps | 148.483 | 148.756 | +0.2% |
| sage-a1.5 | prose_decode_tps | 139.600 | 139.700 | +0.1% |
| sage-a1.5 | code_ttft_s | 0.070 | 0.066 | -6.6% |
| sage-a1.5 | prose_ttft_s | 0.066 | 0.071 | +7.8% |
| sage-a1.5 | markers | 3.000 | 3.000 |  |
| sage-a1.5 | max_worker_swap_bytes | | 9879552 | |
| sage-a1.5 | max_nonresident_vram_bytes | | 0 | |
| sage-a1.5 | verdict | | | pass |

## 2026-10-29

- **llama.cpp** `2280f0fd163b` → `0893ec98f5ea`: **skipped (production baseline failed)**. baseline ornith-1.5-122b: prewarm failed
- **vLLM** `0.32.1rc1.dev602+g5d35ce393.rocm72` → `0.33.0rc1.dev229+g3966924d5.rocm72`: **skipped (production baseline failed)**. sage-a1.5
- **Strata** `7dd5cf18e68c` → `46c152a1310f`: **rejected**. missed a promotion gate; rollback verified
- **Maya** `f26d8bab43f9` → `cf6472cc8448`: **skipped (production baseline failed)**. launcher exited (1) before port 30030 answered
- **Strata DeepSeek** `8183c6b67162` → `46c152a1310f`: **skipped (production baseline failed)**. launcher exited (1) before port 30020 answered

Strata gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| policy | swap_policy | | loading-swap-v3 | |
| policy | worker_swap_limit_bytes | | uncapped | |
| lifecycle | max_worker_swap_bytes | | 0 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | FAIL: lifecycle_sampling_errors |
| qwen3.8-flash-next-iq3_xxs | prefill_tps | 1159.500 | 1160.300 | +0.1% |
| qwen3.8-flash-next-iq3_xxs | code_decode_tps | 73.233 | 72.770 | -0.6% |
| qwen3.8-flash-next-iq3_xxs | prose_decode_tps | 54.100 | 53.765 | -0.6% |
| qwen3.8-flash-next-iq3_xxs | code_ttft_s | 0.247 | 0.250 | +1.5% |
| qwen3.8-flash-next-iq3_xxs | prose_ttft_s | 0.231 | 0.227 | -1.6% |
| qwen3.8-flash-next-iq3_xxs | markers | 3.000 | 3.000 |  |
| qwen3.8-flash-next-iq3_xxs | max_worker_swap_bytes | | 0 | |
| qwen3.8-flash-next-iq3_xxs | max_nonresident_vram_bytes | | 0 | |
| qwen3.8-flash-next-iq3_xxs | verdict | | | pass |

## Nightly schedule restored — October 29

The existing 03:00 timer is enabled and active again; a guarded manual run is in progress. Older updater-pause notes below are historical. Manual runtime pins, other holds and all promotion/rollback gates remain. [Restoration, helper/unit repairs and current status](ENGINE-UPDATER-RESTORED-2026-10-29.md).

## Pre-restoration read-only audit — October 29

At that pre-restoration snapshot, the timer was absent/inactive and its service inactive. Five configured components have newer upstreams; SGLang matches its configured gfx1100-support fork. No builds, promotions or schedule changes were made. [Selected/upstream revisions, coverage and exclusions](ENGINE-UPDATE-AUDIT-2026-10-29.md). The updater remains paused.

The configured updater checks candidate engine builds in isolation. Its timer/hold
status is recorded in the canonical runtime handoff; this text does not enable it.
Promotion retains fixed performance/marker/quality gates and valid lifecycle
memory evidence under loading-swap-v3: loading/parked swap is allowed. Swap reads,
rates and pressure alone do not stop work; a swap stop requires an explicit write
budget plus matched measured slowdown. Dedicated-VRAM spill remains guarded. Independent RAM,
GPU headroom, ownership and thermal protections remain. Manually pinned model
runtimes are excluded from global update comparisons and reported separately.
Anything else is rolled back. Newest entries first. Method: [daily-update/README.md](daily-update/README.md).

## Conditional vLLM promotion — October27

Qwen/Sage qualify on dev602; Bolt remains explicitly on dev435 after two near255K
inference-churn stops, despite its earlier successful8K performance gates. The
updater excludes `manual_runtime_pin` profiles and remains paused. Completed speed
samples are reused; new installed functionality/mixed routing, all failures and
188 CPU regressions per checkout are recorded. Guards/contexts remain unchanged.
[Selected results, qualification and recovery](VLLM-DEV602-PROMOTION-2026-10-27.md).

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](LOADING-SWAP-RETRY-2026-10-27.md).


## Current-RAM retest — October27

After verified inactive compiler temps were retained on disk, both H3 and blocked
vLLM/SGLang/native INT4 profiles were retried with more free RAM and unchanged
guards. H3 advanced to text-encoder loading, then hit its RAM floor; LLM loading
still hit the swapout budget, with an additional Sage auto-Marlin HIP compile
failure. No new model/engine promotion or retirement; no new inference medians.
[All attempts, memory counters and thermals](CURRENT-RAM-RETEST-2026-10-27.md).


## VRAM engine refresh — October27

Qualified llama.cpp19cce691 for Empero/Sage/Flint with profile-specific source
pins; CPU profiles retain2280f0fd. New vLLM dev602 and Sage/Flint native INT4
trials remain held by current-host loading guards; production staysdev435.
Required SGLang f84475cc is already latest. All current guards/settings and the
paused updater remain. [Full fields, paired medians, source pins and failed attempts](VRAM-ENGINE-UPDATE-2026-10-27.md).


## DeepSeek-S retired — October26

At the user's request, S is removed from Maya and Strata; **11 profiles** remain.
XS keeps the shared S Engram shards5/6, matching xs2 drafter and original pack
metadata. S-only shards1–4, old drafter, metadata and routing seeds were removed,
reclaiming **186.18 GB** on Shared NVMe. Config/pack seals and both XS dependency
maps are unchanged. This is storage/CPU/API verification only; no new inference
or speed measurement, and the reduced-RAM holds and paused updater remain.
[Removal, retained dependencies and limits](DEEPSEEK-S-RETIREMENT-2026-10-26.md).

**Current status — October 26:** the timer is disabled; no nightly engine update
is running. Guarded reduced-RAM qualification is authorized only for the two
vLLM profiles and SGLang Qwen DFlash2. It is not update activation. All three
reviewed loading trials were stopped by the 4 GiB cumulative system swapout
budget under the 7 GiB soft / 8 GiB hard worker RAM cap; none qualified. The
early trials used opt-in low-churn. The user subsequently authorized low-churn as
the default policy; this does not activate the updater. [Outcomes and limits](VRAM-QUALIFICATION-2026-10-26.md).

Every night at 03:00 `llm-daily-update.timer` checks llama.cpp, vLLM, SGLang, Strata and
Maya for newer upstream versions. Each one is built in isolation, benchmarked against the
current production build with the shared method, and kept only when every standard
promotion gate passes (prefill and code/prose decode ≥95% of production, short time to
first token within max(1.25×, +0.05 s), no fewer retrieval markers, the default bounded
low-churn swap limits and zero VRAM spill with valid launch-through-shutdown telemetry).
Anything else is rolled back. Newest entries first. Method: [daily-update/README.md](daily-update/README.md).

## 2026-10-25 — fresh tests after the 64 MiB allowance

- **llama.cpp** `6b9ba4f2e8c1` → `2280f0fd163b`: **promoted**. all gates passed
- **Strata DeepSeek** `8183c6b67162` → `4b9e05a2a806`: **rejected before installation**. IQ3_XXS WMMA/scalar parity exceeded tolerance on both GPUs (3.14e-3 > 3e-3); production retained. [Details](FRESH-ENGINE-TESTS-2026-10-25.md#strata-deepseek-parity-rejection).
- **Maya** `f26d8bab43f9` → `6afa525bbabc`: **rejected**. missed a promotion gate; rollback verified

llama.cpp gates (baseline = production in this run):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| policy | worker_swap_limit_bytes | | 67108864 | |
| lifecycle | max_worker_swap_bytes | | 0 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | pass |
| empero-qwen3.8-35b-a3b | prefill_tps | 2967.140 | 2951.966 | -0.5% |
| empero-qwen3.8-35b-a3b | code_decode_tps | 119.683 | 121.652 | +1.6% |
| empero-qwen3.8-35b-a3b | prose_decode_tps | 72.848 | 77.653 | +6.6% |
| empero-qwen3.8-35b-a3b | code_ttft_s | 0.060 | 0.061 | +2.2% |
| empero-qwen3.8-35b-a3b | prose_ttft_s | 0.059 | 0.061 | +2.8% |
| empero-qwen3.8-35b-a3b | markers | 3.000 | 3.000 |  |
| empero-qwen3.8-35b-a3b | max_worker_swap_bytes | | 0 | |
| empero-qwen3.8-35b-a3b | max_nonresident_vram_bytes | | 0 | |
| empero-qwen3.8-35b-a3b | verdict | | | pass |
| nemotron-3.5-super-iq3 | prefill_tps | 432.503 | 430.413 | -0.5% |
| nemotron-3.5-super-iq3 | code_decode_tps | 15.533 | 15.579 | +0.3% |
| nemotron-3.5-super-iq3 | prose_decode_tps | 17.097 | 17.093 | -0.0% |
| nemotron-3.5-super-iq3 | code_ttft_s | 0.926 | 0.956 | +3.2% |
| nemotron-3.5-super-iq3 | prose_ttft_s | 0.631 | 0.649 | +2.8% |
| nemotron-3.5-super-iq3 | markers | 3.000 | 3.000 |  |
| nemotron-3.5-super-iq3 | max_worker_swap_bytes | | 0 | |
| nemotron-3.5-super-iq3 | max_nonresident_vram_bytes | | 0 | |
| nemotron-3.5-super-iq3 | verdict | | | pass |
| sage-a1.5 | prefill_tps | 2806.686 | 2796.396 | -0.4% |
| sage-a1.5 | code_decode_tps | 79.830 | 81.234 | +1.8% |
| sage-a1.5 | prose_decode_tps | 63.932 | 67.740 | +6.0% |
| sage-a1.5 | code_ttft_s | 0.057 | 0.058 | +2.9% |
| sage-a1.5 | prose_ttft_s | 0.055 | 0.057 | +2.1% |
| sage-a1.5 | markers | 3.000 | 3.000 |  |
| sage-a1.5 | max_worker_swap_bytes | | 0 | |
| sage-a1.5 | max_nonresident_vram_bytes | | 0 | |
| sage-a1.5 | verdict | | | pass |
| ornith-1.5-122b | prefill_tps | 718.383 | 711.202 | -1.0% |
| ornith-1.5-122b | code_decode_tps | 11.423 | 11.265 | -1.4% |
| ornith-1.5-122b | prose_decode_tps | 13.312 | 13.470 | +1.2% |
| ornith-1.5-122b | code_ttft_s | 0.556 | 0.545 | -2.0% |
| ornith-1.5-122b | prose_ttft_s | 0.731 | 0.752 | +2.8% |
| ornith-1.5-122b | markers | 3.000 | 3.000 |  |
| ornith-1.5-122b | max_worker_swap_bytes | | 0 | |
| ornith-1.5-122b | max_nonresident_vram_bytes | | 0 | |
| ornith-1.5-122b | verdict | | | pass |

Maya gates (baseline = production in this run):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| policy | worker_swap_limit_bytes | | 67108864 | |
| lifecycle | max_worker_swap_bytes | | 35897344 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | pass |
| glm-5.3-flash-maya | prefill_tps | 539.300 | 537.100 | -0.4% |
| glm-5.3-flash-maya | code_decode_tps | 19.043 | 18.853 | -1.0% |
| glm-5.3-flash-maya | prose_decode_tps | 15.520 | 15.746 | +1.5% |
| glm-5.3-flash-maya | code_ttft_s | 0.082 | 0.082 | -0.0% |
| glm-5.3-flash-maya | prose_ttft_s | 0.094 | 0.095 | +1.3% |
| glm-5.3-flash-maya | markers | 3.000 | 3.000 |  |
| glm-5.3-flash-maya | max_worker_swap_bytes | | 33574912 | |
| glm-5.3-flash-maya | max_nonresident_vram_bytes | | 0 | |
| glm-5.3-flash-maya | verdict | | | pass |
| deepseek-v4.1-flash-1017-maya | prefill_tps | 634.100 | 630.600 | -0.6% |
| deepseek-v4.1-flash-1017-maya | code_decode_tps | 22.586 | 18.997 | -15.9% |
| deepseek-v4.1-flash-1017-maya | prose_decode_tps | 13.313 | 12.417 | -6.7% |
| deepseek-v4.1-flash-1017-maya | code_ttft_s | 0.096 | 0.106 | +10.6% |
| deepseek-v4.1-flash-1017-maya | prose_ttft_s | 0.191 | 0.149 | -22.1% |
| deepseek-v4.1-flash-1017-maya | markers | 3.000 | 3.000 |  |
| deepseek-v4.1-flash-1017-maya | max_worker_swap_bytes | | 0 | |
| deepseek-v4.1-flash-1017-maya | max_nonresident_vram_bytes | | 0 | |
| deepseek-v4.1-flash-1017-maya | verdict | | | FAIL: code_decode_tps, prose_decode_tps |
| deepseek-v4.1-flash-1017-maya-s | prefill_tps | 381.700 | 375.900 | -1.5% |
| deepseek-v4.1-flash-1017-maya-s | code_decode_tps | 5.708 | 6.642 | +16.4% |
| deepseek-v4.1-flash-1017-maya-s | prose_decode_tps | 6.665 | 6.271 | -5.9% |
| deepseek-v4.1-flash-1017-maya-s | code_ttft_s | 0.431 | 0.457 | +5.9% |
| deepseek-v4.1-flash-1017-maya-s | prose_ttft_s | 0.601 | 0.564 | -6.1% |
| deepseek-v4.1-flash-1017-maya-s | markers | 3.000 | 3.000 |  |
| deepseek-v4.1-flash-1017-maya-s | max_worker_swap_bytes | | 0 | |
| deepseek-v4.1-flash-1017-maya-s | max_nonresident_vram_bytes | | 0 | |
| deepseek-v4.1-flash-1017-maya-s | verdict | | | FAIL: prose_decode_tps |


## October 25: minor worker swap allowed (policy validation only)

Promotion now allows up to 64 MiB aggregate owned-worker swap per model and
throughout loading/testing/shutdown; larger amounts fail. Zero VRAM spill,
valid telemetry, complete model coverage and performance/quality gates remain.
All 18 CPU memory/promotion/rollback tests pass. Saved October25 llama.cpp,
Maya and Strata DeepSeek baselines pass the new memory gate; vLLM dev466 still
fails major swap and Qwen prose regression. No new GPU test, runtime promotion
or performance measurement. Original nightly results below are unchanged.
[Exact policy and replay limits](daily-update/README.md#minor-worker-swap-allowance--october-25).

## 2026-10-25

- **llama.cpp** `6b9ba4f2e8c1` → `b3fa69955ea8`: **skipped (production baseline failed)**. ornith-1.5-122b, worker_swap
- **vLLM** `0.32.1rc1.dev435+gc50aca144.rocm72` → `0.32.1rc1.dev466+ge4a5b5537.rocm72`: **rejected**. missed a promotion gate; rollback verified
- **Strata** `8183c6b67162` → `7dd5cf18e68c`: **promoted**. all gates passed
- **Maya** `f26d8bab43f9` → `4615f346d931`: **skipped (production baseline failed)**. glm-5.3-flash-maya, worker_swap
- **Strata DeepSeek** `8183c6b67162` → `7dd5cf18e68c`: **skipped (production baseline failed)**. deepseek-v4.1-flash-1017-strata-s, worker_swap

vLLM gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| lifecycle | max_worker_swap_bytes | | 4041416704 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | FAIL: worker_swap |
| qwen3.8-27b-vllm | prefill_tps | 1517.341 | 1510.649 | -0.4% |
| qwen3.8-27b-vllm | code_decode_tps | 142.258 | 141.623 | -0.4% |
| qwen3.8-27b-vllm | prose_decode_tps | 77.015 | 71.841 | -6.7% |
| qwen3.8-27b-vllm | code_ttft_s | 0.069 | 0.070 | +2.1% |
| qwen3.8-27b-vllm | prose_ttft_s | 0.064 | 0.066 | +3.9% |
| qwen3.8-27b-vllm | markers | 3.000 | 3.000 |  |
| qwen3.8-27b-vllm | max_worker_swap_bytes | | 2535796736 | |
| qwen3.8-27b-vllm | max_nonresident_vram_bytes | | 0 | |
| qwen3.8-27b-vllm | verdict | | | FAIL: prose_decode_tps, worker_swap |
| nemotron-3.5-bolt-vllm | prefill_tps | 2958.688 | 2940.017 | -0.6% |
| nemotron-3.5-bolt-vllm | code_decode_tps | 37.901 | 38.081 | +0.5% |
| nemotron-3.5-bolt-vllm | prose_decode_tps | 37.976 | 38.182 | +0.5% |
| nemotron-3.5-bolt-vllm | code_ttft_s | 0.078 | 0.079 | +0.3% |
| nemotron-3.5-bolt-vllm | prose_ttft_s | 0.070 | 0.076 | +9.3% |
| nemotron-3.5-bolt-vllm | markers | 3.000 | 3.000 |  |
| nemotron-3.5-bolt-vllm | max_worker_swap_bytes | | 8265728 | |
| nemotron-3.5-bolt-vllm | max_nonresident_vram_bytes | | 0 | |
| nemotron-3.5-bolt-vllm | verdict | | | FAIL: worker_swap |

Strata gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| lifecycle | max_worker_swap_bytes | | 0 | |
| lifecycle | max_nonresident_vram_bytes | | 0 | |
| lifecycle | verdict | | | pass |
| qwen3.8-flash-next-iq3_xxs | prefill_tps | 1210.000 | 1206.200 | -0.3% |
| qwen3.8-flash-next-iq3_xxs | code_decode_tps | 76.669 | 75.515 | -1.5% |
| qwen3.8-flash-next-iq3_xxs | prose_decode_tps | 49.000 | 47.440 | -3.2% |
| qwen3.8-flash-next-iq3_xxs | code_ttft_s | 0.229 | 0.232 | +1.3% |
| qwen3.8-flash-next-iq3_xxs | prose_ttft_s | 0.236 | 0.245 | +3.7% |
| qwen3.8-flash-next-iq3_xxs | markers | 3.000 | 3.000 |  |
| qwen3.8-flash-next-iq3_xxs | max_worker_swap_bytes | | 0 | |
| qwen3.8-flash-next-iq3_xxs | max_nonresident_vram_bytes | | 0 | |
| qwen3.8-flash-next-iq3_xxs | verdict | | | pass |

## October 24: zero-swap promotion gate repaired

The comparator now rejects any observed worker swap, alongside VRAM spill, and
fails closed on missing/invalid memory evidence. The updater also samples the
normal inference lifecycle, including loading, and rejects sampling errors or
absent worker samples. Each PID/shared DRM client is counted once. A bad baseline
skips installation; a bad candidate rolls back and smoke-tests the restored build.
CPU-only rejection/rollback tests and saved-record replay validate this repair;
no new inference benchmark or runtime promotion/rollback was performed.

The October24 vLLM candidate records below were promoted under the older gate;
their nonzero swap fields now fail replay. Historical byte totals may double-count
descendants and are retained as reported, without rewriting old timings/results.
[Policy, coverage and limits](daily-update/README.md#zero-swap-gate-correction--october-24).

## 2026-10-24

- **llama.cpp** `edc353842c1b` → `6b9ba4f2e8c1`: **promoted**. all gates passed
- **vLLM** `0.32.1rc1.dev361+g83c078d95.rocm72` → `0.32.1rc1.dev435+gc50aca144.rocm72`: **promoted**. all gates passed
- **Strata** `7ddc17a38fe7` → `8183c6b67162`: **promoted**. all gates passed

llama.cpp gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| empero-qwen3.8-35b-a3b | prefill_tps | 2975.797 | 2977.874 | +0.1% |
| empero-qwen3.8-35b-a3b | code_decode_tps | 119.849 | 120.702 | +0.7% |
| empero-qwen3.8-35b-a3b | prose_decode_tps | 73.520 | 73.471 | -0.1% |
| empero-qwen3.8-35b-a3b | code_ttft_s | 0.059 | 0.058 | -0.5% |
| empero-qwen3.8-35b-a3b | prose_ttft_s | 0.058 | 0.059 | +0.8% |
| empero-qwen3.8-35b-a3b | markers | 3.000 | 3.000 |  |
| empero-qwen3.8-35b-a3b | verdict | | | pass |
| nemotron-3.5-super-iq3 | prefill_tps | 433.020 | 433.601 | +0.1% |
| nemotron-3.5-super-iq3 | code_decode_tps | 15.656 | 15.694 | +0.2% |
| nemotron-3.5-super-iq3 | prose_decode_tps | 17.237 | 17.234 | -0.0% |
| nemotron-3.5-super-iq3 | code_ttft_s | 0.922 | 0.920 | -0.2% |
| nemotron-3.5-super-iq3 | prose_ttft_s | 0.623 | 0.618 | -0.8% |
| nemotron-3.5-super-iq3 | markers | 3.000 | 3.000 |  |
| nemotron-3.5-super-iq3 | verdict | | | pass |
| sage-a1.5 | prefill_tps | 2817.591 | 2816.180 | -0.1% |
| sage-a1.5 | code_decode_tps | 80.897 | 80.740 | -0.2% |
| sage-a1.5 | prose_decode_tps | 64.561 | 65.038 | +0.7% |
| sage-a1.5 | code_ttft_s | 0.056 | 0.056 | -0.6% |
| sage-a1.5 | prose_ttft_s | 0.054 | 0.054 | -0.3% |
| sage-a1.5 | markers | 3.000 | 3.000 |  |
| sage-a1.5 | verdict | | | pass |
| ornith-1.5-122b | prefill_tps | 718.397 | 720.127 | +0.2% |
| ornith-1.5-122b | code_decode_tps | 11.505 | 11.505 | -0.0% |
| ornith-1.5-122b | prose_decode_tps | 13.444 | 13.416 | -0.2% |
| ornith-1.5-122b | code_ttft_s | 0.535 | 0.539 | +0.8% |
| ornith-1.5-122b | prose_ttft_s | 0.724 | 0.732 | +1.1% |
| ornith-1.5-122b | markers | 3.000 | 3.000 |  |
| ornith-1.5-122b | verdict | | | pass |

vLLM gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| qwen3.8-27b-vllm | prefill_tps | 1506.484 | 1510.822 | +0.3% |
| qwen3.8-27b-vllm | code_decode_tps | 142.173 | 142.303 | +0.1% |
| qwen3.8-27b-vllm | prose_decode_tps | 78.315 | 76.769 | -2.0% |
| qwen3.8-27b-vllm | code_ttft_s | 0.070 | 0.071 | +1.0% |
| qwen3.8-27b-vllm | prose_ttft_s | 0.063 | 0.066 | +3.8% |
| qwen3.8-27b-vllm | markers | 3.000 | 3.000 |  |
| qwen3.8-27b-vllm | verdict | | | pass |
| nemotron-3.5-bolt-vllm | prefill_tps | 2941.267 | 2904.223 | -1.3% |
| nemotron-3.5-bolt-vllm | code_decode_tps | 38.060 | 37.964 | -0.3% |
| nemotron-3.5-bolt-vllm | prose_decode_tps | 38.104 | 38.072 | -0.1% |
| nemotron-3.5-bolt-vllm | code_ttft_s | 0.075 | 0.078 | +3.7% |
| nemotron-3.5-bolt-vllm | prose_ttft_s | 0.071 | 0.070 | -0.9% |
| nemotron-3.5-bolt-vllm | markers | 3.000 | 3.000 |  |
| nemotron-3.5-bolt-vllm | verdict | | | pass |

Strata gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | prefill_tps | 918.800 | 915.900 | -0.3% |
| qwen3.8-flash-next-iq3_xxs | code_decode_tps | 73.049 | 73.361 | +0.4% |
| qwen3.8-flash-next-iq3_xxs | prose_decode_tps | 46.371 | 50.008 | +7.8% |
| qwen3.8-flash-next-iq3_xxs | code_ttft_s | 0.238 | 0.236 | -0.7% |
| qwen3.8-flash-next-iq3_xxs | prose_ttft_s | 0.235 | 0.233 | -1.0% |
| qwen3.8-flash-next-iq3_xxs | markers | 3.000 | 3.000 |  |
| qwen3.8-flash-next-iq3_xxs | verdict | | | pass |

## 2026-10-23

- **llama.cpp** `4c3c5810f87e` → `edc353842c1b`: **promoted**. all gates passed
- **vLLM** `0.32.1rc1.dev36+ge68efc685.rocm72` → `0.32.1rc1.dev361+g83c078d95.rocm72`: **promoted**. all gates passed
- **Strata** `9ae93f7b1fe9` → `7ddc17a38fe7`: **promoted**. all gates passed
- **Maya** `25deec505b52` → `f26d8bab43f9`: **promoted**. all gates passed; 17/18 kernel parity tests on each GPU (hip_prefill_fused_parity fails as in 1.1.24; that path stays disabled)

llama.cpp gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| empero-qwen3.8-35b-a3b | prefill_tps | 2975.532 | 2981.328 | +0.2% |
| empero-qwen3.8-35b-a3b | code_decode_tps | 120.747 | 120.466 | -0.2% |
| empero-qwen3.8-35b-a3b | prose_decode_tps | 72.898 | 74.477 | +2.2% |
| empero-qwen3.8-35b-a3b | code_ttft_s | 0.059 | 0.060 | +0.8% |
| empero-qwen3.8-35b-a3b | prose_ttft_s | 0.058 | 0.058 | +0.9% |
| empero-qwen3.8-35b-a3b | markers | 3.000 | 3.000 |  |
| empero-qwen3.8-35b-a3b | verdict | | | pass |
| nemotron-3.5-super-iq3 | prefill_tps | 433.208 | 433.513 | +0.1% |
| nemotron-3.5-super-iq3 | code_decode_tps | 15.600 | 15.606 | +0.0% |
| nemotron-3.5-super-iq3 | prose_decode_tps | 17.165 | 17.141 | -0.1% |
| nemotron-3.5-super-iq3 | code_ttft_s | 0.924 | 0.924 | -0.0% |
| nemotron-3.5-super-iq3 | prose_ttft_s | 0.624 | 0.625 | +0.1% |
| nemotron-3.5-super-iq3 | markers | 3.000 | 3.000 |  |
| nemotron-3.5-super-iq3 | verdict | | | pass |
| sage-a1.5 | prefill_tps | 2832.611 | 2820.943 | -0.4% |
| sage-a1.5 | code_decode_tps | 80.813 | 81.109 | +0.4% |
| sage-a1.5 | prose_decode_tps | 65.023 | 64.277 | -1.1% |
| sage-a1.5 | code_ttft_s | 0.056 | 0.056 | +0.0% |
| sage-a1.5 | prose_ttft_s | 0.055 | 0.055 | -0.2% |
| sage-a1.5 | markers | 3.000 | 3.000 |  |
| sage-a1.5 | verdict | | | pass |
| ornith-1.5-122b | prefill_tps | 714.339 | 715.542 | +0.2% |
| ornith-1.5-122b | code_decode_tps | 11.389 | 11.413 | +0.2% |
| ornith-1.5-122b | prose_decode_tps | 13.321 | 13.332 | +0.1% |
| ornith-1.5-122b | code_ttft_s | 0.545 | 0.538 | -1.2% |
| ornith-1.5-122b | prose_ttft_s | 0.737 | 0.731 | -0.9% |
| ornith-1.5-122b | markers | 3.000 | 3.000 |  |
| ornith-1.5-122b | verdict | | | pass |

vLLM gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| qwen3.8-27b-vllm | prefill_tps | 1476.717 | 1504.942 | +1.9% |
| qwen3.8-27b-vllm | code_decode_tps | 134.980 | 141.984 | +5.2% |
| qwen3.8-27b-vllm | prose_decode_tps | 71.917 | 78.274 | +8.8% |
| qwen3.8-27b-vllm | code_ttft_s | 0.068 | 0.069 | +1.7% |
| qwen3.8-27b-vllm | prose_ttft_s | 0.077 | 0.068 | -11.4% |
| qwen3.8-27b-vllm | markers | 3.000 | 3.000 |  |
| qwen3.8-27b-vllm | verdict | | | pass |
| nemotron-3.5-bolt-vllm | prefill_tps | 2905.876 | 2920.631 | +0.5% |
| nemotron-3.5-bolt-vllm | code_decode_tps | 38.075 | 38.141 | +0.2% |
| nemotron-3.5-bolt-vllm | prose_decode_tps | 38.026 | 38.131 | +0.3% |
| nemotron-3.5-bolt-vllm | code_ttft_s | 0.079 | 0.079 | +0.2% |
| nemotron-3.5-bolt-vllm | prose_ttft_s | 0.071 | 0.073 | +3.7% |
| nemotron-3.5-bolt-vllm | markers | 3.000 | 3.000 |  |
| nemotron-3.5-bolt-vllm | verdict | | | pass |

Strata gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | prefill_tps | 923.000 | 921.800 | -0.1% |
| qwen3.8-flash-next-iq3_xxs | code_decode_tps | 78.583 | 75.323 | -4.1% |
| qwen3.8-flash-next-iq3_xxs | prose_decode_tps | 54.157 | 54.129 | -0.1% |
| qwen3.8-flash-next-iq3_xxs | code_ttft_s | 0.230 | 0.235 | +2.1% |
| qwen3.8-flash-next-iq3_xxs | prose_ttft_s | 0.226 | 0.227 | +0.4% |
| qwen3.8-flash-next-iq3_xxs | markers | 3.000 | 3.000 |  |
| qwen3.8-flash-next-iq3_xxs | verdict | | | pass |

Maya gates (baseline = production the same night):

| Model | Metric | Baseline | Candidate | Change |
|---|---|---:|---:|---:|
| glm-5.3-flash-maya | prefill_tps | 533.700 | 535.800 | +0.4% |
| glm-5.3-flash-maya | code_decode_tps | 19.029 | 19.169 | +0.7% |
| glm-5.3-flash-maya | prose_decode_tps | 15.782 | 16.358 | +3.7% |
| glm-5.3-flash-maya | code_ttft_s | 0.080 | 0.082 | +2.0% |
| glm-5.3-flash-maya | prose_ttft_s | 0.094 | 0.085 | -8.6% |
| glm-5.3-flash-maya | markers | 3.000 | 3.000 |  |
| glm-5.3-flash-maya | verdict | | | pass |
| deepseek-v4.1-flash-1017-maya | prefill_tps | 448.500 | 640.900 | +42.9% |
| deepseek-v4.1-flash-1017-maya | code_decode_tps | 22.254 | 21.739 | -2.3% |
| deepseek-v4.1-flash-1017-maya | prose_decode_tps | 12.918 | 13.628 | +5.5% |
| deepseek-v4.1-flash-1017-maya | code_ttft_s | 0.112 | 0.117 | +4.4% |
| deepseek-v4.1-flash-1017-maya | prose_ttft_s | 0.157 | 0.124 | -20.5% |
| deepseek-v4.1-flash-1017-maya | markers | 3.000 | 3.000 |  |
| deepseek-v4.1-flash-1017-maya | verdict | | | pass |
| deepseek-v4.1-flash-1017-maya-s | prefill_tps | 293.400 | 376.000 | +28.2% |
| deepseek-v4.1-flash-1017-maya-s | code_decode_tps | 6.085 | 6.579 | +8.1% |
| deepseek-v4.1-flash-1017-maya-s | prose_decode_tps | 6.535 | 6.580 | +0.7% |
| deepseek-v4.1-flash-1017-maya-s | code_ttft_s | 0.468 | 0.420 | -10.1% |
| deepseek-v4.1-flash-1017-maya-s | prose_ttft_s | 0.537 | 0.612 | +14.1% |
| deepseek-v4.1-flash-1017-maya-s | markers | 3.000 | 3.000 |  |
| deepseek-v4.1-flash-1017-maya-s | verdict | | | pass |

