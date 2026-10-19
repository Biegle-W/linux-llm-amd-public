# Local LLM reference setups

Graphics models: [one retained Qwen-Image/H3 set and ComfyUI paths](linux/graphics/README.md); 70.40 GiB on Shared SATA. Both families passed ComfyUI generation on the two RX 7900 XTX cards.

Reference hardware configurations, inference-engine setup, reproducible tuning and measured performance for Linux and Windows.

Image/video setup: [ComfyUI walkthrough](linux/hardware/IMAGE-VIDEO-SETUP-2026-10-18.md) and [current graphics inventory](linux/hardware/UNSLOTH-MODEL-INVENTORY-2026-10-18.md). ComfyUI is installed; [generation results](linux/graphics/VALIDATION-2026-10-18.md) and [launch instructions](linux/graphics/INSTALL.md) are current.

Strata RAM requirements: [community evidence at 32 GB](linux/hardware/STRATA-LOW-RAM-COMMUNITY-2026-10-18.md). The local
64 GB gate is conservative; dual-XTX operation at 32 GB remains untested.

<!-- comfyui-validation-2026-10-18 -->

| Graphics validation | Shape / base steps | Denoising | Total including loading |
|---|---|---:|---:|
| Qwen-Image 2.1 BF16 | 512x512 / 40 | ~13 s | 100.9 s |
| MiniMax H3 INT8 | 608x352, 39 frames at 24 fps / 20 | ~29 s | 232.4 s |

Both passed coherent output checks; H3 also produced finite stereo audio.
Single validation runs on 32 GB RAM with SATA weights; H3 staged through swap.
These are staged two-GPU component workflows, not TP or maximum-capacity tests.
[Methods, versions and limits](linux/graphics/VALIDATION-2026-10-18.md).

<!-- freetoken-rocm-2026-10-18 -->
**October 18: FreeToken removed at the user's request.** Runtime, Desktop app,
launchers, saved app data and caches are removed. Shared models and other engines
remain. [Historical measurements and limits](linux/hardware/FREETOKEN-RETIRED-2026-10-18.md).
<!-- /freetoken-rocm-2026-10-18 -->

<!-- moe-offload-2026-10-18 -->
**October 18 current MoE policy:** Qwen 35B-A3B, Empero and Nemotron Bolt now
use CPU expert storage plus real GPU hot-expert caches on **both RX 7900 XTX**
cards through llama.cpp HIP. Each has **262,144 tokens allocated**; arithmetic,
JSON, tools and approximately 64K retrieval passed. Full 256K usage is untested.
Dense Qwen 27B/Muse and SGLang/vLLM settings stay as before. Strata Q3 remains
gated until 64 GB RAM and dual-HIP validation. Earlier GPU-only rows are historical.

| Current MoE API ID | Context allocated | Short code decode t/s | ~64K retrieval prefill t/s |
|---|---:|---:|---:|
| `qwen3.6-35b-a3b` | 262,144 | 96.7 | 417.9 |
| `nemotron-3.5-bolt` (Q4_K_M) | 262,144 | 35.7 | 424.0 |
| `empero-qwen3.8-35b-a3b` | 262,144 | 104.9 | 457.8 |

Nemotron now uses **Q4_K_M**, 12 CPU expert layers, a 7 GiB GPU cache ceiling
and layer split 21:19. [Replacement, measurements and source](linux/hardware/NEMOTRON-Q4-2026-10-18.md).
Its retired IQ2 results remain in the historical report.

Single runs with differing short output lengths; not matched speed rankings. CPU/cache
placement, memory limits, measured token counts and both forums' direct sources:
[validation report](linux/hardware/MOE-OFFLOAD-2026-10-18.md). The normal llama launcher
selects Vulkan for dense models and HIP for MoEs; DSH model IDs remain unchanged.
<!-- /moe-offload-2026-10-18 -->

<!-- cleanup-review-2026-10-18 -->
**October 18 workspace cleanup completed:** removed the five user-approved
groups of obsolete NVIDIA originals, CUDA caches, downloaded installers,
unselected experiment build/cache files and UV package cache. Observed NVMe
recovery: **55.58 GiB**. Current models, AMD runtimes/toolchains and compiled
kernel caches, Strata preparation and private state are preserved.
[Exact scope and checks](linux/hardware/CLEANUP-REVIEW-2026-10-18.md).
The verified [NVIDIA recovery archive](linux/hardware/NVIDIA-ARCHIVE-2026-10-18.md)
remains on Shared SATA (10.16 GiB). Historical setup records, patches and benchmarks
remain in Git for future reference.
<!-- /cleanup-review-2026-10-18 -->

<!-- consolidated-handoff-2026-10-18 -->
**Shared handoff consolidated October 18:** use the single
[current Linux/Windows-client guide](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md).
It reconciles eight active profiles, both AMD cards, current contexts, vLLM's
startup fix, client/API/SSH access and deferred/retired setups. Nine original
Shared documents are preserved in a dated archive; their old settings are historical.
<!-- /consolidated-handoff-2026-10-18 -->

<!-- vllm-startup-2026-10-18 -->
**October 18 vLLM startup fix:** the desktop terminal was closing on a 21 GiB
VRAM admission refusal with about 20.78 GiB free on the display GPU. The validated
profile now uses utilization 0.82 and a 20 GiB admission threshold per card.
TP2, 65,536 context, MTP3 and fixed 3.5 GiB KV per GPU are preserved. Long retrieval,
tools/JSON and prefix caching passed with GPU-resident weights. Startup host
swap was observed on the 32 GB system; see the validation limits.
Desktop startup errors are logged and remain visible until Enter; CLI/SSH failures still return normally.
[Diagnosis, validation and limits](linux/hardware/VLLM-STARTUP-2026-10-18.md).
<!-- /vllm-startup-2026-10-18 -->

<!-- level1-tests-2026-10-17 -->
**October 17–18 Level1Techs candidate tests:** current production profiles are
retained. All model trials use both RX 7900 XTX cards and 65,536 configured
context; timed book depth reaches 16K plus the prompt/template. All rates are t/s.

| Profile | Code / prose decode | Book PP / decode, depth 0 | Book PP / decode, depth 16K |
|---|---:|---:|---:|
| Current vLLM, MTP3 | 133.1 / 78.5 | 1556.0 / 92.6 | 1457.4 / 67.5 |
| llama.cpp Vulkan, MTP3 | 79.4 / 45.5 | 1171.1 / 50.4 | 1031.3 / 51.5 |
| llama.cpp HIP native, MTP3 | 67.0 / 40.9 | 1150.1 / 38.8 | 1001.8 / 36.0 |
| llama.cpp restored rocWMMA | 65.8 / 35.3 | 979.7 / 44.4 | 465.7 / 46.7 |
| Radiance ROCM_ATTN/AITER, MTP3 | 95.3 / 60.4 | 1606.6 / 60.0 | 1264.5 / 21.5 |
| vLLM queue cap 1 trial | 124.7 / 73.6 | 1577.4 / 88.9 | 1420.5 / 64.8 |

Three timed runs plus warm-up per workload; the HIP native/rocWMMA pair is
matched, while cross-engine rows compare complete profiles and quant/cache
formats differ. Restored rocWMMA passed 84 CPU-reference cases but reduced long
prefill speed; Radiance used the existing GPTQ model. P2P remains unavailable;
manual fan A/B still needs administrator access. See [measurements, sources and
limits](linux/hardware/LEVEL1-TESTS-2026-10-17.md).
<!-- /level1-tests-2026-10-17 -->

**Research sources:** [Level1Techs](https://forum.level1techs.com/) and
[lcz.me](https://lcz.me/) are now part of the standing HIP/ROCm/C++ research
workflow. See the [source review and optimization decisions](linux/hardware/FORUM-OPTIMIZATION-SOURCES.md)
for direct posts, upstream code, applicability and local validation status.
Forum-derived changes must retain citations in both repositories.

<!-- vllm-tuning-2026-10-17 -->
**October 17 vLLM optimization — current:** Qwen3.8-27B keeps its INT4 model weights and now uses **BF16 KV**, compiled MTP3, tuned Radeon prefill tiles and 2,048-token prefill chunks on both RX7900XTX cards. Context stays **65,536 tokens**; KV budget is 3.5 GiB per GPU. The existing vLLM launcher and DSH model ID `qwen3.8-27b-vllm` use this profile.

| Matched benchmark | Original profile | Optimized profile |
|---|---:|---:|
| Code decode, median t/s | 79.06 | 131.34 |
| Prose decode, median t/s | 42.27 | 77.46 |
| Book PP2048 estimate, t/s | 1,114.44 | 1,585.23 |
| Book decode, mean t/s | 38.97 | 88.93 |

Three timed runs plus excluded warm-up, saved NVIDIA code/prose prompts and sampling; separate seeded llama-benchy book workload. The tuned INT8-cache profile took 130.38s TTFT on the same 64,033-input marker probe; BF16 took **53.73s** and returned all markers correctly. Small functional and numerical/graph checks passed; rates depend on text and speculative acceptance. No sampled VRAM spill or backend-owned post-load swap growth in the selected run. DSH selection and connection settings are preserved. See [measurements, configuration and limits](linux/hardware/VLLM-TUNING-2026-10-17.md).
<!-- /vllm-tuning-2026-10-17 -->

**Earlier October 17 clean retry — SGLang retained; vLLM superseded above:** SGLang MTP now uses **MTP3**
and the repaired unified verifier at **40,960 tokens**. DFlash2 uses the same
validated repair at **65,536 tokens**. Both retain GPU prefix caching and TP2.
vLLM retains 65,536 tokens/MTP3 and now defaults to RCCL `Simple` for its small
measured gain; SGLang keeps automatic protocol selection. This supersedes the
earlier October 17 MTP2/standard-verifier selection below.

| Selected Qwen profile | Code / prose median decode t/s | Context |
|---|---:|---:|
| SGLang DFlash2, repaired verifier | 205.59 / 71.84 | 65,536 |
| SGLang MTP3, repaired verifier | 114.57 / 66.05 | 40,960 |
| vLLM MTP3, RCCL Simple | 79.16 / 42.50 | 65,536 |

Three warm 256-token runs per task, saved NVIDIA prompts, temperature 0.6,
top-p 0.95, seed 42, thinking disabled. Repairs passed numerical/graph checks
on both GPUs, stronger JSON/reversal/tools checks and near-40K/64K retrieval.
No sampled VRAM spill or post-load swap growth in the repaired runs. Book-based
benchmark gains were smaller and variable; these rates are not universal.
DSH currently defaults to vLLM; select **Local SGLang /
`qwen3.8-27b-sglang-dflash2`** for the faster measured profile. Its saved selection
is preserved. GPU0 reached 108°C hotspot and SMU reported hotspot-limit activity;
a cooling A/B test is still needed to quantify any associated slowdown.
[Full comparison, forum differences and limits](linux/hardware/CLEAN-TUNING-2026-10-17.md).

**October 17 Harness update:** DeepSeek Harness is pinned to
`@deepseek-ai/dsh@0.2.1-rc.2`, the newest official npm prerelease checked on
October 17 (`next` tag), upgraded from `0.1.5-rc.2`. Private Node.js remains
24.21.0. The normal launcher, authenticated web page, four frontend assets and
native terminal smoke check passed. All eight local models, default selection,
chat/session files, stored data and credentials were preserved. This release
imports `data/settings.yaml` into `data/profiles/web/cordis.patch.yml` and retains
`settings.yaml.imported`; the configuration helper now refreshes that profile
without recreating legacy settings. Two configuration regression tests passed.
No inference throughput or model-generation tests were repeated for this UI
upgrade. Harness was stopped after validation; launch it normally when needed.

**Earlier October 17 protocol/MTP tests (superseded selection):** production settings then remained unchanged.
SGLang MTP2 auto measured **88.29 code / 66.30 prose t/s**; forcing RCCL Simple
measured **87.34 / 65.92**; MTP1 measured **57.37 / 49.31**. These are medians
of three warm 256-token runs using the saved NVIDIA prompts and sampling.
Arithmetic, ascending/descending JSON and tool round trips passed in all three
completed cases. Both GPUs held model allocations, with no sampled VRAM spill.
RCCL integrity checks passed for auto and Simple; no consistent latency gain.
MTP3 startup hit the host-memory guard while Unsloth Studio competed for RAM.
The optimized-verifier attempt was cancelled during loading; DFlash2/vLLM
protocol comparisons remain untested. This is not evidence of MTP3 or verifier
incompatibility. Keep MTP2, auto protocol and standard verification. No workers
remain running. [Measurements and limits](linux/hardware/DUAL-TUNING-2026-10-17.md).

**October 17 motherboard update:** MSI MPG Z690 CARBON WIFI, two RX 7900 XTX
24 GB cards, both CPU-connected at **PCIe 4.0 x8**. There is still 32 GB system
RAM; another 32 GB is pending. ROCm P2P remains unavailable.

**October 17 P2P diagnosis:** the 13600KF graphics root ports lack documented
P2P memory read/write routing. amdgpu rejects the cross-root topology; both HIP
peer queries remain false with fine-grain PCIe enabled. Large BARs and kernel
P2P options are already enabled. The proposed remedy while retaining this CPU
and board is a real active PCIe switch shared by both GPUs, pending hardware and
transfer validation. No software fix, kernel/BIOS change or speedup was deployed.
[Evidence and switch requirements](linux/hardware/PCIE-P2P-2026-10-17.md).

**October 17 SGLang tuning:** DFlash2 now has a **65,536-token** context,
GPU prefix caching and 2,048-token prefill chunks. MTP retains **40,960 tokens**
and now also caches prefixes. Both use both RX 7900 XTX cards. Near-window
retrieval, arithmetic, JSON and tool-call checks passed with no sampled VRAM spill.
Eight profiles remain enabled; DFlash2 remains the SGLang default and llama.cpp
Qwen Q4 remains the DSH default. HiCache and Strata wait for the RAM upgrade.

| Current SGLang profile | Context budget | Inventory / code / prose decode t/s | Cold / repeated 8K TTFT |
|---|---:|---:|---:|
| DFlash2, chunk 2,048, GPU prefix cache | 65,536 | 104.23 / 200.57 / 60.12 | 5.564 / 0.292 s |
| MTP2, chunk 512, GPU prefix cache | 40,960 | 74.46 / 89.32 / 66.18 | 5.977 / 0.111 s |

Decode values average two short 256-token samples per workload; TTFT values are
single retrieval probes, not pure prefill throughput. DFlash2's near-64K input
passed in 66.6 seconds; MTP's near-40K input passed in 37.0 seconds. Short decode
is broadly comparable to the DFlash2 16K baseline, but the selected profile's
prose mean was 2.8% lower. Large prompts still take time to process; cache gains
require a matching prefix and disappear when the worker unloads.
[Settings, comparison and limits](linux/hardware/SGLANG-DUAL-CONTEXT-2026-10-17.md).

## Previous motherboard results — October 16

Every enabled model now uses **both RX 7900 XTX cards**. llama.cpp splits layers
1:1 with GPU-resident weights; SGLang and vLLM use ROCm tensor parallelism 2.
The existing Desktop/PATH launchers and separate DSH launcher remain in use.
Seven profiles passed arithmetic, ordered JSON and tool round-trip checks.

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

**On the previous motherboard, SGLang MTP2 was blocked** after repeatable HIP
buffer/index failures. It was hidden from DSH, Turnstone and API model lists until the October 17 retry passed. SGLang defaults to the
working DFlash2 profile. vLLM and llama.cpp retain working MTP. Strata remains
deferred until the planned RAM expansion and dual-HIP validation; its Q3 assets are preserved.

The second card is behind a chipset PCIe 4.0 x4 link and neither card exposes
ROCm peer access. Both-card execution does not guarantee higher speed. The
isolated RCCL compatibility library fixes initial collective failures without
replacing the system/SDK library. See the [migration report](linux/hardware/UPGRADE-DUAL-7900XTX.md)
and [sanitized result data](linux/hardware/dual-amd-2026-10-16.json).

**Historical single-AMD SGLang context update (earlier October 16):** `qwen3.8-27b-sglang` now serves **40,960
total tokens** on one RX 7900 XTX, retaining MTP2 and BF16 KV. The tested static
memory fraction is 0.92, with a 23 GiB free-VRAM loading guard. A 38,410-token
retrieval request passed in 51.94 seconds; peak VRAM was 22.60 GiB with no sampled
spill. Fresh short decode means: 53.50 inventory / 61.93 code / 42.78 prose t/s.
The fresh 16K baseline was 53.74 / 62.18 / 44.66 t/s, so this is not a promise of
zero slowdown. FP8 was tested and not selected because of its workload-dependent
speed penalties. DFlash2 remains 16K BF16; vLLM and llama.cpp are unchanged.
[Full comparison and limits](linux/hardware/SGLANG-CONTEXT-2026-10-16.md).

**October 16 model-folder organization:** both SGLang and vLLM share
`models/Qwen3.8-27B-W4A16-AutoRound-GPTQ/`. SGLang's DFlash2 drafter now lives in
`models/drafts/Qwen3.8-27B-DFlash2-W4A16/`. The former empty `models/HyperQwen/`
folder was removed. This was an in-place rename on Linux NVMe; all model file
inodes and sizes were verified unchanged. SGLang's profile and benchmark helper
use the new location. No model was loaded or benchmark rerun; model weights
remain ignored by Git.

Sanitized Linux and Windows launchers, configuration examples, and model-switching
helpers for local OpenAI-compatible inference. This repository starts with fresh
history. It contains no model weights, installed runtimes, personal connection
settings, chat sessions, or original workstation logs.

These are hardware-specific reference configurations, not a universal installer.
Adapt paths, GPU selection, memory budgets and runtime versions before launching.

## Linux

Official upstream logos/favicons replaced the initial custom artwork on
October 18 for llama.cpp, SGLang, vLLM, Strata Q3, dsh and Turnstone.
[Logo sources, pinned checksums and original licenses](linux/launchers/icons/README.md)
are retained with the setup. Assets are unchanged; Turnstone's existing inline
SVG favicon is decoded from its official HTML. Update each absolute `Icon=` path
when moving the installation. Backend commands and model settings are unaffected.

The `linux/` tree corresponds to a runtime workspace at `/opt/local-llm`.
Copy its contents there or update the example absolute paths consistently.
The current reference hardware is two RX 7900 XTX 24 GB cards. Both participate
in each active model; the earlier RTX 4070 is retired. RAM remains 32 GB.

| Backend | Model / strategy | Context |
|---|---|---:|
| SGLang ROCm | Qwen 27B GPTQ, MTP2 — restored on Z690 | 40,960 |
| SGLang ROCm | Qwen 27B GPTQ, DFlash2 W4A16 drafter | 16,384 |
| vLLM ROCm | Qwen 27B GPTQ, compiled MTP3, BF16 KV | 65,536 |
| llama.cpp Vulkan | Qwen 27B Q4, MTP3 | 65,536 |
| llama.cpp Vulkan | Muse, Qwen MoE, Empero | 32,768 |
| llama.cpp Vulkan | Nemotron Bolt | 65,536 |

The Qwen GPTQ checkpoint and the DFlash drafter belong under
`/opt/local-llm/models` on Linux storage. GGUFs used by both operating systems
belong under the example shared path `/mnt/llm-models`. `dsh/shared_storage.py`
requires a real shared-drive mount path and UUID: replace
`CONFIGURE_SHARED_DRIVE_UUID` before using shared-storage launchers. Review AMD
PCI-device paths and GPU discovery in the guards on your machine.

The SGLang profiles use standard Triton verification
(`SGLANG_RDNA_VLLM_VERIFY=0`). The optimized verification adapter produced invalid
ordered-number output in the earlier single-card configuration. DFlash uses eight draft
tokens, a 2,048-token draft window, two recurrent-state slots and disabled prefix
caching. Repeated conversation history must therefore be processed again.
Both active ROCm launchers require 21 GiB free VRAM on each card at startup.

Runtime versions used for these measurements:

- [Radeon SGLang fork](https://github.com/StevenChenSE/sglang), branch
  `gfx1100-support`, commit `f84475ccf593087df3d1da13c9e675eadee12352`.
- vLLM ROCm nightly `0.32.0rc1.dev190+g3f1bcfd82.rocm723`.
- [llama.cpp](https://github.com/ggml-org/llama.cpp), commit
  `f12aaa344c971556ec35be054d7aac1d901fd510`.
- Private ROCm SDK layout 7.2.3 and GCC 14.4 host toolchain, as referenced by the
  environment/build scripts. Obtain these dependencies separately; they are not
  included here. Inspect build scripts and requirements before installation.

Install the runtime dependencies into the paths expected by the wrappers,
configure the model locations, and initialize private harness settings with
`dsh/configure_local.py`. The `bin/` commands and `launchers/` entries are examples
for separate backend and DSH launchers. Backend switching targets only configured
inference workers. DSH and the network gateway are separate processes.
HyperQwen is retired from the current Linux setup: its CUDA runtime, launchers
and profiles were removed after its unused target. Old SGLang/vLLM CUDA
environments, the old llama.cpp CUDA build and obsolete SGLang Flash-Next
source/dependencies were also removed. Active AMD runtimes are preserved.
See the [cleanup record](linux/hardware/RETIRED-SETUPS-2026-10-16.md). The obsolete LowLatency checkpoint,
separate Qwen MTP GGUF and unused Bolt vision projector were also removed from
the active machine. Historical NVIDIA profiles remain as reference configurations.
The SGLang DFlash2 drafter is still required.

Strata's Q3 assets are preserved, but its profile is disabled until the planned 64 GB RAM is installed
and the AMD HIP candidate is validated. See the [RAM-capacity preparation](linux/hardware/STRATA-AFTER-RAM.md)
for the inactive AMD-only 32K candidate and read-only readiness check. The HIP
build passed AMD device detection and a 64 MiB allocator self-test. No Strata
model load or new speed benchmark was performed during preparation.

## Previous NVIDIA setup

The [linux-nvidia/](linux-nvidia/README.md) archive contains the previous RTX 4070
12 GB + RTX 3060 12 GB / 64 GB RAM configuration: CUDA llama.cpp, SGLang, vLLM,
HyperQwen and Strata, plus separate DSH/Turnstone launchers. It includes historical
TP2/offload profiles, compatibility patches and [pinned build notes](linux-nvidia/BUILD.md).
Use it as an alternative to `linux/`; both use the same example workspace and ports.
It does not change the current AMD configuration or restore retired model files.

## Windows

The `windows/` directory contains configuration and PowerShell/Python helpers
from a Windows setup. Use a workspace such as `C:\Local-LLM`, with shared models
under `D:\GGUF-Models`. Download the runtimes named by the configuration separately.
Start Local LLM.cmd and Start Strata.cmd are the backend entry points.

These retained Windows profiles were validated on a previous two-NVIDIA-GPU
configuration. They have not been migrated or retested for the mixed AMD/NVIDIA
hardware above. Review GPU splits and capacity before using them. Windows syntax
and runtime execution require validation on Windows; this publication was prepared
on Linux.

## Clients and private configuration

The Linux gateway exposes an authenticated OpenAI-compatible API on port 10000.
Connection examples must use your own host address and a privately generated key:

```text
http://YOUR_LLM_HOST:10000/v1
```

`linux/network/configure.py` discovers local LAN/Tailscale addresses and writes
ignored private state. Review the generated network policy before enabling the
service. Do not expose unprotected inference ports to the public Internet.
Windows network helpers maintain their own ignored forwarding state. Strata's
placeholder SDK key is not authentication; access must be restricted separately.

## Saved benchmark results

These tables summarize existing measurements only; no benchmarks were rerun for
publication. **Prefill** processes input; **decode** generates output. Rates are
in tokens per second (t/s). **TTFT** is time to first visible output, including
request handling, prefill and the first decode step. Input tokens divided by TTFT
is a proxy, not isolated engine prefill. Configured context is the total window,
not the actual input length tested. Cold model loading is excluded from decode.

### RX 7900 XTX 24 GB — October 16, 2026

One AMD card, 32 GB system RAM, no CPU weight offload. The RTX 4070 is unused.
The five llama.cpp rows use Vulkan, source `f12aaa344c97`, Q8 KV, batch/microbatch
512/128, one slot and two 256-output-token trials. Inputs are 2,878 tokens for
Muse, 3,428 for Bolt and 3,424 for the other rows. Values are observed ranges, not confidence
intervals. The vLLM row uses ROCm `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, GPTQ
W4A16, Q4 KV and two 3,424-input/256-output-token inventory trials.

| Backend | Model / strategy | Context | Engine prefill t/s | Decode t/s |
|---|---|---:|---:|---:|
| llama.cpp Vulkan | Qwen 27B Q4, MTP3 | 65,536 | 802–804 | 82.4–82.5 |
| llama.cpp Vulkan | Muse Glimmer 30B | 32,768 | 786–790 | 44.0 |
| llama.cpp Vulkan | Qwen 35B A3B, MTP3 | 32,768 | 1,888–1,891 | 163.3–163.6 |
| llama.cpp Vulkan | Empero 35B A3B, MTP3 | 32,768 | 1,837–1,840 | 203.3–203.6 |
| llama.cpp Vulkan | Nemotron Bolt 74B A9B | 65,536 | 804–807 | 75.2–75.4 |
| vLLM ROCm | Qwen 27B GPTQ, MTP3 | 65,536 | Not separately recorded | 29.68–34.68 |

vLLM's input/TTFT proxy was **668–677 t/s**. Its short test ran alongside CPU
compilation, so the timing is indicative. The 59,995-input-token retrieval check
took **529.54 seconds total**; this is a capacity result, not a sustained decode
benchmark. Different quantization, cache settings and measurement methods limit
cross-engine comparisons. The storage move to NVMe was functionally checked but
not rebenchmarked; these timings predate it.

#### SGLang context comparison — later October 16 tests

Two 512-output-token trials per short workload, same AMD GPU/runtime/checkpoint.
MTP BF16 **40K** is now active. FP8 was measured but not selected. All rows passed
the limited functional suite; DFlash FP8/32K was only tested to a 13K input depth.

| Strategy / KV | Context | Inventory t/s | Code output t/s | Prose t/s | Peak card VRAM GiB |
|---|---:|---:|---:|---:|---:|
| DFLASH FP8 | 32,768 | 56.62 | 111.34 | 46.90 | 22.68 |
| MTP BF16 | 16,384 | 53.74 | 62.18 | 44.66 | 20.99 |
| MTP BF16 | 32,768 | 53.37 | 61.92 | 43.52 | 22.06 |
| MTP BF16 | 40,960 | 53.50 | 61.93 | 42.78 | 22.60 |
| MTP FP8 | 32,768 | 38.79 | 50.20 | 40.79 | 20.99 |

The same 30,233-token retrieval request took 156.79 seconds with FP8/32K and
37.92 seconds with BF16/32K. BF16/40K retrieved all markers from 38,410 input
tokens in 51.94 seconds. These are total request times, not pure prefill rates.
40K inventory/code speed was close to the fresh 16K baseline; prose averaged
about 4% lower. No sampled VRAM spill. See the [full context report](linux/hardware/SGLANG-CONTEXT-2026-10-16.md)
for limits, exact settings, and machine-readable results.

#### Qwen speculative decoding by workload

Same-day comparison: two synthetic 512-output-token trials per workload,
temperature zero, warm execution. Values are mean approximate streaming decode
rates. SGLang uses the Radeon fork `f84475ccf593`, GPTQ W4A16, BF16 KV and corrected
standard verification. These earlier measurements used 16K for both SGLang profiles.
The later MTP context comparison below supersedes its 16K production setting.
These are short workloads, not filled-context tests.

| Configuration | Inventory t/s | Code-copy output t/s | Prose t/s |
|---|---:|---:|---:|
| llama.cpp Q4 MTP3 | 82.0 | 104.9 | 57.0 |
| SGLang GPTQ MTP2, corrected verification | 53.9 | 62.2 | 46.4 |
| SGLang GPTQ DFlash2, no prefix cache | 83.0 | 147.9 | 45.9 |

Independent prefill timings were not recorded in this comparison. DFlash2's
large code-copy gain did not extend to prose. Its disabled prefix cache also
means conversation history is processed again. Both SGLang profiles passed
arithmetic, ordered JSON, tool round trips, authenticated streaming and
14,500-token retrieval; MTP → DFlash2 → MTP switching passed. An n-gram + MTP
llama.cpp trial showed no useful improvement on these inputs. These are focused
functional checks, not a broad model-quality evaluation.

### Previous RTX 4070 12 GB + RTX 3060 12 GB

Historical dual-NVIDIA setup with 64 GB RAM. SGLang, vLLM and HyperQwen use TP2
without CUDA P2P; llama.cpp uses layer splitting, sometimes with CPU expert
offload. Strata uses its GPU split and expert paging. The following results
**predate the October 14 nightly update** recorded in
[the NVIDIA build notes](linux-nvidia/BUILD.md); they are not speed claims for
those newer builds or for the current AMD machine.

| Measured engine | Model / strategy | Tested configuration context | Prefill t/s | Decode t/s | Date / sample |
|---|---|---:|---:|---:|---|
| Strata 0.1.39 | Flash-Next IQ3_XXS, MTP | 131,072 | 55.4 / 56.2 | 48.8 / 43.9 | Oct 5; code/prose, 192 output tokens each |
| llama.cpp v0.5.0 | Qwen 27B Q4, MTP | 65,536 | 49.2 / 123.7 | 53.5 / 32.0 | Oct 5; code/prose, 192 output tokens each |
| llama.cpp v0.5.0 | Muse Glimmer 30B | 131,072 | 291.1 | 23.6 | Oct 1; smoke, 70 input / 93 output |
| llama.cpp v0.5.0 | Qwen 35B A3B, partial offload/MTP | 262,144 | 72.7 | 26.2 | Oct 1; smoke, 26 input / 3 output |
| llama.cpp v0.5.0 | Nemotron Lightning, partial offload/MTP | 1,048,576 | 55.0 | 22.1 | Oct 1; smoke, 30 input / 3 output |
| llama.cpp v0.5.0 | Empero 35B A3B, partial offload/MTP | 262,144 | 105.7 | 32.6 | Oct 1; smoke, 26 input / 3 output |
| llama.cpp v0.5.0 | GPT-OSS-20B | 131,072 | 307.6 | 83.9 | Oct 1; smoke, 81 input / 57 output |
| llama.cpp, older build | GPT-OSS-120B, partial offload | 131,072 | 5.6 | 6.8 | Before Oct 1; 81 input / 32 output; later build unverified |
| SGLang 0.5.21 | Qwen 27B INT4, MTP | 40,960 | Not separately recorded | 83.56 / 51.59 | Oct 7; code/prose medians, 3 × 256 output |
| vLLM 0.30.0 | Qwen 27B INT4, MTP3 | 49,152 | Not separately recorded | 86.04 / 58.01 | Oct 7; code/prose medians, 3 × 256 output |
| HyperQwen + vLLM 0.30.0 | Qwen 27B AWQ, MTP3 | 65,536 | Not separately recorded | 108.3 / 66.8 | Oct 5; code/prose medians, 3 × 256 output |
| HyperQwen + vLLM 0.30.0 | Qwen 27B AWQ, DFlash2 | 65,536 | Not separately recorded | 170.1 / 67.3 | Oct 5; code/prose medians, 3 × 256 output |

All dates above are in 2026. Strata/llama.cpp use native engine timing; the other
engines use `(completion_tokens - 1) / (end - first_visible_output)`. Code/prose
inputs were 29/25 tokens. Brief *smoke* replies, especially three-token outputs,
are not sustained throughput benchmarks. Model, quantization, output length and
CPU placement differ; do not use this table as a controlled ranking. Lightning
and GPT-OSS are retired from the current setup. The archived Strata profile later
increased to 256K; the October 5 measurements above used 128K.

#### Direct HyperQwen comparison — October 5, 2026

Three warm runs per task, 256 output tokens, temperature 0.6, top-p 0.95, seed 42,
thinking off. HyperQwen source `10bb48841806`, 46 patches, isolated vLLM 0.30.0.
The baseline was directly retested in this comparison; it is different from the
October 7 vLLM row above. All profiles use TP2 and INT4 KV. HyperQwen's fast INT4
head and FP16 Mamba state differ from the baseline's INT8 head and BF16 state.

| Profile | Context | Code decode t/s | Prose decode t/s | Code / prose TTFT |
|---|---:|---:|---:|---:|
| vLLM baseline, MTP3 | 32,768 | 86.1 | 53.6 | 70 / 67 ms |
| HyperQwen MTP3 | 65,536 | 108.3 | 66.8 | 94 / 91 ms |
| HyperQwen DFlash2, 7 draft tokens | 65,536 | 170.1 | 67.3 | 66 / 99 ms |

DFlash2 was about 1.98× faster on this code prompt and 1.25× on this prose prompt
than the directly retested baseline. These tests used a **1.5 GiB/GPU DFlash KV
pool**, before the later 1 GiB pool and INT8-MLP optimization in the archived
launcher. Do not attribute these numbers to those later settings.

#### Later NVIDIA optimization — October 15, 2026

HyperQwen on the pinned vLLM 0.31.0 fork, both GPUs, 128 output tokens,
temperature zero, warm kernels. These are saved **TTFT** measurements, not
isolated prefill or decode rates. The precision comparison used explicit dense
prefix retention in both arms; INT8 quantization applied to MLP activations only.

| Input case | W4A16 dense-retention TTFT | INT8-MLP dense-retention TTFT, 1 GiB KV/rank |
|---|---:|---:|
| Fresh 5,237-token documents, mean of two | 8.04 s | 5.93 s |
| Immediate 5,237-token repeats, mean of two | 3.02 s | 2.51 s |
| 21,077 tokens, seed 501; 3,392 tokens cached | 34.33 s | 27.32 s |
| 21,077 tokens, seed 502; no cached prefix | 39.40 s | 30.81 s |

The archive instead selects boundary-only retention because dense retention
evicted a useful second-document prefix. These small samples show a precision
tradeoff under the tested cache policy, not a blanket speedup or validation of
all output quality. The October 5 decode figures above must not be relabeled as
measurements of this later configuration.

#### Longer actual inputs

| Historical profile | Input / output tokens | Engine prefill | TTFT | Decode t/s | Date |
|---|---:|---:|---:|---:|---|
| Strata IQ3_XXS, 0.1.39 | 126,462 / 31 | 2,375.0 t/s | Not separately recorded | 32.8 | Oct 5 |
| llama.cpp Qwen Q4, v0.5.0 | 60,042 / 14 | 687.9 t/s | Not separately recorded | 32.8 | Oct 1 |
| SGLang selected 40K, 0.5.21 | 30,049 / 256 per trial | Not separately recorded | 55.20 s, first request | 33.11, median | Oct 7 |
| vLLM selected 48K, 0.30.0 | 30,049 / 256 per trial | Not separately recorded | 63.54 s, first request | 36.99, median | Oct 7 |
| HyperQwen DFlash2, vLLM 0.30.0 | 59,244 / 256 | Not separately recorded | 159.01 s | 19.2 | Oct 5 |

The short retrieval replies for Strata/llama.cpp establish capacity, not sustained
full-window generation speed. October 7 decode medians include repeated prompts
that can reuse prefixes, while the displayed TTFT is the first request. HyperQwen
had zero prefix-cache hits in its October 5 test; input/TTFT was 372.6 t/s at
59,244 tokens, not isolated prefill. Short-prompt gains do not imply the same
speed at long context. No new Windows benchmark was run or inferred from Linux.

## Publication boundaries

Only selected setup code and example configuration are included. Raw reports,
private Git history, user identifiers, actual host addresses and personal commit
email addresses are omitted. Models, credentials, runtime binaries and generated
state are excluded by `.gitignore`. Git exclusions do not protect files already
tracked: inspect staged content and scan for secrets before every publication.
This repository is associated with its GitHub owner's public account; fresh
history does not make repository ownership anonymous.
