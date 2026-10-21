# Local LLM hardware, engines and benchmarks

Two reference builds: **current dual AMD** and **archived dual NVIDIA**.
This repository contains sanitized launchers, configuration, build/patch helpers
and saved measurements for Linux, plus historical Windows setup files.
Model weights, installed runtimes, credentials and personal app data are excluded.

- [AMD: latest setup and results](#amd-latest-setup-and-results)
- [NVIDIA: archived setup and results](#nvidia-archived-setup-and-results)
- [Install, launch and connect](#install-launch-and-connect)
- [Complete benchmark history and experiments](linux/hardware/BENCHMARK-HISTORY.md)

Saved **October21,2026 i9/64GB AMD benchmarks** cover the ten currently active profiles with their distinct methods; retired profiles remain historical; older i5/32 GB results remain dated.
The archived NVIDIA measurements retain their original dates and builds.
[Full fresh AMD method, token counts and numeric evidence](linux/hardware/CURRENT-AMD-BENCHMARKS.md).

<a id="saved-benchmark-results"></a>

Maya’s web sidebar now offers **Maya model → GLM or DeepSeek → Switch model**.
The page stays open during guarded reload; both GPUs, 32K contexts and memory
guards are retained. Reopening `dsh` reuses its verified existing frontend and
leaves inference untouched. [Functional validation](linux/hardware/MAYA-WEB-SWITCHING-2026-10-21.md).

## Reading the measurements

**Context** is the configured total token budget: instructions, tools, history,
input and output. An allocated window is not proof of full-window validation;
the long-input tables show the actual lengths tested. K means 1,024 tokens.
**Prefill (PP)** and **decode** are tokens/s. **TTFT** is seconds from request
submission to the first visible output; model cold-start time is excluded from
the warm benchmarks. **—** means not recorded, not zero.

“Code / prose” gives separate workloads in that order. Warm short results are
three-run medians unless a different sample count or smoke method is stated. Native PP comes from engine
timing; **Book PP** is llama-benchy 0.4.0's latency-adjusted estimate for a
2,048-token prompt at depth 0, not native prompt timing. Input divided by TTFT,
prompt-processing duration and total request time are not substituted for TTFT
or native PP. Different rows can use different workloads and output lengths.
These are saved complete-profile results, not a controlled AMD-versus-NVIDIA ranking.

## Current hardware inventory

**i9-13900KS,64 GB RAM (61.51 GiB OS-visible), two RX 7900 XTX 24 GB**, MSI MPG Z690
CARBON WIFI, CPU PCIe 4.0 x8/x8. The PEX88096 switch is purchased but not installed
or validated. Both GPUs participate in every active profile. llama.cpp/Strata
split layers; SGLang/vLLM use TP2 through host transport with direct P2P disabled.
One managed model runs at a time.

## Strata Linux app update and verified Intel desktop — October 20

Managed Strata **0.1.46.1 /9ae93f7b is active** after candidate and normal
Desktop/native-frontend/authenticated-API validation. The user-selected actual
startup minimum is5GiB/card; engine7/8GiB targets, continuous3GiB protection,
52G/no-swap worker, Q3/13.5GiB/256K and both cards remain. Intel UHD770/i915
renders the desktop. The separate App0.2.1/bundled0.1.46 remains installed.

Promotion-batch three-trial medians: native prefill**912.2t/s**, fresh8K TTFT**9.015s**,
code/prose decode**75.28/50.31t/s**. Actual257984-input/256-output retrieval/code
and258266-input cached full-history follow-up passed. Zero owned swap/spill.
Earlier0.1.45 rates retain their original build; no matched A/B speedup is claimed.
[Update, exact versions and validation limits](linux/hardware/STRATA-STARTUP5-2026-10-20.md).

[DeepInfer compatibility assessment — October20](linux/hardware/DEEPINFER-ASSESSMENT-2026-10-20.md): reviewed upstream774ce244 has no ROCm/gfx1100 build path and expects a Hugging Face checkpoint rather than the existing Maya GGUF packs. Research only; no runtime or weight changes.

## AMD: latest setup and results

**Ten active profiles:** five llama.cpp, one SGLang, one vLLM, one Strata, two Maya.
Hardware: i9-13900KS,64GB installed/61.51GiB OS-visible, two RX7900XTX24GB,
CPU PCIe4x8/x8; Intel desktop. Switch installation/P2P status is unchanged.
Super IQ3 is active; retired Muse Q4/Super Q4 and SGLang MTP remain historical.

All selected stacks remain unchanged; no ROCm10.1 candidate passed every performance and validation gate.
[ROCm10.1 comparison, decisions and exact build fingerprints](linux/hardware/ROCM101-2026-10-21.md),
[all trials/thermals](linux/hardware/results/rocm101-2026-10-21.json).
No driver/kernel update or global SDK replacement was performed.

### Installed and measured builds

| Engine | Source / selected stack | Scope |
|---|---|---|
| llama.cpp | [4c3c5810](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f); dense Vulkan, MoE HIP | Dense Vulkan; four MoEs on HIP7.2.3, both GPUs, unchanged expert backing/cache/MTP/contexts |
| SGLang | [f84475cc](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352), retained ROCm7.2.3 stack | TP2 DFlash2/BF16 KV/163840; local RDNA repairs preserved |
| vLLM | 0.32.1rc1.dev36+ge68efc685.rocm72, retained ROCm7.2.3 stack | TP2/compiled MTP3/BF16 KV/163840 |
| Strata | [9ae93f7b/0.1.46.1](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f), ROCm7.2.3 | Q3/13.5GiB/six workers/256K/INT8 KV32K resident; native frontend unchanged |
| Maya | [3384b5e/v1.1.19](https://github.com/mw00/project-maya/commit/3384b5e9366e696e5f23f51772fb94a8a7948e41), ROCm7.2.3 | Both32K Maya-S profiles; original guards/source/quantization retained |
| ComfyUI | [8f04fd6e/0.42.0](https://github.com/Comfy-Org/ComfyUI/tree/8f04fd6ecf4a548937971e840af2a985529fab76), Torch2.15 nightly/packaged ROCm7.2.1 | Normal-RAM image/video controls; browser/native Desktop share this stack |

### Nine profiles using the shared benchmark method

Fresh October21 controls: three timed requests/task and three fresh prefills,
except vLLM's six fixed-seed controls across two starts. Empero's row uses
six retained-control trials across two starts.
One excluded short warmup/task; max256 output, seed42, temperature0.6/top-p0.95,
thinking off. Different tokenizers count the same fresh record workload differently.
Native PP is used for llama.cpp/Strata/Maya; SGLang/vLLM use engine-phase measurements.
External SSE TTFT/decode are separate; model cold-start is excluded.

| Model / quant | Backend / strategy | Context tokens | Actual fresh input | PP t/s | Fresh TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,185–8,188 | 702.1 | 11.670 | 0.124 / 0.123 | 80.28 / 47.73 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP7, cache/MTP3 | 262,144 | 8,183–8,188 | 379.6 | 21.579 | 0.059 / 0.059 | 124.95 / 76.72 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP7, expert cache | 262,144 | 7,923–7,925 | 223.9 | 35.398 | 0.392 / 0.252 | 36.85 / 36.62 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP7, cache/MTP3 | 262,144 | 8,185–8,190 | 395.1 | 20.727 | 0.058 / 0.057 | 122.11 / 74.32 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 163,840 | 8,188–8,190 | 1449.7 | 5.657 | 0.086 / 0.083 | 211.58 / 72.57 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 163,840 | 8,186–8,189 | 1475.2 | 5.562 | 0.068 / 0.075 | 133.92 / 70.91 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP7, overlap/MTP3 | 262,144 | 8,187–8,189 | 908.5 | 9.047 | 0.223 / 0.229 | 77.33 / 53.25 |
| GLM-5.3-Flash Maya-S | Maya HIP7, layer split/MTP | 32,768 | 6,311–6,312 | 532.5 | 12.041 | 0.086 / 0.097 | 17.96 / 16.09 |
| DeepSeek-V4.1-Flash-1017 Maya-S | Maya HIP7, no DSpark | 32,768 | 6,297–6,301 | 187.3 | 33.666 | 0.380 / 0.553 | 6.92 / 7.08 |

These are selected-stack timings, not a universal SDK or source speedup claim.
Earlier October20/i5/NVIDIA measurements retain their original build/method/date.
The new record retains every actual short input/output count, fresh-input/cache metadata,
quality result, source/library fingerprint and thermal sample coverage.

### Super IQ3 using fixed ~8K-input workloads

| Super / workload | Context | Actual input / output | Native PP t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| IQ3_XXS / code | 32,768 | 8,108 / 256 | 98.64 | 82.213 | 15.94 |
| IQ3_XXS / prose | 32,768 | 8,111 / 256 | 98.31 | 82.517 | 16.94 |

Three trials/task, fixed8108/8111-token inputs,256 outputs, cache_prompt=false.
These TTFTs include8K processing and are **not short-prompt TTFT**. Retain HIP7,
21:19 layer split,19.124GiB CPU experts/2GiB GPU cache, six threads, MTP off.

### Context, storage and validation limits

Empero's failed promotion gate is recorded in the new report; its allocated256K window is not a new full-window production proof.
Qwen3.6/Bolt retain256K allocation; latest shared-method probes are8K, with older
~64K retrieval evidence separately dated. Strata's retained selected build has
October20 near257984-input/256-output and full-history validation; its new SDK7
control timings above are fresh8K. The rejected10.1 Strata build was not tested
near256K. SGLang/vLLM retain their previously validated163840 settings; candidate
vLLM10.1 additionally passed160866-input retrieval/160913-input history, but failed
the diverse-seed speed gate and is not selected. No cache-token count or uncached
PP is inferred when the API omits cache usage. Maya retains its earlier near31.5K
history proof, while this batch adds fresh controls rather than new context sizes.

[Full numeric results](linux/hardware/results/rocm101-2026-10-21.json) ·
[Results index](linux/hardware/results/README.md) ·
[Benchmark ledger](linux/hardware/BENCHMARK-HISTORY.md) ·
[Historical i5/32GB AMD](linux/hardware/AMD-BENCHMARKS-2026-10-19.md).

All previous storage/guards/DSH default/PATH/frontend policies are retained.
No weights were downloaded or moved. Streaming Strata/Maya/Super assets stay on
shared NVMe; resident GGUFs on Shared SATA, SGLang/vLLM checkpoints on Linux NVMe.
[Storage evidence](linux/hardware/results/streaming-storage-2026-10-20.json).

### Graphics controls

Normal allowance61.51GiB, same seeded full workflows, one excluded full warmup
and three timed runs/workflow/stack. QwenImage2.1 BF16:512×512/40steps;
MiniMaxH3 INT8:608×352/39frames/20steps/24fps/audio. Both GPUs stage components,
not TP. Server medians: retained/new image23.686/18.331s, video83.831/85.279s.
Video regressed, so retain current ComfyUI. All16 normal outputs pass technical
checks plus sampled visual review; the separate52GiB pilot's HIP fault remains
recorded and did not recur under normal RAM. [Full comparison](linux/hardware/ROCM101-2026-10-21.md).

## NVIDIA: archived setup and results

**RTX 4070 12 GB + RTX 3060 12 GB (24 GB total VRAM), i5-13600KF, 64 GB RAM.**
Both GPUs participated; there was no CUDA P2P/NVLink. SGLang/vLLM/HyperQwen used
TP2 with fallback transport; llama.cpp/Strata split layers and used CPU backing
where configured. [Archived setup](linux-nvidia/README.md).

### Archived installed builds versus measured builds

The final October 14–15 configuration snapshot contains llama.cpp `a0e6dc7384ed`,
Strata 0.1.44.1 / `296b59d2f73c`, SGLang
`0.5.22.dev20261015+ga12814c158`, vLLM
`0.32.0rc1.dev182+g429a3da66`, and HyperQwen `95ee3b64b0df` on vLLM 0.31.0.
[Build instructions and exact pins](linux-nvidia/BUILD.md).
Most saved throughput tests predate that update; the table records their actual
measured versions. The October 15 HyperQwen results are TTFT-only, below.

### Every model/backend with retained measurements

| Model / quant | Measured backend / strategy | Context tokens | Prefill t/s | Short TTFT s, code / prose | Decode t/s | Date / method |
|---|---|---:|---|---|---|---|
| Flash-Next IQ3_XXS | Strata 0.1.40.3, MTP4, INT8 KV | 262,144 | 1,538.5 native at 14,195 input | — | 68.8 / 64.6 code/prose; 71.9 at 14,195 input/1,024 output | Oct 7; 3 warm short runs/task [NH] |
| Flash-Next IQ2_XS, retired | Strata 0.1.39, MTP | 131,072 | 71.7 / 75.8 native short code/prose | — | 68.9 / 60.3 code/prose | Oct 5; 192 output each [NH] |
| Qwen3.8-27B Q4_K_M | llama.cpp v0.5.0, MTP | 65,536 | 49.2 / 123.7 native short code/prose | — | 53.5 / 32.0 code/prose | Oct 5; 192 output each [NH] |
| Muse-Glimmer-30B Q4 | llama.cpp v0.5.0 | 131,072 | 291.1 native | — | 23.6 | Oct 1; 70 input/93 output smoke [NH] |
| Qwen3.6-35B-A3B MXFP4 | llama.cpp v0.5.0, CPU offload/MTP | 262,144 | 72.7 native | — | 26.2 | Oct 1; 26 input/**3 output**, smoke only [NH] |
| Nemotron Lightning MXFP4, retired | llama.cpp v0.5.0, CPU offload/MTP | 1,048,576 | 55.0 native | — | 22.1 | Oct 1; 30 input/**3 output**; 1M allocation unproven [NH] |
| Empero Qwen3.8-35B-A3B IQ4 | llama.cpp v0.5.0, CPU offload/MTP | 262,144 | 105.7 native | — | 32.6 | Oct 1; 26 input/**3 output**, smoke only [NH] |
| GPT-OSS-20B, retired | llama.cpp v0.5.0 | 131,072 | 307.6 native | — | 83.9 | Oct 1; 81 input/57 output smoke [NH] |
| GPT-OSS-120B, retired | Older llama.cpp, CPU offload | 131,072 | 5.6 native | — | 6.8 | Before Oct 1; 81 input/32 output; later build unverified [NH] |
| Qwen3.8-27B INT4/group128 | SGLang 0.5.21, TP2/MTP | 40,960 | — | — | 83.56 / 51.59 code/prose | Oct 7; 3 warm 256-output medians/task [NH] |
| Qwen3.8-27B INT4/group128 | vLLM 0.30.0, TP2/MTP3 | 49,152 | — | — | 86.04 / 58.01 code/prose | Oct 7; 3 warm 256-output medians/task [NH] |
| Qwen3.8-27B AWQ | HyperQwen `10bb48841806` + vLLM 0.30.0, TP2/MTP3 | 65,536 | — | 0.094 / 0.091 | 108.3 / 66.8 code/prose | Oct 5; 3 warm 256-output medians/task [NH] |
| Qwen3.8-27B AWQ | HyperQwen `10bb48841806` + vLLM 0.30.0, TP2/DFlash2 | 65,536 | — | 0.066 / 0.099 | 170.1 / 67.3 code/prose | Oct 5; same method [NH] |

<a id="direct-hyperqwen-comparison--october-5-2026"></a>

Three-token smoke outputs establish that generation ran; they do not establish
sustained throughput or the advertised context capacity. Old Q5/Bonsai setups
have no retained per-model benchmark in this summary; no results are invented.
HyperQwen's October 5 figures predate INT8-MLP and the later 1 GiB/rank DFlash KV
pool. Its directly retested vLLM baseline at 32K measured **86.1/53.6 decode**
and **0.070/0.067 s TTFT** for code/prose; that is a different batch from the
October 7 vLLM row above. [Original comparison and method](linux/hardware/README-ARCHIVE-2026-10-19.md#direct-hyperqwen-comparison--october-5-2026).

### Long input and later HyperQwen TTFT tests

| Model / measured backend | Context | Actual input / output tokens | Native prefill t/s | TTFT s | Decode t/s | Date |
|---|---:|---:|---:|---|---|---|
| Flash-Next Q3 / Strata 0.1.40.3 | 262,144 | 257,850 / 22 | 2,266.2 | — | Not a sustained decode test | Oct 7 [NH] |
| Flash-Next Q3 / Strata 0.1.39 | 131,072 | 126,462 / 31 | 2,375.0 | — | 32.8, short retrieval | Oct 5 [NH] |
| Qwen27B Q4 / llama.cpp v0.5.0 | 65,536 | 60,042 / 14 | 687.9 | — | 32.8, short retrieval | Oct 1 [NH] |
| Qwen27B INT4 / SGLang 0.5.21 | 40,960 | 39,484 / short retrieval | — | 78.79 | — | Oct 7 [NH] |
| Qwen27B INT4 / vLLM 0.30.0 | 49,152 | 47,666 / short retrieval | — | 120.28 | — | Oct 7 [NH] |
| Qwen27B INT4 / SGLang 0.5.21 | 40,960 | 30,049 / 256 per trial | — | 55.20, first request | 33.11 median, repeats may cache | Oct 7 [NH] |
| Qwen27B INT4 / vLLM 0.30.0 | 49,152 | 30,049 / 256 per trial | — | 63.54, first request | 36.99 median, repeats may cache | Oct 7 [NH] |
| Qwen27B AWQ / HyperQwen DFlash2, vLLM 0.30.0 | 65,536 | 59,244 / 256 | — | 159.01 | 19.2 | Oct 5 [NH] |

On October 15, the newer HyperQwen/vLLM 0.31.0 build compared W4A16 versus
INT8-MLP with **dense prefix retention in both arms** (128 output tokens):

| Input / cache condition | W4A16 TTFT s | INT8-MLP TTFT s |
|---|---:|---:|
| Fresh 5,237 input tokens, two-run mean | 8.04 | 5.93 |
| Immediate 5,237-token repeat, two-run mean | 3.02 | 2.51 |
| 21,077 input, 3,392 cached tokens | 34.33 | 27.32 |
| 21,077 input, no cached prefix | 39.40 | 30.81 |

These are TTFT measurements, not isolated PP/decode. The archived default later
selected boundary-only prefix retention, so this trial is not an exact-default
benchmark. [Saved method and limitations](linux/hardware/README-ARCHIVE-2026-10-19.md#later-nvidia-optimization--october-15-2026).
No Windows throughput is inferred from Linux results.

## Install, launch and connect

| Reference files | Purpose |
|---|---|
| [`linux/`](linux/) | Current dual-AMD wrappers, profiles, patch/build helpers |
| [`linux-nvidia/`](linux-nvidia/README.md) | Historical dual-NVIDIA configuration; use as an alternative installation |
| [`windows/`](windows/) | Historical NVIDIA Windows helpers; not migrated/validated for the current dual-AMD machine |
| [Consolidated handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) | Model IDs, storage, API/SSH use and validation limits |
| [Full dated benchmark ledger](linux/hardware/BENCHMARK-HISTORY.md) | Single-AMD, earlier motherboards, tuning controls, retired engines and update stages |
| [Previous README archive](linux/hardware/README-ARCHIVE-2026-10-19.md) | All previous publication tables and chronological notes |

The Linux tree assumes `/opt/local-llm`. Active resident GGUF examples use
`/mnt/shared/GGUF-Models`; Strata/Maya streaming assets use
`/mnt/shared-nvme/LLM-Models`. HF GPTQ weights and the DFlash2 drafter remain
under Linux NVMe `models/`. Obtain binaries/dependencies separately, adapt paths
and GPU PCI addresses, and configure both `CONFIGURE_SHARED_DRIVE_UUID` and
`CONFIGURE_SHARED_NVME_UUID` before using the storage helpers. Generate private harness/network settings locally and keep
credentials outside Git. These hardware-specific examples are not a universal installer.

To mount both model drives at desktop login, install the user service
[`linux/network/local-llm-mounts.service`](linux/network/local-llm-mounts.service)
with `systemctl --user enable local-llm-mounts.service`. It uses udisks without sudo.
Ubuntu allows unprompted mounts only for the active local session, so log in to the
desktop after a reboot before launching over SSH. Launchers still verify their own drive.

[Maya](linux/maya/README.md) adds `llm-maya`, two 32K DSH profiles and loopback API 30030.

Backend launchers start visible terminals; **dsh** is separate. **Strata Q3** /
`llm-strata` starts the managed backend. **Strata App** is the separate AMD
AppImage GUI; it does not inherit the managed profile/watchdog. See
[menu installation](linux/launchers/STRATA-APP.md) and
[official icon sources/licenses](linux/launchers/icons/README.md).
Backend switching stops only configured inference workers, preserving DSH,
the gateway and unrelated applications.

The authenticated OpenAI-compatible LAN/Tailscale gateway uses
`http://YOUR_LLM_HOST:10000/v1`. Use your own private key and address;
[client and SSH instructions](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md).

Graphics generation is separate from the LLM benchmark tables:
[Official Comfy Desktop setup/validation](linux/graphics/DESKTOP-2026-10-20.md)
(`comfy-desktop`, reuses existing models/workflows; normal startup passed October21;
terminal server remains `comfyui`),
[ComfyUI setup](linux/graphics/INSTALL.md), [retained Qwen-Image/H3 models](linux/graphics/README.md)
and [saved generation results](linux/graphics/VALIDATION-2026-10-18.md).

Research-derived tuning retains direct [lcz.me](https://lcz.me/) and
[Level1Techs](https://forum.level1techs.com/) post URLs and primary upstream sources
in the [source ledger](linux/hardware/FORUM-OPTIMIZATION-SOURCES.md). Forum speeds
are not local measurements. Personal repair/warranty records, model weights,
private history, runtime binaries and app state are outside this public reference.

[L1]: linux/hardware/LEVEL1-TESTS-2026-10-17.md
[D16]: linux/hardware/UPGRADE-DUAL-7900XTX.md
[MOE]: linux/hardware/MOE-OFFLOAD-2026-10-18.md
[Q4]: linux/hardware/NEMOTRON-Q4-2026-10-18.md
[C17]: linux/hardware/CLEAN-TUNING-2026-10-17.md
[U18]: linux/hardware/RUNTIME-UPGRADE-2026-10-18.md
[CTX19]: linux/hardware/STRATA-CONTEXT-2026-10-19.md
[NH]: linux/hardware/BENCHMARK-HISTORY.md#update-history-nvidia-pair-64-gb-ram

The managed Strata Q3 and Maya launchers also open their native Chat/Monitor pages locally after their workers are ready; terminal logs stay visible. See the [frontend guide](linux/hardware/NATIVE-FRONTENDS-2026-10-20.md). DSH remains separate.
