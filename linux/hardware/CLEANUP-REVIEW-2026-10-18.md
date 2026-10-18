# Working-directory cleanup review — October 18, 2026

**Awaiting user confirmation. No files have been deleted.** NVIDIA archival
is authorized separately; deleting its source copies is still pending approval.

The exact proposed scope is in [the path manifest](CLEANUP-REVIEW-2026-10-18.json).
Paths below are relative to the runtime workspace. Listed directories include
their contents; group C includes only the 62 explicitly listed installer files,
not the surrounding reports or future downloads.

| Group | Proposed deletion | Estimated NVMe recovery | Reason / consequence |
|---|---|---:|---|
| A | Old NVIDIA rollback environments and isolated Flash-MTP source | 24.12 GiB | Retired CUDA setup; remove originals only after recovery archive verification. |
| B | Old CUDA vLLM/SGLang/FlashInfer/NVIDIA kernel caches | 6.24 GiB | Current AMD wrappers use `runtime-cache/rocm`; old kernels are not selected. |
| C | 62 downloaded ROCm `.deb` installers | 4.35 GiB | Installed SDK and libraries stay; reinstalling would need these packages downloaded again. |
| D | Unselected Level1 experiment caches, writable test directory and rocWMMA test build | 3.43 GiB | Production does not select these. Repeating the experiment needs recompilation; source, patches, logs and measurements stay. |
| E | UV downloaded/extracted package cache | 17.24 GiB | Installed environments stay. Future installs/builds may download packages again. |

**Total estimate: 55.39 GiB on NVMe.**
This is regular-file allocated-block accounting with inode/link-count checks,
not a sum of apparent directory sizes. Directory blocks are excluded. Free-space
changes can differ with concurrent writes and caches; the archive consumes separate
space on Shared SATA. Space has not been reclaimed yet.

## Exact directory roots

```text
# A NVIDIA rollback originals
.private-backups/runtime-upgrade-2026-10-14
llm-tools/llama-flash-mtp-src
# B obsolete CUDA kernel caches
llm-tools/runtime-cache/vllm
llm-tools/runtime-cache/sglang
llm-tools/runtime-cache/sglang-flash-next
llm-tools/runtime-cache/flashinfer
llm-tools/runtime-cache/nvidia
# D unselected experiment caches/build
hardware/generated/level1-tests-2026-10-17/cache
hardware/generated/level1-tests-2026-10-17/test-rw
hardware/generated/level1-tests-2026-10-17/llama-rocwmma/build-test
# E UV package cache
llm-tools/runtime-cache/uv
```

The installer filenames for group C are enumerated individually in the linked
JSON manifest; approval does not authorize deleting other `.deb` files.

## Archive and retained files

The [NVIDIA recovery archive](NVIDIA-ARCHIVE-2026-10-18.md) was created and
fully compared against the originals; its source copies still await deletion approval. The archive contains the old CUDA rollback environments,
Flash-MTP source/patch, HyperQwen history and benchmark report, October 14
runtime-upgrade records and the existing sanitized `linux-nvidia/` snapshot.
The public NVIDIA snapshot and Windows tree remain in place as historical
references. Private archives and installed runtimes must never enter Git.

Keep all current model weights and draft checkpoints on NVMe/Shared, all
Strata Q3 assets and HIP preparation, both current llama.cpp builds/source,
ROCm vLLM/SGLang environments/source, the ROCm SDK, no-hostcall RCCL, Vulkan
SDK, private base Python, benchmark tools and selected RDNA3 kernel source.

**Keep `llm-tools/cuda-build`: AMD builds and SGLang JIT use its C++ compiler,
sysroot and libraries despite its CUDA name. Keep `llm-tools/runtime-cache/rocm`
to avoid discarding the currently selected compiled kernels.**

Preserve DSH/Turnstone dependencies, settings, sessions, workspace files and logs,
all benchmark reports/raw results, source pins, forum citations, consolidated
handoff originals and the user-supplied `LOCAL-LLM-CLIENT.md`. Retain historical
tracked configuration paths to avoid breaking documentation and recovery references.

## Checks and execution gate

All proposed deletion paths are already ignored and contain no tracked files.
Read-only inspection found no active-environment symlink or editable Python
`.pth`/`.egg-link` dependency into the proposed deletion roots. Current AMD
build/runtime wrappers were checked for compiler and cache references. No
configured inference worker was found during this review. No model was launched,
benchmark repeated, runtime setting changed or process stopped for this task.

Before executing a later explicit approval: verify the archive remains accessible,
recheck the exact candidate paths and active references, and ensure no worker or
build job is using them. Delete only the approved groups; do not expand scope
to other generated directories, logs, models or user files.
