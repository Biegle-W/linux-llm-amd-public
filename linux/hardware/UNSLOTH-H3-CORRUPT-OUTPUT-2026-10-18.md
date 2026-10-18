# Unsloth MiniMax-H3 corrupt output — October 18

Status: investigated an existing user-generated clip; root cause unconfirmed.
No inference process was started, runtime replaced, or model downloaded for this
investigation. ComfyUI remains a proposed setup, not an installed fallback.

## Observations

- The saved clip is 864x480, 124 frames at 24 fps, text-to-video, using
  `unsloth/MiniMax-H3-GGUF/minimax_h3_fl2va_pruned-Q2_K.gguf`.
- Its recipe records 30 steps, guidance 1.0, flow shift 12.0, automatic memory
  mode and group offload. The log reached all 30 denoising steps, decode, export
  and completion. Generation request to completion took about 22 minutes 35
  seconds. This is a failed-quality render, not a usable speed benchmark.
- A decoded frame approximately two seconds into the MP4 shows repetitive
  tiles with no recognizable scene, consistent with the user's report.
- The managed ROCm engine install record identifies upstream
  `leejet/stable-diffusion.cpp` release `master-951-f89d9b1`, substituted for
  requested Unsloth build `master-951-f89d9b1-uafac7a7`. Its installer explicitly
  warns that the fallback lacks H3 fixes.
- The runtime warned that GPU-run offloaded weights would require 26.9 GiB of
  pinned host RAM versus about 25.3 GiB available, and selected CPU text encoding.
  This can affect speed/fit; it does not prove the cause of corrupt output.
- The installed H3 command builder pins CFG to 1.0 and does not introduce a
  blanket `--type`. A header-only scan of the downloaded denoiser found 532
  tensors; all 267 normalization/one-dimensional tensors retain F32, F16 or
  BF16 types. No quantized one-dimensional tensor was found. Therefore the
  installer's warning about quantizing norms is not established as the cause.

The denoiser is aggressively quantized, but Q2 alone has not been isolated as
the failure. A completed progress bar does not validate model output. Increasing
steps or buying more RAM is not a demonstrated correction.

## Next validation sequence

1. Record the exact engine and all four component files in the next test.
   Validate a short, small text-only clip with a simple fixed prompt/seed first.
2. Use an H3-capable patched engine or a compatible ComfyUI loader; preserve
   working LLM environments. Validate both GPUs explicitly before activating
   a profile under the workstation's dual-GPU policy.
3. Compare fixed settings before changing quantization, attention or offload.
   Only scale to 124 frames after the small test produces a recognizable scene.
4. Validate image conditioning separately from text-to-video. Do not call a
   text-only success proof that image-to-video works on gfx1100.

Primary references:

- [Unsloth H3 model/component instructions](https://huggingface.co/unsloth/MiniMax-H3-GGUF):
  H3-specific encoder, video/audio VAEs and CFG 1.0. Its sd.cpp examples are
  backend-specific; do not transplant unrelated ComfyUI sampling settings.
- [Unsloth H3 command builder](https://github.com/unslothai/unsloth/blob/main/studio/backend/core/inference/sd_cpp_args.py).
- [ComfyUI H3 guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3):
  native templates, model variants and sampling schedule. The native template's
  safetensors loader cannot simply be pointed at a GGUF file.
- [gfx1100 image-conditioning report](https://github.com/leejet/stable-diffusion.cpp/issues/1985):
  another user's older Unsloth-fork ROCm build hung on I2V while T2V worked.
  This is a separate upstream report, not a local reproduction or explanation
  of the present text-only corrupt clip.

No private prompt, media, raw logs, account data or model binaries are included.
