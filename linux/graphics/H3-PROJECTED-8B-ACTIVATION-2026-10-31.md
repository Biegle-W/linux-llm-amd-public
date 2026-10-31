# H3 projected 8B encoder activated — October 31, 2026

Normal H3 **text-to-video** now uses stock Qwen3-VL 8B FP8 with its matching ClipProj v3.1 ridge projection. The owner requested activation after the [completed encoder comparison](H3-PROJECTED-8B-COMPARISON-2026-10-31.md). This changes text conditioning architecture; the earlier comparison's quality and attribution limits remain.

## Using it and restoring 32B

Open **MiniMax H3 INT8** in ComfyUI or Comfy Desktop. The maintained GUI/API defaults use `GraphicsH3ProjectedCLIPLoader` on GPU 1. **MiniMax H3 Native32B** retains the exact previous NVFP4 workflow for image-conditioned work or rollback, with both original graph hashes verified by CPU contracts. API equivalents are `minimax-h3-base-api.json` and `minimax-h3-native32b-api.json`. Image/ref inputs fail with a Native32B instruction, including after CLIP cloning.

The INT8 DiT stays on GPU 0; encoder and both VAEs stay on GPU 1. Attention remains PyTorch SDPA. Reserve, allocator, offload, DynamicVRAM and cache settings are unchanged. This is component placement across both cards, not the isolated fcys TP2 benchmark. No encoder, VAE or DiT weights were moved, duplicated or removed. The model-path configuration registers the existing `experimental/h3-8b-comparison-20261031` directory; its name is a storage provenance label.

The launcher installer now copies the complete maintained extension, pinned vendor implementation, licence and provenance into either launcher's existing runtime. The three vendor implementation modules are byte-identical to [ClipProj c01ba8fb8f41](https://github.com/nicolab28/ComfyUI-ClipProj/tree/c01ba8fb8f41b4f2094dbd0b185cdc238fb6134c). The thin initializer installs no vendor UI mappings or global resident/unload hooks. Loading constructs the selected 8B encoder on GPU 1 and checks architecture/projection dimensions/tap before model allocation.

## Normal-runtime qualification

One successful request used the actual `graphics/start-comfyui` launcher, normal ComfyUI runtime, saved API graph and native INT8 denoiser. Only the output filename prefix changed. Temporary observation hooks checked every output tensor from conditioning, sampler (including both video/audio latent components), video VAE and audio VAE; they returned the original results and were removed after shutdown. No conditioning fixture or benchmark TP2 server was substituted.

- 608×352, 39 frames, 24 fps, seed 42, 20 `res_multistep` steps and the saved teapot prompt; API success in **215.58 s**. This is a fresh-server normal-path functional result, not a matched speed comparison.
- All observed conditioning, sampled latent, decoded image and audio tensors are finite. Full H.264/AAC decoding passes: 39 video frames and stereo 32 kHz audio. Six sampled frames show a stable red teapot, sunlit wooden table, plant background and changing steam above its spout, without obvious gross corruption. This brief review is separate from signal validity; no general perceptual-quality, audio-semantics or speech claim follows.
- 219 lifecycle samples, zero telemetry errors, zero explicit guard faults and zero dedicated spill. Minimum sampled host availability **4.07 GiB**; whole-card free VRAM **2.73/7.50 GiB**. Worker swap occupancy peaked at 6.51 GiB; occupancy is distinct from swap I/O.
- This short smoke has zero complete 30-second inference windows; its zero-fault result does not independently validate sustained swap-rate ceilings. The prior longer comparison supplies separate evidence.
- Existing `loading-swap-v4`: loading/parked swap allowed; 128 MiB/s inference writes and 160 MiB/s combined I/O over complete 30-second windows. 1 GiB host floor; 2 GiB free-VRAM soft floor for four samples, 1.5 GiB hard floor, physical-MemTotal scope cap, zero spill. Scope OOM/kill events remain zero.
- Thermal telemetry: 221 samples with 0 errors. Junction peaks were 73/60 °C (GPU0/GPU1). Raw SMU limit flags are retained numerically; they are status observations rather than a causal thermal-throttling diagnosis. No clock/fan settings changed.
- Owned server/workers exited, KFD drained, task reservation released, temporary observer removed. Unrelated source/runtime fingerprints were preserved. Seven CPU contracts pass per maintained checkout.

Two preparatory harness issues (a private path preflight and observer classmethod/schema compatibility) were corrected before any generation. After API success and tensor checks, the cleanup endpoint returned an empty body; the harness incorrectly tried to decode JSON. Saved success, finite-tensor, lifecycle and ownership evidence was independently verified without rerunning generation. Original failed evidence is retained privately. The completed 14-run comparison was not repeated. The preceding scheduled updater completed naturally; it was not stopped, restarted or retested.

## Assets and limits

The [stock 8B FP8 encoder](https://huggingface.co/Comfy-Org/Qwen3-VL/tree/02f0d3eefb59528799653d16735818801177ef1f/text_encoders) is 10,588,637,512 bytes; the [matching v3.1 ridge projection](https://huggingface.co/NicoLab28/ClipProj-MiniMax-H3/tree/2ebdbcdc27a29a9607efdb221a9afcb9a0cdd808) is 41,990,896 bytes. Exact asset and preserved graph hashes are recorded in the numeric evidence and provenance. The original 32B NVFP4 weights and separate 32B W4A8 benchmark assets remain.

Qualification is a short text-only request on the current 32 GB host. It does not qualify image/reference conditioning with 8B, long prompts, speech, maximum duration/resolution, 96 GB/P2P or native TP2. The native Desktop workflow is installed but no new graphical-interaction test is claimed. Existing engines, packages, kernel, guards, RAM holds, services and schedules remain.

[Curated settings, tensor/media checks and measured lifecycle evidence](../hardware/results/h3-projected-8b-activation-2026-10-31.json).
