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
