# Projected 8B versus native 32B H3 encoder — October 31, 2026

Subsequent owner-authorized [normal T2V activation](H3-PROJECTED-8B-ACTIVATION-2026-10-31.md) is complete. The comparison below remains dated isolated evidence; its 32B W4A8 baseline is distinct from the retained normal Native32B NVFP4 workflow.

The projected 8B path reduces encoder loading and encoder memory, while complete generation time remains close and variable. The tested text-to-video scenes remain coherent, with composition and detail changes.

Treat stock 8B + ClipProj as a viable isolated candidate for this bounded text-only workload. Before scheduled preparation, encoder load falls by 35.1% and the complete-request median by only 4.0%. Across all six pairs, complete-generation medians are effectively equal, and two late 8B runs overlap scheduled CPU preparation. Encoder VRAM/RSS savings are substantial; whole-pipeline owned RAM is almost unchanged because the denoiser/VAE still dominates. These results support a memory/loading option within the tested workload; broader quality and production performance remain unqualified.

## Matched workload and timing

Six fresh-process requests per encoder: three structured text-only prompts (teapot, toy bus and bee/flower), seeds 42 and 43, 608×352, 124 frames at 24 fps (5.167 seconds), 20 res_multistep/simple steps and batch 1. Two smaller 39-frame end-to-end canaries are excluded. Order is counterbalanced AB/BA across the six pairs.

Both arms use the same retained INT8 ConvRot diffusion model, CK attention, actual fcys RCCL TP2, BF16 compute/wire, no-P2P transport and rank-0-only AV decode. Encoder processes exit before the TP2 stage; rank0 GPU placement precedes rank1 loading. Actual saved graphs verify matched seeds/settings, and both ranks verify each trial’s conditioning fixture hash. Production selection, installed packages, model files, guards and schedules were preserved.

Encoder files receive file-specific `POSIX_FADV_DONTNEED` advisories, with physical read counters retained; there is no global cache flush. Load time includes the encoder and projection, synchronized with the GPU. First-encode timing includes token conditioning and the projection. Complete time runs from the encoder controller start through finished AV history, including process startup, serialization/shutdown and stage transition. Shared diffusion/VAE and kernel caches are not globally controlled. These are complete first-generation measurements under the recorded host conditions, not warm-service throughput or a pure kernel-speed claim.

| Timing, median seconds (range), n=6 per arm | Native 32B W4A8 / HIP INT8 | Stock 8B FP8 + ClipProj |
|---|---:|---:|
| Encoder + projection load | 45.884 (42.589–52.294) | 31.983 (29.156–48.159) |
| First encode | 2.700 (2.400–3.633) | 2.109 (1.456–7.703) |
| Sampling after both ranks are ready | 101.666 (98.299–115.910) | 100.971 (98.207–126.125) |
| Generation stage after conditioning, including common loading/decode | 202.631 (192.488–222.824) | 210.612 (191.036–237.669) |
| Complete staged generation | 273.296 (262.042–307.628) | 272.336 (239.853–315.878) |

### Timing before scheduled preparation

The existing 03:00 updater began isolated CPU preparation during the late bee runs. Its service/schedule was preserved; GPU testing/activation is gated by GPU-LOCK, and no updater GPU activation occurred during this comparison. The first four matched pairs (both teapot and bus seeds) finished before preparation started. All six pairs remain in the table and numeric record above; the subset below separates the earlier timing conditions from that known background change.

| Pre-update timing, median seconds (range), n=4 per arm | Native 32B | Projected 8B |
|---|---:|---:|
| Encoder load | 49.092 (45.165–52.294) | 31.855 (29.156–34.076) |
| First encode | 2.700 (2.615–3.209) | 1.996 (1.456–7.703) |
| Complete staged generation | 270.471 (262.042–298.628) | 259.608 (239.853–275.012) |

Before scheduled preparation, the 8B median load is 35.1% lower; complete-generation median is 4.0% lower. It is faster in 3/4 of those pairs; the bus/seed42 pair is slower. No extra GPU trials were run to replace the scheduled-overlap observations.

Across all six pairs, the 8B median encoder load is **30.3% lower**. Its complete-generation median is **0.4% lower**; 8B is faster in **4/6 pairs**. Individual paired 8B time changes range from **-10.2% to +15.8%** (negative is less time). Variation in the common stages can outweigh the encoder saving. Sampling’s joint-ready span removes the earlier rank’s wait for its peer; per-rank times are not added.

## Memory and safeguards

| Observed maximum, GiB, n=6 per arm | Native 32B | Projected 8B |
|---|---:|---:|
| Encoder process RSS high-water | 16.475 | 11.338 |
| Encoder Torch reserved VRAM | 17.568 | 10.195 |
| Whole-pipeline owned scope RAM, including cache | 24.372 | 24.337 |
| Whole-pipeline owned swap occupancy | 3.934 | 4.511 |

Encoder RSS and Torch VRAM fall with the smaller path; the common denoiser/VAE still determines much of the whole-pipeline peak. Scope RAM includes charged file cache and is not process RSS. Scope/host/card counters are sampled each second; allocator and process high-water counters capture their own peaks. No transient-extrema guarantee is implied. Swap occupancy is distinct from swap I/O and does not establish a storage-wear effect.

The same qualified isolated H3 floors remain: 1 GiB host/swap-monitor availability, 2 GiB whole-card free-VRAM soft floor for four samples, 1.5 GiB hard floor, zero dedicated spill, physical-MemTotal scope cap and unlimited swap occupancy. Current `loading-swap-v4` permits loading/parked swap and enforces 128 MiB/s inference writes / 160 MiB/s combined swap I/O over complete 30-second windows. OS oomd is unchanged. All 14 runs have zero explicit guard faults, zero sampling errors, zero dedicated spill and verified owned shutdown; cgroup OOM/kill events are zero.

## Sampled quality

Observations below were recorded from anonymous A/B sheets before reading the arm labels: six evenly spaced frames per clip. This is a small low-resolution text-to-video sample, not a perceptual non-inferiority study or a BF16 accuracy comparison.

| Scene / seed | Native 32B | Projected 8B |
|---|---|---|
| teapot / 42 | Main scene and stable composition pass; steam-origin/detail partial. | Main scene and stable composition pass; spout attachment clearer, thin-ribbon detail partial. |
| teapot / 43 | Main scene and stable composition pass; precise steam attachment partial. | Main scene and stable composition pass; spout-origin detail clear in sampled frames. |
| toy-bus / 42 | Subject, three-red-block count, direction and sampled stability pass; small-block size detail partial. | Subject, three-red-block count, relative block size, direction and sampled stability pass. |
| toy-bus / 43 | Subject, initial three-red-block count, movement direction and sampled stability pass; small-block detail partial. | Subject, initial three-red-block count, small-block size, movement direction and sampled stability pass. |
| bee-flower / 42 | Main scene, sampled fine detail and wing/body movement pass; exact continuous leg contact unqualified. | Main scene, sampled fine detail and wing/body movement pass; exact continuous leg contact unqualified. |
| bee-flower / 43 | Main scene, sampled fine detail and wing/body movement pass; exact continuous leg contact unqualified. | Main scene, sampled fine detail and wing/body movement pass; exact continuous leg contact unqualified. |

All six outputs per arm retain the requested main scenes in the sampled frames. Projected 8B shows clearer spout attachment in the two teapot seeds and smaller red blocks matching the relative-size instruction in the bus seeds. Both bus paths retain three initial red blocks and rightward motion, with later occlusion. Bee pairs retain macro detail and evolving wing/body pose without a clear overall sampled winner. Framing, pot/bus design and background details change; exact continuous leg contact and transient defects between sampled frames remain unqualified.

All 12 timed clips fully decode as 124-frame 608×352 H.264 video at 24 fps with stereo 32 kHz AAC. Conditioning, sampled rank1 latents and decoded PCM are finite. Signal checks do not qualify perceptual audio semantics; no speech, multilingual pronunciation, image/reference conditioning, long-prompt or maximum-capacity claim follows. Full paired clips remain available with the local comparison deliverable.

## Assets, execution and preserved state

The native arm retains the [32B W4A8 checkpoint](https://huggingface.co/AX1Y2JP/MiniMax-H3-W4A8-ConvRot/tree/61a33b9224f9aa119e2332cb24a884051c9cf810) and the per-call integer option from the [earlier matched encoder-format comparison](H3-AMD-ENCODER-FORMATS-2026-10-28.md). An excluded canary verifies 350 `comfy_kitchen.backends.hip.w4a8_int8_linear` calls. Diagnostic dispatch hooks are absent from measured calls.

The new arm loads [stock Qwen3-VL 8B FP8](https://huggingface.co/Comfy-Org/Qwen3-VL/tree/02f0d3eefb59528799653d16735818801177ef1f/text_encoders) and the [v3.1 8B ridge projection](https://huggingface.co/NicoLab28/ClipProj-MiniMax-H3/tree/2ebdbcdc27a29a9607efdb221a9afcb9a0cdd808). The [original ClipProj implementation](https://github.com/nicolab28/ComfyUI-ClipProj/tree/c01ba8fb8f41b4f2094dbd0b185cdc238fb6134c) supplies raw H3 tokenization, tap24, 4096→5120 projection and the attention-sink vector; its model math is unmodified. FP32 output and exact 8B/projection hashes/shapes are checked. The 8B file is 10,588,637,512 bytes and projection 41,990,896 bytes, **10.631 decimal GB combined**, versus **16.476 GB** for the retained 32B file. New weights remain experimental, with original files intact. This replaces the text-conditioning architecture; shared vision-tower dimensions are not a quality-equivalence argument.

The retained Comfy 0.42.0 snapshot has 1,025 unchanged Python files versus the prior matched test; only the isolated encoder node differs. The complete comparison harness is frozen across trials. No production launcher, package, kernel, clock, profile, hold or schedule was changed. No comparison job or owned GPU reservation remains; unrelated work is preserved. There is no automatic retry or promotion.

The comparison is complete; no benchmark work or automatic retry remains. Keep the candidate isolated and retain the existing production selection. Broader reference-image, speech/audio semantics, long-prompt or production integration would be a separate qualification scope.

[Curated protocol, individual measurements, source hashes and quality observations](../hardware/results/h3-projected-8b-comparison-2026-10-31.json).
