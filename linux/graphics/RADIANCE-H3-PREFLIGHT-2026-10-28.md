# Radiance H3 on two 7900 XTX cards — October 28 preflight

**The tested Radiance H3 source cannot provide accelerated inference on gfx1100 as shipped.** This is a device-kernel compatibility blocker before model loading; no memory guard fired, no GPU inference was launched and no Radiance output or timing exists.

## Verified attempt

The experimental H3 Full-Ref branch is pinned to `a0653376c3f816cbd06f715fa56040c0407fc869` (Radiance 1.12.0). A fresh isolated CMake configuration explicitly targets `gfx1100` with the retained ROCm 7.2.3 SDK. The first compiler setup missed the private SDK's host libraries; restoring the same retained library paths resolves that setup error. The second configuration succeeds and prints:

> libr4d: RDNA4 (gfx12xx) only, and this build targets gfx1100 -- not built

The generated build target list contains no `radiance_home/kernels/libr4d.so` target. A minimal compile-only probe using the FP8 WMMA builtin and operand types from `libr4d/r4d_fp8_wmma.h` fails for gfx1100 with a requirement for `gfx12-insts,wavefrontsize32`; the exact same probe compiles for gfx1201. Neither probe executes on a GPU. The source architecture filter was not bypassed and the reference-kernel debug override was not presented as an accelerated GPU result.

Upstream main's build files, fetched October 28, retain the same gfx12-only accelerated plugin restriction. See the [H3 fork's build filter](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869/libr4d/CMakeLists.txt), [FP8 instruction implementation](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869/libr4d/r4d_fp8_wmma.h), and [upstream filter](https://codeberg.org/StillDeadcode/radiance/src/branch/main/libr4d/CMakeLists.txt).

FFmpeg development metadata was absent; media support was deliberately off for this kernel-availability configuration. This was not a complete generation-ready runtime build. No converted RAD weights were downloaded or existing model files changed.

## Comparison boundary

| Result | RAM | Full server request | Denoising/sampler span | Scope |
|---|---:|---:|---:|---|
| October21 retained one-card denoiser | 61.51 GiB | 83.831 s median | not separately reported here | Three measured trials |
| October28 completed one-card denoiser | 30.56 GiB | 210.098 s | 28.324 s | One measured completion after excluded warmup |
| Radiance TP2 on gfx1100 | 30.56 GiB | not measured | not measured | Device-kernel preflight blocked |

The completed Comfy control uses GPU0 for denoising and GPU1 for text encoder/VAEs. It is not dual-card DiT computation. The [post-upgrade record](H3-POST-UPGRADE-2026-10-28.md) retains its successful outputs and earlier v2 stop. No speedup or quality comparison with Radiance is possible.

The published full-ref native path also uses a Ref2VA FP8 RAD and admits at least 124 frames, whereas the saved Comfy control uses FL2VA INT8 ConvRot and 39 frames. A future completed run must align model, precision, conditioning and workload before claiming a matched performance comparison. [Source environment/workload limits](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869/README.md).

## Memory policy and next action

The user reaffirmed swap permission during this task. [The corrected v3 policy](../hardware/SWAP-TASK-CONTINUITY-2026-10-28.md) makes rates/reads/pressure advisory and requires an explicit write budget plus matched measured slowdown for an optional swap-related stop. It does not disable OS swap or terminate work because of swap use. Physical-RAM and VRAM protections remain separate. The prior 8 GiB activation reservation belongs to Kaihui SP2; it is not imposed as a Radiance requirement.

The former H3 stop at 14.874 MiB/s was read-heavy and does not establish harmful writes. The former SP2 2.673 GiB available-RAM stop was a separate physical-RAM floor. Neither is a Radiance failure observation. Display output being elsewhere does not eliminate model workspace or temporary allocation needs; the prior VRAM floors were conservative margins, not measured optimal minima.

Next action: supply or implement and validate a gfx1100 device-kernel path, then conduct an admitted trial under the current swap policy. More system RAM or a smaller free-VRAM margin does not add missing gfx12 instructions. Production Comfy/LLM configurations and paused schedules remain. No Radiance worker, GPU lock or unfinished compile job is retained.

[Numeric source/build/probe record](../hardware/results/radiance-h3-preflight-2026-10-28.json).
