# Two RX 7900 XTX migration — October 16, 2026

The user reports installing the second RX 7900 XTX and explicitly requests both
cards for every active model. This supersedes the earlier single-card preference.
After a reboot during the session, Linux and ROCm enumerate two gfx1100 devices
with 24,560 MiB usable VRAM each. The RTX 4070 is no longer detected.

## Hardware and policy

- First GPU: CPU-connected PCIe 4.0 x16 path.
- Second GPU: PCIe 4.0 x4 upstream path through the chipset. Its internal GPU link
  reports x16; that does not change the x4 upstream bottleneck.
- ROCm peer access: false in both directions.
- Kernel: second GPU reports no PCIe atomic-operation support.
- RAM remains 32 GB (about 30.6 GiB usable); keep GPU-resident model weights.
- Strata remains deferred until RAM expansion and its AMD model validation. It is
  not part of the eight active profiles and has not been enabled by this change.

## Runtime configuration

llama.cpp Vulkan uses both devices, `split-mode = layer`, `tensor-split = 1,1`,
and GPU token embeddings. Each card must have at least 18 GiB free before launch.
The HIP alternative is a candidate, not a newly benchmarked default.
SGLang and vLLM use TP2, both ROCm devices visible, and custom all-reduce disabled.
Their headroom guards check both cards (21 GiB each), not a hard-coded PCI address.
SGLang's memory fraction is 0.85; context and speculative settings remain.
Both SGLang profiles disable prefix caching: the MTP cache-tracking path
failed in a PyTorch GPU indexing operation on the chipset-connected card.
Repeated chat history is therefore processed again; this can increase prefill
latency compared with the earlier single-card cached MTP profile.
No fallback to a single card is implicit. Missing cards fail before handover.
The backend switch skips NVIDIA-driver queries when no NVIDIA GPU is present;
its process-ownership boundary is unchanged.

## RCCL compatibility

The stock isolated ROCm 7.2.3 RCCL failed SGLang's first all-reduce before model
loading. A compatible no-hostcall gfx1100 RCCL 2.27.7 passed two-rank FP32/BF16 all-reduce and all-gather (1, 4,096 and 1,048,576 elements) and is installed separately
under `llm-tools/rccl-nohostcall`; system and original SDK libraries are preserved.
`hardware/install-rccl-dual.sh` reproduces the isolated install. It pins release
v0.1.0 from cadamcat/dual-radeon-vllm and source commit
`23c2beb2e200353fda84afa216c2cea2f7c579e9` for the dependency stub.

Binary SHA-256: `0717e4f59d174b89bb6d249ea93e5cfeff75be6f2cadd9260f5a6feabf67dfcb`.
The checksum matches the publisher. Direct extraction of the compressed gfx1100
ELF and successful LLVM note inspection found no `hidden_hostcall_buffer`,
`__assert_fail` or `__ockl_fprintf`; `ncclCommDump` is exported. The upstream
inspection script's llvm-objdump step crashed, so that script was not counted
as a pass. Both GPUs remained visible with the isolated library loaded.

ROCm environment selects the local library through LD_LIBRARY_PATH and explicit
SGLang/vLLM library overrides. `NCCL_P2P_DISABLE=1` and `HSA_ENABLE_SDMA=0` are
scoped to these runtimes. These flags alone do not remove the hostcall issue.
Weights, downloaded binaries, extracted device images and raw logs are ignored.

Sources: [RCCL diagnosis and fix](https://github.com/cadamcat/dual-radeon-vllm),
[deployment notes](https://github.com/cadamcat/dual-radeon-vllm/blob/23c2beb2e200353fda84afa216c2cea2f7c579e9/docs/deploy-vllm.md).

## SGLang KV kernel compatibility

After RCCL initialization succeeded, graph warmup failed on the chipset-connected
card in `store_kvcache`. Its device `assert` introduced a hostcall requirement.
The pinned-source patch in `sglang/apply-rocm-fixes.py` replaces that AMD-only
assert with `if (!(index >= 0 && index < size_limit)) __builtin_trap()`.
The same bounds condition remains enforced, including release builds; CUDA keeps
the original assertion. Source-content cache keys force recompilation. This
patch enabled the DFlash2 profile on both GPUs.

MTP2 remains blocked. Its prefix-tracking GPU indexing failed; disabling prefix
caching exposed a graph-buffer copy failure on rank 1. Per-tensor copy, eager
execution, disabled overlap planning and synchronous scheduling did not fix it.
A narrow Triton copy experiment passed 80 synthetic dtype/size/bounds cases per
GPU but then MTP failed at another PyTorch operation; that experiment was reverted.
No diagnostic copy patches remain. Only the validated KV bounds-trap and existing
MTP weight-sharing patches are retained. The MTP profile is disabled and rejected
before stopping an active worker; DFlash2 is SGLang's default. No TP1 fallback.

## Validation and results

| Model / strategy | Engine | Context budget | Short decode t/s | Sampled peak VRAM GPU0 / GPU1 GiB |
|---|---|---:|---:|---:|
| Qwen3.8 27B Q4 · MTP3 | llama.cpp Vulkan | 65,536 | 56.27 | 9.77 / 10.06 |
| Muse Glimmer 30B Q4 | llama.cpp Vulkan | 32,768 | 34.89 | 8.80 / 7.87 |
| Empero Qwen3.8 35B A3B IQ4 · MTP3 | llama.cpp Vulkan | 32,768 | 111.16 | 10.47 / 10.05 |
| Qwen3.6 35B A3B MXFP4 · MTP3 | llama.cpp Vulkan | 32,768 | 101.11 | 11.86 / 11.02 |
| Nemotron 3.5 Bolt 74B A9B | llama.cpp Vulkan | 65,536 | 47.82 | 10.83 / 11.72 |
| Qwen3.8 27B GPTQ · DFlash2 | SGLang ROCm TP2 | 16,384 | 77.70 | 13.54 / 12.96 |
| Qwen3.8 27B GPTQ · MTP3 | vLLM ROCm TP2 | 65,536 | 53.67 | 13.79 / 13.29 |

These are **single short smoke measurements**, not repeated benchmark averages
or full-context stress tests. Each sample requested at most 256 output tokens;
timing includes emitted reasoning. Muse's throughput sample used all 256 tokens
for reasoning and did not reach a final answer; its separate short correctness
checks passed. No new prefill benchmark was run. Earlier single-card/NVIDIA
results below are historical and are not a controlled speed comparison.
Context budgets are retained, not newly established maximums. Sampled VRAM
includes desktop/runtime allocations and can miss brief peaks.

**SGLang MTP2 is blocked** on this dual-card topology after repeatable HIP
buffer/index failures. It is hidden from DSH, Turnstone and API model lists;
direct requests fail before unloading a working model. SGLang defaults to the
working DFlash2 profile. vLLM and llama.cpp retain working MTP. Strata remains
deferred until RAM expansion and dual-HIP validation; its Q3 assets are preserved.

The second card is behind a chipset PCIe 4.0 x4 link and neither card exposes
ROCm peer access. Both-card execution does not guarantee higher speed. The
isolated RCCL compatibility library fixes initial collective failures without
replacing the system/SDK library. See the [migration report](UPGRADE-DUAL-7900XTX.md)
and [sanitized result data](dual-amd-2026-10-16.json).


- Both GPU allocations were observed for every passing profile.
- FP32/BF16 two-rank RCCL all-reduce/all-gather passed on both cards.
- Hardware/launcher regression checks cover renumbered identical cards, missing
  cards, second-card headroom, absent/present NVIDIA, and blocked profile handling.
- The actual llama.cpp, SGLang and vLLM launchers are checked through their model
  catalog endpoints; workers from validation are stopped afterward.
- Source versions: llama.cpp `f12aaa344c971556ec35be054d7aac1d901fd510`;
  Radeon SGLang `f84475ccf593087df3d1da13c9e675eadee12352`;
  vLLM `0.32.0rc1.dev190+g3f1bcfd82.rocm723`; private ROCm SDK 7.2.3.
- Existing visible terminals, SSH/PATH commands, backend-switch ownership rules,
  API authentication and model storage locations are preserved.
