# MiniMax H3 Image added, ComfyUI moved to 0.45.4 — November 15, 2026

Owner request: add MiniMax H3 Image to the image models in an appropriate quantization, with council research first.
The owner approved the ComfyUI update and the download after seeing the research.

## What was installed

| Role | File | Bytes | SHA-256 |
|---|---|---:|---|
| Denoiser, INT8 ConvRot | `diffusion_models/minimax_h3_image_pruned_int8_convrot.safetensors` | 20,979,314,802 | `83eb140f1ff95c068f8a6886e6d3f3d0d4ab2e07bb2fe6d2ef992a51146ee622` |
| Image VAE, FP16 | `vae/minimax_h3_image_vae_fp16.safetensors` | 1,168,505,312 | `d80e9c2e5cfc9844869961ff5a58c9a9e52182df6bfb30b26018dd7f348721af` |
| Text encoder (reused, already installed) | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` |

Source: [Comfy-Org/MiniMax-H3-Image](https://huggingface.co/Comfy-Org/MiniMax-H3-Image) at revision `0bb149f51e3156ed4b90dd45d5620346bfe1df8f`.
Both downloads matched the published SHA-256 before they were moved into place. The installed encoder was hashed and matches the
hash the image repository publishes, so it is the same file and nothing was duplicated.

**Why INT8:** the BF16 denoiser is 40.2 GB and does not fit one 24 GB card; INT8 is the highest-quality published format that does,
it is the official template default, and it uses the same quant layout as the installed H3 video INT8 file. The 4-bit files were
ruled out by the collection's quality policy and GGUF needs a plugin this server does not have.

The model is a 33.1B-parameter image generation and editing model released November 10–11. It is distilled to 6 steps without
CFG inside the checkpoint. Its community licence excludes the USA, EU, UK and South Korea from its territory and restricts some
commercial use; the owner was told before installation.

## How to run it

API graph: `graphics/workflows/minimax-h3-image-t2i-api.json`. Settings from the official template: `euler` / `simple`, 6 steps,
CFG 1.0, denoise 1.0, batch 1, CLIP type `minimax`, no prompt enhancer. Placement is the usual staged one: denoiser on GPU 0,
encoder and VAE on GPU 1. Sizes are multiples of 32; the model is meant for 4 to 20 megapixels.

## Measured on this server

| Run | Mode | Time | Peak VRAM GPU 0 / GPU 1 | Lowest free RAM |
|---|---|---:|---:|---:|
| 2048×2048, files already in the page cache | staged | 36.3 s (2.2 s per step) | 20.7 / 16.9 GiB | 40.1 GiB |
| 4096×4096, warm | staged | 126.3 s (11.9 s per step) | 22.5 / 17.0 GiB | 35.3 GiB |
| 2048×2048, first job after start | production (two-card mode server) | 46.1 s | not sampled separately | — |
| 2048×2048, after an H3 video job | production | 96.4 s | — | — |
| 2048×2048, first job through `graphics/start-comfyui`, files read from SATA | production | 114.8 s | — | — |

Sampling itself takes about 13 s at 2048×2048; the rest is loading 37 GB of weights, so a run takes 36 s when the files are cached in RAM and about 100 to 115 s when they are read from the SATA drive. Every model loaded completely with no partial offload. No swap was used. The 2048 and 4096 images were viewed: a coherent
teapot scene in both, and the 4096 image renders the requested "LOCAL LLM" tag text correctly (the 2048 one garbles it).
The upstream mixed-dtype attention bug (ComfyUI issue 17713) did not occur. No kernel fault, no GPU hold.

Not tested: sizes other than these two, more than one reference picture, the INT8 text encoder, and quality against BF16.

## Image editing and editor workflows (added the same evening)

One edit with a single reference picture ran through the production launcher: the 2048×2048 teapot image above as `<Picture 1>`, with the instruction to make the teapot cobalt blue and replace the fern with a small lemon tree. API success in 110.3 s read from SATA (64.9 s for a second run with the files cached); peak VRAM 21.6 / 19.4 GiB; no error. The result keeps the scene, light, steam and tag and turns the teapot blue, but the fern was **not** replaced, and the picture is visibly sharper and harsher than its source. One prompt and one seed: this shows the reference path works on these cards, not how well the model follows edits.

Editor workflows are saved in the ComfyUI workflow list as **MiniMax H3 Image INT8** and **MiniMax H3 Image Edit INT8** (`graphics/workflows/minimax-h3-image.json`, `minimax-h3-image-edit.json`; API graphs `minimax-h3-image-t2i-api.json`, `minimax-h3-image-edit-api.json`). They were made by loading the tested API graphs in the 0.45.4 editor; the text-to-image one converts back to the same API graph, and the edit one was queued from the editor and succeeded. The edit workflow expects a picture named `h3_image_edit_reference.png` in the input folder; choose your own in its Load Image node.

## ComfyUI 0.44.0 → 0.45.4

The installed 0.44.0 has no H3 Image support. 0.45.4 was set up as a second source checkout beside the old one, sharing the
same Python environment; the only package difference is `comfyui-workflow-templates` 0.11.102 → 0.11.109, held in the new
checkout's dependency overlay. Torch, comfy-kitchen, comfy-aimdo and the frontend are unchanged. `graphics/runtime-versions.json`
now selects the new checkout.

Re-run on 0.45.4, all successful: FLUX text-to-image (94 s) and edit (108 s), Qwen-Image (94 s), H3 native-32B video
(143 s staged, 145 s in production mode), and default H3 video in two-card tensor-parallel mode (132 s, twice). Both two-card
videos decode fully (39 frames, AAC audio). Not repeated: the November 5 finite-tensor hooks and the Qwen-Image edit workflow.

**One fix was needed.** In production mode the two-card loader recognised H3 by the shape of one attention weight, which the
image denoiser shares. It split the image model in half and waited for a second rank that had no job, until the RCCL watchdog
aborted the pair after 300 s. `graphics/h3-tp2/tp_boot.py` now also requires the audio stream that only the video model has
(the same test ComfyUI uses), so the image model loads whole. Verified on both checkpoints and both pre-sliced halves.

**Rollback:** in `graphics/runtime-versions.json`, copy `previous_runtime_selection` back over `runtime_selection`. The 0.44.0
checkout and its overlay are untouched. H3 Image cannot run on 0.44.0.

## Research

A council of agents (codex, hermes, kimi, agy, with Claude managing) researched the model, every published quantization, AMD
evidence and the official workflow; each result was checked by a second member. One council claim was wrong and corrected here:
it reported 0.45.0 as the latest ComfyUI release, while 0.45.1 to 0.45.4 exist. No published run of this model on an
RX 7900 XTX was found beforehand, so the numbers above are the first for this hardware.
