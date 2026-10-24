# Daily engine updates

Every night at 03:00 `llm-daily-update.timer` checks llama.cpp, vLLM, SGLang, Strata and
Maya for newer upstream versions. Each one is built in isolation, benchmarked against the
current production build with the shared method, and kept only when every standard
promotion gate passes (prefill and code/prose decode ≥95% of production, short time to
first token within max(1.25×, +0.05 s), no fewer retrieval markers, zero VRAM spill).
Anything else is rolled back. Newest entries first. Method: [daily-update/README.md](daily-update/README.md).

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

