# vLLM dual-Radeon performance tuning — October 17, 2026

The selected Qwen profile uses the existing GPTQ INT4/group64 checkpoint, BF16 activations, BF16 KV/Mamba state, MTP3, TP2, Inductor compilation with full decode graphs, 2,048-token prefill chunks and gated Radeon prefill tiles. The served context remains **65,536 tokens**. KV allocation is **3.5 GiB per GPU**, with **98,114 tokens** reported by the allocator. Weights remain GPU-resident.

## Short-prompt comparison

Three warm timed runs per task plus excluded warm-up; same saved NVIDIA code/story prompts, temperature 0.6, top-p 0.95, seed 42, thinking off, at most 256 output tokens. Rates are medians of external SSE timing, `(completion_tokens - 1)/(stream end - first visible output)`; speculative bursts limit precision. These are complete profile comparisons, not isolated kernel or hardware gains.

| Configuration | Code t/s | Prose t/s |
|---|---:|---:|
| Original: INT4 KV, compilation off, chunk 512 | 79.06 | 42.27 |
| INT8 KV, compilation off | 107.59 | 54.88 |
| FP16 activations + INT8 KV, compilation off | 105.38 | 57.31 |
| INT8 KV + compilation, chunk 512 | 130.98 | 71.33 |
| INT8 KV + compilation + Radeon tiles, chunk 2048 | 130.66 | 71.76 |
| BF16 KV + compilation, upstream tiles | 131.35 | 72.14 |
| BF16 KV + compilation + Radeon tiles (selected) | 131.34 | 77.46 |
| BF16 KV + compilation + Radeon tiles, MTP4 | 124.13 | 57.81 |

The selected MTP3 profile improved code/prose medians by **66.1% / 83.2%** over the same-batch original-profile control. The control reproduced the previous saved 79.16 / 42.50 t/s results. Story throughput varies with speculative acceptance and floating-point paths; these are not universal speed guarantees.

MTP4 passed the small correctness checks but was slower (124.13 code / 57.81 prose t/s), so MTP3 is retained.

## Book workload and context

Pinned llama-benchy 0.4.0, source `446dd42fde2ebbaa1d68a0dfe9dc1e5b833f95ad`, fixed text offsets/noise seed 42, PP2048/TG128, temperature zero, one sequence, three runs plus warm-up, no-cache, generation latency mode. PP is the tool’s latency-adjusted estimate. Depth 16,384 adds the prompt and chat template; it is not total input length. The forum author did not publish matching book offsets.

| Configuration | Depth | PP estimate t/s | Decode mean ± std t/s |
|---|---:|---:|---:|
| Original INT4 KV | 0 | 1114.44 | 38.97 ± 2.81 |
| BF16 KV, upstream tiles | 0 | 1445.83 | 83.31 ± 1.37 |
| BF16 KV, upstream tiles | 16,384 | 825.40 | 62.12 ± 7.80 |
| INT8 KV, tuned tiles | 0 | 1449.57 | 83.16 ± 2.75 |
| INT8 KV, tuned tiles | 16,384 | 945.73 | 57.90 ± 8.06 |
| Selected BF16 KV, tuned tiles | 0 | 1585.23 | 88.93 ± 0.91 |
| Selected BF16 KV, tuned tiles | 16,384 | 1431.67 | 65.13 ± 5.14 |
| BF16 KV, tuned tiles, MTP4 | 0 | 1589.58 | 76.27 ± 2.09 |

The selected profile retrieved all three markers from **64,033 input tokens**, TTFT **53.73 seconds**, compared with **130.38 seconds** for the tuned INT8 profile on the same marker workload. These probes returned only 22 output tokens and do not establish sustained near-limit decode speed. No earlier NVIDIA run used this exact marker request.

## What changed and why

- The original INT4 cache uses a 256-wide Hadamard fallback implemented as several eager PyTorch butterfly stages on this GPU. Its packed-cache path also excludes multi-query MTP verification from split-K. INT8 avoids the Hadamard work; full BF16 cache avoids per-token-head quantized-attention work while fitting the retained 64K context. Model weight precision stays INT4.
- Inductor mode 3 compiles the target and MTP graphs; full decode graphs remain enabled. BF16 activations and Mamba state are retained.
- The gated prefill port follows [JartX’s RDNA3 tile recipe](https://github.com/JartX/vllm/blob/perf/rdna3_full_stack/docs/design/rdna3_full_stack.md), commit `822d27588a69de52abe7a0f624f8b8bf71e5f6c4`. It uses 32/64/128 query-row tiles with 2/4/8 warps and one stage, on gfx1100, head size 256, GQA ratio 6, and BF16/INT8 caches. Small continuation queries keep upstream tile sizing. MTP verification tile sizing is unchanged. Partial query groups are masked in the tuned prefill path to avoid overlapping writes.
- The official nightly already contains the RDNA3 W4A16 linear-kernel adapter. The deployment keeps that wheel plus local patches; the complete JartX fork binary was not built or benchmarked. Standard PYNCCL host transport and `NCCL_PROTO=Simple` remain; no P2P, BIOS, fan, clock or power override was applied.

## Correctness, memory and limitations

Twenty numerical cases across both GPUs and both cache types passed dense FP32 attention comparisons, scattered-page remapping and two graph replays per case; maximum absolute error was **0.00806**, within the recorded BF16 tolerances. Model checks passed arithmetic, ordered JSON 1–12 and 1–100, descending and irregular reversal, and an inventory tool-call/result round trip. The near-64K probe passed. These checks are narrower than a broad accuracy evaluation.

The initial chunk-2048 attempt was stopped by a global post-load swap-growth guard with 18.6 GB available host RAM and no sampled VRAM spill; its HTTP500 followed the guard’s SIGTERM, not a demonstrated model OOM. The harness now guards swap growth in the owned backend process tree, while recording global swap and per-request I/O separately. The 12 GiB startup floor, 2 GiB available-memory floor, 256 MiB VRAM-spill guard and 1 GiB owned-swap-growth guard remain. A repeat without tuned tiles exceeded its original 180-second long-request timeout without a resource alert. Failed/incomplete cases are retained in JSON and excluded from usable-profile rankings.

An experimental fused H256 transform was discarded after its standalone multi-GPU graph/dispatch test process encountered illegal memory access. Its cause was not established and its code was removed. It is not part of the production runtime.

Selected-run telemetry recorded whole-card VRAM peaks of 17.17 / 15.26 GiB, hotspot peaks of 107 / 93°C, and memory-temperature peaks of 103 / 86°C. Sampling found zero nonresident VRAM and zero backend-owned post-load swap growth. Telemetry can miss brief events; these runs do not quantify thermal throttling or isolate CPU/PCIe costs.

## Reproduction and runtime integration

Runtime: `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, ROCm 7.2.3, no-hostcall RCCL 2.27.7, Intel i5-13600KF, dual RX7900XTX CPU PCIe4 x8/x8, 32 GB RAM. Existing MTP vocabulary sharing is retained. `vllm/apply-rdna-prefill.py` accepts only the pinned original/known patched attention source and is idempotent. The launcher enables `VLLM_LOCAL_RDNA_PREFILL=1`; bootstrap verifies the validated source SHA256 before starting. Setting the flag to 0 is the control path. Apache-2.0 attribution and the upstream license are retained.

```bash
vllm/.venv-rocm/bin/python vllm/apply-rocm-fixes.py
vllm/.venv-rocm/bin/python vllm/apply-rdna-prefill.py
sglang/.venv-rocm/bin/python hardware/bench-dual-tuning.py --engine vllm --mode mtp --steps 3 --protocol Simple --vllm-kv bfloat16 --vllm-kv-bytes 3758096384 --compile-mode 3 --chunk 2048 --rdna-prefill --long --benchy-depth 0 16384 --tag repeat
sglang/.venv-rocm/bin/python hardware/test-vllm-production.py --cache
```

Run `hardware/test-vllm-rdna-prefill.py` with the vLLM ROCm Python and `--device 0/1 --kv int8/bf16` for each numerical configuration, with the normal ROCm environment sourced. Normal Desktop/PATH launchers and `qwen3.8-27b-vllm` in DSH remain the same. Model IDs, endpoints and credentials are unchanged; DSH selection is preserved. All test workers are stopped after validation. Runtime binaries, models and raw logs remain ignored.

Production-router validation: **passed**, actual TP2/context/cache/compilation/speculation flags checked, JSON/arithmetic/tool probes passed and no sampled nonresident VRAM.

An identical ~8K marker request restored its GPU prefix cache: initial TTFT 6.502s, repeat 0.528s, with positive server hit-counter deltas and correct retrieval on both requests.

[Sanitized measurements and per-run metadata](vllm-tuning-2026-10-17.json). [Earlier NVIDIA measurements](../../README.md).

## Forum research provenance

The comparison workload was informed by [lcz.me topic 1814](https://lcz.me/topic/1814);
[topic 1252](https://lcz.me/topic/1252) documents the native W4A16/MTP setup. These
are other users' configurations, not matching local runs. The
[Level1Techs and lcz.me source review](FORUM-OPTIMIZATION-SOURCES.md) records
applicability, primary code links and remaining HIP/ROCm/C++ candidates.
