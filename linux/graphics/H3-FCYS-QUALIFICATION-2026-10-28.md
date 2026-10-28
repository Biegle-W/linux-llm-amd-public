# Actual fcys RCCL TP2 + CK qualification — October 28, 2026

The actual published fcys transport and quantized row hooks passed bounded operator fixtures on this dual RX7900XTX host. The five-frame TP2 full workflow then stopped at the independent host-RAM floor while both text encoders were loading. **No dual-rank denoising, finished video/audio, matched timed benchmark or new speedup is established.** The candidate stays isolated.

The matched one-visible-card five-frame control completed all 20 denoising steps and exported decodable AV while keeping minimum available RAM 3.792 GiB. Visual inspection of frames 1/3/5 failed prompt compliance: two small wild canids in grass instead of the requested red ceramic teapot. Its guard/function pass is separate from this rejected quality gate; the cause is not isolated to CK, the INT8 plugin or the short frame count. The records below distinguish the control from the dual-rank failure. Earlier host-staged prototype medians belong to a different implementation and remain historical.

## Source and matching protocol

Used the four unmodified tp2-comfy v1.0.0 source files from [fcys reply 17](https://lcz.me/topic/2643/17), privately hash-pinned. The dependency is [ComfyUI-INT8-Fast-ROCM](https://github.com/patientx/ComfyUI-INT8-Fast-ROCM/tree/6b28bf637782d25225a88e316d864a8f551be000), revision `6b28bf637782d25225a88e316d864a8f551be000`. Its updater self-heal import downloads and writes a batch script, so that import was disabled in the isolated copy before use. Original sources, production files and pins remain. No source with an assumed redistribution license is exported.

Both arms used the same frozen ComfyUI 0.42.0 source (`8f04fd6ecf4a548937971e840af2a985529fab76`), Torch `2.15.0.dev20260827+rocm7.2`, HIP 7.2.53211, comfy-kitchen 0.2.39, INT8 loader, original checkpoint files/storage, fixed prompt, CPU RandomNoise seed 42, BF16 compute, CK attention, 608×352×5 at 24 fps, 20 res_multistep/simple steps and batch 1. Both disable dynamic VRAM, pinned memory and asynchronous offload, reserve 2 GiB and use cache-none. TP2 uses the unmodified bootstrap with one physical card visible in each process; the control uses one visible card and the same graph settings. Readiness waited for both installed model hooks, not merely the source's earlier READY event.

## What passed

- CK selected its HIP INT8 attention path. The checkpoint has 56 attention heads of 128 dimensions, split to 28 heads per TP rank. A 28-head, 128-dimension, 257-token BF16 operator fixture returned finite outputs. Extra 14-head and 256-dimension cases also passed; these are operator checks, not a complete H3 attention/quality benchmark. Maximum absolute difference against SDPA was 0.013672–0.023438 across all four cases; RMSE 0.001421–0.001466.
- RCCL 2.27.7 initialized on distinct physical cards and returned the expected SUM and MAX values in both BF16 and FP32. With P2P disabled, the observed route was SHM/direct/direct. The admitted fixture used 1 MiB buffers and one channel; an earlier default-channel attempt reached the host floor before a collective result. [AMD documents the buffer and channel controls](https://rocmdocs.amd.com/projects/rccl/en/develop/userguide/source/env.html#nccl-buffsize). This single configuration pass is not a transport performance result or proof that channel count alone caused the earlier memory difference.
- All eight row-parallel cases per rank reached the actual fcys shared-scale quantizer hook: tensorwise/per-row weights, ConvRot off/on and BF16/FP32 wire choices. Compute dtype restored afterward. The custom INT8 loader calls this Triton quantizer directly, so the separate Kitchen registry path did not bypass the hook in these fixtures.

## One-card media check

The control exported five distinct 608×352 H.264 frames at 24 fps (0.208333s) with stereo 32 kHz AAC audio (0.200000s). FFmpeg decoded both streams without error; decoded audio was finite, peak 0.094029 and RMS 0.014752. Frames1/3/5 show a coherent canid scene, which fails the submitted teapot prompt. This is a semantic quality rejection despite a valid container. Audio semantics and long-range video consistency cannot be qualified from this 0.2 s canary. The earlier native 39-frame control depicts the teapot, but backend/loader/frame-count differences prevent attributing this new failure to one cause.

## Precision correction

The earlier source-review wording that implied unconditional FP32 was too broad. `TP_WIRE` defaults to `bf16`; it preserves the existing compute dtype. Selecting a non-BF16 wire temporarily sets the plugin's compute dtype to FP32, which also changes activation/ConvRot computation. The BF16 fixtures differed from the unsplit BF16 reference by relative L2≈0.270–0.284%; FP32 comparisons against that BF16 reference were≈0.164–0.590%. These small fixtures demonstrate routing and finite numerical behavior, not exact equality, a model-quality gate, or a confirmed model bug. FP32 is not simply a lossless wire-format substitution.

## Attempts and memory admission

Host is i9-13900KS with 30.558 GiB OS-visible RAM and two 24 GB RX7900XTX cards. Values below are whole-host/per-card sampled minima and owned swap maxima. Lifecycle duration in the numeric record includes startup/loading/shutdown and is not generation speed.

| Attempt | Status | Host available min GiB | Card free minima GiB | Owned swap max GiB |
|---|---|---:|---:|---:|
| ck-preflight | failed | 20.421 | 23.882 / 23.958 | 0.000 |
| ck-operator | passed | 20.343 | 23.629 / 23.958 | 0.000 |
| ck-h3-heads | passed | 21.140 | 23.590 / 23.958 | 0.000 |
| rccl-numerical | guard_stopped | 2.417 | 23.696 / 23.727 | 0.238 |
| rccl-small-buffer | passed | 3.410 | 23.235 / 23.266 | 0.000 |
| canary-tp2 | guard_stopped | 2.417 | 12.895 / 13.008 | 11.387 |
| canary-control | harness_failed | — | — | 0.000 |
| canary-control2 | passed | 3.792 | 2.644 / 23.958 | 6.496 |

The first CK probe queried an inapplicable registry operation name; the corrected public API calls passed. The first control launch failed a TIME_WAIT-sensitive port precheck before spawning a worker; the listener check found no existing server and the port check was corrected. These setup failures are not model or kernel failures.

The TP2 canary's minimum available RAM was 2.417 GiB. The latched stop was `host_available_below_3GiB` during text-encoder loading; the lowest free VRAM was 12.895 GiB and dedicated spill stayed zero. Owned swap reached 11.387 GiB and was allowed. **Swap amount/rate, reads and PSI did not trigger the stop.** There is no measured DiT/RCCL sampling failure to infer from this loading result.

Every launched test retained loading-swap-v3, the immediate 3 GiB host floor, 2 GiB free-VRAM soft floor over 4 samples, 1.5 GiB hard floor, physical-RAM scope cap, unlimited permitted scope swap, zero dedicated spill, ownership locks and complete-lifecycle thermal recording. The TP2 canary has 58 thermal samples (GPU junction peaks 40/38°C, CPU package 78°C); the one-card control has 192 samples (junction 66/35°C, CPU package 76°C), both without sampler errors. The numeric record includes sample counts, per-card/CPU peaks and available SMU flags. Those flags are observed samples, not measured slowdown or proof of overheating. No guard was reduced.

## Disposition and next action

All owned workers exited, KFD clients cleared and GPU/server locks released. Production launchers/settings, paused schedules and model files remain. There is no promotion and no native Radiance qualification.

The next implementation steps are to isolate the one-card prompt-compliance failure and design a bounded common preprocessing/conditioning handoff that avoids duplicate text-encoder residency and uses identical saved inputs for both arms. Re-admit the five-frame DiT and AV path before any 39-frame warmup/timed series. The current request ends at these tested loading and quality blockers; no unchanged full-workflow retry or larger workload is justified by these results. See the [numeric evidence](../hardware/results/h3-fcys-qualification-2026-10-28.json) and the earlier [source review](H3-MULTIGPU-RESEARCH-2026-10-27.md#community-tp2-evidence-and-source-distinction--october28).
