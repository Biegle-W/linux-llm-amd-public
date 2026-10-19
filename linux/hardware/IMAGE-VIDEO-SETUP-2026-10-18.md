# Image and video generation on two RX 7900 XTX cards

Current model selection: **one Qwen-Image 2.1 BF16 base and one MiniMax H3
fl2va pruned INT8 base**, with one encoder and the required VAEs per family.
See the [retained collection](../graphics/README.md) and
[current inventory](UNSLOTH-MODEL-INVENTORY-2026-10-18.md). The former Unsloth
Q4/Q2/alternate-encoder cache copies are retired. Do not redownload them.

**Model-file preparation and runtime setup are separate.** ComfyUI remains
uninstalled and no new generation or speed benchmark is claimed. The earlier
[Unsloth H3 Q2 corrupt-output report](UNSLOTH-H3-CORRUPT-OUTPUT-2026-10-18.md)
is historical, not a result for the new native INT8 pipeline.

Target hardware: i5-13600KF, two 24 GB gfx1100 GPUs at CPU PCIe4 x8/x8,
32 GB RAM, no native ROCm peer access. Use an isolated ROCm PyTorch environment;
keep existing LLM engines independent. DSH remains the chat harness.

## 1. Use the retained files first

Use native Qwen/H3 templates, then change their loader dropdowns to the actual
retained filenames. Do not accept automatic downloads merely because a template
names a different VAE or quant. The selected files are native safetensors layouts;
this collection does not require a GGUF plugin. The lossless Qwen transformer
keeps its supported unfused MLP layout. Select `qwen_image` for Qwen's CLIPLoader
and `minimax` for H3's. Preserve base-model schedules; no Turbo LoRA is installed.

Daily workflow:

1. Load the Qwen-Image text-to-image template, select the BF16 transformer,
   BF16 encoder and FP32 VAE, and start with batch 1 and a fixed seed. Validate
   a small image before 1024x1024. Use the base schedule, not an 8-step Turbo
   or Viggle schedule.
2. Save the chosen PNG and workflow JSON. For edits, open the matching Qwen
   editing template, provide the PNG, and describe the requested change.
3. Release the image pipeline and open H3's native image-to-video template.
   Select the retained INT8 model, native compact encoder and both H3 VAEs.
   Feed the PNG into the first-frame input; describe motion, camera and sound.
4. Validate a small, short shape accepted by the template before a 124-frame,
   864x480 draft at 24 fps. Native base H3 defaults to 20 steps. Do not use a
   Turbo schedule without its corresponding adapter. Keep default supported
   attention first; Comfy Kitchen attention does not support INT8 ConvRot H3.
5. Decode video/audio separately through their matching VAEs, connect both to
   Create Video / Save Video, and save MP4 plus workflow JSON. Increase duration
   or resolution one at a time only after visually correct drafts.

These are starting candidates, not locally validated speed/fit claims. Use both
GPUs through explicit component placement below; detecting two cards alone does
not prove the workflow used both.

## 2. Prepare disk and host memory

Keep the runtime and virtual environment on a Linux filesystem. Store model
weights in `SHARED/Graphics-Models` on Shared SATA, with `diffusion_models`,
`text_encoders` and `vae` subdirectories. Add adapter directories only when
needed. Use ComfyUI's `extra_model_paths.yaml` so
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
shared_graphics:
  base_path: /mnt/shared/Graphics-Models
  is_default: true
  diffusion_models: diffusion_models
  text_encoders: text_encoders
  vae: vae
```

This uses the [official path configuration](https://github.com/Comfy-Org/ComfyUI/blob/master/extra_model_paths.yaml.example).
Use the templates' official model links. A missing loader filename is distinct
from a missing custom node; native Qwen/H3 templates should be tested before
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

## 6. Validate retained H3 before speed experiments

MiniMax H3: follow the [official native template](https://docs.comfy.org/tutorials/video/minimax/minimax-h3).
Use the retained pruned INT8 ConvRot, native compact text encoder, FP16 video
VAE and FP32 audio VAE. Load one variant only. Use 864x480/124 frames and the template schedule;
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
