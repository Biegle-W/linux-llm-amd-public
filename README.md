# Local LLM reference setups

## Current dual-AMD results — October 16

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

**SGLang MTP2 is blocked** on this dual-card topology after repeatable HIP
buffer/index failures. It is hidden from DSH, Turnstone and API model lists;
direct requests fail before unloading a working model. SGLang defaults to the
working DFlash2 profile. vLLM and llama.cpp retain working MTP. Strata remains
deferred until RAM expansion and dual-HIP validation; its Q3 assets are preserved.

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

The `linux/` tree corresponds to a runtime workspace at `/opt/local-llm`.
Copy its contents there or update the example absolute paths consistently.
The current reference hardware is two RX 7900 XTX 24 GB cards. Both participate
in each active model; the earlier RTX 4070 is retired. RAM remains 32 GB.

| Backend | Model / strategy | Context |
|---|---|---:|
| SGLang ROCm | Qwen 27B GPTQ, MTP2 — **disabled pending dual-GPU fix** | 40,960 (inactive) |
| SGLang ROCm | Qwen 27B GPTQ, DFlash2 W4A16 drafter | 16,384 |
| vLLM ROCm | Qwen 27B GPTQ, MTP3, Q4 KV | 65,536 |
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

Strata's Q3 assets are preserved, but its profile is disabled until RAM is installed
and the AMD HIP candidate is validated. See the [RAM-expansion preparation](linux/hardware/STRATA-AFTER-RAM.md)
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
