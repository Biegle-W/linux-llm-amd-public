# Daily engine updates

Every night at 03:00 `llm-daily-update.timer` checks llama.cpp, vLLM, SGLang, Strata and
Maya for newer upstream versions. Each one is built in isolation, benchmarked against the
current production build with the shared method, and kept only when every standard
promotion gate passes (prefill and code/prose decode ≥95% of production, short time to
first token within max(1.25×, +0.05 s), no fewer retrieval markers, at most 64 MiB aggregate observed
worker swap and zero VRAM spill with valid launch-through-shutdown memory telemetry).
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

