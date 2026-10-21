# ROCm 10 / tuning candidates for other engines — October 20, 2026

These are isolated candidates. **Production Strata and llama.cpp stay on ROCm 7.2.3.**
Maya v1.1.19 is already promoted on SDK 7 after its separate gates; SDK 10 lost
its speed test and one DeepSeek fallback stalled. [Maya decision](MAYA-ROCM10-2026-10-20.md).

Hardware: i9-13900KS, 64 GB installed /61.51 GiB OS-visible, two RX 7900 XTX
24 GB on CPU PCIe 4.0 x8/x8, Intel desktop rendering. Purchased switch remains
uninstalled; no direct-P2P change. Existing models, quants, CPU expert backing,
GPU hot caches, contexts and memory guards remain unchanged. One workload at a time.

[Full trials, provenance, memory and thermal coverage](results/rocm10-other-engines-2026-10-20.json).
Native PP and SSE TTFT/decode are different measurements. Three samples per
workload do not establish significance or universal speedups. OS/page/expert
cache state evolves between independent starts, whose ordering is retained.

## Strata: same source and profile

Source [9ae93f7b](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f),
Qwen Flash-Next IQ3_XXS, 13.5 GiB experts, 256K configured /INT8 KV with 32K
resident, MTP3, six workers, both GPU layer groups. Native reserve targets7/8GiB,
actual startup5GiB/card, continuous3GiB/hard1.5GiB,52G no-swap and latched telemetry
remain. Weights/verified expert pack stay on shared NVMe.

| SDK / table | Code t/s | Prose t/s | Native PP t/s | Fresh SSE TTFT s | Actual fresh inputs |
|---|---:|---:|---:|---:|---|
| 10.0.0 / matching100401 | 80.04 | 52.18 | 1185.9 | 6.934 | 8187,8190,8183 |
| 7.2.3 / no table (control) | 75.81 | 54.21 | 918.0 | 8.956 | 8187,8186,8190 |
| 7.2.3 / matching100202 | 79.50 | 49.26 | 1203.6 | 6.836 | 8189,8187,8188 |

Each arm has three 256-cap short code/prose trials and three fresh~8K/64-cap
requests, with excluded warmups and identical expert seeds. Math, synthetic
tool roundtrip, SSE and actual~30K marker retrieval passed; numerical evidence
retains the exact counts. This is not full256K, full-history or normal-launcher
validation for the SDK 10 build. No promotion follows from allocation/throughput.

The first control stopped after short trials because the Strata Python lacked
`tokenizers` for Qwen corpus sizing. Native inference did not fail. Its partial
measurements are preserved separately. The fresh-r2 control and both table arms
use the isolated benchmark Python; native server/context probes continue through
Strata Python. Installed Strata dependencies were not changed.

Tables are pinned with the reviewed Strata source:
[100202](https://github.com/Niko1221/Strata/blob/9ae93f7b1fe989d04a8e404d32cddaeeff10505f/tools/hip/gfx1100-hipblaslt-100202.txt),
[100401](https://github.com/Niko1221/Strata/blob/9ae93f7b1fe989d04a8e404d32cddaeeff10505f/tools/hip/gfx1100-hipblaslt-100401.txt).
Native logs confirm26 tuned rows for7/100202 and43 for10/100401; the control loads no table. Loaded library maps confirm the tested SDK. These compare complete matching SDK/compiler/table configurations; differing table coverage prevents attributing every change to the SDK alone.

## llama.cpp: same source, four HIP MoEs

Source [4c3c5810](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f).
Release/gfx1100/native CPU build flags match: HIP graphs/MFMA enabled, HIP VMM
disabled, RCCL off; CUDA/Vulkan off for this isolated HIP binary. The exact
configured flags and tested binary SHA are retained numerically. Both cards
use the unchanged layer splits; CPU experts/hot caches and q8 KV remain.

Qwen3.6 uses MXFP4_MOE, Bolt Q4_K_M and Empero IQ4_XS; all settings and exact model filenames are retained numerically.

### Shared short/fresh~8K method

| Model | SDK | Configured context | Code t/s | Prose t/s | Native PP t/s | Fresh TTFT s | Actual inputs |
|---|---|---:|---:|---:|---:|---:|---|
| qwen3.6-35b-a3b | 7 | 262,144 | 124.36 | 77.11 | 380.1 | 21.552 | 8186,8189,8191 |
| nemotron-3.5-bolt | 7 | 262,144 | 37.01 | 36.79 | 224.8 | 35.246 | 7927,7923,7924 |
| empero-qwen3.8-35b-a3b | 7 | 262,144 | 119.23 | 73.35 | 395.2 | 20.722 | 8191,8187,8186 |
| qwen3.6-35b-a3b | 10 | 262,144 | 120.12 | 76.71 | 377.3 | 21.713 | 8187,8189,8188 |
| nemotron-3.5-bolt | 10 | 262,144 | 37.34 | 37.16 | 225.3 | 35.188 | 7926,7925,7926 |
| empero-qwen3.8-35b-a3b | 10 | 262,144 | 125.63 | 81.53 | 392.0 | 20.895 | 8186,8187,8187 |

Three timed256-cap short trials per task and three fresh~8K/64-cap markers
per model/SDK, excluding warmups. Allocation256K is not full-window validation.
Dense Qwen Vulkan is excluded; its existing production settings remain unchanged.

### Super IQ3 fixed~8K/256-output method

| SDK / task | Configured context | Actual inputs | PP t/s | External TTFT s | Decode t/s |
|---|---:|---|---:|---:|---:|
| 7 / code | 32,768 | 8108,8108,8108 | 98.55 | 82.287 | 15.92 |
| 7 / prose | 32,768 | 8111,8111,8111 | 98.12 | 82.672 | 16.90 |
| 10 / code | 32,768 | 8108,8108,8108 | 98.67 | 82.189 | 15.91 |
| 10 / prose | 32,768 | 8111,8111,8111 | 98.42 | 82.421 | 16.76 |

This preserves Super’s original workload instead of treating an~8K TTFT as a
short-prompt TTFT. Each task has an excluded32-output warmup and three256-cap
timed requests with prefix reuse disabled. Every timed output contained256 tokens. Super uses the shared NVMe IQ3 copy,
HIP21:19, six CPU threads,2GiB hot cache,32K, no MTP. Super math/JSON/synthetic
tool/stream checks passed. The SDK7 Super helper initially failed an import before any Super load/timing. Only Super was rerun in a fresh owned server; the completed shared-model controls remain unchanged. Its lifecycle and library proof are separate, not backfilled into the earlier shared run. Three other llama models have benchmark arithmetic/
SSE/fresh-marker checks; no broad new kernel-quality or full-window validation
is inferred. Protected production configs were fingerprinted before/after.

## Thermal and memory coverage

Full server lifecycles and per-request samples are distinct. Each row below is
the full candidate server scope; numeric records preserve power/clocks/fans/raw
SMU masks and unavailable sensors. Peaks are sampled, not guaranteed transient
maxima; flags do not quantify lost speed or time throttled. SDK7 shared3 and SDK10 shared3+Super lifecycle peaks have different coverage; use per-request/Super-only records for matching scopes.

| Arm | Samples / errors | GPU0 memory/edge/junction C | GPU1 memory/edge/junction C | CPU package C |
|---|---:|---|---|---:|
| strata-rocm10 | 141 / 0 | 84.0/77.0/96.0 | 80.0/63.0/84.0 | 93.0 |
| strata-rocm7-r2 | 151 / 0 | 79.0/74.0/95.0 | 78.0/63.0/86.0 | 100.0 |
| strata-rocm7-tuned | 140 / 0 | 80.0/74.0/94.0 | 78.0/63.0/84.0 | 100.0 |
| llama-sdk7 shared3 | 535 / 0 | 80.0/72.0/84.0 | 72.0/47.0/60.0 | 77.0 |
| llama-sdk10 shared3+Super | 1348 / 0 | 84.0/77.0/89.0 | 72.0/46.0/60.0 | 90.0 |
| llama-sdk7-Super-r2 | 815 / 0 | 84.0/77.0/90.0 | 72.0/46.0/60.0 | 86.0 |

All completed Strata arms retain zero owned worker swap/spill. Super’s monitor
retains zero swap/spill; other llama models use the unchanged managed continuous
guards and per-request benchmark memory records. No unrelated application, DSH
or gateway was stopped. SDK10 remained isolated; no system package/driver or
global compute-device variable was changed.

## Framework limits and sources

Existing SGLang/vLLM are Python3.12/torch2.13/HIP7.2 with RDNA repairs. No matching
ROCm10 framework stack was installed or benchmarked; native C++ results cannot
be assigned to those engines. An aligned Torch/Triton/extension build and full
profile validation are required. [AMD matrix](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/vllm.html).

[lcz.me1532/95](https://lcz.me/topic/1532/95) reports different SGLang MTP3 workloads;
[lcz.me2032/3](https://lcz.me/topic/2032/3) uses single-XTX Swift1.5/older Strata.
[Level1Techs AMD source index](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053)
has official source pointers, not a matching dual-XTX measurement. None substitutes
for the local tables. [Authors/dates/hardware and primary sources](FORUM-OPTIMIZATION-SOURCES.md).

No production migration is made here; Maya-first/other-engines-unchanged scope
remains in force. Any proposed runtime or table activation needs its own quality,
near-window and normal launcher/frontend/API proof.

## Observed changes and retained production

Relative medians below compare complete tested configurations; they are not statistical significance or causal kernel measurements. The failed-harness short-only control remains available separately and is not selectively substituted for the repaired full control.

- strata_table7: code_decode_tps +4.9%, prose_decode_tps -9.1%, native_prefill_tps +31.1%.
- strata_tuned10_to_tuned7: code_decode_tps +0.7%, prose_decode_tps +5.9%, native_prefill_tps -1.5%.
- qwen3.6-35b-a3b SDK10/7: code_decode_tps -3.4%, prose_decode_tps -0.5%, native_prefill_tps -0.7%.
- nemotron-3.5-bolt SDK10/7: code_decode_tps +0.9%, prose_decode_tps +1.0%, native_prefill_tps +0.2%.
- empero-qwen3.8-35b-a3b SDK10/7: code_decode_tps +5.4%, prose_decode_tps +11.2%, native_prefill_tps -0.8%.
- nemotron-3.5-super-iq3 SDK10/7: code_decode_tps -0.1%, prose_decode_tps -0.8%, native_prefill_tps +0.1%.

Strata’s table raises prefill relative to the untuned control, with a prose-decode tradeoff. The tested10+table does not outperform7+table in every phase. Empero’s higher observed decode makes it a follow-up candidate; earlier7 results and evolving caches reinforce the need for a repeated matching pair and quality/context/normal-launcher checks before attributing or deploying a gain. Other production engines stay7.2.3; Maya alone was source-updated on retained7.2.3.
