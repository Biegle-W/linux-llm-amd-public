# Image and video workflow on two RX 7900 XTX cards

ComfyUI is installed and both retained families passed real generation.
[Results and resource measurements](../graphics/VALIDATION-2026-10-18.md),
[exact versions](../graphics/runtime-versions.json),
[reproduction/start instructions](../graphics/INSTALL.md).

## Generate an image

1. Open **ComfyUI** from the desktop/menu, or run `comfyui` in a terminal.
   Its terminal stays visible. Open http://127.0.0.1:8188.
2. Open **Workflows → Qwen-Image 2.1 BF16**. Refresh the workflow list if needed.
3. Edit the prompt in Text Encode Qwen Image 2.1. Start with the saved 512px
   size, batch 1, seed 42, 40 steps, Euler/simple and CFG 1. No prompt enhancer
   or Turbo adapter is required.
4. Click Run. Save the PNG from the output node or `graphics/outputs/validation/`.
   The first run took 100.9 seconds including loading; denoising was about 13 s.
   Larger image sizes need separate memory/quality validation.

## Generate video with sound

1. Open **Workflows → MiniMax H3 INT8** and describe the scene, motion, camera
   and sound in the prompt. This validated workflow is text-to-video.
2. Keep the saved 608x352 size, 39 frames, 24 fps, seed 42 and 20-step
   res_multistep/simple base schedule. It creates a 1.625-second draft.
   Frame lengths follow 17k+5; the trained 124+ frame range is a later test.
3. Click Run. The workflow decodes video and audio with their matching VAEs,
   then saves an H.264 MP4. The first run took 232.4 seconds including loading;
   denoising was about 29 s. The video was coherent and stereo audio finite.
4. Check the draft before increasing duration or resolution. No Turbo LoRA is
   installed; an 8-step schedule is not a supported substitute for the base test.

The retained H3 fl2va checkpoint also supports first/last-frame conditioning,
but image-to-video and Qwen editing were not tested here. A future workflow can
feed a saved Qwen image into H3's first-frame input; that is not a validated
cross-model pipeline yet. The old Unsloth Q2 render is historical and does not
describe this new native INT8 result.

## Placement, storage and memory

Denoiser: **GPU 0**. Text encoder and VAEs: **GPU 1**. Both cards were observed
working across stages; this is component placement, not TP. Two small maintained
loaders pass the device into ComfyUI's standard APIs at construction, avoiding
the native retarget node's duplicate encoder allocation. Core ComfyUI and the
weights are unchanged. No third-party node pack or GGUF plugin is required.

The seven retained weight files remain in `Shared/Graphics-Models` on SATA;
ComfyUI reads them through `extra_model_paths.yaml`. Its isolated environment,
logs and output media are on the Linux filesystem and ignored by Git.
No additional model quant was downloaded. The full inventory is
[here](UNSLOTH-MODEL-INVENTORY-2026-10-18.md).

Only 32 GB RAM is installed. H3 actively swapped during staging; first-load
latency is substantial even though the tested denoiser fit GPU memory. Do not
assume storage cannot affect time when model staging, offload or swap is active.
Run large LLM inference and graphics generation separately. The existing LLM
shutdown guard does not terminate ComfyUI. Stop its server with Ctrl+C when needed.

## Sources and remote use

[Install notes](../graphics/INSTALL.md) include the official ComfyUI, Qwen and
H3 sources, the gfx1100 corruption issue, and pinned runtime details.
[lcz.me 1168](https://lcz.me/topic/1168), Ang Lee, describes a different
single-XTX/64 GiB INT8/Turbo workload; its timings are not local benchmarks.
[Level1Techs 252735](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735),
locutusofborg780, July 16/August 18, 2026, reports RDNA4/32 GB runtime sensitivity.
See [forum source records](FORUM-OPTIMIZATION-SOURCES.md).

The server listens on loopback. From another PC, forward SSH port 8188, then
open http://127.0.0.1:8188 on the client. Windows may reuse the Shared weights
with its own ComfyUI runtime and paths; Windows generation was not validated.
