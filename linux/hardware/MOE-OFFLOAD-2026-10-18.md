# MoE CPU offload and expert caching — October 18, 2026

The three active MoEs now use CPU-backed expert weights and llama.cpp's real GPU
hot-expert cache on both RX 7900 XTX cards. Dense Qwen 27B and Muse retain Vulkan
GPU-resident profiles. Existing model files, launchers and API model IDs are reused.
The user's requested offload policy supersedes the earlier GPU-only MoE defaults.

## Current 32 GB configuration

Each MoE has 20 alternating expert-bearing main layers backed by pinned system
RAM, with the remaining expert/dense/attention weights on the GPUs. A **12,288 MiB
total cache ceiling** is shared across both cards with layer split 1:1. Actual
allocation is capped by each GPU's host-expert set (table below). Cached copies
also occupy VRAM: offload plus a large cache is not a free reduction in total
memory use. Missed expert matrices are uploaded for GPU computation; this is
CPU weight storage, not a claim that every expert computes on the CPU.
`n-cpu-moe=0` is intentional: explicit tensor overrides select alternating layers
instead of applying a second override to consecutive layers.

HIP is selected for these MoEs. Qwen/Empero retain MTP3; their MTP expert layer
stays on GPU and the draft context does not use the main model's expert cache.
Bolt keeps speculation off. All use Q8_0 K/V, flash attention, one slot,
batch/microbatch 512/128, six CPU threads, `load-mode=none`, `cache-ram=0` and
no prompt checkpoint allocation. Tensor split is incompatible with this native
expert cache; the 1:1 setting describes layer allocation, not TP2.

All three allocated **262,144 total context tokens** and passed arithmetic,
ordered JSON, an actual function-call/result round trip and three-marker
retrieval at approximately 64K input. Full 256K filling, sustained decode there
and general long-document accuracy remain untested. Context includes output.

| API model | CPU expert GiB | Actual GPU cache GiB, total | Short code decode t/s | Retrieval input tokens | Retrieval prefill t/s | Retrieval total seconds | Minimum available RAM GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.6-35b-a3b` | 8.82 | 8.82 | 96.7 (48 tokens) | 63,911 | 417.9 | 153.2 | 14.74 |
| `nemotron-3.5-bolt` | 7.83 | 7.85 | 40.7 (87 tokens) | 63,911 | 526.4 | 122.0 | 16.29 |
| `empero-qwen3.8-35b-a3b` | 7.97 | 7.97 | 104.9 (128 tokens) | 63,911 | 457.8 | 139.9 | 15.79 |

These are single functional probes, not repeated benchmark medians. The short
code outputs have different lengths and cannot be compared as a matched model
speed ranking. Retrieval used uncached repeated inventory records with markers
at the start/middle/end; reported prefill is native prompt timing. Retrieval
followed the short checks, so the expert cache was partially warmed even though
the long prompt had no cached prefix. Its 19-token
answer is too short to establish sustained decode. Worker swap stayed at zero;
sampled VRAM stayed bounded. Dedicated VRAM residency was measured for Empero
and Bolt; it was not sampled in the first Qwen run. See the sanitized
[measurement record](moe-offload-2026-10-18.json).

## Validation and tradeoffs

An initial Vulkan/all-main-experts-CPU 8 GiB-cache trial failed during structured
output with a RADV command-submission/device-loss error. A Vulkan plain-host
128K/16 GiB-cache variant passed but was slower (84.3 prefill t/s at 8K input).
An all-CPU-expert HIP 64K/8 GiB-cache variant passed (192.9 prefill t/s at 8K).
The selected half-CPU HIP profiles passed the larger allocation/retrieval checks.
Those variants differ in placement, cache and context; this is not an isolated
HIP-versus-Vulkan A/B. Previous GPU-only benchmark rows remain historical.

Cold offloaded prefill can be slower than a GPU-resident profile. A larger cache
helps only where expert reuse occurs; each loaded model has its own cache, lost
on unload/switch. Prompt-prefix caching and `cache-ram` are separate mechanisms.
No weights were requantized, experts pruned or routing top-k reduced.

The same llama launcher/router switches its owned native parent between Vulkan
(dense) and HIP (MoE) on demand and publishes all five model IDs throughout.
DSH, Turnstone and the authenticated LAN/Tailscale gateway retain their existing
addresses. Only one model/backend runs at a time; frontend settings/sessions
are preserved. The catalog refresh may require reopening a frontend.

New loads reserve the selected host-expert bytes plus 4 GiB available RAM;
already-loaded requests require 3 GiB. Swap capacity is not counted. An owned
worker monitor stops only the native worker if RAM stays below 3 GiB, owned swap
exceeds 256 MiB or dedicated VRAM spill persists above 256 MiB. The guard never
kills DSH, unrelated applications or arbitrary Python/GPU processes. More host
RAM adds capacity/headroom; it does not make PCIe or memory channels faster.

Normal managed-launcher validation also passed authenticated API generation
for all three MoEs, repeated requests without reloading, and switching back to
dense Qwen/Vulkan. All five llama IDs remained discoverable and the gateway kept
its eight enabled profiles. Both repositories passed 35 hardware/memory-policy
and two DSH-configuration unit tests; 14 backend ownership/switch tests passed
in the operational repository. These checks include refusing low-memory loads
and limiting a memory-guard shutdown to its owned native worker.

After validation, the prior vLLM backend/model was restored in its visible
terminal and authenticated generation passed. DSH remained running with its
protected page returning HTTP 401, as expected without frontend credentials.
The user's current frontend model selection was preserved.

## After the additional 32 GB arrives

The retained Strata Q3 pack has roughly 40 GiB of expert data and remains
disabled on the current 32 GB. Its generated candidate uses **both GPUs**, HIP,
automatic layer split without single-card fallback, CPU-resident/mapped expert
storage and GPU caching. It requires at least 60 GiB OS-visible total and 48 GiB
available RAM. Start at 32K Q8 KV after RAM stability is confirmed; only raise
64K/128K/256K after actual retrieval, tools, memory and throughput validation.
No automatic Strata activation or maximum-context claim follows from installing
RAM. See [Strata readiness and preparation](STRATA-AFTER-RAM.md).

## Forum research and implementation sources

- [lcz.me, guonetnet's Strata setup](https://lcz.me/topic/2059), reviewed October
  18: a single 7900 XTX, Xeon and 64 GB four-channel DDR4 example supports testing
  CPU expert residency/caching. Its CPU/RAM topology and reported speed are not
  measurements or predictions for this dual-card workstation.
- [lcz.me dual-card cache discussion](https://lcz.me/topic/2249/8) describes an
  NVIDIA/NVLink setup; its topology and older split limitations must not be copied
  literally. The retained Strata source permits resident CPU experts with layer split.
- [Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396),
  eduncan911, August 25, 2026, motivates measuring cache misses and CPU/PCIe paths.
  It does not establish gfx1100 compatibility; FreeToken was not installed.
- [Level1Techs 7900 XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
  ivgranite, May 31, describes a single card and 96 GB RAM. Memory headroom and
  one-request testing apply; that capacity and throughput are not our results.
- Native implementation: [expert-cache PR29887](https://github.com/ggml-org/llama.cpp/pull/29887),
  [multi-GPU PR30112](https://github.com/ggml-org/llama.cpp/pull/30112), and
  [pinned cache source](https://github.com/ggml-org/llama.cpp/blob/f12aaa344c971556ec35be054d7aac1d901fd510/src/llama-moe-cache.cpp).
  Installed source already contains these; no new fork or runtime update was needed.
- Strata [AMD HIP guide](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/AMD_HIP.md)
  and [pinned generation code](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/src/program/generate.cpp)
  support preparation only; live dual-HIP validation is still pending.

Full source applicability is retained in [the forum source trail](FORUM-OPTIMIZATION-SOURCES.md).
