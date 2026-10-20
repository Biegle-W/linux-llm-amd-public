# Local LLM hardware, engines and benchmarks

Two reference builds: **current dual AMD** and **archived dual NVIDIA**.
This repository contains sanitized launchers, configuration, build/patch helpers
and saved measurements for Linux, plus historical Windows setup files.
Model weights, installed runtimes, credentials and personal app data are excluded.

- [AMD: latest setup and results](#amd-latest-setup-and-results)
- [NVIDIA: archived setup and results](#nvidia-archived-setup-and-results)
- [Install, launch and connect](#install-launch-and-connect)
- [Complete benchmark history and experiments](linux/hardware/BENCHMARK-HISTORY.md)

Saved **October 20, 2026 i9/64 GB AMD benchmarks** cover the ten currently active profiles with their distinct methods; retired profiles remain historical; older i5/32 GB results remain dated.
The archived NVIDIA measurements retain their original dates and builds.
[Full fresh AMD method, token counts and numeric evidence](linux/hardware/CURRENT-AMD-BENCHMARKS.md).

<a id="saved-benchmark-results"></a>
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

Fresh three-trial medians: native prefill**912.2t/s**, fresh8K TTFT**9.015s**,
code/prose decode**75.28/50.31t/s**. Actual257984-input/256-output retrieval/code
and258266-input cached full-history follow-up passed. Zero owned swap/spill.
Earlier0.1.45 rates retain their original build; no matched A/B speedup is claimed.
[Update, exact versions and validation limits](linux/hardware/STRATA-STARTUP5-2026-10-20.md).

## AMD: latest setup and results

**Ten active profiles:** five llama.cpp, one SGLang, one vLLM, one Strata, two Maya.
Super IQ3 remains selectable at 32K. Muse Q4 and Super Q4 are retired at the user's request; their weights are removed and historical measurements are preserved.
Strata keeps Q3 and the 13.5 GiB budget, with 6 workers / all CPUs selected.
[CPU/RAM, storage, pool tests and limits](linux/hardware/CPU-RAM-PROFILES-2026-10-20.md).

### Installed and measured builds

| Engine | Retained build | Validation scope |
|---|---|---|
| llama.cpp HIP/Vulkan | [`4c3c5810`](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f) | Four retained shared-method models plus Super IQ3; source-candidate timings and production-rebuild functional proofs. Retired models stay in dated evidence. |
| SGLang ROCm | [gfx1100 fork `f84475cc`](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352) + local fixes | DFlash2 at 160K, actual 160,861-input retrieval; separate MTP profile retired |
| vLLM ROCm | `0.32.1rc1.dev36+ge68efc685.rocm72` | Retained local fixes; 160K BF16, actual 160,868-input retrieval and full-history follow-up |
| Strata HIP | [0.1.46.1 / `9ae93f7b`](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f) | Exact tested binary, 5 GiB/card startup, six-worker13.5GiB pool, near256K/history and actual Desktop/UI/API proof |
| Maya HIP | [v1.1.17 / `8d9a9b5d`](https://github.com/mw00/project-maya/commit/8d9a9b5d705049a87da853717cdc59440252de30) | Selected Maya-S v2/DeepSeek-S, 32K, both cards, near-30K probes and normal API/model switching |

The llama.cpp and vLLM updates were performance-neutral within noise; newer
source is not presented as a measured speedup. Older builds keep their original
results. [Current full report](linux/hardware/CURRENT-AMD-BENCHMARKS.md).

### Nine profiles using the shared benchmark method

Medians shown: six timed requests per workload across two GLM starts; three for the other shared-method rows. Fresh prefill probes use ~8K
Qwen tokens; tokenizer counts differ. Short TTFT/decode use separate short
code/prose prompts and a 256-output cap. Native PP is used for llama.cpp/Strata/Maya;
SGLang/vLLM use their own measured engine-prefill phases. Context is the total
configured window, not proof of that entire window's quality or speed.

| Model / quant | Backend / strategy | Context tokens | Actual prefill input | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,187–8,190 | 670.4 | 12.222 | 0.132 / 0.131 | 77.10 / 45.86 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,189 | 373.5 | 21.933 | 0.059 / 0.059 | 126.73 / 78.36 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, expert cache | 262,144 | 7,923–7,926 | 220.3 | 35.989 | 0.400 / 0.243 | 37.21 / 36.87 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,185–8,188 | 388.4 | 21.083 | 0.057 / 0.057 | 125.85 / 77.07 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 163,840 | 8,185–8,191 | 1314.8 | 6.235 | 0.102 / 0.097 | 178.82 / 63.40 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 163,840 | 8,187–8,188 | 1413.8 | 5.806 | 0.066 / 0.092 | 130.31 / 68.96 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlap/MTP3 | 262,144 | 8,185–8,188 | 912.2 | 9.015 | 0.229 / 0.233 | 75.28 / 50.31 |
| GLM-5.3-Flash Maya-S | Maya HIP, layer split/MTP | 32,768 | 6,310–6,316 | 487.9 | 13.031 | 0.095 / 0.112 | 16.83 / 14.44 |
| DeepSeek-V4.1-Flash-1017 Maya-S | Maya HIP, layer split/no DSpark | 32,768 | 6,295–6,302 | 185.5 | 33.956 | 0.374 / 0.550 | 6.24 / 6.84 |

GLM now uses six matched ABBA trials per workload; other shared-method rows retain their original three-trial method. [GLM S/S24 selection](linux/hardware/MAYA-S-VS-S24-2026-10-20.md).

The retired Muse/Q4 Super measurements remain in the [original numeric batch](linux/hardware/results/dual-amd-i9-64gb-2026-10-20.json). They are historical, not active profiles.

Maya's two added rows retain every trial and actual tokenizer count in the
[Maya numeric record](linux/hardware/results/maya-dual-amd-2026-10-20.json); [settings, selection and limits](linux/hardware/MAYA-2026-10-20.md).

### Super IQ3 using fixed ~8K-input workloads

| Super quant / workload | Context | Actual input / output | Native PP t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| IQ3_XXS / code | 32,768 | 8,108 / 256 | 98.21 | 82.566 | 15.90 |
| IQ3_XXS / prose | 32,768 | 8,111 / 256 | 97.84 | 82.911 | 16.95 |

These TTFT values include ~8K input processing and are **not short-prompt TTFT**.
MTP is off. IQ3 uses HIP 21:19, 19.124 GiB CPU experts and a 2 GiB cache,
six CPU threads and 32K total context. It retrieved all markers at 28,546 input /
22 output. Those candidate trials overlapped authorized copy/hash/download IO;
they are not an isolated engine A/B. A separate production rebuild passed normal
launcher tools/JSON/streaming/placement checks. The retired Q4 profile's results
remain in the dated ledger and original numeric batch.

Super IQ3 now loads from a verified copy on the shared NVMe: **42 s instead of 112 s**,
with identical inference speed (−0.12%). The SATA original is kept as a backup.
SSD streaming (`load-mode mmap`) was rejected: it reproducibly broke forced tool calls
and saved no RAM. [Trial and decision](linux/hardware/SUPER-NVME-LOAD-2026-10-20.md).

### Long context and model storage

Strata's corrected-NVMe selected profile passed **257,984 actual input /
256 output**, then a cached full-history follow-up, at native 256K.
The selected fresh probe measured 1,000.1 native PP t/s and 67.1 native decode t/s; external TTFT was not measured. The full-history follow-up took 1.732s total, which is not TTFT. Both pool trials retained zero owned swap/spill. No RoPE extension is enabled.
The three smaller llama.cpp MoEs retain 256K allocation with ~64K retrieval on
older builds; their latest 8K probes do not prove full-window operation.
SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](linux/hardware/QWEN-INT4-CONTEXT-2026-10-20.md).

Strata's managed backend and standalone app share verified weights on the new
shared NVMe. The generated expert pack was checked against every source expert
byte before reuse. Maya's validated S24/DeepSeek-S weights and required generated
assets also use that NVMe. Other resident GGUF models stay
on Shared SATA; SGLang/vLLM target/draft checkpoints stay on Linux NVMe.
[Storage inventory](linux/hardware/results/streaming-storage-2026-10-20.json).

[Current results index](linux/hardware/results/README.md) · [Dated benchmark ledger](linux/hardware/BENCHMARK-HISTORY.md)
· [Historical i5/32 GB AMD report](linux/hardware/AMD-BENCHMARKS-2026-10-19.md).

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
