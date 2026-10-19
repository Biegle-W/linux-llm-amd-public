# ComfyUI on two RX 7900 XTX cards

Installed October 18, 2026, in an independent Python 3.12 environment. See
[exact runtime versions](runtime-versions.json), [dependency lock](requirements-validated.txt)
and [local validation](VALIDATION-2026-10-18.md). Existing LLM environments are
independent of this installation.

## Start and use

Open the **ComfyUI** desktop/menu launcher. It opens a visible terminal and the
local web interface at **http://127.0.0.1:8188**. Alternatively, run `comfyui`
from a terminal or SSH; use SSH port forwarding for a remote browser:

```bash
ssh -L 8188:127.0.0.1:8188 user@linux-host
```

Then open the same loopback address on the client. The server binds to loopback;
this installation does not expose a new unauthenticated LAN service.

Choose **Workflows**, then **Qwen-Image 2.1 BF16** or **MiniMax H3 INT8**.
Refresh the list if needed. Edit the prompt, keep batch count 1 and click Run.
Use the saved base-model schedules; neither workflow needs a prompt enhancer,
Turbo adapter, GGUF loader or third-party node pack. The small maintained
device-loader extension is installed by the launcher.

`graphics/workflows/*.json` contains the editor workflows; `*-api.json` contains
the matching API graphs. Outputs go into `graphics/outputs/validation/`, and
the server log is visible in the terminal and saved under `graphics/generated/`.
Both directories are ignored by Git. Close the server with Ctrl+C in its terminal.
Launching again opens the existing server rather than starting a second copy.

The denoiser uses GPU 0; the encoder and VAEs use GPU 1. This is staged component
placement, not tensor parallelism or a promise that both cards compute at once.
Run large LLM inference and image/video generation separately: they share the
same VRAM. The existing LLM switching guard deliberately does not kill ComfyUI.

## Reproduce the isolated installation

Set `LOCAL_LLM_ROOT` to this repository and select an installed Python 3.12.
These commands reproduce the tested source and wheel set rather than upgrading
another inference environment. A future upgrade needs new output validation.

```bash
cd "$LOCAL_LLM_ROOT"
git clone https://github.com/Comfy-Org/ComfyUI.git runtime/comfyui
git -C runtime/comfyui checkout 8f04fd6ecf4a548937971e840af2a985529fab76
uv venv --python /path/to/python3.12 runtime/comfyui/.venv
uv pip install --python runtime/comfyui/.venv/bin/python \
  --index-url https://download.pytorch.org/whl/nightly/rocm7.2 \
  'torch==2.15.0.dev20260827+rocm7.2' \
  'torchvision==0.30.0.dev20260831+rocm7.2' \
  'torchaudio==2.11.0.dev20260831+rocm7.2'
uv pip install --python runtime/comfyui/.venv/bin/python \
  --constraint graphics/requirements-validated.txt \
  -r graphics/requirements-validated.txt
uv pip check --python runtime/comfyui/.venv/bin/python
```

Edit `graphics/extra_model_paths.yaml` for the real Shared SATA mount. It points
at the seven retained files without copying weights onto NVMe. Copy the two
editor workflow JSONs into `runtime/comfyui/user/default/workflows/`.
Run `graphics/start-comfyui --auto-launch`. For PATH access install the small
`graphics/comfyui` wrapper into `~/.local/bin/`; set `LOCAL_LLM_ROOT` when using
a different repository location. Adjust the desktop file's absolute paths for
another workstation.

The launcher leaves both GPUs visible, reserves 2 GB, disables pinned memory,
async offload and DynamicVRAM, and uses PyTorch attention with no intermediate
node cache. It removes inherited expandable allocator options. These are the
validated baseline settings, not a claim of maximum performance. Comfy Kitchen's
HIP backend is available; its NVFP4 storage fallback does not imply RDNA3 FP4
hardware acceleration. No Comfy Kitchen attention override is enabled for H3.

## Why two direct device loaders

The initial native `CLIPLoader -> SelectCLIPDevice` test reloaded a second
encoder via `deepclone_multigpu` and created excessive host staging/swap before
denoising. That attempt was stopped and is not a generation result.
[Core implementation at the tested revision](https://github.com/Comfy-Org/ComfyUI/blob/8f04fd6ecf4a548937971e840af2a985529fab76/comfy/model_patcher.py)
explains the fresh loader call. The maintained
[direct loaders](comfyui-device-loaders/__init__.py) pass the target device to
ComfyUI's own `load_clip` and `VAE` APIs instead. Upstream source and model
weights remain unchanged. Native model management still handles offloading.

## Source trail and limits

- [Official AMD installation](https://github.com/Comfy-Org/ComfyUI#amd-gpus-linux)
  supplies the ROCm nightly path. The selected commits and wheels are recorded
  locally; a development version alone is not evidence of faster generation.
- [Qwen's base-model example](https://huggingface.co/Qwen/Qwen-Image-2.1)
  uses 40 steps. [Official Comfy template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_2_1_t2i.json)
  provides the native encoder/latent pipeline and CFG 1 path.
- [Official H3 guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
  and [template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_t2v.json)
  distinguish base 20-step sampling from Turbo schedules requiring an adapter.
- [gfx1100 issue and follow-ups](https://github.com/Comfy-Org/ComfyUI/issues/15314)
  report version/memory-dependent corruption and allocator problems. Validate
  actual decoded output; successful model loading is insufficient.
- [lcz.me 1168](https://lcz.me/topic/1168), Ang Lee, reports single-XTX/64 GiB
  INT8/Turbo H3 results. Those timings do not predict this base-model workload.
- [Level1Techs 252735](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735),
  locutusofborg780, July 16/August 18, 2026, reports RDNA4/32 GB runtime and
  memory sensitivity. It supports isolated testing, not copying RDNA4 version
  pins or timings onto gfx1100. See [forum sources](../hardware/FORUM-OPTIMIZATION-SOURCES.md).

Shared weights can be reused by a separate Windows ComfyUI installation with
Windows paths. The Linux environment and validation do not establish Windows
runtime compatibility. Larger image sizes, longer videos, image-to-video,
editing, Turbo and maximum capacity require separate validation.
