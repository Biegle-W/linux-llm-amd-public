# Local LLM reference setups

Sanitized Linux and Windows launchers, configuration examples, and model-switching
helpers for local OpenAI-compatible inference. This repository starts with fresh
history. It contains no model weights, installed runtimes, personal connection
settings, chat sessions, or original workstation logs.

These are hardware-specific reference configurations, not a universal installer.
Adapt paths, GPU selection, memory budgets and runtime versions before launching.

## Linux

The `linux/` tree corresponds to a runtime workspace at `/opt/local-llm`.
Copy its contents there or update the example absolute paths consistently.
The reference hardware is RX 7900 XTX 24 GB + RTX 4070 12 GB. Current activated
models run on AMD alone; the NVIDIA card does not participate in ROCm TP.

| Backend | Model / strategy | Context |
|---|---|---:|
| SGLang ROCm | Qwen 27B GPTQ, corrected MTP2 | 16,384 |
| SGLang ROCm | Qwen 27B GPTQ, DFlash2 W4A16 drafter | 16,384 |
| vLLM ROCm | Qwen 27B GPTQ, MTP3, Q4 KV | 65,536 |
| llama.cpp Vulkan | Qwen 27B Q4, MTP3 | 65,536 |
| llama.cpp Vulkan | Muse, Qwen MoE, Empero | 32,768 |
| llama.cpp Vulkan | Nemotron Bolt | 65,536 |

Qwen GPTQ/retained HF-format checkpoints and the DFlash drafter belong under
`/opt/local-llm/models` on Linux storage. GGUFs used by both operating systems
belong under the example shared path `/mnt/llm-models`. `dsh/shared_storage.py`
requires a real shared-drive mount path and UUID: replace
`CONFIGURE_SHARED_DRIVE_UUID` before using shared-storage launchers. Review AMD
PCI-device paths and GPU discovery in the guards on your machine.

The SGLang profiles use standard Triton verification
(`SGLANG_RDNA_VLLM_VERIFY=0`). The optimized verification adapter produced invalid
ordered-number output in this single-card configuration. DFlash uses eight draft
tokens, a 2,048-token draft window, two recurrent-state slots and disabled prefix
caching. Repeated conversation history must therefore be processed again.
DFlash requires 23 GiB free AMD VRAM at startup.

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
HyperQwen is disabled for this AMD/NVIDIA combination because its retained CUDA
checkpoint exceeds 12 GB. Strata's historical CUDA profile remains deferred.

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

## Measurements and limitations

October 16, 2026: two synthetic 512-output-token trials per workload, temperature
zero, cold loading excluded. Approximate streaming decode rates on one 7900 XTX:

| Configuration | Inventory t/s | Code-copy output t/s | Prose t/s |
|---|---:|---:|---:|
| llama.cpp Q4 MTP3 | 82.0 | 104.9 | 57.0 |
| SGLang GPTQ MTP2, corrected verification | 53.9 | 62.2 | 46.4 |
| SGLang GPTQ DFlash2, no prefix cache | 83.0 | 147.9 | 45.9 |

Both SGLang profiles passed focused arithmetic, ordered JSON, tool round trips,
authenticated streaming and 14,500-token retrieval checks. MTP → DFlash2 → MTP
switching also passed. These are workload-specific measurements, not general
quality guarantees or full-context generation rates. Different checkpoints and
cache types limit cross-engine comparisons. An n-gram + MTP llama.cpp trial showed
no useful improvement on these inputs.

## Publication boundaries

Only selected setup code and example configuration are included. Raw reports,
private Git history, user identifiers, actual host addresses and personal commit
email addresses are omitted. Models, credentials, runtime binaries and generated
state are excluded by `.gitignore`. Git exclusions do not protect files already
tracked: inspect staged content and scan for secrets before every publication.
This repository is associated with its GitHub owner's public account; fresh
history does not make repository ownership anonymous.
