# Graphics model collection

One quality-oriented precision per image/video model, with one required encoder
and the corresponding VAEs. Runtime installation and full generation validation
are separate from this file migration. No new speed benchmark is claimed.

| Role | Retained file | Origin |
|---|---|---|
| Qwen-Image 2.1 base | `diffusion_models/qwen_image_2.1_bf16.safetensors` | Lossless merge of existing Unsloth BF16 shards; original unfused MLP layout supported by ComfyUI |
| Qwen encoder | `text_encoders/qwen3vl_8b_bf16.safetensors` | Lossless merge and key mapping of existing BF16 shards |
| Qwen VAE | `vae/qwen_image_2.1_vae_fp32.safetensors` | Existing FP32 tensors mapped to Comfy/Wan layout, with singleton shape changes only |
| H3 first/last-frame base | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | New native Comfy INT8 replacement for the removed Q2 |
| H3 encoder | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | New matching native compact encoder |
| H3 video VAE | `vae/minimax_h3_video_vae_fp16.safetensors` | Existing downloaded file, moved intact |
| H3 audio VAE | `vae/minimax_h3_audio_vae_fp32.safetensors` | Existing downloaded file, moved intact |

## Storage and integration

The collection lives on the shared SATA filesystem in `Graphics-Models`.
Use [extra_model_paths.yaml](extra_model_paths.yaml) with the local mount path;
on Windows use its corresponding drive path. This points ComfyUI at real files,
without symlinks or duplicate model copies. Do not reselect the retired Unsloth
Hub entries: loading a missing cached model there can download it again.
The installed Unsloth application and generated user media are not removed.

Use the native `Load Diffusion Model`, `CLIPLoader` and `VAELoader` nodes.
Choose `qwen_image` for Qwen's encoder and `minimax` for H3's encoder.
The model files here are safetensors; no GGUF plugin is required for this set.
H3 `fl2va` supports text and first/last frames; it is not a `ref2va` checkpoint.

This selection prioritizes quality: Qwen keeps BF16 rather than Q4, and H3 uses
INT8 rather than Q2. No Turbo/Lightning LoRA is installed, and no base checkpoint
should be run on an unrelated distilled schedule. Start with the corresponding
base template's sampler, scheduler and steps. Additional adapters are optional
future choices, not duplicate model quants to retain now.

## Hardware placement and limits

Target hardware is two 24 GB gfx1100 GPUs and 32 GB system RAM. Propose the
denoiser on one GPU and the encoder/VAEs on the other, explicitly through Comfy
device-placement nodes. Both GPUs must be validated before enabling production
profiles. This is staged component placement, not a combined 48 GB allocation
or a proven tensor-parallel speedup. Activations still need headroom; H3 can need
bounded offload at larger resolutions. The full H3 BF16 denoiser is about 40 GB,
so it cannot be treated as a GPU-resident module on either 24 GB card.

Header/key/shape checks, lossless tensor-byte verification and download hashes
validate file integrity and format. They do not prove generation speed, quality
or a successful maximum-resolution run. ComfyUI remains uninstalled by this
storage-only task; existing LLM engines and launchers are unchanged.

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
