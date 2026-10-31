# AMD H3 text-encoder formats compared — October 28, 2026

Follow-up: the [distinct 8B projected-encoder comparison](H3-PROJECTED-8B-COMPARISON-2026-10-31.md) measures fresh complete requests and sampled quality against this native 32B W4A8 path. It changes the conditioning architecture; the same-architecture format results below remain dated evidence.

W4A8 with verified native HIP INT8 matrix multiplication is a viable AMD candidate for the 7900 XTX on the tested workload. It substantially reduces encoding time, with similar owned RAM and slightly lower peak Torch-reserved VRAM than corrected NVFP4. The paired clips retain the requested main scenes, while composition changes and shared negative-instruction failures remain. The gain applies to encoding; loading remains large and variable.

The comparison keeps H3's 50-layer Qwen3-VL-32B architecture, tokenizer, raw prompts, FP32 hidden-state output, GPU initialization and staged encoder/TP2 execution. The tested alternative is W4A8 safetensors, using the installed HIP implementation on the 7900 XTX. Its default floating-point multiplication and an isolated native-integer option are measured separately. Production selection remains unchanged.

## Format and execution paths

The retained [official NVFP4 checkpoint](https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/text_encoders) is the corrected baseline: Triton stays disabled during encoder preprocessing and eager dequantization supplies floating-point weights. The old all-NaN path is excluded from this comparison; its [diagnosis and repair](H3-FCYS-QUALITY-FIX-2026-10-28.md) remain recorded.

The [W4A8 candidate](https://huggingface.co/AX1Y2JP/MiniMax-H3-W4A8-ConvRot/tree/61a33b9224f9aa119e2332cb24a884051c9cf810) is pinned to revision `61a33b9224f9aa119e2332cb24a884051c9cf810`, file `text_encoders/qwen3vl_32b_minimax_h3_w4a8_mixed.safetensors`, SHA256 `cf0fb6a8bb278418008ffa13ff2702b42c728fd7a4e74d1dc6a83d7cf3200682`. Its header identifies 50 layers and unnormalized output after layer 50; projection and embedding shapes match the H3 encoder. It is a separate published quantization, with no re-quantization of the retained NVFP4 weights. Original weights remain intact and the new file stays in an experimental directory.

ComfyUI's text-encoder loader normally forces floating-point matrix multiplication. In that mode, W4A8 reached the installed HIP dequantizer 350 times per prompt. The experimental integer option uses the existing quantized-matmul context and temporarily opts eligible quantized linear layers out of forced casting, restoring their flags after each call. It reached `comfy_kitchen.backends.hip.w4a8_int8_linear` **350 times per prompt**. FP32 intermediate outputs and normalization remain. No installed kernel, runtime package or production loader was edited. The benchmark includes the integer option's per-call setup/restoration cost.

Both encoder formats keep the Triton backend disabled. The actual fcys RCCL TP2 denoiser retains CK attention, its pinned INT8 loader, BF16 compute/wire, no-P2P transport and rank-0-only AV decode. The four external TP source files and same-instance import bridge remain unchanged. Stack: ComfyUI 0.42.0 (`8f04fd6ecf4a548937971e840af2a985529fab76`), Torch `2.15.0.dev20260827+rocm7.2`, HIP 7.2.53211 and comfy-kitchen 0.2.39.

The official BF16 and INT8 encoder files are 51,506,295,256 and 27,141,342,152 bytes respectively. Both require offload or a different placement plan with the current guarded one-card encoder stage. They were screened by published sizes rather than loaded beyond the card's admission budget. The W4A8 candidate fits the existing stage.

## Speed: loading and encoding measured separately

One excluded full-process warmup precedes **three measured fresh-process trials per arm**. Every process sees the same physical card 0 and uses one excluded encode warmup plus three measured encodes for each of three prompts. Each table value is the median of three per-process medians; individual samples are retained in the [numeric record](../hardware/results/h3-amd-encoder-formats-2026-10-28.json). Tokenization is measured separately, and fixture serialization/hashing occurs outside encode timing. GPU synchronization brackets load and encode calls. Timed calls have no diagnostic dispatch wrapper or per-module hooks.

Before each measured load, a read-only file-specific `POSIX_FADV_DONTNEED` advisory targets only that encoder's file. Actual process `read_bytes` deltas are recorded to verify physical reads. No system-wide cache flush, swap setting or unrelated process is changed. Trials use counterbalanced order; the two W4A8 modes share the same weight file and loader. Their loading-time differences measure run variability rather than a different loading algorithm.

| Format / execution | File GiB | Load median s (range) | Encode median s: teapot / toy bus / bee |
|---|---:|---:|---:|
| NVFP4 / eager dequant + FP matmul | 14.610 | 85.580 (46.260–95.598) | 1.3113 / 1.3025 / 1.3063 |
| W4A8 / HIP dequant + FP matmul | 15.344 | 77.706 (59.647–127.211) | 1.3036 / 1.2934 / 1.2967 |
| W4A8 / native HIP INT8 matmul | 15.344 | 73.434 (46.324–100.002) | 0.1617 / 0.2195 / 0.2209 |

The integer W4A8 option encodes these prompts **5.91–8.11× faster** than the corrected NVFP4 baseline. This is an encoder-stage result. Loading varies substantially, and the shared denoiser/AV stages dominate additional work; no whole-workflow speedup follows from the encode ratio. Fresh-process startup and loading are not folded into an inflated encoding-throughput claim.

## RAM and VRAM

| Format / execution | Peak owned scope RAM GiB | Peak encoder-process RSS GiB | Min host available GiB | Peak Torch allocated / reserved GiB | Min card-0 free VRAM GiB | Max owned swap GiB |
|---|---:|---:|---:|---:|---:|---:|
| NVFP4 / eager dequant + FP matmul | 25.895 | 15.222 | 10.852 | 16.057 / 17.947 | 5.080 | 2.611 |
| W4A8 / HIP dequant + FP matmul | 25.876 | 15.996 | 10.311 | 16.805 / 18.734 | 4.768 | 5.294 |
| W4A8 / native HIP INT8 matmul | 25.702 | 15.729 | 10.206 | 16.805 / 17.568 | 5.945 | 3.882 |

Native W4A8 has a larger allocated-memory peak (16.805 GiB versus 16.057 GiB for NVFP4), while its reserved peak is lower (17.568 versus 17.947 GiB). The file is also larger. Treat this as a mixed memory tradeoff rather than a general VRAM reduction.

Scope RAM includes charged file cache and owned processes. Process RSS includes mapped weight pages at its high-water mark. Available RAM and free VRAM are whole-host/card observations sampled once per second; Torch peak counters also capture allocator transients. These quantities describe different parts of memory use. The numeric record retains each trial, swap observation and lifecycle thermal sample summary. Allowed loading/parked swap and reads remain permitted; timing variability is not assigned solely to swap without a matched causal test.

## Quality through the same actual TP2 denoiser

A saved finite fixture from measured trial 1 of each arm is used for each prompt. Both TP ranks verify the same fixture hash. All nine paired runs use 608×352×39 frames, 24 fps, 20 res_multistep/simple steps, seed 42, CPU noise and batch 1. Encoder processes exit fully before TP2 starts, and rank 0 alone decodes video/audio.

The three prompts cover a red ceramic teapot and steam; a yellow toy bus moving across a blue tabletop beside three red blocks; and a bumblebee on a violet flower. Review covers frames 1/20/39 of every clip. It is a small prompt/seed sample, with short 1.625-second clips; longer prompts, long-range motion and image-conditioned encoder use remain unqualified.

| Prompt | Encoder | Sampled visual verdict | Observations |
|---|---|---|---|
| teapot | NVFP4 / eager dequant + FP matmul | Main scene pass; steam-origin detail partial | Red rounded ceramic teapot, pale wooden table, blurred green plant and warm light. Pot stays stable; steam changes. Exact spout origin is unclear in sampled frames. |
| teapot | W4A8 / HIP dequant + FP matmul | Main scene pass; steam-origin detail partial | Red teapot, wood, plant and warm light retained. Broader pot shape and background/steam placement differ from NVFP4. Stable subject across sampled frames; exact spout origin unclear. |
| teapot | W4A8 / native HIP INT8 matmul | Main scene pass; steam-origin detail partial | Closely matches W4A8 floating-point composition and stable pot outline. Changing steam is visible. No obvious added distortion in sampled frames; exact spout origin remains unclear. |
| toy-bus | NVFP4 / eager dequant + FP matmul | Subject/count/motion pass; no-logo instruction fails | Yellow toy bus moves right on dark blue tabletop past three red blocks. Stable composition. Stylized side markings/logo appear despite negative instruction. |
| toy-bus | W4A8 / HIP dequant + FP matmul | Subject/count/motion pass; no-logo instruction fails | Yellow bus, blue tabletop, three red blocks and rightward movement retained. Cyan background, wider blocks and bus design differ from NVFP4. Side markings remain. |
| toy-bus | W4A8 / native HIP INT8 matmul | Subject/count/motion pass; no-logo instruction fails | Yellow bus moves right beside three red blocks on blue tabletop. Door/window layout and side markings differ from W4A8 FP. No obvious additional failure in sampled frames; unwanted markings remain. |
| bee-flower | NVFP4 / eager dequant + FP matmul | Main scene/detail pass in sampled frames | Fuzzy striped bumblebee on violet flower with blurred green background. Wings, legs and petals remain coherent; sampled wing angles change. No visible text/logo. |
| bee-flower | W4A8 / HIP dequant + FP matmul | Main scene/detail pass in sampled frames | Bee/flower colours, fuzzy body, legs and detailed petals retained. Crop and wing pose differ from NVFP4; no obvious collapse across sampled frames. No visible text/logo. |
| bee-flower | W4A8 / native HIP INT8 matmul | Main scene/detail pass in sampled frames | Coherent fuzzy bumblebee, wings/legs and violet petals on green background. Pose/framing differ from the other paths; no obvious additional failure in sampled frames. No visible text/logo. |

All nine clips contain 39 decoded frames at 608×352, H.264 video and stereo 32 kHz AAC audio. FFmpeg reports no decode errors; audio samples and rank-1 video/audio latents are finite. Signal checks do not establish perceptual audio quality or audio prompt compliance. Embedding cosine/L2 comparisons to NVFP4 are retained as diagnostics; the quantized NVFP4 baseline is not a BF16 accuracy oracle, and embedding similarity is not a perceptual-quality score.

## Decision, safeguards and preserved state

Recommend the native-HIP W4A8 option as the tested candidate for this short, text-only staged workload. Loading W4A8 through the default ComfyUI text-encoder path keeps floating-point multiplication and delivers essentially the same encode time as NVFP4. The faster result requires the explicitly tested per-call integer option; it is not a filename-only speedup. Production selection remains unchanged.

This sample does not establish perceptual non-inferiority, BF16 accuracy, long-prompt behaviour, image-conditioned use, long-range motion or audio prompt compliance. Teapot steam does not clearly originate at the requested spout, and all bus variants contain unwanted side markings. No matched full-workflow timing series or production promotion is claimed.

The nine measured encoder trials and nine completed quality generations have no explicit host/VRAM guard faults, zero dedicated spill and verified owned-worker shutdown. One additional parallel-loading quality attempt was killed by the existing systemd-oomd parent memory-pressure policy before conditioning was used. Its cgroup OOM counters were zero and host availability remained above the explicit floor; the system journal identified the separate OS policy. That failed attempt is preserved in the numeric record. The remaining quality runs serialize rank0 GPU model placement before queueing rank1, reducing concurrent CPU checkpoint residency. No oomd preference, threshold, service or other guard was relaxed. The minimum sampled host availability across these tests was 10.206 GiB. Both private host checks remain explicitly **1 GiB**. Other guards remain: 2 GiB whole-card free-VRAM soft floor over four samples, 1.5 GiB hard floor, physical-RAM scope cap, swap maximum `max`, ownership locks and lifecycle thermals. Loading-swap-v3 continues to allow loading/parked swap and reads; rates and PSI remain advisory.

Sensor peaks and SMU flag samples remain in the numeric evidence. Flags are sampled observations, not measured time throttled or proof of a performance loss. Existing production workflows, launcher files, version pins and paused schedules are preserved. All owned GPU workers exited, KFD clients cleared and matching locks were released. New weights and tested wrappers remain isolated; this comparison does not promote a production configuration or change native Radiance qualification.
