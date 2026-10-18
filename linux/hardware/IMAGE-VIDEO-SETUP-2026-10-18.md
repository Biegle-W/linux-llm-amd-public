# Image and video generation on two RX 7900 XTX cards

Research checked October 18, 2026. **Proposed setup only: not installed or locally
benchmarked.** Current workstation: i5-13600KF, two 24 GB gfx1100 cards, CPU
PCIe4 x8/x8, 32 GB RAM with another 32 GB pending, no native ROCm peer access.
Use ComfyUI with an isolated ROCm PyTorch environment. Keep existing LLM engines
and their environments independent. DSH remains the chat harness; ComfyUI provides
the image/video workflow interface.

## 1. Choose a small initial model set

| Purpose | First candidate | Initial settings proposed for this hardware |
| --- | --- | --- |
| Images / editing | Qwen-Image 2.1 Turbo BF16 | 1024x1024, batch 1, 8 steps, CFG 1 |
| First video pipeline test | Wan2.2 TI2V 5B FP16 | Template defaults, batch 1, short low-resolution clip |
| Higher-end video/audio | MiniMax H3 pruned INT8 ConvRot | 864x480, 124 frames; stock schedule first, matched Turbo LoRA later |
| Additional video candidate | LTX-2.3 distilled FP8 | Short low-resolution template; check memory/offload before scaling |

These are candidates and starting targets, not confirmed performance or fit
claims. A file fitting VRAM does not leave room automatically for activations,
attention, text encoding and VAE decode. Quantization labels do not establish
kernel acceleration on gfx1100. Prefer a BF16 correctness baseline for the
smaller image model, then compare INT8 at fixed settings if needed.

Qwen's official [Comfy model card](https://huggingface.co/Comfy-Org/Qwen-Image-2.1)
provides base/Turbo variants and 8-step CFG-1 guidance. Download only:

- `diffusion_models/qwen_image_2.1_turbo_bf16.safetensors`
- `text_encoders/qwen3vl_8b_bf16.safetensors`
- `vae/qwen_image_2.1_vae_bf16.safetensors`

Use the native Qwen-Image-2.1 template and select these files; preserve its
scheduler/sampler. BF16 text weights can live on the second card. INT8 text
encoding is a later comparison, not a required first download.

The [official Wan2.2 tutorial](https://docs.comfy.org/tutorials/video/wan/wan2_2)
provides the starter video workflow and model links:

- `diffusion_models/wan2.2_ti2v_5B_fp16.safetensors`
- `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `vae/wan2.2_vae.safetensors`

Keep the template schedule. Begin with a short draft, such as 49 frames at
640x352 if accepted by the workflow's resolution/frame grid; adjust to the
node's constraints. This is a pipeline test, not a final-quality recommendation.
Do not use the 14B model's VAE for this 5B workflow.

## 2. Prepare disk and host memory

Keep the runtime and virtual environment on a Linux filesystem. Store model
weights in one central Shared SATA folder, for example `SHARED/ComfyUI-Models`,
with subdirectories `diffusion_models`, `text_encoders`, `vae`, `checkpoints`,
`loras` and `latent_upscale_models`. Use ComfyUI's `extra_model_paths.yaml` so
there are no duplicate weights or model shortcuts. Windows may reuse the
weights but needs its own environment and configuration.

The local inspection still found about 30.6 GiB usable RAM; the additional RAM
is not installed yet. Close a managed LLM worker before a large video run and
check live available RAM and swap activity. Swapped-out idle pages alone do not
prove current thrashing: use `vmstat 1` while loading/rendering. With only 32 GB,
avoid loading several video families together. Extra RAM helps staging/offload;
it does not add VRAM or guarantee faster GPU computation.

SATA is reasonable when weights remain in RAM/VRAM after loading. Disk-backed
DynamicVRAM/offload and active swap make storage speed part of generation time.
The upstream [startup flags](https://github.com/Comfy-Org/docs/blob/main/development/comfyui-server/startup-flags.mdx)
explicitly describe `--fast-disk` for fast NVMe. Do not enable that for SATA and
assume speed is unaffected. Any later NVMe model exception should be justified
by a measured disk-bound workflow.

## 3. Create an isolated environment

The following are manual instructions, **not commands already run**. Select an
installed Python 3.12 interpreter; the workstation's system Python is 3.14.
Set `PYTHON_BIN` and `COMFY_DIR` to your paths first.

```bash
PYTHON_BIN=/path/to/python3.12
COMFY_DIR="$HOME/Desktop/comfyui"
git clone https://github.com/Comfy-Org/ComfyUI.git "$COMFY_DIR"
cd "$COMFY_DIR"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --pre torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/nightly/rocm7.2
python -m pip freeze > rocm-constraints.txt
export PIP_CONSTRAINT="$COMFY_DIR/rocm-constraints.txt"
export UV_CONSTRAINT="$PIP_CONSTRAINT"
python -m pip install -r requirements.txt
python -m pip check
```

The Linux nightly index follows the [current upstream installation guide](https://github.com/Comfy-Org/ComfyUI#amd-gpus-linux).
Record the actual resolved versions and ComfyUI Git commit; nightlies change.
Keep constraints active when adding nodes. Use a separate candidate environment
if a new node requires different Torch/ROCm versions. No existing LLM environment
or system ROCm upgrade is part of these instructions.

Check acceleration before downloading large weights:

```bash
python - <<'PY'
import torch
print('Torch:', torch.__version__, 'HIP:', torch.version.hip)
assert torch.version.hip and torch.cuda.is_available()
assert torch.cuda.device_count() == 2
for i in range(2):
    print(i, torch.cuda.get_device_name(i))
    x = torch.randn((512, 512), device=f'cuda:{i}', dtype=torch.float16)
    print((x @ x).float().mean().item())
PY
```

The `torch.cuda` name is also used for AMD ROCm. This checks GPU calculation,
not cross-GPU workflow correctness. Install FFmpeg through the OS package manager
if the selected video workflow requires the executable; `ffmpeg` was not on
PATH during the local inspection.

## 4. Point ComfyUI to the central weights

Create `extra_model_paths.yaml` inside the ComfyUI directory, replacing the
example Shared mount with the real path:

```yaml
shared_generation:
  base_path: /mnt/shared/ComfyUI-Models
  is_default: true
  diffusion_models: diffusion_models
  text_encoders: text_encoders
  vae: vae
  checkpoints: checkpoints
  loras: loras
  latent_upscale_models: latent_upscale_models
```

This uses the [official path configuration](https://github.com/Comfy-Org/ComfyUI/blob/master/extra_model_paths.yaml.example).
Use the templates' official model links. A missing loader filename is distinct
from a missing custom node; native Qwen/Wan templates should be tested before
adding large custom-node packs.

## 5. Launch visibly and place components across both GPUs

A conservative compatibility starting command, not a measured fastest profile:

```bash
env -u PYTORCH_ALLOC_CONF -u PYTORCH_CUDA_ALLOC_CONF \
  -u HIP_VISIBLE_DEVICES -u CUDA_VISIBLE_DEVICES \
  ROCR_VISIBLE_DEVICES=0,1 \
  python main.py --cuda-device all --listen 127.0.0.1 --port 8188 \
  --reserve-vram 2 --disable-pinned-memory --disable-async-offload \
  --disable-dynamic-vram --cache-none
```

Open `http://127.0.0.1:8188`. Leave the terminal visible. The memory flags are a
conservative candidate informed by the gfx1100 H3 issue, not a universal speed
preset. Once output is correct, compare default memory management against this
candidate with identical prompts, seeds and output settings, one flag at a time.

Use the current core [multi-GPU nodes](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_multigpu.py):

1. Insert **Select Model Device** after the diffusion loader: `gpu:0`.
2. Insert **Select CLIP Device** after the text encoder loader: `gpu:1`.
3. Insert **Select VAE Device** after the VAE loader: `gpu:1`.
4. Keep their downstream connections to encoding, sampling and decode nodes.
   In nested template subgraphs, open the subgraph containing the loaders.
5. Inspect logs and per-card memory/utilization during each stage. The device
   nodes can pass through unchanged if a device is unavailable: do not assume
   placement succeeded merely because the workflow completed.

This honors the two-card policy across workflow stages. It is **not tensor
parallel denoising** and does not mean both cards compute continuously. Each
component must fit its own card or offload. The absence of native P2P on this
machine makes frequent cross-card model shuttling a poor untested default;
component placement is the proposed baseline. Actual output and memory transfer
behavior still require local validation.

The older [ComfyUI-MultiGPU repository is archived](https://github.com/pollockjj/ComfyUI-MultiGPU/issues/223)
as of September 30. Do not install it as a maintained default when core
component-placement nodes cover the initial need.

## 6. Add higher-end video after the small workflow passes

MiniMax H3: follow the [official native template](https://docs.comfy.org/tutorials/video/minimax/minimax-h3).
Start with pruned INT8 ConvRot, its template-matched text encoder, video VAE and
audio VAE. Load one variant only. Use 864x480/124 frames and the template schedule;
compare its matched 8-step Turbo LoRA after correctness. W6A8 is a smaller recent
candidate, not validated locally. Do not treat NVIDIA FP4 filenames as proof of
native AMD FP4 acceleration.

The [gfx1100 upstream issue](https://github.com/Comfy-Org/ComfyUI/issues/15314)
contains an October 15 firsthand 7900 XT/32 GB report: ComfyUI 0.40.0,
Torch 2.14.1+rocm7.2, 864x480/124 frames/8-step Turbo, 314 seconds including loading.
It reports clean output with the conservative memory flags above and warns about
`expandable_segments:True`. Earlier reports describe corruption on other stacks.
This is a close hardware reference, not our benchmark; validate the chosen
nightly rather than assume every newer build fixes it.

True H3 dual-GPU denoising is a separate experiment:
[Kaihui-AMD's sequence-parallel node](https://github.com/Kaihui-AMD/ComfyUI-MiniMaxH3-MultiGPU)
reports 149.16 s versus 262.34 s on **two 32 GB R9700s**, 864x480/124 frames/20 steps.
The recorded envelope approaches 26 GiB per card and validates ComfyUI 0.30.0
only. This is not a drop-in 24 GB XTX preset. Gate it on local RCCL transfer tests,
current-version compatibility, reduced memory settings and actual video parity;
keep any RCCL workaround isolated from the production LLM environment.

LTX-2.3: the [official templates](https://docs.comfy.org/tutorials/video/ltx/ltx-2-3)
include distilled FP8 checkpoints and separate text encoder downloads. Treat this
as an additional candidate after Wan/H3; 22B FP8 weights plus activations can
still exceed one 24 GB card. FP8 storage is not proof of fast native RDNA3 compute.

## 7. Measure before expanding

Use batch 1, one prompt/seed, a fixed resolution/frame count and unchanged
sampler/steps. Record a cold load separately from three warm runs. Include text
encoding, denoising and VAE/MP4 time, peak VRAM on each card, available host RAM,
swap I/O and visual/audio correctness. Compare total seconds per image/clip;
LLM tokens/s is not a video metric. Increase resolution or duration separately.
Do not publish forum speeds as measurements on this workstation.

## Forum evidence and limitations

- [lcz.me topic 49](https://lcz.me/topic/49/13700cpu-32g-1g-7900xtx): yongjun liu,
  i7-13700/32 GB/7900 XTX, Linux logs; terry recommends checking backend/logs.
  Several replies describe Windows bundles. Dates are not exposed in the fetched
  page; do not transplant its old ROCm 6.x package advice into this new stack.
- [lcz.me topic 1410](https://lcz.me/topic/1410): 7900 XTX/H3 workflow discussion.
  Several users report setup difficulty or recommend native templates. Its long
  Xiaote reply identifies itself as an AI assistant; the specific fix claims were
  checked against the upstream issue rather than accepted as firsthand testing.
- [Level1Techs: RX 9070 XT experience](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735):
  locutusofborg780, July 16, i5-12600K/32 GB. A newer stack stalled; an isolated
  ROCm 7.1/Torch 2.9.1 stack worked. RDNA4 and different workflows make this a
  reproducibility lesson, not a reason to downgrade the current H3 installation.
