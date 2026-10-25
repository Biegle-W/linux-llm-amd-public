# Ubuntu LLM AMD

Current workstation: **2 × RX 7900 XTX 24 GB, Intel i9-13900KS, 64 GB RAM**,
MSI MPG Z690 CARBON WIFI, CPU PCIe 4.0 x8/x8. Every active model uses both AMD
cards. This repository covers the Ubuntu HIP/ROCm system. The independent
Windows RTX 3060 / i5-13600KF / 16 GB system has its own
[Windows NVIDIA repository](https://github.com/Biegle-W/windows-llm-nvidia-public).

| Public repository | System |
|---|---|
| [ubuntu-llm-amd-public](https://github.com/Biegle-W/ubuntu-llm-amd-public) | Ubuntu / dual RX 7900 XTX |
| [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) | Windows / RTX 3060 |

Private repositories remain private. Public files exclude credentials, personal
settings, model weights, installed runtimes, raw private logs and private history.
The local Ubuntu checkout names remain unchanged for installed launcher and daily
publisher compatibility. GitHub repository names identify the system and hardware.

## Start and connect

This public tree is a hardware-specific reference. Adapt example paths, install the pinned runtimes and validate your own hardware before launching. Active source is under `linux/`; install that tree in the example `/opt/local-llm` workspace.

| Command | Purpose | Loopback port |
|---|---|---:|
| `llm-llama` | Empero, Super IQ3, Sage and Ornith | 8080 |
| `llm-sglang` | Qwen27B DFlash2 / TP2 | 30000 |
| `llm-vllm` | Qwen27B MTP3 / TP2 and Bolt | 30010 |
| `llm-strata` | Strata Qwen Q3 and DeepSeek S / XS | 30020 |
| `llm-maya` | Maya GLM and DeepSeek S / XS | 30030 |
| `dsh` | Separate client frontend | 3080 |

The model hub loads a selected backend on demand. The authenticated client API
uses port 10000 and `/v1`; use the [canonical handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md)
for access, storage, startup and per-engine limits. **DSH defaults to Strata Q3.**
Managed inference unloads after 600 seconds without inference activity. Active
requests/loading/jobs and GPU-LOCK defer unloading; DSH, gateway and unrelated
apps are preserved. Update acceptance permits up to 64 MiB aggregate owned-worker
swap; background system swap is allowed. Existing RAM/VRAM admission, worker
cgroup limits and latched guards remain.

## Active profiles

| Model API ID | Engine | Configured context |
|---|---|---:|
| `empero-qwen3.8-35b-a3b` | llama | 262,144 |
| `nemotron-3.5-super-iq3` | llama | 32,768 |
| `sage-a1.5` | llama | 65,536 |
| `ornith-1.5-122b` | llama | 32,768 |
| `qwen3.8-27b-sglang-dflash2` | sglang | 163,840 |
| `qwen3.8-27b-vllm` | vllm | 163,840 |
| `nemotron-3.5-bolt-vllm` | vllm | 262,144 |
| `qwen3.8-flash-next-iq3_xxs` | strata | 262,144 |
| `deepseek-v4.1-flash-1017-strata-s` | strata | 32,768 |
| `deepseek-v4.1-flash-1017-strata-xs` | strata | 32,768 |
| `glm-5.3-flash-maya` | maya | 32,768 |
| `deepseek-v4.1-flash-1017-maya` | maya | 32,768 |
| `deepseek-v4.1-flash-1017-maya-s` | maya | 32,768 |

Configured context is allocation capacity. It does not establish full-window
quality or throughput; reports state actual tested prompt and output lengths.
No model, quantization, context, hardware setting or measured speed changed in
this repository organization.

<a id="amd-latest-setup-and-results"></a>
<a id="saved-benchmark-results"></a>

## Current measurements and engine pins

[October25 fresh tests](linux/hardware/FRESH-ENGINE-TESTS-2026-10-25.md) promoted llama.cpp
`2280f0fd`; Maya 1.1.28 failed DeepSeek decode gates and rolled back, while Strata
DeepSeek 0.1.51 failed selected kernel parity before installation. The 64 MiB swap
allowance passed the fresh baselines; current contexts/guards/dual-GPU settings remain.

The [current AMD report](linux/hardware/CURRENT-AMD-BENCHMARKS.md),
[numeric-results index](linux/hardware/results/README.md) and
[benchmark ledger](linux/hardware/BENCHMARK-HISTORY.md) retain exact builds,
hardware/RAM, tested lengths, thermals and timing methods. Native prefill,
external SSE TTFT/decode and functional-only checks remain distinct. Follow the
[Strata table selection](linux/hardware/STRATA-TUNING-2026-10-24.md) and
[DeepSeek integration](linux/hardware/STRATA-DEEPSEEK-2026-10-24.md) for their newer,
separately dated evidence. Historical speeds are not attributed to later builds.

Current validated engine pins live in the [daily ledger](linux/hardware/DAILY-UPDATES.md)
and the handoff. The 03:00 updater tests newer sources in isolation and promotes
only after all gates pass, including at most 64 MiB aggregate worker swap and
zero VRAM spill with valid launch-through-shutdown telemetry. ROCm 7.2.3 is retained. See the
[updater method](linux/hardware/daily-update/README.md).

## Directory map

| Location | Scope |
|---|---|
| `linux/dsh/`, `linux/bin/`, `linux/launchers/`, `linux/network/` | Active catalog, guarded launchers, client/network helpers |
| `linux/sglang/`, `linux/vllm/`, `linux/maya/`, `linux/strata-dsv41/` | Current engine setup, source pins and patches |
| `linux/hardware/` | Current validation, dated research and numeric records |
| `linux/graphics/` | Current ComfyUI / native Comfy Desktop setup |
| [archives/](archives/README.md) | Retired system configurations and previous overview |

Models, environments and generated state stay outside tracked source. New static
weights use the configured SATA destination and new streaming packs use system
NVMe; the storage admission helper enforces the 90% limit. Existing model assets
and shared build dependencies stay in their validated locations.

<a id="nvidia-archived-setup-and-results"></a>

## Retired setups

The [archive index](archives/README.md) distinguishes the former Ubuntu
RTX 4070 + RTX 3060 system, retired models/backends, historical measurements and
recovery requirements. NVIDIA results retain their original CPU/RAM, hardware,
source version and workload; they do not describe current AMD performance.

The [complete previous overview](archives/documentation/ubuntu-readme-before-organization-2026-10-24.md)
retains all earlier tables and detailed narratives. Windows retired setups are
maintained in the [Windows archive](https://github.com/Biegle-W/windows-llm-nvidia-public/tree/main/archives).
