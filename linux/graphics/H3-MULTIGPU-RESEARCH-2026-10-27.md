# MiniMax H3 multi-GPU methods — October 27, 2026

Research for the dual RX 7900 XTX / gfx1100 workstation. This review changes no
ComfyUI environment, workflow, model, attention backend, driver or GPU topology.
Sources were checked October 27, including the user-supplied topics below.
The later browser review exposed dates for those posts; earlier sources retain
their original date limitations. Firsthand reports, implementation evidence and
local validation are distinguished.

## Subsequent local trial

The user subsequently authorized an isolated Kaihui/control benchmark. The
[guarded trial report](H3-SP2-2026-10-27.md) records stock ComfyUI0.42 API
incompatibility, reduced-RAM guard stops and an isolated CPU-checked compatibility
pilot. No SP2 speedup or completed generation qualification is established.
The source review below retains its original research-only scope.

## Correction: a firsthand dual-XTX SP2 report exists

[J I, topic 2594, reply 3](https://lcz.me/post/28082), October 26, reports
running one H3 generation with **SP2 in ComfyUI on two RX 7900 XTX 24 GB cards**:
480p videos of 8–10 seconds succeeded. The author recalls about 1.8× single-card
speed; this is an approximate recollection without a timing log or matched
benchmark. At 576p some attempts succeeded and some failed with tight VRAM.
The reply describes attention-head distribution and uneven per-rank work.
It does not identify the exact plugin revision, checkpoint, workflow or timing
boundaries. It establishes a firsthand XTX success report, while those missing
details prevent an exact reproduction or local speed prediction.

[terry's opening post, topic 2594](https://lcz.me/topic/2594), October 26,
summarizes Bunsei's **R9700** work and asks for XTX validation. The opening post
and J I's later reply therefore have different hardware evidence. The earlier
version of this review missed J I's report; the assessment below supersedes it.

## Two concrete implementations to distinguish

### ComfyUI sequence parallelism: Kaihui-AMD

The [AMD-focused ComfyUI implementation](https://github.com/Kaihui-AMD/ComfyUI-MiniMaxH3-MultiGPU/tree/ebf3953f6385360ef211d93e4ecf23696599eaa3)
was reviewed at `ebf3953f6385360ef211d93e4ecf23696599eaa3`, September 8.
Its `AMDMinimaxH3SequenceParallelLoader` replaces the diffusion-model loader.
It splits sequence rows and permanently shards QKV weights/scales into 28
attention heads per card. A head-to-sequence exchange preserves full-sequence
attention; each rank retains the full-width output projection for INT8 ConvRot
parity. MLP/residual work is sequence-local. Rank 0 retains packing, refinement
and output heads; rank 1 keeps the 50 main transformer blocks. This is shared
DiT computation, beyond assigning an encoder or VAE to a second GPU.

The [primary README](https://github.com/Kaihui-AMD/ComfyUI-MiniMaxH3-MultiGPU/blob/ebf3953f6385360ef211d93e4ecf23696599eaa3/README.md)
validates **two R9700 32 GB cards**, ROCm 7.2.4, PyTorch 2.10 and ComfyUI 0.30,
using FL2VA INT8 ConvRot, 864×480, 124 frames and 20 steps. Denoising was about
240.6→129.0 seconds; end-to-end 262.34→149.16 seconds. Cold model loading was
excluded. These are external R9700 results, not XTX measurements. The reported
peak below roughly 26 GiB per card does not establish fit on 24 GB cards.
The loader reserves 8 GiB for activations; video/audio VAE decoding stays on the
primary card. Newer ComfyUI versions were not validated by this release.

[Peer exchange](https://github.com/Kaihui-AMD/ComfyUI-MiniMaxH3-MultiGPU/blob/ebf3953f6385360ef211d93e4ecf23696599eaa3/minimax_h3_amd_sp/peer_ops.py)
uses PyTorch distributed sends/receives; the
[runtime](https://github.com/Kaihui-AMD/ComfyUI-MiniMaxH3-MultiGPU/blob/ebf3953f6385360ef211d93e4ecf23696599eaa3/minimax_h3_amd_sp/runtime.py)
selects the NCCL backend on HIP, i.e. RCCL, plus Gloo control traffic.
It is a different transport path from Radiance's native peer transfers.
This host's raw peer-read restriction alone does not prove RCCL SP impossible;
the actual workload and transport would need validation. J I's reply does not
name this plugin, so it is a concrete candidate, not an established attribution.

### Radiance native tensor parallelism: Bunsei

[Bunsei, topic 2582](https://lcz.me/topic/2582), October 25, provides a
[Radiance fullref fork](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869),
reviewed branch `h3-fullref`, commit
`a0653376c3f816cbd06f715fa56040c0407fc869`.
Comfy components prepare conditioning; native Radiance executes the DiT and
decoding. This is not simply a standard ComfyUI loader setting.
[The author's explanation](https://lcz.me/post/27809) describes sharded DiT
matrix weights, QKV/FFN intermediates and modulation tables, while hidden
states and some other tensors remain replicated. Its estimated equivalent
VRAM figures are workload models, not a unified 48/64 GB allocation.

The fork targets **gfx1201/RDNA4 and two R9700s**, with libr4d kernels,
HIP 7.14.60850 and PyTorch 2.12.0+rocm7.14.0. Its documented recipe includes
`--gpu-headroom-mib 2048 --host-pool-mib 12288 --p2p on`, RAM vision-tower
placement and layer offload. The host pool is **12 GiB per rank**, before
conditioning/runtime overhead; it exceeds this host's current 14.83 GiB RAM
when both ranks are counted. Native peer transfers and RDNA3 kernel support
must also be established. The converted
[Ref2VA FP8 Radiance model](https://huggingface.co/Bunsei/MiniMax-H3-Ref2VA-FP8-Radiance)
is a custom RAD file (26.86 GB), distinct from the retained FL2VA INT8 Comfy model.

The [primary comparison](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869/docs/H3_COMPARISON_20261025.md)
uses matching 832×480 inputs, 20 Euler steps, CFG 1 and no LoRA. On R9700s,
full-reference Radiance TP2 sampling took 479.800 seconds versus 937.809 for
single-card Comfy; the tested dual-card Comfy path ran out of memory before
completing its first step. Image-only sampling was 66.5 / 144.067 / 80.865
seconds for Radiance TP2 / Comfy single / Comfy dual, respectively. These are
sampling times, excluding preprocessing and separate decode times, not complete
request latency. The Comfy dual test used the Kaihui plugin commit above with
five local file changes, so it does not qualify the stock release for fullref.
The [benchmark helper](https://codeberg.org/Bunsei/radiance-h3-fullref/src/commit/a0653376c3f816cbd06f715fa56040c0407fc869/scripts/h3_comfy_benchmark.py)
identifies its loader explicitly. No local result is implied by these comparisons.

## What is already validated locally

The [October 18 local generation record](VALIDATION-2026-10-18.md) already proves
two-card component placement: GPU0 denoised H3, while GPU1 handled its encoder
and VAEs. The native INT8 ConvRot FL2VA base produced a coherent 608×352,
39-frame video with finite stereo audio in 232.4 seconds for the whole prompt;
denoising alone was about 29 seconds. This was one cold generation on 32 GB RAM,
not simultaneous two-card DiT computation. Staging added 8.39 GiB swap use.
Those historical results do not qualify H3 on the current 14.83 GiB host.

## Methods found in firsthand sources

| Method | What each GPU does | Evidence and limits |
|---|---|---|
| ComfyUI SP2 | Sequence rows / attention heads distributed between cards | J I reports successful dual-XTX H3 at 480p; exact implementation and measured speed remain unspecified. Kaihui supplies a separate, inspectable AMD SP implementation validated on R9700. |
| Radiance native TP2 | Main DiT weights and selected intermediates sharded between ranks | Bunsei supplies code and R9700 comparisons; gfx1100 port, transport and host-RAM fit remain unvalidated here. |
| Component placement | DiT/sampling on one card; encoder and VAEs on the other | Already locally validated above. It frees room for the denoiser and avoids some component reloads; it does not divide every DiT operation between cards. |
| DisTorch2 weight distribution | One compute GPU; the other holds donor weights copied to the compute GPU as needed | Leon Y's [dual 3090 H3 report, topic 1075](https://lcz.me/topic/1075): about 10 GB compute-card weights, 19 GB donor weights and 2.7 GB CPU fallback; 15 s 624×1104 video/audio. The reported NVLink transport and elapsed time belong to 3090 hardware. |
| Dual-Sage attention | Heads split between root/helper GPUs, with other components assigned separately | Chi Kui Chan's [dual R9700 report, topic 1469](https://lcz.me/topic/1469): 56 heads split 28+28, ROCm 7.2.4, PyTorch 2.9.1; 1.5675× synthetic attention result. 10 s 1312×736 refinement finished in 10:48; 15 s failed in QKV/LoRA allocation. This is RDNA4/32 GB-per-card evidence, not XTX speed or capacity evidence. |
| Distributed sampling plus separate decoding | FSDP/Ulysses sampling ranks; a separate GPU decodes transferred latents | abaalei's [topic 2138](https://lcz.me/topic/2138) and [author's reproduction report](https://github.com/peterhon168/h3-multigpu-pipeline/blob/main/FORUM_REPRODUCTION.md) use 4/8 Tesla T10 workers, a 3080 Ti decoder and an optional independent XTX sampler. It is not a demonstrated two-XTX sampling pool. |
| Independent instances | Each card runs its own workflow | Chan-Ivan's [dualXTX report, topic 189](https://lcz.me/topic/189) uses separate 8188/8189 instances for FLUX/LTX. This improves concurrency rather than combining the cards for one H3 generation. |

## DisTorch2 details worth retaining

The implementation source of the method is the now-archived
[ComfyUI-MultiGPU repository](https://github.com/pollockjj/ComfyUI-MultiGPU),
reviewed at `37a73feda5804045e4f39d8c640905d62a2169d1` (September 20).
Its [loader documentation](https://github.com/pollockjj/ComfyUI-MultiGPU/blob/37a73feda5804045e4f39d8c640905d62a2169d1/web/docs/UNETLoaderDisTorch2MultiGPU.md)
exposes `compute_device`, `donor_device` and `expert_mode_allocations` on
`UNETLoaderDisTorch2MultiGPU`. Explicit byte allocations control how much model
storage goes to each device; CPU is a possible fallback. The author's 3090 post
reports preferring byte allocations because expanded-size estimation miscounted
the compressed H3 weights, and reserving 4–5 GB on the donor card for loading.
Those are source-system observations, not approved XTX allocations.

The same post needed `--disable-dynamic-vram` and compatibility guards for removed
CLIP loaders on its ComfyUI 0.30 installation. The reviewed repository now
documents DynamicVRAM integration, so that launch flag is version-dependent,
not a blanket instruction for the installed 0.42.0 environment. Its loader's
`eject_models` defaults to true; any isolated test here must avoid evicting
unrelated work.

ROCm also exposes AMD devices as `cuda:0`/`cuda:1` through PyTorch. The reviewed
[device enumeration code](https://github.com/pollockjj/ComfyUI-MultiGPU/blob/37a73feda5804045e4f39d8c640905d62a2169d1/device_utils.py)
explicitly includes AMD/ROCm. However,
[its P2P helper](https://github.com/pollockjj/ComfyUI-MultiGPU/blob/37a73feda5804045e4f39d8c640905d62a2169d1/p2p_registry.py)
loads `libcudart.so` directly. That helper needs ROCm compatibility review
before any path that invokes it; it is not proof that every loader fails.
This workstation's [existing peer-read constraints](../hardware/PCIE-P2P-2026-10-17.md)
also mean the 3090/NVLink transfer result cannot be assumed here.

## Dual-Sage and attention portability

The R9700 post links no downloadable Dual-Sage implementation or workflow in the
retrieved text. [SageAttention PR 381](https://github.com/thu-ml/SageAttention/pull/381)
is open; reviewed head `6aa2622f0fdad0b3cbccbfc30d6f5954f8c29020` adds HIP import/
dispatch support and `num_stages=1` for the Triton path. Its posted tests are on
gfx1151. The PR itself does not implement or validate the forum's dual-card
head split on gfx1100. [AMD's July20 attention guide](https://rocm.blogs.amd.com/software-tools-optimization/comfyui-fa-backends/README.html)
documents backend selection and experimental Sage support, not a universal H3
speedup. Any attention change needs same-seed image/video and audio checks as
well as measured end-to-end latency.

## Applicability to this workstation

The supplied links establish a firsthand two-XTX ComfyUI SP2 success report
and two inspectable implementations beyond component placement. The existing
local component-placement run remains the local control. For an authorized
future experiment, Kaihui's Comfy SP loader is the closer implementation to the
retained FL2VA INT8 model; compatibility with installed ComfyUI 0.42, 24 GB
per-card capacity and host staging still require isolated validation. Bunsei's
Radiance route needs a gfx1100 port, a different converted checkpoint, working
native peer transfers and a revised memory plan before a local trial.

Compare matching model/quant, seed, frames, resolution, sampler, steps and
adapters; record loading, denoising, decoding, end-to-end time, output quality,
per-card memory and host staging. Retain the existing loading guards and RAM
limits. The source review itself did not authorize GPU tests; the subsequent
user-authorized attempt is linked above.

The standing Level1Techs and Digital Spaceport references were also searched.
No additional directly reproducible dual-XTX H3 implementation was found on
those two sites in this review. No plugin, adapter, model or runtime was installed.
