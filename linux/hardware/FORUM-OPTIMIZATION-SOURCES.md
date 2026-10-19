# Forum optimization sources — October 17, 2026

Research scope: dual RX 7900 XTX (gfx1100), Intel i5-13600KF/Z690, CPU PCIe4 x8/x8,
32 GB host RAM, GPU-resident models. This review adds sources and future candidates;
it makes no runtime changes and adds no benchmark results. Existing measurements
remain in the [vLLM tuning report](VLLM-TUNING-2026-10-17.md) and
[SGLang tuning report](CLEAN-TUNING-2026-10-17.md).

## Level1Techs findings

| Direct source and attribution | Finding | Applicability here |
|---|---|---|
| [7900 XTX inference notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869), ivgranite, May 31, 2026 | Single 7900 XTX, Ryzen 9600X, 96 GB RAM, ROCm 7.2.3; compares Qwen3.6 MoE MTP against Gemma4 at 32K. Faster token emission did not guarantee faster completed answers. | Record time to answer, reasoning/output length and quality alongside t/s. Different models and one card; no direct speed prediction for our dense Qwen3.8 TP2 profile. |
| [Advice on local AI setup](https://forum.level1techs.com/t/advice-on-where-to-start-on-local-ai-setup/250434), May 2026 discussion | Replies recommend comparing HIP and Vulkan with the same model, quant, prompt, context and batch, and recording the software stack. | Consistent with the existing per-model selection policy. Retain measured Vulkan winners; ROCm is not automatically faster for every llama.cpp workload. |
| [DeepSeek thread, post 246](https://forum.level1techs.com/t/deepseek-deep-dive-r1-at-home/225826?page=13), ubergarm, June 28, 2025 | Firsthand 7900 XTX comparisons link mainline Vulkan/HIP and ik_llama.cpp discussions; fork support differed at that time. | Historical evidence, not a current fork ranking. Review each fork's current source and matching quant kernels before switching. Primary discussions: [llama.cpp #10879](https://github.com/ggml-org/llama.cpp/discussions/10879), [ik_llama.cpp #562](https://github.com/ikawrakow/ik_llama.cpp/discussions/562). |
| [PCIe-switch report, post 20](https://forum.level1techs.com/t/does-the-lrlink-pcie-bridge-fix-rccls-broken-p2p-on-dual-r9700-update-yes-it-does/249623/20), TrailFeatures, May 15, 2026 | Reports working peer communication through a switch on dual R9700/gfx1201, followed by a dynamic-padding training failure mitigated with fixed padding. | Relevant topology evidence, not a validated switch/product fix for this workstation. Training padding is not an inference-kernel optimization. The linked [RX7900XTX RCCL issue #6074](https://github.com/ROCm/legacy-rocm-build/issues/6074) is a separate report, not proof of a shared cause. |

## lcz.me findings and implementation sources

| Direct source and attribution | Finding | Local status / primary implementation |
|---|---|---|
| [Dual-XTX vLLM setup, topic 1252](https://lcz.me/topic/1252), flyer666; publication date absent in retrieved page | Dual XTX/Ryzen 9600X/32 GB, native gfx1100 W4A16 and MTP-loader fixes; discusses three-token speculation. | Native W4A16 is already present in the installed nightly: [upstream PR #41394](https://github.com/vllm-project/vllm/pull/41394). MTP3 is locally selected by measurement, not merely copied from the post. |
| [Comparison, topic 1814](https://lcz.me/topic/1814), Ben Lee; measurements September 18, 2026 | Dual XTX/Ryzen 9600X/64 GB, W4A16 Qwen3.8-27B; separates prefill/decode, MTP/DFlash and context depth. | Useful methodology and baseline, not an exact replay: book offsets, host platform, caches and stack differ. Do not import its host-cache budget onto 32 GB RAM. Our prefix reuse was independently verified. |
| [RDNA3 SGLang post, topic 1640](https://lcz.me/topic/1640) | Short favorable workloads and long-context book workloads produce different speculative rates. | Existing [SGLang fork source](https://github.com/StevenChenSE/sglang/blob/gfx1100-support/README.zh-CN.md), reviewed runtime revision `f84475ccf593087df3d1da13c9e675eadee12352`, plus local verifier repairs. See the local report for correctness and throughput limits. |

## HIP kernels, ROCm and C++: decisions

1. **Already applied:** native RDNA3 W4A16, compiled MTP3 and gated adaptive
   attention tiles in vLLM. The tile port follows [JartX's design](https://github.com/JartX/vllm/blob/perf/rdna3_full_stack/docs/design/rdna3_full_stack.md),
   reviewed revision `822d27588a69de52abe7a0f624f8b8bf71e5f6c4`.
   Our selected cache is BF16 at 64K. The complete fork and its native quantized
   attention kernels were not built or benchmarked here.
2. **C++ build basics already present:** Release, `GGML_HIP=ON`, explicit
   `gfx1100`, HIP clang++, isolated ROCm and limited build parallelism. See
   [upstream build documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
   and [reviewed HIP CMake source](https://github.com/ggml-org/llama.cpp/blob/f12aaa344c971556ec35be054d7aac1d901fd510/ggml/src/ggml-hip/CMakeLists.txt).
   That source has HIP graphs and optional kernel-resource diagnostics. It has no
   `ROCWMMA_FATTN` option: the old forum flag is not a current tuning recipe.
   No blanket fast-math or copied hard-coded ROCm paths were added.
3. **Candidate, untested:** isolate native HIP INT8/INT4 attention versus our
   BF16 path if greater context/concurrency becomes necessary. JartX's source
   describes separate kernel translation units to control register pressure.
   That warrants source review and numerical/graph/model checks, not an assumed
   gain from cache compression. Preserve the current measured profile meanwhile.
4. **Peer communication remains conditional:** JartX reports Intel Z790 peer-read
   corruption after a forced kernel allowlist, unlike native EPYC peer access.
   His push/QuickReduce work is not a validated drop-in for this Z690 machine.
   Keep custom peer collectives disabled. A future switch test must validate
   reads, writes, collectives and generated output, not just reported bandwidth.
   See [local P2P evidence](PCIE-P2P-2026-10-17.md) and
   [Linux P2PDMA documentation](https://docs.kernel.org/driver-api/pci/p2pdma.html).

For future experiments, cite the originating forum post and exact implementation,
then report matched prefill/TTFT, decode, completed-answer latency, cache hits,
quality, context, concurrency, residency and thermal conditions. Distinguish
microbenchmarks from end-to-end results. No new speedup is claimed by this review.

## Follow-up: additional Level1Techs leads

Checked October 17, 2026; no runtime changes or new measurements.

- **Patched rocWMMA attention / direct-P2P llama.cpp:**
  [Twitch_Blade's August 21–25 dual-R9700 report](https://forum.level1techs.com/t/dual-r9700-llama-cpp-rocm-tensor-split-working-p2p-on-proxmox-qwen3-8-27b/254183)
  reports better prefill after re-enabling rocWMMA. Its direct-P2P patch measured
  decode 28.58→31.42 t/s but prefill 934.58→871.65 t/s. This is RDNA4 on AM4
  inside Proxmox with working P2P, not our RDNA3/Intel platform. Primary patch:
  [JohnTDI-cpu/llama-hip-p2p-allreduce](https://github.com/JohnTDI-cpu/llama-hip-p2p-allreduce).
  A rocWMMA port would require actual source adaptation, not adding the removed
  build flag. Neither path has been validated here.
- **Radiance-derived RDNA3 candidate:** the same Level1Techs thread points to
  Radiance, whose [GitHub mirror](https://github.com/magiccodingman/vllm-radiance)
  targets R9700. Further primary-source review found a separate
  [gfx1100 deployment/port](https://github.com/mkadrlik/vllm-radiance-p2p), with
  Qwen3.8-27B AWQ INT4/group32, TP2 and MTP. This is more relevant than copying
  the R9700 FP8 command. Its advertised AWQ gain compares against its own W8A8
  setup, not our already-INT4 GPTQ configuration. Its published deployment assumes working P2P and
  describes IOMMU/ACS changes; those do not establish usable peer reads on our
  Intel root ports. Treat it as an isolated future comparison, not a proven
  upgrade or an instruction to change host security/topology settings.
  Follow-up local testing established that the existing GPTQ checkpoint can run
  using ordinary host transport with custom collectives disabled; working P2P
  is a prerequisite for the peer fast path, not all Radiance execution. The
  [local candidate tests](LEVEL1-TESTS-2026-10-17.md) record that distinction.
- **ROCm sources:** [ajc9988's AMD AI links](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053)
  provide official SDK/nightly entry points, but no measured speedup for this
  machine. An SDK replacement needs compatibility testing with the existing
  PyTorch/vLLM/SGLang patches; a newer version number is not performance evidence.

Local priority: a controlled cooling A/B test before another broad software
migration. Existing [SGLang telemetry](CLEAN-TUNING-2026-10-17.md) records a
108°C GPU0 hotspot and SMU hotspot/power-limit activity; the selected vLLM run
reached 107°C. This is local evidence, not a Level1Techs benchmark. The speed loss
has not been quantified, so no percentage gain is promised. Keep stock memory
clocks during comparisons. After cooling, the worthwhile software experiments
are an isolated rocWMMA port or native HIP attention test with matching model,
context and correctness checks. Direct-P2P collectives remain conditional on
validated peer access. Do not replace the working production profiles merely
because another machine has a higher headline rate.

## Local validation

[October 17–18 candidate measurements](LEVEL1-TESTS-2026-10-17.md) distinguish
CPU-reference/model correctness checks, actual throughput, unsupported peer
collectives and the fan comparison that still needs administrator access. The
restored rocWMMA port reduced 16K-depth prefill from 1,001.78 to 465.65 t/s in
the matched HIP pair; it is not enabled in production. Source-linked forum
suggestions are candidates until the retained hardware profile is validated.

## October 18: CPU expert backing and GPU expert caches

The user's newer policy keeps CPU expert offload plus hot-expert GPU caches for
all MoE models; it supersedes GPU-resident-only MoE defaults. Dense Qwen 27B
and Muse are separate. See [implementation, tests and RAM plan](MOE-OFFLOAD-2026-10-18.md).

- **lcz.me, [topic 2059](https://lcz.me/topic/2059)**, guonetnet, retrieved
  October 18 (page-reader publication date unavailable): single 7900 XTX,
  Xeon E5-2683 v3, 64 GB quad-channel DDR4 and Strata. Its CPU-resident experts,
  GPU cache and bounded resident KV are relevant; its throughput is not our
  dual-XTX/13600KF result. Primary source: [Strata AMD guide](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/AMD_HIP.md).
- **lcz.me, [topic 2249, post 8](https://lcz.me/topic/2249/8)**, user discussion,
  retrieved October 18: dual modified 2080 Ti/NVLink expert-cache recipes.
  Historical option incompatibilities must be checked against current source:
  retained Strata now explicitly supports CPU expert residency with layer split;
  remote helper caches remain incompatible. Do not import the NVIDIA topology.
- **Level1Techs, [FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396)**,
  eduncan911, August 25, 2026: adaptive CPU execution/PCIe cache-fill scheduling
  is a useful lead. The opening post describes CUDA-focused support; it is not
  proof of AMD compatibility or permission to replace the installed engine.
  [Primary project](https://github.com/FlashML-org/FreeToken).
- **Level1Techs, [7900 XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869)**,
  ivgranite, May 31, 2026: retain per-model validation, one request, desktop VRAM
  reserve and completed-answer measurements. Its 96 GB/single-card system is
  not a capacity or speed match for the temporary 32 GB installation.

The retained llama.cpp `f12aaa344c971556ec35be054d7aac1d901fd510` already contains
[host-expert GPU caching, PR 29887](https://github.com/ggml-org/llama.cpp/pull/29887)
and [multi-GPU cache placement, PR 30112](https://github.com/ggml-org/llama.cpp/pull/30112).
Use its actual `--moe-cache-mib` mechanism with explicit CPU expert placement,
not `--cache-ram` (prompt/KV parking). Cache budgets compete with KV and compute
VRAM. Keep layer splitting; the cache rejects tensor split mode. We did not add
expert pruning, change router top-k, use CUDA-only cache forks, or install a new
engine based solely on a forum speed claim. Test outcomes and limits are recorded
separately in the local report linked above.

## October 18: historical FreeToken ROCm experiment (removed)

The Level1Techs FreeToken lead above prompted a separate local ROCm source build,
since removed, pinned to [8f49e0af98ba](https://github.com/FlashML-org/FreeToken/tree/8f49e0af98ba444dd261af69e82d5a1841778c68).
[RDNA support merged in PR 132](https://github.com/FlashML-org/FreeToken/pull/132);
the [upstream AMD guide](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/docs/install_amd.md)
still describes an older Torch stack than current source requires. Official AMD
Torch 2.14/ROCm 10.1 packages were isolated from production ROCm 7.2.3 and
were removed with the experiment.

Both local gfx1100 cards pass FP32/BF16 RCCL all-reduce/all-gather without P2P;
this does **not** establish model TP2.
[GGUF embeddings explicitly reject TP sharding](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/python/freetoken/layers/quantization/embedding/gguf.py).
The user temporarily permitted one GPU for FreeToken; that exception is retired.
Two early Qwen MoE loads were stopped
by local swap guards; later guarded API trials are recorded below.

The [lcz.me single-XTX/64 GB topic](https://lcz.me/topic/2059) discusses Strata,
while the [Level1Techs FreeToken topic](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396)
is the FreeToken research lead. Neither establishes this 32 GB machine's
FreeToken serving speed. See the [historical tests and limitations](FREETOKEN-RETIRED-2026-10-18.md).

## October 18: Nemotron Q4 candidate and legacy FreeToken removal

The user requested a Q4 replacement for the old 24GB IQ2 Bolt quant. The
selected [Q4_K_M model repository](https://huggingface.co/darioooooo0o/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-GGUF)
is pinned to `b739f8c7c5484413ae3e55e6da8383f0f2570cee`; tensor metadata and
local memory guards determine CPU/cache placement rather than assuming all
45 GiB of weights plus context fit in 48 GB VRAM.

The previously cited [lcz.me Strata offload setup](https://lcz.me/topic/2059)
and [Level1Techs 7900 XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869)
remain research context, not Q4 measurements on this machine. The retained
[native cache implementation](https://github.com/ggml-org/llama.cpp/blob/f12aaa344c971556ec35be054d7aac1d901fd510/src/llama-moe-cache.cpp)
is used without a new inference fork. See [the replacement report](NEMOTRON-Q4-2026-10-18.md)
for actual validation status and limits.

The incompatible NVIDIA-only FreeToken beta/CUDA environment was subsequently
removed at the user's request. A later request removed the AMD build, Desktop
frontend, saved app data and all FreeToken launchers/caches as well. See the
[retirement report](FREETOKEN-RETIRED-2026-10-18.md).

## October 18: historical MoE tests in FreeToken AMD (removed)

[Historical MoE validation](FREETOKEN-RETIRED-2026-10-18.md) passed existing
Empero IQ4_XS and Qwen35B MXFP4 with CPU expert banks and GPU hot-expert caching.
[Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396)
(eduncan911, August 26, NVIDIA A5500/64 GB) and [lcz.me topic 2059](https://lcz.me/topic/2059)
(7900 XTX/X99/Strata) were checked; neither is a measured FreeToken AMD/32 GB
recipe. The successful per-model 26 GiB/no-swap scope is a local finding using
[systemd resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).
The [pinned GGUF expert loader](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/python/freetoken/models/gguf/experts.py)
requires CPU backing for all routed banks in offload mode. Published measurements
exclude hardware UUIDs, raw command paths, request traces and private app state.

## October 18: proposed image/video setup (not installed)

The [ComfyUI walkthrough](IMAGE-VIDEO-SETUP-2026-10-18.md) records current core
component placement across both AMD cards, an isolated ROCm nightly candidate,
Qwen-Image 2.1, Wan2.2 and gated H3/LTX candidates. No local generation speed
is established. [lcz.me 49](https://lcz.me/topic/49/13700cpu-32g-1g-7900xtx)
(i7-13700/32 GB/XTX) and [1410](https://lcz.me/topic/1410) (XTX/H3) were checked;
the latter's AI-assistant reply is not firsthand validation.
[Level1Techs](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735),
locutusofborg780, July 16, i5-12600K/32 GB/9070 XT, shows why rollback/pinning
matters, not a speed prediction for this machine. Direct upstream model, device-node,
H3-correctness and archive-status sources are linked beside the guide's claims.

## October 18 image/video model fit assessment

Checked October 18, 2026; forum results are reports, not local measurements.

- [lcz.me 1168](https://lcz.me/topic/1168), Ang Lee (post date not rendered):
  single RX 7900 XTX, 64 GiB guest RAM; H3 pruned INT8 ConvRot, NVFP4-AWQ
  encoder, matched 8-step Turbo LoRA, 1024x768 / 175 frames / muted audio.
  Reports about 445 seconds. Different RAM, precision, steps and workload from
  the local failed 30-step Q2 render; no speed ratio is valid. The listed
  attention settings are not blindly reproduced: current official Comfy docs
  warn that Comfy Kitchen attention does not support INT8 ConvRot checkpoints.
- [lcz.me 2050](https://lcz.me/topic/2050), perter (date not rendered):
  Viggle Qwen-Image 2.1 Turbo v0.3, 6-step schedule and LoRA workflows.
  Its 8/30-second image timings lack matching XTX hardware context; no local
  timing prediction is made. [Viggle's own workflows](https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo/tree/main/comfyui)
  confirm v0.3 workflow files. The [official Comfy Qwen card](https://huggingface.co/Comfy-Org/Qwen-Image-2.1)
  separately documents an 8-step Turbo model/LoRA; these are distinct schedules.
- [lcz.me 1469](https://lcz.me/topic/1469), Chi Kui Chan (date not rendered):
  dual R9700 32 GB, 64 GB RAM, mixed INT8 H3 and custom Dual-Sage attention.
  Higher-resolution pass uses about 27.5-30.3 GB on one GPU; this is not a
  ready-to-copy recipe for dual 24 GB RDNA3. Its 1.5675x figure is a synthetic
  attention result, not full-workflow speedup.
- [Level1Techs 252735](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735),
  locutusofborg780, July 16 / August 18, 2026: RX 9070 XT, i5-12600K, 32 GB;
  reports version-dependent OOM/stalls and RAM pressure. Supports isolation and
  measured version selection, not extrapolating RDNA4 timings or downgrading
  this gfx1100 machine blindly. No matching dual-XTX H3 comparison was found
  there in this search.
- [Comfy H3 issue 15314](https://github.com/Comfy-Org/ComfyUI/issues/15314),
  October 15 and 18 firsthand gfx1100 updates report clean newer-stack I2V/R2V
  results with INT8/W6A8 variants. These are PyTorch/Comfy results, not proof
  that Unsloth's sd.cpp corruption has the same cause or fix.
  [Official H3 guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
  documents 16 GB W6A8, 21 GB INT8, mode-specific Turbo adapters and attention
  constraints. [Comfy H3 model card](https://huggingface.co/Comfy-Org/MiniMax-H3)
  states its NVFP4-AWQ encoder does not require Blackwell; the label does not
  establish native FP4 acceleration on RDNA3. Validate the loader/kernel path.

Recommendation is a test order, not a proven optimum: retain Qwen base as a
baseline, test matched Turbo for images, then a native H3 INT8 or W6A8 candidate
with the correct fl2va Turbo adapter and explicit two-card component placement.
Do not delete existing weights before a replacement produces correct output.

## October 18 selected graphics files after cache cleanup

The user selected native H3 INT8 and one quality-oriented Qwen precision.
See [retained collection](../graphics/README.md) and
[verified inventory](UNSLOTH-MODEL-INVENTORY-2026-10-18.md).
[lcz.me 1168](https://lcz.me/topic/1168), Ang Lee, is firsthand XTX/64 GiB
INT8/Turbo evidence, not a local speed target. The chosen base H3 has no Turbo
adapter. [Level1Techs 252735](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735),
locutusofborg780, July 16/August 18, 2026, concerns RDNA4/32 GB stability;
it motivates isolated validation, not copying its version pin to gfx1100.
Native file/loader details are checked against
[Comfy Qwen](https://huggingface.co/Comfy-Org/Qwen-Image-2.1),
[Comfy H3](https://huggingface.co/Comfy-Org/MiniMax-H3) and
[ComfyUI source 8f04fd6](https://github.com/Comfy-Org/ComfyUI/tree/8f04fd6ecf4a548937971e840af2a985529fab76).
File integrity/format was validated during preparation; generation results now follow below.

## October 18 ComfyUI installation validation

Local generation now passes on both RX 7900 XTX cards using staged components.
[Results](../graphics/VALIDATION-2026-10-18.md) and
[exact runtime](../graphics/runtime-versions.json) separate denoising from full
SATA/32 GB staging time. Qwen BF16: 512x512/40 steps, 100.9 s total; H3 INT8:
608x352/39 frames/20 steps, 232.4 s total. These are single local base-model
runs, not a matched comparison with [Ang Lee's XTX/64 GiB Turbo report](https://lcz.me/topic/1168).
The [Level1Techs RDNA4/32 GB report](https://forum.level1techs.com/t/my-experiences-with-comfyui-on-an-rx-9070xt/252735)
remains a version-isolation rationale, not an XTX speed claim. No Turbo adapter,
Comfy Kitchen attention override or archived MultiGPU pack was installed.

[ComfyUI issue 15314](https://github.com/Comfy-Org/ComfyUI/issues/15314) motivated
avoiding the inherited expandable allocator and checking decoded output.
The initial core retarget test was stopped after duplicate encoder staging;
[the exact deepclone source](https://github.com/Comfy-Org/ComfyUI/blob/8f04fd6ecf4a548937971e840af2a985529fab76/comfy/model_patcher.py)
reloads the loader factory. Two maintained direct CLIP/VAE loaders now pass the
target device to core load APIs at construction, with no upstream patch or
weight change. Larger sizes, full-length video and speed tuning remain separate
work. The old Unsloth Q2 corruption has not been attributed to the same cause.

## October 18 Strata low-RAM community check

[Research and limits](STRATA-LOW-RAM-COMMUNITY-2026-10-18.md):
[Strata #364](https://github.com/Niko1221/Strata/issues/364) reports 32 GB /
dual 24 GB NVIDIA success; [lcz.me 2053](https://lcz.me/topic/2053) reports
about 30 GB / one 48 GB gfx1100 card. Neither establishes the exact dual-XTX
32 GB profile. [Level1Techs](https://forum.level1techs.com/t/creating-an-agent-harness-and-self-hosting-part-2-my-hardware-setup/252909)
was checked without a matched result. The retained source supports complementary
resident storage across a layer split; the local 64 GB readiness gate is
conservative, not an engine minimum. No local inference or benchmark was run.

## October 18 dual-XTX Strata validation

The [local 32 GB report](STRATA-DUAL-AMD-2026-10-18.md) now supplies an actual
dual-RX7900XTX result, distinct from [lcz.me 2053](https://lcz.me/topic/2053)
and [Strata #364](https://github.com/Niko1221/Strata/issues/364). The
[Level1Techs review](https://forum.level1techs.com/t/creating-an-agent-harness-and-self-hosting-part-2-my-hardware-setup/252909)
remains general supporting discussion. Source-reviewed resident split support
was used with an 8 GiB bound, fixed GPU cache and a worker-only no-swap scope.
Near-32K retrieval/tools/streaming passed; a future 64 GB / 128K candidate is
prepared but inactive. All measured rates and failure limits are in the report.

## October 18: fast Qwen 27B and AMD alternatives

[Focused research](QWEN27B-AMD-SPECULATION-2026-10-18.md) traces the roughly
1,000 tokens/s headline to aggregate concurrency and separates prompt-copy
speculation from ordinary single-request generation. Primary benchmark sources
and exact experimental AMD fork revisions are linked there.

- [lcz.me topic 1640](https://lcz.me/topic/1640), flyer666 / Radeon SGLang fork,
  September 11 update: dual RX 7900 XTX, Qwen 27B W4A16 target/draft, TP2
  DFlash2; code roughly 180–250 tokens/s depending on acceptance. Matching
  hardware, author report rather than a new local measurement.
- [lcz.me topic 1870](https://lcz.me/topic/1870): NInfer experiment on RTX 5090,
  a different GPU and quantization route; do not label its result Radeon speed.
- [Level1Techs dual R9700 discussion, page 2](https://forum.level1techs.com/t/dual-r9700s-amd-vllm-container-woes/250053?page=2):
  ROCm serving and evolving DFlash support, but RDNA4 rather than this machine's
  gfx1100. Reviewed as a compatibility lead, not a matching benchmark.
- [Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396):
  context for heterogeneous offload; current [AMD integration roadmap](https://github.com/FlashML-org/FreeToken/issues/541)
  still distinguishes two-GPU collectives from full model-level TP. FreeToken
  remains retired locally at the user's request.

The new [RX 7900 XTX ExLlamaV3 ROCm port](https://github.com/phoenixhaxor/exllamav3-rocm)
is a promising source-backed candidate, with single-card DFlash2 results. It is
not a locally validated dual-card profile. Keep its new EXL3 format, workload,
KV precision and context separate from the existing GPTQ/GGUF measurements.
