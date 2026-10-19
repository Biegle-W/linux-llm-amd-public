# Local LLM hardware, engines and benchmarks

Two reference builds: **current dual AMD** and **archived dual NVIDIA**.
This repository contains sanitized launchers, configuration, build/patch helpers
and saved measurements for Linux, plus historical Windows setup files.
Model weights, installed runtimes, credentials and personal app data are excluded.

- [AMD: latest setup and results](#amd-latest-setup-and-results)
- [NVIDIA: archived setup and results](#nvidia-archived-setup-and-results)
- [Install, launch and connect](#install-launch-and-connect)
- [Complete benchmark history and experiments](linux/hardware/BENCHMARK-HISTORY.md)

Saved **October 19, 2026 AMD benchmarks** cover all ten profiles in two distinct batches.
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
three-run medians unless labeled smoke/single probe. Native PP comes from engine
timing; **Book PP** is llama-benchy 0.4.0's latency-adjusted estimate for a
2,048-token prompt at depth 0, not native prompt timing. Input divided by TTFT,
prompt-processing duration and total request time are not substituted for TTFT
or native PP. Different rows can use different workloads and output lengths.
These are saved complete-profile results, not a controlled AMD-versus-NVIDIA ranking.

## AMD: latest setup and results

**Two RX 7900 XTX 24 GB (48 GB total VRAM), i5-13600KF, MSI MPG Z690 CARBON
WIFI, 32 GB RAM, CPU PCIe 4.0 x8/x8.** Another 32 GB RAM is planned; its
candidates remain inactive. Every active profile uses both GPUs. llama.cpp and
Strata split layers; SGLang/vLLM use TP2 through host transport because direct
ROCm peer access is unavailable. Only one managed model/backend runs at a time.

### Latest installed runtime pins

“Latest” here means the latest locally installed and validated builds in the
October 18–19 records, not a live claim about today's upstream head.

| Engine | Installed build | Validation after this update |
|---|---|---|
| llama.cpp HIP / Vulkan | [`31288c9c66e5`](https://github.com/ggml-org/llama.cpp/commit/31288c9c66e59377f7788d920678a565bb89dd37) | Original five profiles plus the separate Nemotron Super IQ3 validation |
| SGLang ROCm | [gfx1100 fork `f84475ccf593`](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352) + local repairs | Fresh prefill, TTFT and code/prose decode on both profiles |
| vLLM ROCm | `0.32.0rc1.dev329+g39983a5e7.rocm723` | Fresh prefill, TTFT and code/prose decode; earlier 64K retrieval retained |
| Strata HIP | [0.1.45 / `477ac13cbe8e`](https://github.com/Niko1221/Strata/commit/477ac13cbe8e582c20484871ce459d20d82df09d) | Fresh prefill, TTFT and code/prose decode; earlier native 256K check retained |

[Build dependencies, fixes, validation and rollback](linux/hardware/RUNTIME-UPGRADE-2026-10-18.md).
SGLang uses its Radeon-specific fork; official main was not an unchanged compatible replacement.

### Nemotron Super IQ3: 32 GB RAM profile

The additional `nemotron-3.5-super-iq3` profile uses **32,768 total context**, both
AMD GPUs with HIP layer split **21:19**, **19.124 GiB CPU expert backing** and a
**2 GiB total GPU expert-cache ceiling**, with MTP off. It passed tools, JSON,
streaming and three-marker retrieval at **28,546 actual input tokens**.

| Workload, median of 3 | Actual input / output | Native prefill t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|
| Code | 8,108 / 256 | 95.75 | 84.699 | 14.16 |
| Prose | 8,111 / 256 | 97.13 | 83.521 | 16.32 |

These TTFT values include approximately 8K input processing; the original
nine-profile batch below uses separate short prompts for short TTFT/decode.
Q4_K_XL remains an inactive **64 GB RAM candidate**, without measured speed.
[Settings, memory peaks, rejected splits and activation gates](linux/hardware/NEMOTRON-SUPER-2026-10-19.md)
· [Every numeric trial](linux/hardware/results/nemotron-super-2026-10-19.json).

### Original nine-profile benchmark batch

All rows below were timed on the installed builds above, with production
contexts retained. Medians of three timed requests/workload; one excluded short
warm-up per task. New prefill probes use a shared synthetic corpus sized around 8K Qwen tokens,
not a filled window. Actual per-model token counts are shown; Muse tokenizes
this corpus to about 6.35K, Nemotron to about 7.92K.

| Model / quant | Backend / strategy | Context tokens | Actual prefill input tokens | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,187–8,189 | 695.1 | 11.788 | 0.132 / 0.129 | 75.80 / 45.58 |
| Muse-Glimmer-30B UD-Q4_K_XL | llama.cpp Vulkan | 32,768 | 6,346–6,349 | 1375.5 | 4.725 | 0.258 / 0.259 | 37.85 / 37.92 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,191 | 379.3 | 21.603 | 0.061 / 0.060 | 123.70 / 76.34 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, expert cache | 262,144 | 7,920–7,926 | 222.8 | 35.549 | 0.387 / 0.249 | 36.49 / 36.29 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,190 | 399.2 | 20.515 | 0.058 / 0.058 | 120.48 / 76.46 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, MTP3 | 40,960 | 8,186–8,190 | 1397.7 | 5.871 | 0.084 / 0.080 | 115.22 / 68.85 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 65,536 | 8,186–8,188 | 1491.5 | 5.510 | 0.086 / 0.083 | 210.42 / 70.88 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 65,536 | 8,184–8,189 | 1488.2 | 5.513 | 0.067 / 0.081 | 131.05 / 73.31 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlap/MTP3 | 262,144 | 8,186–8,189 | 900.9 | 9.126 | 0.238 / 0.245 | 71.50 / 48.46 |

Short code/prose uses the saved 29/25-token prompts, temperature 0.6, top-p 0.95,
seed 42 and 256 output-token cap. Actual counts are retained. Native prompt PP
is used for llama.cpp/Strata; SGLang/vLLM use their measured engine prefill phases.
TTFT/decode use external SSE timing. Phase definitions differ; this is not a
kernel-only comparison. Muse may spend its short cap in reasoning; its final
marker probes use a 1,024-output allowance and passed 2/3 checks.
Retrieval failures remain in the reported medians. Other marker probes use 64.

[Complete method, all trials, input lengths, memory and reproduction](linux/hardware/CURRENT-AMD-BENCHMARKS.md).
All accepted marker probes reported zero cached input; experts were warmed by
preceding requests. Older-build and single-AMD speeds remain in the history.

### Long input, cache behavior and capacity

| Model / backend | Configured context | Actual input / output tokens | Native prefill t/s | TTFT s | Decode t/s / limit | Evidence |
|---|---:|---:|---:|---|---|---|
| Qwen27B / SGLang MTP3 | 40,960 | 39,440 / 22 | — | 35.54 | 85.29; short retrieval only | Oct 17 [C17] |
| Qwen27B / SGLang DFlash2 | 65,536 | 64,033 / 22 | — | 64.02 | 102.43; short retrieval only | Oct 17 [C17] |
| Qwen27B / vLLM dev329 MTP3 | 65,536 | 64,033 / 22 | — | 54.56 | Not used as sustained decode | Oct 18 [U18] |
| Qwen35B / llama.cpp HIP `f12aaa3` | 262,144 | 63,911 / 19 | 417.9 | — | Short retrieval only | Oct 18 [MOE] |
| Empero35B / llama.cpp HIP `f12aaa3` | 262,144 | 63,911 / 19 | 457.8 | — | Short retrieval only | Oct 18 [MOE] |
| Nemotron Bolt Q4 / llama.cpp HIP `f12aaa3` | 262,144 | 63,911 / 19 | 424.0 | — | Short retrieval only | Oct 18 [Q4] |
| Flash-Next / Strata 0.1.45 | 262,144 | 258,044 / 256 | 775.1 | — | 39.9; one retrieval + code sample | Oct 19 [CTX19] |

The three llama.cpp MoEs allocated 256K but were tested only around **64K actual
input**, on the older build. Latest-build near-limit retrieval was not repeated.
Qwen27B/Muse dense near-window evidence is from an earlier single-AMD profile,
not fresh capacity validation of the latest dual-card build. Those measurements
remain in the [dated history](linux/hardware/BENCHMARK-HISTORY.md).

Strata's separate production conversation used 258,025 fresh input tokens at
956.9 native PP; prompt processing took **269.64 s**. A subsequent full-history
follow-up reused 258,048 tokens and took **0.84 s total**. Neither duration is a
measured TTFT. The uncached 258,044-token code probe took 332.93 s of prefill.
vLLM's separate 8K prefix test reduced TTFT **5.73 → 0.55 s** on reuse. Cache hits
change the workload and cannot be compared with fresh-prompt timing.

The selected Strata profile uses INT8 KV, 32K GPU KV residency, full host KV
backing, 13.5 GiB CPU expert budget, split 26, 2,048-token prefill and 7/8 GiB
startup VRAM reserves. Its 64 GB candidate stays at native 256K and requires
separate validation; no experimental 512K/RoPE result is claimed. [CTX19]


Maintenance reconciled saved results without rerunning timings or changing profiles.
The purchased PEX88096 switch is pending installation/P2P validation.
[Maintenance record](linux/hardware/WORKSPACE-MAINTENANCE-2026-10-19.md).

<a id="previous-rtx-4070-12-gb--rtx-3060-12-gb"></a>

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

The Linux tree assumes `/opt/local-llm`; shared GGUFs/Strata assets use example
path `/mnt/llm-models`. HF GPTQ weights and the DFlash2 drafter use Linux NVMe
under `models/`. Obtain binaries/dependencies separately, adapt paths and GPU
PCI addresses, and replace `CONFIGURE_SHARED_DRIVE_UUID` before using shared
storage helpers. Generate private harness/network settings locally and keep
credentials outside Git. These hardware-specific examples are not a universal installer.

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
