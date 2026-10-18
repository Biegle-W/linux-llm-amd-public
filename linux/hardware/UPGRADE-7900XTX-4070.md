# RX 7900 XTX + RTX 4070 migration

> Historical single-AMD/RTX 4070 migration. The RTX 4070 is now retired.
> Current hardware and both-card policy: [dual-7900-XTX report](UPGRADE-DUAL-7900XTX.md).
> Earlier single-card defaults and speed results below are historical.

The planned next hardware change is documented in
[dual-7900-XTX migration](UPGRADE-DUAL-7900XTX.md). It has not been installed or
validated; the notes below describe the earlier mixed-vendor setup.

**Latest October 16 status:** all five retained llama.cpp GGUF profiles are activated
on AMD alone; see [migration validation](LLAMA-MIGRATION-2026-10-16.md).
Qwen SGLang/vLLM ROCm profiles are also active. HyperQwen is disabled because
its CUDA-only 14.707 GiB target cannot fit the remaining 12 GB NVIDIA card.
The unused HyperQwen target has now been removed. Strata remains deferred;
[the current RAM-capacity preparation](STRATA-AFTER-RAM.md) supersedes the Strata
build/storage planning below. Earlier planning notes below are historical.

**Current policy:** choose the fastest validated runtime per model. Bolt keeps
Vulkan after its HIP comparison; ROCm is used for AMD vLLM/SGLang. Qwen now has ROCm SGLang/vLLM profiles; see
[October 16 ROCm validation](rocm-2026-10-16/README.md) and the main README for
the active launcher state. Earlier Vulkan-first preparation below is historical.

**Later October 16 update:** Bolt replaced Lightning and is the first activated
AMD-only model, through the existing llama.cpp launcher. Other migrations remain
deferred. See [Bolt validation](NEMOTRON-BOLT-2026-10-16.md). The earlier test-only
status below describes the state before this replacement.

Prepared 2026-10-15; status updated 2026-10-16. **GPUs installed; normal launcher
migration not activated.** AMD Vulkan sees RX 7900 XTX at x16 and RTX 4070 at x4.
This test configuration uses 32 GB system RAM. Work in this historical phase is
explicitly limited to GPU-resident models. Prefer AMD alone; add the 4070 only
when a model cannot fit safely on AMD with a usable context. All six selected
October 16 test presets fit on AMD alone (Nemotron without MTP). See [October 16 GPU tests](GPU-RESIDENT-2026-10-16.md).
The plans below were prepared for 64 GB; do not activate CPU-resident Strata expert
caching against the reduced RAM. Existing 4070/3060 launcher profiles are guarded
and are not usable on this new topology until deliberately migrated.
The user reports a 1,000 W PSU; its model and the exact 7900 XTX board/case
clearance are not yet known.

## Intended layout

- RX 7900 XTX: 24 GB, RDNA3 / gfx1100, primary CPU-connected x16 slot.
- Retained RTX 4070: 12 GB, CUDA SM89, secondary slot (currently x4), preferably
  driving the desktop to leave the AMD card's VRAM available for inference.
- Replace the RTX 3060. Do not assume old device ordinals survive the swap.
- Keep 64 GB system RAM and all model weights on Shared SATA. Runtime builds and
  compiler caches stay on NVMe. Strata's SSD PLE and paging paths can still depend
  on disk speed; reassess storage only if measurements justify moving hot data.

There is 36 GB aggregate VRAM, but CUDA cannot address the AMD card. Do not set
CUDA TP=2/PP=2 expecting both vendors to participate. Prefer a model that fits
the AMD card alone. llama.cpp Vulkan layer splitting across both vendors is an
experimental capacity option, to compare with single-card performance later.
Separate concurrent models are another option, but the existing exclusive-launch
policy intentionally remains: a managed pair mode and memory checks are needed
before allowing two backend processes. Do not bypass the handover lock.

Physical installation: use PSU-manufacturer-compatible cables and the connectors
required by the specific graphics cards (partner XTX boards vary). A quality
1,000 W unit is a reasonable capacity target; wattage alone does not establish
cable compatibility. Check cooler thickness against the secondary slot and case,
and shut down/disconnect power before the swap. The i5-13600KF has no integrated
graphics; connect the monitor to an installed GPU.

## Backend plan

| Backend | Prepared direction | Remaining validation |
|---|---|---|
| Strata | Native HIP gfx1100, XTX alone, existing Flash-Next IQ3_XXS + MTP; mmap plus pageable CPU expert residency | Install isolated compatible ROCm SDK; build/test HIP; retune CPU threads, expert cache and context |
| llama.cpp | Separate Vulkan server; existing Qwen 27B Q4 first on XTX alone | Enumerate actual device name; test Q8 KV, MTP, tools and 32K; then compare HIP and larger contexts |
| vLLM | Separate ROCm environment/container on XTX, TP1; retain CUDA environment | gfx1100 quantization/kernel support for the retained INT4 checkpoint, Qwen architecture and MTP; do not reuse CUDA Marlin settings blindly |
| SGLang | Separate Radeon-capable ROCm build, TP1; retain CUDA environment | Current upstream/downstream RDNA3 support and exact quant/attention kernels; AITER defaults may be unsuitable |
| HyperQwen | Preserve isolated CUDA fork for 4070 | Current 27B two-card profiles no longer fit unchanged; no AMD or mixed-vendor path is validated here |

The current Qwen INT4 files should be tried before downloading another quant,
but loading a checkpoint requires support for its exact quantization format.
The existing GGUF Q4 is the lower-risk initial 27B path. No new weights were
downloaded, moved or converted during preparation. All other retained GGUFs stay
available, but their CUDA0/CUDA1 tensor overrides must be retuned before migration.

## Prepared files and protection

- `dsh/hardware_guard.py`: all five normal backend launchers verify the current
  4070/3060 CUDA topology **before** handover. Missing/reordered GPUs or an
  unavailable NVIDIA driver cause a clear error without stopping another backend.
- `llm-upgrade-check` in PATH: read-only PCI, NVIDIA, KFD/render-node, build and
  expert-pack checks. Exit 2 means target hardware not detected; exit 0 means
  target detected, **not** a successful inference test.
- `hardware/build-vulkan.sh`: builds `llama.cpp/build-vulkan/bin/llama-server`
  separately from the active `llama.cpp/build`. Uses the installed development
  source `a0e6dc7384edb8f5d927155e1d26c10b4a310e6d` and private build tools.
- `hardware/build-strata-hip.sh`: build recipe for the separate
  `strata/build-hip/strata`, gfx1100 and HIP MMQ. Requires a selected `ROCM_PATH`;
  never overwrites the CUDA engine. The prepared source is
  `296b59d2f73c8f04a805df29c2fa97655adace78` (0.1.44.1).
- `python3 hardware/prepare-candidates.py`: regenerates ignored, inactive
  `hardware/generated/llama-7900xtx-candidate.ini` and
  `hardware/generated/strata-7900xtx-candidate.json` from existing model paths.
  llama uses a deliberately unresolved `AMD_VULKAN_DEVICE` marker. Strata uses
  HIP ordinal 0, to be confirmed on the installed card, and loopback test port
  18030. Neither file is registered in DSH, Turnstone or the gateway.

Both candidates start at **32,768 tokens**, not a measured maximum. llama keeps
MTP draft max 3 and starts with Q8 KV; Strata keeps MTP draft max 4 and INT8 KV,
starts with prefill 512, six CPU pool workers, 3 GiB VRAM reserve, and disables
conversation cache for the first measurements. These are conservative test
settings, not claimed throughput optima. Strata's existing 40 GiB `experts.bin`,
dense pack, MTP runtime and original PLE shard are retained on Shared.

## Driver and runtime preparation

Observed system: Ubuntu 26.04.1, kernel 7.0.0-38, Mesa 26.0.8 and NVIDIA 595.99.02.
The kernel amdgpu module and RADV Vulkan ICD are already present. They cannot
be validated against absent hardware. No NVIDIA removal, system driver upgrade,
ROCm replacement, group change, BIOS change or reboot was performed.

Vulkan development packages were extracted locally under `llm-tools/vulkan-sdk`
because unattended sudo is unavailable. This avoids modifying the system driver:
libvulkan-dev/libvulkan1 1.4.341.0-1, glslc/libshaderc1 2026.1-1,
spirv-headers 1.6.1+1.4.341.0-1, vulkan-tools 1.4.341.0+dfsg1-1.
Recreate by downloading those Ubuntu packages with `apt-get download`, extracting
each using `dpkg-deb -x PACKAGE llm-tools/vulkan-sdk`, then running the build script.
The private existing C++ toolchain supplies CMake, Ninja and GCC 14.4.

AMD's current ROCm 10.1 matrix includes this OS/kernel generation and RX 7000
gfx1100. Still select a mutually compatible driver, SDK, PyTorch and engine build
after the card arrives. Follow the user's development/nightly preference when
selecting candidates, record exact versions, and test before activation. Do not
silently reuse Strata setup's older default TheRock wheel pin. An isolated SDK
is preferable to replacing shared CUDA environments. Strata setup can alter its
engine/configuration, so do not run its full installer in the active CUDA tree.

Strata's HIP build supports MTP, mmap and ordinary RAM expert residency. Enable
HIP MMQ, but add a hipBLASLt tuning table only when **both gfx1100 and the exact
hipBLASLt version match**. Keep `lib_dirs` in the generated profile consistent
with the selected HIP SDK; do not inject CUDA libraries into it.

## After the physical swap

1. Run `llm-upgrade-check --json`. Confirm one working RTX 4070, amdgpu-bound
   24 GB Navi31, writable `/dev/kfd` and render node. If group access is missing,
   apply the required render/video membership and log in again. Check firmware,
   negotiated PCIe width under load, temperatures and power before benchmarking.
2. Enumerate Vulkan devices using the separate server's `--list-devices` and
   the private Vulkan loader/tool libraries. Verify the AMD device's actual name
   and PCI mapping; replace `AMD_VULKAN_DEVICE` in the candidate INI. Do not
   assume `Vulkan0`, `CUDA0` and `HIP0` refer to the same physical card.
3. Install/select an isolated ROCm SDK, record its version, run
   `ROCM_PATH=/path/to/sdk bash hardware/build-strata-hip.sh`, then run the
   resulting `strata-device --list-devices` and `--selftest`. Validate library
   resolution and HIP ordinal before using the generated Strata configuration.
4. Stop the current inference through its owned launcher before an AMD load.
   Extend `backend_switch.py` for the **exact** new Vulkan/HIP server paths and
   AMD memory-release checks before wiring them into normal launchers. Its
   current driver-release check is NVIDIA-only. Preserve DSH, Turnstone, gateway
   and unrelated GPU jobs; do not use blanket process killing.
5. Validate short generation, streaming, tool-call/result round trips and MTP
   acceptance/correctness. Compare MTP on/off and Q4/Q8 KV where supported.
   Increase contexts in measured steps: 32K → 64K → 128K → 256K where the model
   supports them. Test long prompts, not just cache allocation. Record prefill,
   decode, latency, peak VRAM/RAM and disk activity with model/commit/context.
6. Once validated, adapt the routers and `run-strata-backend` (currently forces
   CUDA 0,1), replace only the relevant active profiles, and revise the hardware
   guard to accept the activated layout. Synchronize actual contexts in DSH,
   Turnstone and gateway catalogs. Keep API model IDs and port 10000 if possible;
   verify LAN/Tailscale addresses and authenticated client calls after reboot.
7. Update README benchmarks with **new measured** results, this handoff, the
   Shared handoff and GitHub. Existing results belong to the old two-NVIDIA setup.

No inference speed, maximum context, AMD driver operation or cross-vendor
performance has been measured yet. The first activation remains post-swap work.

## Preparation validation

The separate Vulkan build completed and `--list-devices` enumerated both current
NVIDIA cards. No model was loaded into that build. Five upgrade regression tests
and all 13 existing automatic-handover tests passed. The real current topology
passed its guard, and the existing Strata Q3 service still reported healthy after
preparation. `llm-upgrade-check` was installed as an actual PATH command file.
Details and executable checksum: [validation record](validation-2026-10-15.json).

Read-only Vulkan enumeration from the repository root:

```bash
LD_LIBRARY_PATH="$PWD/llm-tools/vulkan-sdk/usr/lib/x86_64-linux-gnu:$PWD/llm-tools/cuda-build/lib" \
  llama.cpp/build-vulkan/bin/llama-server --list-devices
```

## Sources checked October 15

- [AMD ROCm compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html)
- [Strata HIP build and serving](https://github.com/Niko1221/Strata/blob/main/docs/AMD_HIP.md)
- [Strata RX 7900 XTX performance methodology](https://github.com/Niko1221/Strata/blob/main/docs/AMD_HIP_PERFORMANCE.md)
- [llama.cpp build backends](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [vLLM GPU installation and Radeon targets](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
- [AMD SGLang Radeon notes and AITER limitation](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/sglang.html)
- [Upstream SGLang RDNA tracking](https://github.com/sgl-project/sglang/issues/30599)
- [RDNA3 SGLang plugin, candidate only](https://github.com/AMD-AIM/sglang-radeon/)
- [RX 7900 XTX specifications](https://www.amd.com/en/products/graphics/desktops/radeon/7000-series/amd-radeon-rx-7900xtx.html)
