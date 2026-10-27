# MiniMax H3 multi-GPU methods — October 27, 2026

Research for the dual RX 7900 XTX / gfx1100 workstation. This review changes no
ComfyUI environment, workflow, model, attention backend, driver or GPU topology.
Sources were checked October 27; forum publication dates were not exposed in
the retrieved page text. Firsthand posts are distinguished from suggestions
and automated replies.

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

The reviewed material establishes usable methods beyond single-card component
loading, but this search did not locate a reproducible firsthand two-XTX H3
DiT/attention split with pinned code and workflow. A specific user-supplied
post could change that assessment. Automated forum replies claiming that the
second GPU can never help are not treated as implementation evidence.

For a future authorized experiment, component placement is the existing local
control. DisTorch2 is a capacity candidate; Dual-Sage is a compute candidate
once its implementation is available. Compare matching model/quant, seed,
frames, resolution, sampler, steps and adapters; record loading, denoising,
decoding, end-to-end time, output quality, per-card memory and host staging.
Keep the current loading guards and RAM limits; the published large-RAM setups
do not justify a new H3 run on this reduced-RAM host.

The standing Level1Techs and Digital Spaceport references were also searched.
No directly reproducible dual-XTX H3 implementation was found there in this
review. No plugin, adapter, model or runtime was installed.
