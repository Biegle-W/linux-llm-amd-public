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
   At that earlier selection our cache was BF16 at 64K; the [October 20 context update](#qwen-int4-context-october-20) supersedes it. The complete fork and its native quantized
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

## October 19: Strata dual-gfx1100 handoff and desktop headroom

- Primary: [Strata handoff PR936](https://github.com/Niko1221/Strata/pull/936),
  bsvinay, October 5, and the [pinned multi-GPU guide](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/MULTI_GPU.md).
  Its two-XTX/9900X/52 GB report motivates testing `STRATA_SPLIT_OVERLAP=1`;
  the author's 53→70.1 code / 45→55.9 prose t/s are not local measurements.
  This overlaps layer-stage handoff; it does not implement TP or require P2P.
- [lcz.me dual-XTX Strata report, topic2062](https://lcz.me/topic/2062),
  reviewed October 19: Swift IQ3_XXS, Strata0.1.38/HIP7.2, 128K allocation,
  CPU x8 plus OCuLink x4. Its report explicitly distinguishes layer splitting
  from TP and records roughly 50 GiB host use after dual-card startup. Different
  RAM, checkpoint/profile and topology prevent importing its speeds or context.
- [Level1Techs 7900-XTX inference notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
  ivgranite, reviewed October 19: broader gfx1100/ROCm/memory-budget experience,
  not a matching Strata overlap experiment. No performance gain is attributed
  to that discussion. The local bounded test uses only both existing AMD cards.
- Desktop safety basis: [pinned AMD guide](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/AMD_HIP.md)
  discusses graphics headroom alongside expert caching. A startup reserve is
  not a hard allocation cap; continuous checks cannot guarantee prevention of
  every burst allocation or driver fault. Local code stops only the owned
  Strata worker and latches a guard failure until explicit reload/restart.

Local measurements, retained settings and validation limits are recorded in
[the October19 optimization report](STRATA-OPTIMIZATION-2026-10-19.md).

## October 19: one versus two 12 GB NVIDIA cards in Strata

Research only; no local runtime, model, launcher or benchmark changed. Do not
interpret these external results as a measurement of the current AMD setup.

- [Upstream README, Option A](https://github.com/Niko1221/Strata#option-a-the-strata-app),
  reviewed October 19: the app and terminal use the same inference engine and
  models. Installing the app is not a separate inference-speed optimization.
- [Upstream multi-GPU measurements](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md#measured):
  the matched Coder/32K example uses RTX5080 + RTX3090 / Ryzen9950X3D, not two
  12 GB cards. At 28K prompt length, single5080 1,970 -> best split2,357 t/s
  (+19.6%); prose83-87 ->84 t/s; code88-105 ->110 t/s. Strata splits layers,
  caches their experts on their owning GPU and pipelines prompt chunks; this
  is not tensor parallelism and does not require NVLink/P2P. Extra cache room
  can reduce CPU expert work, but each card also consumes buffers; 12+12 GB
  is not equivalent to one24 GB GPU. This does not establish a 3060 gain.
- [Strata issue2007](https://github.com/Niko1221/Strata/issues/2007), jds1-ai,
  October14: two RTX3060 12 GB on Linux, CUDA13.3, driver595.91.07,
  PCIe3x16 each (12.3 GB/s probes), IQ3_XXS, 128K allocation /32K resident
  INT8 KV, spec4, auto split26. Nine short requests per start: decode medians
  61.6 t/s (0.1.43.1),58.9 (0.1.44),63.4 (0.1.44 plus LINK_ABS).
  This is a version/setting comparison with both cards, not a single/dual A/B;
  reported spread under about7% was not a demonstrated optimization gain.
- [Strata0.1.42 release](https://github.com/Niko1221/Strata/releases/tag/v0.1.42):
  one RTX3060 / IQ3_XXS already measured47.7 ->62.1 t/s by adjusting CPU/PCIe
  share (five interleaved pairs, tail-skip on in both). CPU/RAM/workload are not
  established as matched to issue2007. Neither 62.1 versus61.6 nor older30 versus newer60
  is a valid estimate of the second card's benefit.
- [lcz.me1988/50](https://lcz.me/topic/1988/50), benson Playben, reviewed
  October19: single RTX3060 12 GB, Swift1.5,128K allocation, reported32 t/s;
  missing controlled prompt/build/RAM details. [lcz.me2048](https://lcz.me/topic/2048)
  documents RTX4070+3060 12+12 GB, i5-13600KF/64 GB, Strata0.1.31,
  IQ2_XS/IQ3_XXS128K; its differing links, workloads and quantizations do not
  supply an identical3060 single/dual control. Preserve its historical status.
- [Level1Techs local-server discussion](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001),
  October8: discusses single3090 Strata and a separate dual-R9700 Radiance
  report. Neither is a matched one/two12 GB NVIDIA Strata result. No exact
  matched comparison was located in the forum searches reviewed this date.

Conclusion: the second12 GB card adds expert-cache/context capacity, but a fixed
percentage decode improvement is not established. The upstream roughly20%
prefill example is evidence on different cards, not a forecast for dual3060.
A credible percentage needs the same engine, quant, CPU/RAM, actual prompt
length, MTP, routing flags and warmed workloads, with single/dual runs interleaved.


## October 19: RAM-backed native 256K on 32 GB / dual XTX

[Local context sweep](STRATA-CONTEXT-2026-10-19.md) passed 64K,128K and 256K
with INT8 KV/32K GPU residency, bounded CPU expert complement and unchanged
HIP 0.1.45. [Pinned setup accounting](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/setup.py)
and [multi-GPU implementation](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/MULTI_GPU.md)
support streamed host KV. The new admission check budgets full host KV beside
experts and headroom. [lcz.me topic 2163](https://lcz.me/topic/2163), reviewed October 19,
is the dual5060Ti IQ3_S196K/256K precedent; its hardware/speed are different.
[Level1Techs October 8 discussion](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001)
provides offload/PCIe context, no matched dual-XTX 32 GB experiment. No forum
speed was imported. No experimental RoPE extension or new weight quant was used.

## October 19: Nemotron Super 32/64 GB preparation

Both forums were searched for matching Super VL/dual-XTX results; no matching
measurement was established. [lcz.me single-XTX Qwen/KVMem report](https://lcz.me/topic/1972/9)
and [Level1Techs RAM/partial-offload tests](https://forum.level1techs.com/t/ryzen-9950x-ram-tuning-and-benchmarks/219347)
have different models, memory and/or GPU hardware. They were reviewed for
applicability, not copied as local benchmarks or direct configuration recipes.
Use the [Unsloth primary guide](https://unsloth.ai/docs/models/nemotron-3.5-super-vl)
and installed [llama.cpp implementation](https://github.com/ggml-org/llama.cpp/commit/31288c9c66e59377f7788d920678a565bb89dd37)
for architecture/cache support, and the [new local result](NEMOTRON-SUPER-2026-10-19.md)
for actual capacity and throughput. No runtime update was required.

<a id="pcie-switch-purchase-october-19"></a>

## PCIe switch purchase — October 19

The owner reports buying the four-GPU PEX88096 kit whose listing spells it
“plx8096 PCIe4.0扩展 四卡GPU”. Installation, link negotiation, HIP peer access,
RCCL correctness and inference speed are pending local validation. Current
benchmarks still use the motherboard x8/x8 layout and host transport.

- [lcz.me, 张光璞, September 2026 purchase thread](https://lcz.me/topic/1791):
  Taobao four-slot kit, reported RMB 2,380 including host card/two cables.
- [Same owner's dual-7900-XTX follow-up](https://lcz.me/topic/1791/118):
  PEX88096, 32 GiB BARs, 7.23 GB/s peer copy / 7.06 GB/s direct peer kernel read;
  GPU-facing links remained Gen2 x16. These are forum results, not this PC's.
- [Level1Techs, TrailFeatures, May 2026](https://forum.level1techs.com/t/does-the-lrlink-pcie-bridge-fix-rccls-broken-p2p-on-dual-r9700-update-yes-it-does/249623/14):
  different dual-R9700 hardware; firmware/ACS/BAR configuration mattered.
- [Broadcom PEX88000 product brief](https://docs.broadcom.com/doc/BC-0484EN)
  documents the switch family. Chip capability does not validate a board's
  routing, signal integrity or RX 7900 XTX compatibility.

No PCI register, BIOS, kernel or runtime-transport changes were applied for this purchase.

## i9 / 64 GB CPU and expert-cache validation — October 20

These sources motivated bounded candidates, not promised local speeds. Local
measurements and selected settings are in [the validation report](CPU-RAM-PROFILES-2026-10-20.md).

| Source | Relevant setup / implementation | Applicability here |
|---|---|---|
| [lcz.me topic 2027, post 13](https://lcz.me/topic/2027/13) | Single RX 7900 XTX / 64 GB; resident CPU experts and available RAM | Verify actual available RAM and worker residency; another Strata version is not a speed target. |
| [lcz.me topic 2032, post 19](https://lcz.me/topic/2032/19) | Older Strata 0.1.27 / HIP library tuning | Tables depend on architecture and library build; no external tuning table was installed for this task. |
| [Level1Techs mixed-offload thread](https://forum.level1techs.com/t/9950x3d-reviewed-and-benchmarked-tokens/227386) | March 2025 discussion, including tk11/ubergarm; another CPU/platform/model | Memory movement can limit mixed offload; it supplies no 13900KS/Super-Q4 result. |
| [Pinned llama.cpp expert-cache source](https://github.com/ggml-org/llama.cpp/blob/4c3c5810f87efe177949f1b85ae509d38a2a311f/src/llama-moe-cache.cpp) | 50/50 SLRU replaces LRU in 4c3c5810; large batches reuse cached expert copies and upload misses | Compare microbatches with exact placement/cache settings and guards; CPU-backed weights are still computed on GPUs in this path. |
| [Pinned Strata CPU-affinity source](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/src/program/generate.cpp) | `--pool-workers` and `--pool-affinity p-cores` | Compare six unpinned workers and seven P-core workers on the detected 8P+16E CPU; core count alone does not establish the fastest pool. |

The same-placement Q4 thread controls (6/6 versus 8/24 physical-core settings)
stayed near 45 native prefill t/s and 8 decode t/s, one timed trial per task.
They do not establish a benefit from more threads. Placement, microbatch and
cache changes are complete-profile experiments; keep their actual input lengths,
quality checks and guard outcomes beside the timings.

<a id="project-maya-october-20"></a>

## Project Maya / GLM and DeepSeek — October 20

Local setup uses two RX 7900 XTX cards, i9-13900KS and 64 GB RAM. The downloaded
quants and exact measured limits are in [the Maya report](MAYA-2026-10-20.md).
External results are not local benchmarks.

| Source | Reviewed evidence | Applied scope |
|---|---|---|
| [lcz.me topic 2195, post 3](https://lcz.me/topic/2195/3), johnnybegood, test October 8 | Maya 1.0.11; 3080 20 GB + 3090 24 GB; 128 GB RAM; 65K; GLM S24/S/M and differing sampling | S24 is a candidate for limited VRAM; lower-temperature MTP results change sampling and do not establish an equal-quality speed gain here. |
| [Level1Techs topic 258001](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001), rqzer0, October 8 | Planned 9900X/96 GB/3090; model-memory budgeting, not a Maya dual-gfx1100 measurement | Preserve desktop RAM/VRAM reserves; no matching two-7900-XTX Maya benchmark found in this search. |
| [Pinned upstream AMD guide](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/docs/AMD_MAYA.md) | Experimental HIP; dual-card layer splitting, version-matched gfx1100 hipBLASLt tables and prefill sub-batches | Isolated build, `MAYA_GLM_PREFILL_SUB=1024`, 4 GiB prompt budget, both GPUs; validate locally before activation. |
| [GLM RAM budgeting](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/src/core/glm_fast_path.cu#L1429) | RAM budget is divided across the layer groups | Explicit 36 GiB whole-machine ceiling, not 36 GiB per card. |
| [DeepSeek grouping, mapping and CPU pools](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/src/ds4/ds4_model.cu#L1720) | TP depends on quant block divisibility; mmap/page-cache backing differs from a copied expert tier; `DS4_COPY_GB` is an experimental static copy | Selected GGUF downgrades TP width to 1 while retaining both layer groups. No direct P2P or full expert residency claim. Disk-weight skipping changes answers and stays off. |
| [Official ROCm 7.2.3 notes](https://rocm.docs.amd.com/en/docs-7.2.3/about/release-notes.html) and [rocWMMA tag](https://github.com/ROCm/rocWMMA/tree/48b7db12a9ade97f0b7ab2ff9321ba0cbb4e5b77) | rocWMMA 2.2.0 | Missing headers supplied only to the isolated Maya build; SDK and other engine builds unchanged. |

The broad DeepSeek GGUF suite still fails two bit-exact mixed Q4_K/IQ4_XS cases
on each card. Actual selected Maya-S metadata contains neither type. That limit
is retained and enforced by admission; it is not silently called a full-suite
pass. Local arithmetic/JSON/tools/marker checks do not establish general quality.


<a id="qwen-int4-context-october-20"></a>

## Qwen INT4 context expansion — October 20

External reports and locally reviewed implementation are separate from validation.

- [lcz.me topic 1921, original report](https://lcz.me/topic/1921/5), 懒人烘培 (date not exposed in the fetched page; reviewed October 20): Ryzen 7500F, 96 GB, dual 7900 XTX TP2, same AutoRound GPTQ target, SGLang f84475cc, BF16 KV/DFLASH/196608 configured context, HiCache. This supplies a compatible candidate, not a speed prediction. Its initial vLLM “cold” table contains prefix hits, acknowledged later; it must not be imported as cold prefill performance.
- [lcz.me topic 1921 follow-up](https://lcz.me/topic/1921/11), 张光璞 (reviewed October 20): GPU-evicted-prefix tests distinguish write-through host reuse from a GPU hit. `hicache-size` is per rank, so TP2 doubles that allocation. HiCache is prefix retention, not a substitute for enough live GPU KV capacity. No host-cache allocation is added merely to enlarge a context flag.
- [lcz.me dual-XTX discussion](https://lcz.me/topic/1674), flyer666/community (reviewed October 20): SGLang BF16 KV and vLLM INT8 KV have different capacities. Reported gfx1100 FP8 execution is slower in the discussed implementation. Preserve the previously faster BF16 SGLang path and evaluate vLLM per-token/head INT8 only with actual long-prefill/retrieval checks.
- [lcz.me RDNA3 vLLM implementation discussion](https://lcz.me/topic/1252/14), iamvirus/community (reviewed October 20), links [JartX RDNA3 source branch](https://github.com/JartX/vllm/tree/perf/rdna3_full_stack). Its INT8 prefill/decode kernels are candidates for that branch; no fork/kernel upgrade is installed by this task. Our retained wheel already exposes per-token/head INT8 KV, but performance and support must be validated on the exact installed build.
- [Level1Techs Crucible discussion](https://forum.level1techs.com/t/crucible-llm-bench-your-llm-and-server-is-it-fast-enough-for-everyone/257531), MadGoat, October 1 with October 12 release details: measure actual token counts, retrieval at different depths and per-request TTFT/decode separately. This is methodology, not a matching gfx1100 configuration or a reason to copy another system's rate. Existing local probes already count tokens and place markers near the beginning/middle/end; no new benchmark package is installed.

Primary implementation references: [pinned SGLang runner](https://github.com/StevenChenSE/sglang/blob/f84475ccf593087df3d1da13c9e675eadee12352/python/sglang/srt/model_executor/model_runner.py), [SGLang HiCache documentation](https://docs.sglang.io/docs/advanced_features/hicache), and [vLLM quantized-KV documentation](https://docs.vllm.ai/en/latest/features/quantization/quantized_kvcache/). The installed Triton attention backend lists `int8_per_token_head`; the local pinned wheel/source and existing Radeon tile fixes remain unchanged. Higher configured context alone is not validation; retain a GPU-resident dense target, both cards, speculation settings and measured headroom.

## Maya higher-quality quant assessment — October 20

[Assessment, precision recipes and proposed A/B criteria](MAYA-QUANT-OPTIONS-2026-10-20.md):
initial research only, followed by the measured A/B below. GLM Maya-S was the
smallest candidate; M/L increase fidelity and cache/streaming demands. DeepSeek
Maya-M is absent from the checked publisher revision.

- [lcz.me 2195/3](https://lcz.me/topic/2195/3), johnnybegood, October 8: Maya1.0.11, 3950X/128GB,3080-20GB+3090-24GB,65K,S24/S/M; differing sampling prevents a matched speed/quality comparison or a dual-gfx1100 prediction.
- [Level1Techs 258001](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001), rqzer0,October8: memory planning only; no matched Maya higher-quant/two-XTX/64GB measurement found.
- [Publisher GLM recipes/metrics](https://huggingface.co/peasantsmith/GLM-5.3-Flash-Maya-GGUF), [pinned S24 comparison](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/bench/results/MAYA-S24.md), [DeepSeek file listing](https://huggingface.co/api/models/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF) at276e0bad: quant metadata/availability, not local speed claims.


## Locally measured GLM S/S24 follow-up — October 20

[Matched comparison](MAYA-S-VS-S24-2026-10-20.md) and [numeric evidence](results/maya-s-vs-s24-2026-10-20.json): Maya-S passed the declared speed, functional/memory and normal-launcher checks; it is now selected. Same hardware/build/32K/guards, ABBA with six trials per workload. Candidate selection is based on local data, not the differently sampled [lcz.me2195/3](https://lcz.me/topic/2195/3) NVIDIA report or [Level1Techs258001](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001) hardware-planning thread. Their original applicability limits remain above.

## October 20 — Strata app update and Intel desktop rendering

Reviewed the [official0.2.1 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.1)
and [development source9ae93f7b](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f).
App0.2.1 bundles HIP0.1.46;0.2.1.1 is a Windows Terminal fix. The local
development HIP0.1.46.1 candidate is built, not promoted: actual6GiB/card startup
admission failed. No new engine speed, new default tuning or larger context is
claimed. [Local evidence and pending desktop change](STRATA-LINUX-UPDATE-2026-10-20.md).

- [lcz.me2059/7](https://lcz.me/topic/2059/7), reviewed October20: different X99
  single7900XTX/Strata setup with a separate R7 display card; desktop/browser
  VRAM contention motivates separating rendering. Its reported saving/speed is
  not a local measurement or proof of this GNOME fix.
- [Level1Techs193307/2](https://forum.level1techs.com/t/how-to-get-display-output-on-secondary-gpu-non-primary/193307/2),
  DS_DV, January23,2023: links the preferred-primary Mutter rule on a different
  APU/VFIO setup; no current dual7900XTX inference benchmark.
- Implementation: [GNOME Mutter multi-GPU documentation](https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md).
  Local monitor already scans out on IntelUHD770, while GNOME50.1 logs AMD BootVGA
  rendering. The reviewed8086:a780 rule is installed/tag-verified and needs a new
  session; no global compute environment, AMD driver or inference-device selection
  is changed. Real post-login VRAM savings are unmeasured.

Local follow-up, October20 after user logout/login: GNOME's new-session journal
explicitly selects Intel as primary via the reviewed rule. Both AMD cards idle at
about27MiB, but two unchanged Strata9ae93f7b starts still fail actual6GiB/card
admission (exact loaded5.388/6.269GiB free). This is a local memory-admission
result, not confirmation of any forum speed claim. The forum/source links above
remain the implementation trail. [Retest evidence](results/strata-linux-update-2026-10-20.json)
and [limits](STRATA-LINUX-UPDATE-2026-10-20.md).

Later local validation, October20: the user authorized5GiB actual startup
admission. Strata9ae93f7b/0.1.46.1 passed all guards, functional/near256K/history
and normalDesktop/UI/API checks and is promoted. Fresh three-trial medians are
nativePP912.2, fresh8K TTFT9.015s, code/prose75.28/50.31t/s. This is a local
rollout result, not a matched A/B or confirmation of forum rates. The existing
[lcz.me display topic2059/7](https://lcz.me/topic/2059/7),
[Level1Techs preferred-primary post193307/2](https://forum.level1techs.com/t/how-to-get-display-output-on-secondary-gpu-non-primary/193307/2)
and [reviewed upstream9ae source](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f)
remain the trail. [Local method and limits](STRATA-STARTUP5-2026-10-20.md).

## October20 — DeepInfer compatibility review, no deployment

Reviewed official source774ce244b87cc0eb8d4b94ab9f5de2ab22049f01:
[platform/model scope](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/README.md),
[build selector](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/build.sh),
[device discovery](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/deep_cluster/hardware/device.py),
[checkpoint loader guide](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/examples/README.md).
No ROCm/gfx1100 path is present in the reviewed selection code. No installation,
model download, engine change or local speed claim follows.

Consulted lcz.me and Level1Techs with exact-name site searches and public front
pages. No relevant indexed DeepInfer/gfx1100 local result was returned; lcz.me's
JavaScript-only content limits coverage. No specific forum post is cited as a
successful local deployment because none was verified. This is not a claim of
exhaustive forum/fork coverage, and no forum-derived tuning is imported.
[Assessment, queries, source fingerprints and limits](DEEPINFER-ASSESSMENT-2026-10-20.md).

## October20: reconciling forum headlines with local speed

[Focused comparison](FORUM-SPEED-COMPARISON-2026-10-20.md) uses saved local
measurements only; no runtime setting or benchmark changed.

- [lcz.me2317](https://lcz.me/topic/2317), farmer node, reviewed October20
  (post date unavailable): EPYC7452/about125GiB/twoXTX/IQ3_S/Strata0.1.43;
 70–80t/s per independent single-card replica,160t/s aggregate. This corrects
  the TP wording in [the secondary summary2318](https://lcz.me/topic/2318):
  the original author explicitly says replicas, not TP2 or layer splitting.
- [lcz.me1640](https://lcz.me/topic/1640), flyer666, September11 refresh:
  distinguish short code180–250t/s from standardized depth0/16K128.3/108.8.
  Current local code178.82/prose63.40 uses different sampled prompts.
- [lcz.me2062/5](https://lcz.me/topic/2062/5), J I, reviewed October20
  (post date unavailable): Ultra7265K/64GB/x8+x4/noP2P/IQ3_XXS/Strata0.1.38;
  fixed32K/128K prefill1838/2129t/s. Local8K912.2/near258K992.7 is lower
  but is not a matched workload or causal2x regression measurement.
- [Level1Techs250869](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
  ivgranite, May31: singleXTX/96GB/Qwen3.6MoE/Gemma4, differing output lengths;
  report answer latency as well as t/s, not a matching TP2/Strata speed target.

Primary [pinned Strata multi-GPU implementation guide](https://github.com/Niko1221/Strata/blob/9ae93f7b1fe989d04a8e404d32cddaeeff10505f/docs/MULTI_GPU.md)
separates layer handoff from tensor-parallel collectives. The remaining gap
requires matched telemetry/workloads; no promise is made that the pending
switch, smaller context, reduced reserves or a newer build will remove it.

## Maya v1.1.19 and ROCm10 review — October20

[Local controlled evaluation](MAYA-ROCM10-2026-10-20.md) distinguishes reviewed
source3384b5e/v1.1.19, same-sourceSDK7.2.3/10.0.0 and a no-table10 arm.
GLM Maya-S remains the quant, on shared NVMe; community S24 is a different arm.

- [Maya PR292](https://github.com/mw00/project-maya/pull/292), Cass67,October20:
  **four7900XT/80GB**, GLM-S24,32K,ROCm10/hipBLASLt100401; native greedy
  benchmark. Table-only8K prefill382→602t/s; decode51.6→50.4. Reviewed source
  [f8c33e50](https://github.com/mw00/project-maya/commit/f8c33e50b1b2b24a8dd45a3676b329c9dd241a8e)
  contains the matching table. Our existing7.2.3 GLM control already has a
  working60-row100202 table. Table benefit is not a whole-SDK speedup.
- [lcz.me1532/95](https://lcz.me/topic/1532/95), BenLee,accessedOctober20
  (exact post date unavailable in fetched view): two7900XTX,TP2/MTP3/BF16KV,
  PR34058/N=1,~64K. Reported7.2.3→10 single-query decode62.2→74.1t/s,
  but prefill1338→1146 and C2TTFT49.78→57.35s. Current local DFlash2 differs.
  [Upstream scheduling PR34058](https://github.com/sgl-project/sglang/pull/34058)
  concerns prefill/decode fairness; no scheduler change follows from this review.
- [lcz.me2032/3](https://lcz.me/topic/2032/3),naniandemeng,accessedOctober20
  (exact post date unavailable): one7900XTX,E5-2678v3/64GBDDR3,Strata0.1.27,
  Swift1.5IQ3_XXS,ROCm10/256K. Tuning743→1179PPt/s;8K1453PP/82.7decode.
  Model derivative, MTP4, batch8192 and source differ from the retained local arm.
- [Level1Techs official-source index](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053),
  ajc9988,January7,2026 thread: useful official AMD/TheRock locations. Its
  gfx1151 examples are not gfx1100 results or matched dual-XTX speed claims.
- [AMD vLLM installation matrix](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/vllm.html),
  [CLI compatibility](https://rocm.docs.amd.com/projects/rocm-cli/en/latest/engines/vllm.html)
  and [TheRock packaging](https://github.com/ROCm/TheRock/blob/main/RELEASES.md):
  an aligned Torch/Triton/engine stack is needed. Documented10.0 prebuilt vLLM
  uses Python3.14 and an older vLLM minor; it does not replace the retained
  Python3.12/0.32/RDNA-patched stack by changing a library path.

Locally, GLM10 tuned PP479.2 beats same10 untuned355.5 but trails new-source7
PP500.4; code/prose17.77/14.56 versus18.18/15.92t/s fails the declaredSDK gate.
Both GLM candidates passed near32K/tools/JSON/SSE and memory gates. DeepSeek
new-source7 passed fresh31,488 and follow-up31,520 inputs; itsSDK10 automatic
expert-streaming arm emitted a pull-completion timeout warning. The matched
`DS4_STREAM=0` SDK7 arm passed near32K/tools/JSON/SSE and measured6.89/7.08decode,
188.6PP; SDK10 stalled at one output token in its first timed request and was
stopped with verified owned cleanup. No completed timed SDK10-fallback rate is
published. CPU experts/GPU hot caching and all guards remain enabled. These
observations alone do not diagnose a hardware or coherence fault. [Pinned lane policy](https://github.com/mw00/project-maya/blob/3384b5e9366e696e5f23f51772fb94a8a7948e41/src/ds4/ds4_model.cu#L5914-L6070).
No community rate is substituted for a local measurement. Maya source19/SDK7 was subsequently promoted after normal proof; SDK10 remains rejected. Other production engines remain unchanged. Final decisions and normal proof are maintained in the local evaluation report.

Local other-engine comparisons are now complete: [Strata/llama SDK results and limitations](ROCM10-OTHER-ENGINES-2026-10-20.md). Retained-SDK7 controls and isolated table/SDK10 candidates use matching sources/profiles. These do not promote a new runtime or convert external forum rates into local ones.

## ROCm10.1 six-engine comparison — October21

The user requested isolated10.1 comparisons across ComfyUI, Strata, Maya,
llama.cpp, SGLang and vLLM. [Method and decisions](ROCM101-2026-10-21.md).
[AMD10.1 release notes](https://rocm.docs.amd.com/en/latest/about/release-notes.html)
are datedOctober5; [official framework packages](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html)
provide gfx1100 Torch2.13/2.14 and matching10.1 libraries. These are primary
implementation sources, not measured local gains.

Rechecked [BenLee, lcz.me1532/95](https://lcz.me/topic/1532/95), accessedOctober21
(exact post date not visible): dual7900XTX/SGLangTP2/MTP3/BF16KV/~64K; ROCm10
decode improvement accompanied slower prefill/TTFT. It does not measure10.1
or our DFlash2/160K profile. [ajc9988, Level1Techs January7 source index](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053)
was recheckedOctober21; its official download links are useful, while gfx1151
examples are not gfx1100 results. Keep forum claims, new candidates and locally
validated results separate. No production migration follows from the sources alone.

Local10.1 outcome: all selected stacks retained. SGLang/Maya lose; Strata prose loses8.38%; vLLM/Empero diverse-seed gains1.63%/0.30% miss the3% gate; Comfy H3 regresses despite faster images. New results are local measurements, not forum estimates.

## Sage-A1.5 and ROCm branch selection — October 21

[Selection report](ROCM-SELECTION-2026-10-21.md) separates local results from
community reports. [Ben Lee, direct ROCm comparison](https://lcz.me/topic/1532/95)
(accessed October21; retrieved view has no exact date) uses dual7900XTX,
SGLangTP2/MTP3/BF16KV/~64K and [PR34058](https://github.com/sgl-project/sglang/pull/34058).
Reported 7.14 improves decode6.8% over7.2.3;10 improves19% but loses cold-prefill
13–14%/TTFT14–15%. These are not our DFlash2/160K or Sage measurements.
[Later 7.14 setup](https://lcz.me/topic/1674/8): Ryzen9600X/X870E/64GB,
not a matching local A/B.

[Level1Techs official-source collection](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053)
(ajc9988,January7,2026) provides AMD/TheRock links; no matched dual-XTX Sage
7.14.1 result was found. [ivgranite,May31](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869):
oneXTX/Ryzen9600X/96GB/7.2.3/llama9425,32K uncapped reasoning; faster decode
does not guarantee faster completed answers when output lengths differ.
Primary references: [official Sage Q4](https://huggingface.co/InternScience/Sage-A1.5-Q4_K_M-GGUF/tree/48ffaf2d61da137314074fc6a46dc73136ff111e),
[AMD7.14.1 caveats](https://rocm.docs.amd.com/en/docs-7.14.1/about/release-notes.html),
[AMD10.1](https://rocm.docs.amd.com/en/latest/about/release-notes.html),
[pinned llama source](https://github.com/ggml-org/llama.cpp/tree/4c3c5810f87efe177949f1b85ae509d38a2a311f).
Retain current production versions unless matching local validation and speed
gates pass. Global driver replacement and untested framework-wheel migration
are not justified by a newer version number.

## Ornith-1.5-122B investigation — October21

No matched122B/dual7900XTX/64GB benchmark found in either forum search.
[lcz1382](https://lcz.me/topic/1382/12), accessed October21 (exact date not exposed):
西域草影 reports35B/dual6800XT/llama.cpp-turboquant-hip, while others describe
quant-dependent agent reliability; incomplete quant/context/workload, not122B.
[Level1Techs post7](https://forum.level1techs.com/t/one-week-of-local-ai-on-strix-halo/254086/7),
lhl,August23,2026: gfx1100/gfx1151 projects and35B evaluations in a Strix-Halo
thread, not matched dual-XTX122B measurements. Neither supports a local speed claim.
Primary evidence: [pinned publisher config/card](https://huggingface.co/ornith-ai/Ornith-1.5-122B/tree/7681ef608624e7532d8164128bcffdbdbaf1b1af),
[officialQ4](https://huggingface.co/ornith-ai/Ornith-1.5-122B-GGUF/tree/8d5893d767c449a4f18dd08f4bb6d0d6d4426175),
[UnslothIQ3](https://huggingface.co/unsloth/Ornith-1.5-122B-GGUF/tree/3842d003341507c216295c6f28dfcd30349925c6),
[retained llama class/MTP implementation](https://github.com/ggml-org/llama.cpp/blob/4c3c5810f87efe177949f1b85ae509d38a2a311f/src/models/qwen35moe.cpp).
[Assessment](ORNITH-122B-ASSESSMENT-2026-10-21.md) separates bounded header/tensor
inspection and memory candidates from publisher scores and unperformed runtime
validation. Q4 CPU backing/cache and IQ3 alternatives are proposals, not selected
profiles. No full checkpoint download, inference, benchmark or runtime change.

## vLLM alternatives for Bolt and Sage — October 21

No lcz.me or Level1Techs report covers Nemotron-3.5-Bolt or Sage-A1.5 on vLLM/ROCm.
- [Level1Techs: R9700 TP2/TP4 guide](https://forum.level1techs.com/t/amd-radeon-r9700-linux-tp2-and-tp4-the-definitive-guide/250504)
  covers Qwen3.5-122B GPTQ-Int4 with AITER MoE on RDNA4, not gfx1100.
- [Level1Techs: vLLM/ROCm 7.14 on 4× R9700](https://forum.level1techs.com/t/vllm-0-23-x-rocm-7-14-upgrade-on-4x-radeon-ai-pro-r9700-50-regression-on-one-model-unaffected-on-another-but-a-free-9-via-kernel-tuning/253460)
  reports about a 50% FP8 MoE regression (RDNA4).
- [Level1Techs: "I need help with ROCm"](https://forum.level1techs.com/t/i-need-help-with-rocm/242075)
  (Froz04, December 6, 2025) describes failed dual-7900 XTX vLLM setup.
- [lcz.me topic 353](https://lcz.me/topic/353) covers single-card 7900 XTX llama.cpp.

None supports a local speed claim. See [the research note](VLLM-ALTERNATIVES-BOLT-SAGE-2026-10-21.md).

## Slow-model optimization research — October 22

- [r/LocalLLaMA, u/coder543 (mirror)](https://reddit.sentinel-team.org/posts/1tany5t/snapshots/2026-05-15T23%3A40%3A01.25497Z):
  `-ub 512 → 4096` raised gpt-oss-120b CPU-offload prefill 380 → 1,682 tok/s.
- [lcz.me #1929](https://lcz.me/topic/1929) (johnnybegood, September 25): GLM-5.3-Flash dual 3090:
  DFlash2 n=2 +21–25% decode; UBATCH 4096 raised prefill but lowered decode; decode is CPU-bound.
- [lcz.me #2357](https://lcz.me/topic/2357) (johnnybegood, October 16): Strata-DSV4.1 DeepSeek ~26 tok/s on a 4090 (custom quant, ~600 GB SSD).
- [Level1Techs: Optimal local AI on 12 GB VRAM](https://forum.level1techs.com/t/optimal-local-ai-on-12-gb-vram/251461)
  and [DeepSeek R1 at home](https://forum.level1techs.com/t/deepseek-deep-dive-r1-at-home/225826): thread count about equal to physical cores; hybrid-core defaults hurt.
- [Doctor-Shotgun MoE offload guide](https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide): `-b/-ub 4096`, op-offload threshold.

None supports a local speed claim. See [the research note](SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md).

## October23 — Maya1.1.24 update

Reviewed [upstream25deec5](https://github.com/mw00/project-maya/commit/25deec505b525212e05faa58697d9d2b7d17fdb3), [AMD DS4 changes3453271](https://github.com/mw00/project-maya/commit/3453271) and [gfx1100 fused enablement18bc575](https://github.com/mw00/project-maya/commit/18bc575). Locally selected Maya-S/32K/bothXTX on7.2.3: GLM failed fused path disabled; DS4 prefill185.1→299.0t/s, decode similar. These are local measurements, not community speeds. [All gates and limits](MAYA-UPDATE-2026-10-23.md).

Forum context: [LCZ GLM test dated2026-10-08](https://lcz.me/topic/2195/9) used Maya1.0.11/3080+3090/64K and changed sampling (author unavailable in fetched excerpt). [Level1Techs JWNoctis,October15,post60](https://forum.level1techs.com/t/ultimate-2x-r9700-guide-for-qwen-3-8-27b-mxfp4-200t-s-c-1-500t-s-at-c-8/257789?page=3) discusses Radiance/RDNA4 timing/token-accounting differences, not matched Maya/gfx1100. Neither justifies a local70t/s claim or deploying its settings. User-supplied NVIDIA Maya-XS screenshots differ in quant/drafter/hardware; no image/account/private message exported.
