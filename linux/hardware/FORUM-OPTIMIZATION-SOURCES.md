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
