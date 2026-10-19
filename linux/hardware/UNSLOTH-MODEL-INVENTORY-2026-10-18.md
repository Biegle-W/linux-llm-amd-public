# Current graphics models — October 18, 2026

The user requested one quality-oriented precision for Qwen-Image 2.1 and MiniMax
H3, retaining only components reusable by ComfyUI. **Completed:** the collection
is now at `/mnt/shared/Graphics-Models` on Shared SATA. The old
Unsloth Hub model repositories have been cleared; there are no remaining weight
files in that cache. No shortcuts or duplicate model links were created.

| File | Precision | GiB |
|---|---|---:|
| `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | INT8 ConvRot | 19.53 |
| `diffusion_models/qwen_image_2.1_bf16.safetensors` | BF16 | 13.25 |
| `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | NVFP4 AWQ | 14.61 |
| `text_encoders/qwen3vl_8b_bf16.safetensors` | BF16 | 16.33 |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | FP32 | 0.56 |
| `vae/minimax_h3_video_vae_fp16.safetensors` | FP16 | 4.85 |
| `vae/qwen_image_2.1_vae_fp32.safetensors` | FP32 | 1.26 |

**Seven weight files, 70.40 GiB total.** The previous Unsloth collection had
16 weight files totaling 93.18 GiB. Net weight-storage reduction is **22.78
GiB**, including the newly downloaded H3 replacement and encoder. This is a
file-byte comparison, not a benchmark or a claim about unrelated disk activity.

## Selection and reuse

- Qwen retains its existing base BF16 transformer and BF16 text encoder. This
  is higher precision than the removed Q4/FP8/INT8 alternatives. The shards were
  combined without casting. The encoder was renamed to native Comfy keys; the
  original unfused transformer MLP layout is supported by current ComfyUI.
- The existing Qwen FP32 VAE was mapped to native Comfy/Wan key/shape layout.
  Singleton reshape operations and key renaming preserve every tensor byte;
  this is not merely a filename change or a lossy VAE conversion.
- The user explicitly chose the new Comfy-native H3 pruned INT8 ConvRot model.
  Its native NVFP4-AWQ encoder is the compact companion selected for a 24 GB
  card. INT8 H3 encoder weights are larger than one 24 GB card; NVFP4 storage
  does not imply native FP4 hardware acceleration on gfx1100.
- Both existing H3 VAEs were moved intact after full upstream SHA-256 checks.
- The source Unsloth Qwen BF16 snapshot is
  `20f5a734a394f0fce241bf2f9dc1b3d97ac18b2a`; the original H3 VAE snapshot is
  `d629413c2e5b51b38c453668b75ca3b06ca92703`.
- New H3 downloads use Comfy-Org/MiniMax-H3 revision
  `e5eb578a89295337b8ff433a035929ce0279e0b6`. Official Qwen reference headers
  use revision `a8342359c61979b06a8dafb1a47991fe1f30e994`.

## Removed scope

Removed Qwen Q4 GGUF, its alternate FP8 and INT8 text encoders, H3 Q2 GGUF,
both old H3 GGUF text encoders, and the bge embedding model. Removed the original
Qwen shard/VAE copies only after their replacement payloads passed byte checks.
Five exact model-cache directories and their stale lock directories were cleared.
LLM models, inference runtimes, the Unsloth application, generated images/videos
and private app data remain untouched.

## Verification and limits

- All 1,285 repacked Qwen tensors were independently read back and checked
  against their source bytes. Text/model keys and shapes match the native
  reference layout, accounting for the supported unfused MLP representation.
- New H3 downloads passed full official SHA-256 verification before their
  partial files were renamed. The retained H3 VAEs passed the cached upstream
  LFS SHA-256 checks. All seven files passed the native safetensors parser
  and have valid contiguous extents; parser checks loaded no inference tensors.
- Full file hashes are in [graphics/MANIFEST.json](../graphics/MANIFEST.json)
  and the collection's `SHA256SUMS`. Model binaries are ignored by Git.
- Current RAM remains 32 GB. Plan denoising on one XTX and text/VAE work on the
  other with native device-placement nodes. Both-card generation, activations,
  host offload and output quality still need runtime validation.
- **ComfyUI was not installed or benchmarked in this file-only task.** No new
  image/video speed is claimed, and the former corrupt Q2 render is not a
  result for this replacement. No Turbo LoRA or extra model family was added.

Use the [collection setup](../graphics/README.md),
[path configuration](../graphics/extra_model_paths.yaml) and
[Comfy walkthrough](IMAGE-VIDEO-SETUP-2026-10-18.md).
The [forum comparison](FORUM-OPTIMIZATION-SOURCES.md#october-18-imagevideo-model-fit-assessment)
contains the provenance and separates firsthand reports from local validation.
