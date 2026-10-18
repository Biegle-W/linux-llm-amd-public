# Downloaded Unsloth generation models — October 18, 2026

Read-only inventory of the existing Unsloth Hugging Face cache on Shared SATA.
Cache root: `/mnt/shared/Unsloth/hub`. No files were downloaded, moved, deleted or loaded.
There are **16 weight files totaling 93.18 GiB** (100,050,424,232 bytes), excluding
small configurations/tokenizers and filesystem allocation overhead.

| Repository / component | Downloaded format | Weight size GiB |
| --- | --- | ---: |
| Qwen-Image-2.1 transformer, two shards | BF16 safetensors, Diffusers layout | 13.25 |
| Qwen-Image-2.1 text encoder, four shards | BF16 safetensors | 16.33 |
| Qwen-Image-2.1 VAE | FP32 safetensors | 1.26 |
| Qwen-Image-2.1 image transformer | `qwen-image-2.1-Q4_K_M.gguf` | 3.91 |
| Qwen-Image-2.1 text encoder | FP8 safetensors | 8.75 |
| Qwen-Image-2.1 text encoder | INT8 ConvRot safetensors | 8.71 |
| MiniMax H3 video transformer | `minimax_h3_fl2va_pruned-Q2_K.gguf` | 6.26 |
| MiniMax H3 Qwen3VL 32B text encoder | Q2_K_M GGUF | 12.20 |
| MiniMax H3 Qwen3VL 32B text encoder | Q4_K_M GGUF | 16.97 |
| MiniMax H3 video VAE | FP16 safetensors | 4.85 |
| MiniMax H3 audio VAE | FP32 safetensors | 0.56 |
| bge-small-en-v1.5 embedding model | FP32 safetensors, plus one I64 tensor | 0.12 |

## What is complete and what is only metadata

The Qwen BF16 Diffusers snapshot has all four indexed text-encoder shards,
both indexed transformer shards, VAE, scheduler and processor/tokenizer files.
It totals **30.84 GiB of weights**. The newer second snapshot contains only
`model_index.json`; it is not another complete model copy.

The `Qwen-Image-2.1-FP8` repository cache contains **only the two text encoder
variants** above, under different snapshots. The FP8 or INT8 image-transformer
files listed in cached repository metadata are **not downloaded**. Do not infer
model availability from a repository folder or its `trees/` manifest alone.

MiniMax H3 has the Q2 video transformer, two alternative text-encoder quants and
both VAEs. This establishes component availability, not a tested complete
ComfyUI workflow; GGUF loaders and template compatibility must be checked.
No H3 INT8 video transformer, H3 Turbo LoRA, Qwen-Image Turbo, Wan or LTX
weights were found in this Unsloth cache. A Z-Image-Turbo lock directory exists
but no corresponding weight repository is present.

The bge model is for embeddings, not image/video generation. The tiny
`stories260K.gguf` and `ggml-vocab-*` files in the Unsloth runtime are test or
vocabulary fixtures, not extra downloaded production generation models.

## Verification and reuse

All 15 image/video weight files match their byte sizes in cached Hugging Face
repository manifests. All safetensors headers and tensor-data extents are valid;
GGUF file magic/version headers are valid. The two Qwen shard indices have no
missing referenced shards. No `.incomplete` download files were found.
This is **not a full SHA-256 integrity check or generation/quality benchmark**.
The embedding file passed the safetensors structure check; its cached remote
size manifest was not available.

Reuse these existing files before downloading another base model. The BF16
Qwen model is a multi-folder Diffusers checkpoint, not the single-file Comfy
Turbo checkpoint named in the earlier proposed guide. A compatible loader or
conversion is required; renaming files does not convert formats. Do not move
or delete Unsloth's snapshots while it still references them.

The [ComfyUI walkthrough](IMAGE-VIDEO-SETUP-2026-10-18.md) remains a proposal;
this inventory supersedes any assumption there that no generation weights are
available. Prefer testing reuse of the existing Qwen/H3 components first.

## Hardware fit assessment — October 18 follow-up

The downloaded families are reasonable candidates, but this inventory does not
establish the best quants or fastest runnable profiles for two 24 GB gfx1100
cards and the last verified 32 GB host RAM. No new benchmark was run.

- Qwen base BF16 is useful as a quality baseline; Q4 is a compact alternative.
  Neither is the speed-oriented Turbo model. Keep existing components until a
  compatible Comfy loader is verified. An INT8 text encoder is a useful candidate,
  not a proven faster option than BF16 on this installation.
- For fast images, test the official 8-step Qwen Turbo model/LoRA first, or a
  separately tested Viggle v0.3 6-step workflow. Do not apply Turbo schedules to
  the unmodified base. These adapters/models are not downloaded yet.
- H3 Q2 plus Q2/Q4 text encoders is a memory-saving sd.cpp collection, not a
  locally validated quality/speed optimum. The existing Q2 render is corrupt;
  that does not prove Q2 caused it. Native Comfy H3 INT8 plus a matched 8-step
  fl2va Turbo LoRA has closer firsthand XTX evidence. W6A8 is a smaller native
  candidate when INT8 activation headroom is inadequate, not an established
  local winner. Existing H3 VAEs may be reused through compatible loaders.
- Allocate denoising and text/VAE work explicitly between cards. Two cards do
  not automatically provide one 48 GB allocation, or double generation speed.
  This placement remains unvalidated locally.

See the [forum source assessment](FORUM-OPTIMIZATION-SOURCES.md#october-18-imagevideo-model-fit-assessment).
No models were added, removed or changed following this comparison.
