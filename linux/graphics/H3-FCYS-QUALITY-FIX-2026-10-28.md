# H3 off-prompt conditioning fixed — October 28, 2026

The saved text conditioning was entirely NaN. Opting into the Triton backend routed NVFP4 weight dequantization to a failing path on this gfx1100/ROCm stack. Disabling Triton **in the encoder preprocessing process** restored finite conditioning while keeping GPU initialization. The optimized actual fcys RCCL TP2 run then completed 20 steps and exported a 39-frame red-teapot clip. A matched true one-card control also passed sampled visual and technical AV checks. No production promotion or new speedup is claimed.

## Evidence for the cause

The old fixture's prompt hash matched the submitted teapot prompt, but all **389,120 values** of its float32 `[1,76,5120]` text embedding were NaN. Its initial audio/video latents were finite zeros. Hash identity proves that ranks share a fixture; it does not prove that the fixture is valid.

Previously completed native-Comfy one-card controls with this same invalid fixture produced canids at five frames and a sunset at 39 frames. Increasing length alone did not restore the prompt. A fresh original CPU-initialized encoder path also reached a non-finite first query projection. Its initial diagnostic logger then failed because a node argument shadowed Python's `type`; this instrumentation error was fixed and the attempt was cleanly shut down. The subsequent GPU-initialized trace recorded finite float32 input, maximum absolute value `0.0931093767`, entering `layers.0.self_attn.q_proj`, followed by non-finite output. This occurs before attention. Relevant core encoder, quantization, operations and loader files match the earlier successful source snapshot.

A small guarded operator test isolated the first projection's unchanged checkpoint tensors. Raw weight scales were finite. For both float16 and float32 output, eager NVFP4 dequantization returned finite `[8192,5120]` weights. Enabling Triton selected its NVFP4 implementation and returned **20,971,520 NaNs out of 41,943,040 elements** in each output. This is direct evidence of the failing backend path on the tested stack.

Static inspection explains the dispatch mismatch: the Triton NVFP4 implementation uses NVIDIA inline PTX and declares a minimum compute capability of 10.0. The registry obtains device major/minor values from Torch; the AMD device reports 11.0 and is accepted by the measured selection. This source-level explanation is an inference supported by the operator result, rather than a new cross-platform compatibility test.

## Corrected low-RAM execution

The encoder keeps `initial_device=cuda:0`, GPU load device and CPU offload device. Its process starts with the Triton backend disabled, so NVFP4 dequantization uses eager. All 50 encoder layers and all exported conditioning values are finite. The corrected fixture SHA256 is `fdb5e79caabcf4976e314dd2c5c9e49dd60a41920909ae833f4158b43ae5dbda`; the old fixture is preserved as failure evidence. Export, load and a CPU-only preflight before GPU ownership now reject non-finite floating tensors. The preflight also checks the prompt hash.

The completed encoder process exits before denoising starts. Both actual fcys TP ranks load the same finite conditioning. CK attention and the denoiser's Triton-backed INT8 operations remain selected; BF16 compute/wire, no-P2P RCCL SHM transport, one channel and 1 MiB communication buffers remain. Rank 0 alone loads the audio/video decoders. Rank 1 exports finite sampled latents. The same-instance import bridge and all four original fcys source files remain unchanged.

The [posted fcys source](https://lcz.me/topic/2643/17) and [INT8 plugin revision](https://github.com/patientx/ComfyUI-INT8-Fast-ROCM/tree/6b28bf637782d25225a88e316d864a8f551be000) are preserved privately; source with unclear redistribution permission is not bundled. This is ComfyUI 0.42.0 (`8f04fd6ecf4a548937971e840af2a985529fab76`), Torch `2.15.0.dev20260827+rocm7.2`, HIP 7.2.53211 and comfy-kitchen 0.2.39. No installed runtime or weight was changed.

## Corrected generation and control

Both arms use the same corrected conditioning, INT8 plugin loader, ConvRot setting, CK, 608×352×39 workload, 20 res_multistep/simple steps, seed 42, CPU noise and batch 1. The control sees one physical card and does not initialize TP. The TP arm uses two physical cards and the actual fcys model hooks; each rank confirms 28 heads and the expected half-width dimensions.

Each exported MP4 contains **39 distinct 608×352 H.264 frames at 24 fps, 1.625 seconds**, plus stereo 32 kHz AAC audio. FFmpeg decodes both streams without errors and audio samples are finite. Sampled frames 1/20/39 show a red ceramic teapot on a pale wooden table, warm sunlight, a blurred green plant and changing steam with a fixed composition. Steam rises mainly above the lid rather than precisely from the spout. No visible text/logos appear in sampled frames. Audio semantics and broader motion quality are not established by these short clips and signal checks.

TP rank 1 exports finite float32 video `[1,24,12,22,38]` and audio `[1,32,2,65]` latents. Passing subject compliance does not establish full-model numerical equivalence between one card and TP2. No excluded warmup plus three-trial timing series was run for this repair; single-request and lifecycle durations remain diagnostic measurements.

## Memory, safeguards and cleanup

Corrected preprocessing and TP2 retained at least **11.286 GiB host RAM available**. TP2 alone retained 12.506 GiB, with sampled free-VRAM minima 7.096/12.581 GiB. The one-card control retained 6.222 GiB host RAM available. Owned swap was permitted; corrected preprocessing/TP2 reached 6.221/10.982 GiB respectively, with zero dedicated spill and no guard faults.

| Diagnostic | Execution result | Min host available GiB | Min free VRAM GiB, card 0 / card 1 |
|---|---|---:|---:|
| Native 5 frames, invalid fixture | passed | 6.288 | 3.728 / 23.958 |
| Native 39 frames, invalid fixture | passed | 6.252 | 3.425 / 23.958 |
| Original CPU initialization, Triton enabled | failed | 6.333 | 8.308 / 23.958 |
| GPU initialization, Triton enabled | failed | 11.213 | 6.794 / 23.958 |
| GPU initialization, Triton disabled | passed | 11.286 | 5.532 / 23.958 |
| Raw NVFP4 backend comparison | passed | 24.757 | 22.368 / 23.958 |
| Corrected actual TP2, 39 frames | passed | 12.506 | 7.096 / 12.581 |
| Corrected one-card control, 39 frames | passed | 6.222 | 2.685 / 23.958 |

The first two native controls passed execution but failed prompt compliance with the invalid fixture. The CPU diagnostic's logging error and the GPU trace's expected non-finite rejection are workflow failures, not memory-guard stops. The operator comparison completed successfully as a diagnostic while demonstrating the bad Triton outputs.

Both isolated host checks remain explicitly **1 GiB**. All other safeguards remain: 2 GiB whole-card free-VRAM soft floor for four samples, 1.5 GiB hard floor, physical-RAM scope cap, `MemorySwapMax=max`, zero dedicated spill, ownership locks, lifecycle thermals and loading-swap-v3. Loading/parked swap and reads are allowed; rates/PSI remain advisory. Production launchers, workflow files, pins, guard sources and paused schedules are preserved.

| Corrected stage | Thermal samples / errors | Sampled junction peaks °C, card 0 / card 1 |
|---|---:|---:|
| GPU initialization, Triton disabled | 175 / 0 | 58.0 / 35.0 |
| Corrected actual TP2, 39 frames | 204 / 0 | 70.0 / 65.0 |
| Corrected one-card control, 39 frames | 235 / 0 | 76.0 / 38.0 |

Sensor peaks and SMU flag samples are retained in the [numeric evidence](../hardware/results/h3-fcys-quality-fix-2026-10-28.json); flags are not measured time throttled or proof of a performance loss. All owned workers exited, KFD clients cleared and matching GPU ownership was released. The corrected candidate remains isolated. Any future performance claim needs a separately defined matched timing protocol; these completed diagnostic tests need not be repeated for documentation.
