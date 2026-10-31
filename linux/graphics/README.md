# Graphics model collection

**October 31 normal H3 activation:** projected 8B FP8 + v3.1 projection is now the default for text-to-video. One guarded actual-normal-ComfyUI 39-frame request passes API, finite-tensor and full AV-decode checks. Exact Native32B workflows remain for image-conditioned work/rollback. Component placement, attention, guards and other runtime selections are preserved. [Activation and rollback](H3-PROJECTED-8B-ACTIVATION-2026-10-31.md).

[AMD H3 encoder-format comparison](H3-AMD-ENCODER-FORMATS-2026-10-28.md): Tested W4A8 on the same H3 encoder against corrected NVFP4. Native HIP INT8 encoding was 5.91–8.11× faster across three prompts after warmup; separate cold-file load times, RAM/VRAM, nine paired TP2 clips and quality limits are recorded. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. Both host floors remain 1 GiB; other guards and production selection remain.

## Fresh H3 one-card versus two-card test — October28

Fresh tests completed on one physical 7900 XTX and on two 7900 XTX cards: one excluded warmup plus three timed 39-frame generations per arm, with a new isolated server for every generation. Full-request medians are 270.098 s on one card and 146.603 s on two (45.7% shorter on the two-card path). Sampler medians are 30.237/59.749 s. This establishes the measured fresh-server workflow result; loader/storage/noise/source differences limit attribution to GPU count alone. All independent guards and loading-swap-v3 remained. No production promotion or native Radiance run. [Fresh protocol, individual samples and limits](H3-ONE-VS-TWO-2026-10-28.md).


Later fcys reply 17 now supplies source code; the earlier no-source observation is superseded. Community W7900 timings remain external evidence.

[October28 Radiance H3 preflight](RADIANCE-H3-PREFLIGHT-2026-10-28.md): no gfx1100 accelerated kernel plugin is built; no GPU generation or speedup result. [Current swap policy](../hardware/SWAP-TASK-CONTINUITY-2026-10-28.md) lets work continue through swap activity unless an explicit write budget and measured matched slowdown support a stop.

[October 27 guarded H3 SP2 trial](H3-SP2-2026-10-27.md): stock-loader API incompatibility and reduced-RAM guard stops are recorded; no completed matched speedup or production change.

[October 27 H3 multi-GPU research](H3-MULTIGPU-RESEARCH-2026-10-27.md) now includes a firsthand dual-XTX ComfyUI SP2 report, the Kaihui AMD SP implementation and Bunsei’s separate R9700 Radiance TP2 fork. It distinguishes these from locally validated component placement, DisTorch2 and Dual-Sage. Research only; no runtime/workflow change or new graphics benchmark.

One selected image/video base model with its companions; H3 retains a smaller
text-only encoder and the original 32B image-conditioning/rollback encoder. ComfyUI is installed in an isolated ROCm environment;
both families passed two-GPU generation. See [measured results](VALIDATION-2026-10-18.md)
and [start/install instructions](INSTALL.md). The official **Comfy Desktop**
application-menu app imports the existing runtime, models and workflows;
the Desktop ComfyUI shortcut opens its browser interface;
normal startup with the official Ubuntu sandbox passed October21;
[Desktop validation](DESKTOP-2026-10-20.md).

| Role | Retained file | Origin |
|---|---|---|
| Qwen-Image 2.1 base | `diffusion_models/qwen_image_2.1_bf16.safetensors` | Lossless merge of existing Unsloth BF16 shards; original unfused MLP layout supported by ComfyUI |
| Qwen encoder | `text_encoders/qwen3vl_8b_bf16.safetensors` | Lossless merge and key mapping of existing BF16 shards |
| Qwen VAE | `vae/qwen_image_2.1_vae_fp32.safetensors` | Existing FP32 tensors mapped to Comfy/Wan layout, with singleton shape changes only |
| H3 first/last-frame base | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | New native Comfy INT8 replacement for the removed Q2 |
| H3 default T2V encoder + projection | `experimental/h3-8b-comparison-20261031/qwen3vl_8b_fp8_scaled.safetensors` + `mmh3-8b-ClipProj-v3.1.safetensors` | Stock FP8 8B + pinned v3.1 ridge projection; text-only |
| H3 native32B fallback encoder | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | Retained NVFP4 storage baseline, with eager dequantization on gfx1100 |
| H3 video VAE | `vae/minimax_h3_video_vae_fp16.safetensors` | Existing downloaded file, moved intact |
| H3 audio VAE | `vae/minimax_h3_audio_vae_fp32.safetensors` | Existing downloaded file, moved intact |
| FLUX 3 Image Klein (distilled) | `diffusion_models/flux3-image-klein-bf16.safetensors` | Official BFL ComfyUI release, BF16 (October 23) |
| Klein encoder | `text_encoders/qwen3vl_4b_bf16.safetensors` | Official BFL ComfyUI release, BF16 |
| Klein prompt upsampler | `text_encoders/qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors` | Official BFL ComfyUI release, INT8 ConvRot |
| Klein VAE | `vae/flux2-vae.safetensors` | Official BFL ComfyUI release |

**FLUX 3 Image Klein (October 23):** text-to-image and reference-image edits pass on both 7900 XTX
(1024×1024 in 34 s, a 1248×832 edit in 48 s, cold). Edits need the patchify-Conv3d workaround in
`comfyui-device-loaders` for the current torch nightly. Licence: FLUX Kommunity (non-commercial,
with exceptions). [Report](FLUX3-KLEIN-2026-10-23.md).

## Storage and integration

The collection lives on the shared SATA filesystem in `Graphics-Models`.
Use [extra_model_paths.yaml](extra_model_paths.yaml) with the local mount path;
on Windows use its corresponding drive path. This points ComfyUI at real files,
without symlinks or duplicate model copies. Do not reselect the retired Unsloth
Hub entries: loading a missing cached model there can download it again.
The installed Unsloth application and generated user media are not removed.

Use the native `Load Diffusion Model`, `CLIPLoader` and `VAELoader` nodes.
Choose `qwen_image` for Qwen's encoder and `minimax` for H3's encoder. The saved
workflows use the maintained direct CLIP/VAE loaders for efficient two-card placement.
The model files here are safetensors; no GGUF plugin is required for this set.
H3 `fl2va` supports text and first/last frames; it is not a `ref2va` checkpoint.

This selection prioritizes quality: Qwen keeps BF16 rather than Q4, and H3 uses
INT8 rather than Q2. No Turbo/Lightning LoRA is installed, and no base checkpoint
should be run on an unrelated distilled schedule. Start with the corresponding
base template's sampler, scheduler and steps. Additional adapters are optional
future choices, not duplicate model quants to retain now.

## Hardware placement and limits

Current hardware is two 24 GB gfx1100 GPUs; the live host exposes 30.56 GiB
RAM after the October28 reboot, up from the preceding 14.83 GiB state. Earlier
generation timings below retain their October18 32 GB hardware attribution. The
new host-staged trial and current control RAM-floor failures are recorded above.
The saved validated
workflows use the denoiser on GPU 0 and encoder/VAEs on GPU 1. Direct loaders set
the target at construction to avoid native retargeting's second encoder copy.
This is staged component placement, not TP or a combined 48 GB allocation.

Qwen passed 512x512 / 40 steps in 100.9 seconds total (about 13 seconds denoising).
H3 passed 608x352 / 39 frames / 20 steps in 232.4 seconds total (about 29 seconds
denoising), with coherent video and finite stereo audio. The 32 GB host swapped
while staging; larger sizes and maximum capacity remain untested. Original model payloads
stay on Shared SATA. The isolated host-staged trial retains 21.06 GB of derived
rank shards on the system disk; production model placement is unchanged. See the
[validation report](VALIDATION-2026-10-18.md) for sampling and timing limits.

## Provenance and reproduction

- [Comfy Qwen model layout](https://huggingface.co/Comfy-Org/Qwen-Image-2.1),
  reference header revision `a8342359c61979b06a8dafb1a47991fe1f30e994`.
- [Comfy H3 component set](https://huggingface.co/Comfy-Org/MiniMax-H3),
  download revision `e5eb578a89295337b8ff433a035929ce0279e0b6`.
- [ComfyUI loader source](https://github.com/Comfy-Org/ComfyUI/tree/8f04fd6ecf4a548937971e840af2a985529fab76),
  including native Qwen/H3 model detection, encoder handling and VAE support.
- Qwen VAE inverse naming was checked using the installed Unsloth
  `studio/backend/core/inference/diffusion_comfy_components.py`
  `_convert_wan_nested_vae` routine against official Comfy VAE headers.
- [Streaming repacker](repack-safetensors.py): combines/relabels safetensors with
  bounded RAM and independently checks every output tensor against its input
  bytes. It never changes dtype. Keep the generated verification sidecars with
  the local model collection; do not commit weights.
- [lcz.me firsthand XTX H3 report](https://lcz.me/topic/1168) supports testing a
  native INT8 path but uses a different 64 GiB/Turbo setup; its speed is not a
  prediction for these quality-oriented base profiles.
- [Level1Techs AMD generation report](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735)
  motivates isolated runtime validation; its RDNA4 results are not XTX results.
- [Official H3 workflow guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
  distinguishes native templates, quant formats and attention limitations. The
  encoder's NVFP4 storage format does not imply native RDNA3 FP4 acceleration.

See the maintained [inventory](../hardware/UNSLOTH-MODEL-INVENTORY-2026-10-18.md)
for final sizes, checksums, removal scope and validation status.

### Repack existing Qwen files before cache cleanup

These commands require the original source snapshot. Set `SOURCE_SNAPSHOT` and
`GRAPHICS_MODELS` to real directories first; the tool refuses to overwrite files.
The checked VAE map contains only tensor names and target shapes, not weights.

```bash
python3 graphics/repack-safetensors.py \
  --inputs "$SOURCE_SNAPSHOT"/transformer/*.safetensors \
  --output "$GRAPHICS_MODELS/diffusion_models/qwen_image_2.1_bf16.safetensors"
python3 graphics/repack-safetensors.py \
  --inputs "$SOURCE_SNAPSHOT"/text_encoder/*.safetensors \
  --rename-prefix model.language_model. model. \
  --output "$GRAPHICS_MODELS/text_encoders/qwen3vl_8b_bf16.safetensors"
python3 graphics/repack-safetensors.py \
  --inputs "$SOURCE_SNAPSHOT/vae/diffusion_pytorch_model.safetensors" \
  --key-map graphics/qwen-image-2.1-vae-map.json \
  --output "$GRAPHICS_MODELS/vae/qwen_image_2.1_vae_fp32.safetensors"
```

## October21 ROCm10.1 comparison

Retain the existing shared browser/native-Desktop Torch2.15nightly/packagedROCm7.2.1
stack. Normal61.51GiB RAM, one excluded full warmup and three timed full graphs
per workflow/stack: server medians image23.686/18.331s, H3 83.831/85.279s
(retained/new). Both workflows must improve; H3 regressed. All16 normal outputs
pass technical dimensions/frames/audio checks and sampled visual review. The
separate52GiB pilot's third timed H3 HIP fault stays recorded; not reproduced
under normalRAM, cause unproven. Models/workflows/component placement/reserves
are unchanged. [Methods, exact builds, thermal coverage and failed arms](../hardware/ROCM101-2026-10-21.md).
