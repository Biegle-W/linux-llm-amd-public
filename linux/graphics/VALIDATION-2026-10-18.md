# ComfyUI model validation — October 18, 2026

**Both retained model families passed actual generation.** Qwen produced the
requested red teapot, white cup, wooden table and leafy background. H3 produced
a coherent red teapot with moving steam across the clip. Six frames spanning
its beginning, middle and end were visually inspected; no mosaic, random-pixel
or black-frame corruption was observed. Audio decoded as finite, nonzero stereo;
this is a technical audio check, not a subjective listening evaluation.

| Model | Test | Denoising only | Full server prompt | Result |
|---|---|---:|---:|---|
| Qwen-Image 2.1 BF16 | 512x512, batch 1, 40 steps, Euler/simple, CFG 1 | about 13 s (3.05 iterations/s average) | 100.9 s | Clean PNG |
| MiniMax H3 INT8 ConvRot | 608x352, 39 frames / 1.625 s at 24 fps, 20 steps, res_multistep/simple, CFG-free | about 29 s (1.46 s/iteration average) | 232.4 s | Clean H.264 MP4 with audio |

Seed 42; base checkpoints without Turbo adapters or a prompt enhancer. H3 uses
the native shifts 12 video / 3 audio. Denoising times come from the progress
bars; full prompt time comes from server execution events and includes loading,
conditioning, decoding and saving. These are single first-per-family runs in
this session, not repeated warm averages or a comparison against forum timings.
Do not interpret diffusion iterations per second as LLM tokens per second.

## Runtime and device evidence

[Exact versions](runtime-versions.json): ComfyUI 0.42.0 at
`8f04fd6ecf4a548937971e840af2a985529fab76`, isolated Python 3.12.14,
PyTorch `2.15.0.dev20260827+rocm7.2`, HIP 7.2.53211,
Comfy Kitchen 0.2.39, aimdo 0.5.6, frontend 1.55.18.
Dependency compatibility and BF16 matrix checks on both gfx1100 GPUs passed.
Comfy Kitchen HIP was available; the H3 log listed native INT8 operations and
emulated NVFP4. NVFP4 is compact storage here, not native RDNA3 FP4 arithmetic.

Denoising ran on GPU 0; encoding and VAE work ran on GPU 1. Loader logs and
per-card memory/activity samples confirm both cards were used. This is staged
component placement, not tensor parallelism or simultaneous dual-card denoising.
The H3 denoiser and encoder loaded completely on their assigned GPUs. Qwen's
BF16 source encoder computed in the default FP16 mode, its FP32 source VAE in
BF16; H3 used BF16 DiT compute, FP16 encoder/video VAE and FP32 audio VAE.

| Sampled resource | Qwen | H3 |
|---|---:|---:|
| GPU 0 peak total VRAM | 14.36 GiB | 21.10 GiB |
| GPU 1 peak total VRAM | 21.35 GiB | 20.52 GiB |
| Minimum available system RAM | 7.60 GiB | 3.64 GiB |
| Peak additional swap use from that run's starting point | 2.77 GiB | 8.39 GiB |

VRAM values include desktop/context allocations. Two-second sampling can miss
short peaks. Existing swap occupancy is not attributed to these runs. The
32 GB host did actively swap while staging H3; the short denoising phase was
GPU-resident. Loading time is therefore substantial and storage is not
universally speed-independent. These tests do not establish maximum capacity.

## Retargeting fix and output checks

The first Qwen attempt using core `CLIPLoader -> SelectCLIPDevice` was stopped
before denoising: its fresh deepclone created a second encoder copy and excessive
staging/swap. It is excluded from the table. The maintained
[direct CLIP/VAE loaders](comfyui-device-loaders/__init__.py) call ComfyUI's normal
load APIs with the target device set at construction. No upstream source or
weights were patched. See the [install/source notes](INSTALL.md#why-two-direct-device-loaders).

The H3 MP4 was independently decoded with PyAV: 608x352, 39 frames, 24 fps;
all frames were nonblank (minimum pixel standard deviation 71.18), with visible
steam motion. Its 32 kHz stereo audio contains 52,000 samples per channel;
all are finite, peak amplitude 0.0858, RMS 0.0111. The earlier Unsloth Q2 corrupt
render is a different runtime/quant/workload and is not a controlled comparison
or a proven diagnosis of that older failure.

Actual outputs and raw logs stay local under ignored `graphics/outputs/` and
`graphics/generated/`. No media, weights or private raw logs are published.
Models were unloaded after validation; the ComfyUI server remains available in
a visible terminal. A desktop/menu launcher and `comfyui` PATH command are installed.

Use the [saved workflows](workflows/) and [installation guide](INSTALL.md).
Longer videos (124+ frames), larger images, image-to-video, edits, Turbo and
Windows execution were not tested. No maximum-resolution or speed-optimum claim
is made. Existing LLM benchmarks were not rerun or changed.
