# Qwen3.8-27B speculative decoding: AMD options, October 18, 2026

These are upstream or author-reported results, not new measurements on this workstation.
Current local hardware is two RX 7900 XTX 24 GB cards, PCIe4 x8/x8, and 32 GB
RAM. Both cards remain required for active local profiles. The fastest retained
Qwen 27B path is the Radeon SGLang DFlash2 profile; see the local benchmark tables
and the runtime upgrade report for actual measurements.

## What the roughly 1,000 tokens/s claims measure

The [HyperQwen author’s RTX 3090 report](https://www.reddit.com/r/LocalLLaMA/comments/1vsy4l2/i_pushed_qwen3827b_limits_again_dflash2_134_tps/)
explicitly separates about 138 tokens/s for one ordinary request from about
942–1,000 tokens/s across **64 concurrent requests**. The
[project README](https://github.com/syv-ai/HyperQwen) likewise distinguishes
single-user performance, prompt-copy workloads and aggregate throughput. Its current
summary is **127 single-stream versus 1,035 aggregate at 64 concurrent**; that
batch mode uses ordinary batching rather than the single-user speculative path.
A [follow-up by the same author](https://www.reddit.com/r/LocalLLaMA/comments/1vtup5s/i_pushed_qwen3827b_to_381_tps_for_a_single/)
reports about 382 tokens/s when reproducing text already in the context, using
lookup drafting to extend verification blocks to 16 tokens; ordinary chat is
about 133 tokens/s. Longer blocks and quantized KV introduce capacity, latency
and workload trade-offs. These are useful optimizations, but neither headline
establishes 1,000 tokens/s for ordinary single-user generation on a 24 GB card.

[NInfer’s official Qwen 27B benchmark](https://github.com/Neroued/ninfer/blob/master/docs/performance/qwen3.8-27b.md)
uses one **RTX 5090 with 32 GB**, revision `7f6aafedb5f20200def820cfe51ab81c09c20eeb`,
September 28–29. Its 922.4 tokens/s is aggregate MTP3 throughput at concurrency 8;
the corresponding concurrency-1 saturation result is 147.7. DFlash2 single-request
NVFP4 results vary by workload: code 285.7, story 129.2 and structured output
377.3 tokens/s. Some outputs hit their generation limit; these are throughput
measurements, not completed-task accuracy scores. The
[lcz.me NInfer experiment](https://lcz.me/topic/1870) also uses a 5090, not a 7900 XTX.

A newer [NInfer-3090 v0.11.0 release record](https://github.com/Ryan-gsq/ninfer-16g-5070ti-5080-5090-qwen3.8-27b-gsq-rco/blob/main/RELEASE_NOTES_0.11.0.md)
reports **187 tokens/s single stream** and 130,000 context on one RTX 3090 24 GB,
with up to 2,989 tokens/s prefill. This is a CUDA/Ampere fork, not upstream's
5090 benchmark or a Radeon implementation. Its quantization and quality trade-offs
must be retained when comparing the figure; prefill and decode are separate.

MTP and DFlash2 are alternative speculative methods in these engines. Enabling
both names does not combine their speedups automatically. Draft acceptance,
verified output, sampling, prompt length, batch size and output length must be
reported alongside speed. Prompt-copy and structured-output speeds should not
be presented as ordinary prose generation.

## AMD implementations worth considering

| Engine | Evidence and fit | Current decision |
| --- | --- | --- |
| [StevenChenSE SGLang gfx1100 fork](https://github.com/StevenChenSE/sglang/tree/gfx1100-support) | Already installed: Qwen W4A16 target and W4A16 DFlash2, TP2, Radeon-specific kernels and locally repaired verification. [Author report, lcz.me topic 1640](https://lcz.me/topic/1640): two 7900 XTX cards, roughly 180–250 tokens/s code and 70–120 language-dependent QA. Workload and correctness checks matter. | Best established fit for the user's dual-card policy; retain the tested patches. |
| [phoenixhaxor/exllamav3-rocm](https://github.com/phoenixhaxor/exllamav3-rocm) | Author-tested on **one RX 7900 XTX**, ROCm 7.2.4; Qwen EXL3 3.5 bpw plus EXL3 DFlash2 5 bpw. Reports code-style 157 tokens/s at 2K, 147 at 32K, 107 at 99K; TabbyAPI code about 186 and prose about 78. Q8 target/Q4 draft KV; 192K DFlash2 and 256K MTP profiles with retrieval probes. Some API results use an ablation sidecar. | Promising experimental RDNA3 equivalent, not locally installed/tested. Requires new EXL3 weights. Published serving recipe is single-card; dual-card suitability is unvalidated. Do not silently relax the GPU policy. |
| [CarouselAether/rocm_exl3](https://github.com/CarouselAether/rocm_exl3) | ROCm ExLlamaV3 fork with DFlash2/MTP, MoE and CPU-expert work. Primarily validated on gfx1151; gfx1100 build targets exist. Upstream v1.5.3 synchronization documented. **ROCm tensor parallel kernels are unavailable**; exposed generic TP CLI flags do not imply working AMD TP. | Research candidate. Its published speeds are not matching 7900 XTX measurements. Layer splitting would need validation before deployment. |
| [shisa-ai/hipEngine](https://github.com/shisa-ai/hipEngine) | HIP-native, Torch-free, OpenAI-compatible, gfx1100 support and existing GGUF reuse. W7900 48 GB Qwen Q4_K_M report: 30.8 decode, 39.7 with MTP. Single GPU per process; no multi-GPU inference. Its long-context DMS/INT8 modes do not support speculation. | Useful AMD-native design, but not a demonstrated faster dual-card replacement. Does not meet current placement policy. |
| [FreeToken AMD guide](https://github.com/FlashML-org/FreeToken/blob/main/docs/install_amd.md) | AMD support exists and is explicitly experimental. RDNA3/RDNA4 supported; NVIDIA acceleration integrations are CUDA-only and ROCm uses fallbacks. | Previously tested and explicitly retired locally for poor performance. Historical end-to-end measurements are in [retirement record](FREETOKEN-RETIRED-2026-10-18.md); they are not isolated decode or proof about every newer build. The [upstream AMD roadmap](https://github.com/FlashML-org/FreeToken/issues/541) still distinguishes passing RCCL collectives from future model-level TP. No reinstall authorized. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Current source includes draft-dflash/DFlash2 selection and HIP/Vulkan backends. Existing GGUF target can be reused; a matching GGUF drafter is needed. | Retained general-purpose dual-GPU engine. DFlash2 presence alone does not establish an advantage over current SGLang. |
| [NInfer](https://github.com/Neroued/ninfer) | Specialized C++/CUDA implementation; official upstream targets RTX 5090, with separate community Ampere/Ada forks. | No validated gfx1100 port found in this review. NVIDIA NVFP4 kernels do not become Radeon kernels by changing a flag. |

## Forum cross-check and practical priorities

The [lcz.me dual-XTX DFlash2 thread](https://lcz.me/topic/1640) is the strongest
matching hardware source. Its retained fork head is
[`f84475ccf593087df3d1da13c9e675eadee12352`](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352).
The [Level1Techs dual-R9700 discussion](https://forum.level1techs.com/t/dual-r9700s-amd-vllm-container-woes/250053?page=2)
is useful for ROCm serving and evolving speculative support, but R9700 is RDNA4;
it is not evidence of identical RX 7900 XTX performance. The
[Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396)
also does not establish a matching 1,000 tokens/s single-request Radeon result.

Keep Radeon-specific low-batch matmul, graph-compatible verification and prefix
reuse as priorities. The installed SGLang draft loader also reports that DFlash2
candidate selection falls back from CUDA FlashInfer to `torch.topk`; the source's
`_radix_topk` confirms that fallback. An AMD-native selector is a concrete profiling
lead, not a measured 2x local speedup or an applied patch. See the
[pinned selector implementation](https://github.com/StevenChenSE/sglang/blob/f84475ccf593087df3d1da13c9e675eadee12352/python/sglang/srt/models/dflash.py). Compare ordinary code/prose at the same sampling and context,
include a long prompt and tools, and inspect target/draft acceptance and VRAM
residency. Benchmark aggregate concurrency separately if throughput is the goal.
Do not enable FP8/FP4 paths merely because they accelerate a Blackwell/CDNA result;
RDNA3 kernel support and actual timing must be verified. More RAM benefits MoE
expert offload and staging but does not supply missing dense-model GPU kernels.

Research source heads inspected (not installed): phoenixhaxor `360c9025188810a0ac9d434c837dc3cb6b8e39cd`,
CarouselAether `5226de53a23fd5248658559b0eb876f6fc0c249a`, hipEngine
`52b087148234ea44edb207922581db23154ea1fe`, FreeToken
`fd410ee6165cdad0a29b00489c571e84c1e4c6c3`. A newer FreeToken revision is not
assumed to inherit or improve the retired build's local benchmark.
