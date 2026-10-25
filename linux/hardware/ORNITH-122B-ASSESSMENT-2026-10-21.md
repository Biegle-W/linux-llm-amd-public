# Ornith-1.5-122B hardware assessment — October 21, 2026

**Worth testing as a larger agent/coding model; not an established speed upgrade.**
The official Q4 is a plausible candidate with CPU expert backing and GPU hot
caching on both RX 7900 XTX cards. IQ3 requires less offload. Neither has been
loaded, benchmarked or added to DSH here. Ten production profiles and the Sage
test model remain unchanged. Only public cards/configs/file inventories and two
bounded 12 MiB GGUF prefixes were fetched; no complete checkpoint was downloaded.

## What it is and what the scores mean

[Publisher model card](https://huggingface.co/ornith-ai/Ornith-1.5-122B/tree/7681ef608624e7532d8164128bcffdbdbaf1b1af):
MIT-licensed reasoning/agent model with vision and tool calling. The publisher
reports SWE-bench Pro 76.9, Verified 84.5 and TerminalBench 2.1 81.2, using its
stated evaluation conditions. These are publisher results, not independent local
GGUF scores or an apples-to-apples comparison with our Sage smoke tests. The
[self-improvement methodology](https://ornith.ai/ornith_1_5.html) also involves
training tasks and scaffolds; putting weights behind DSH does not reproduce an
evaluation harness automatically. Reasoning tokens, complete-task time and tool
reliability matter alongside decode speed.

Pinned [config](https://huggingface.co/ornith-ai/Ornith-1.5-122B/blob/7681ef608624e7532d8164128bcffdbdbaf1b1af/config.json)
and GGUF directory inspection establish Qwen3.5-family `qwen35moe`: 48 ordinary
layers, 256 experts/eight selected per layer, hidden size3072, 12 full-attention
layers plus36 linear-attention layers, two KV heads/head dimension256, and one
MTP layer. Declared native context is262,144. That is not a locally tested window;
1M YaRN examples are context-extension proposals, not proof of local quality or
memory fit.

## Actual checkpoint sizes

File sizes are from pinned Hugging Face inventories; GiB means bytes/2^30.
Multi-file quants include every shard. These are storage sizes, not total runtime
memory. Projector is separate (approximately0.85GiB).

| Candidate | Checkpoint GiB | Assessment for 48GiB VRAM +61.51GiB OS-visible RAM |
|---|---:|---|
| Official Q4_K_M | 70.64 | Quality-oriented first candidate; substantial CPU backing required |
| Unsloth UD-Q4_K_XL | 74.24 | Larger mixed quant; no local quality/speed advantage established |
| Unsloth UD-Q3_K_XL | 55.66 | Middle-size alternative; also requires CPU backing |
| Unsloth UD-IQ3_XXS | 46.11 | Smaller first speed/memory candidate; still needs offload to preserve GPU reserves |
| Unsloth UD-Q2_K_XL | 41.48 | Smaller, but not the first quality-oriented choice |
| Official Q5_K_M | 82.62 | More pressure on host capacity/cache/desktop headroom; not the initial recommendation |
| Base BF16 safetensors | 232.99 | Exceeds combined installed RAM/VRAM even before overhead |

Sources: [official GGUF revision8d5893d7](https://huggingface.co/ornith-ai/Ornith-1.5-122B-GGUF/tree/8d5893d767c449a4f18dd08f4bb6d0d6d4426175),
[Unsloth revision3842d003](https://huggingface.co/unsloth/Ornith-1.5-122B-GGUF/tree/3842d003341507c216295c6f28dfcd30349925c6).
The card's generic single80GB-GPU statement cannot describe loading its base
BF16 checkpoint unchanged. Actual precision and overhead must be specified.

## Candidate configuration for this workstation

Start with retained llama.cpp4c3c5810/HIP7.2.3, both cards through layer split,
q8_0 KV, one slot and32K context. Preserve existing RAM/VRAM/no-swap guards;
log thermals throughout any future tests. Source explicitly recognizes the
[48-layer122B-A10B class and MTP tensors](https://github.com/ggml-org/llama.cpp/blob/4c3c5810f87efe177949f1b85ae509d38a2a311f/src/models/qwen35moe.cpp).
Architecture support does not prove that these exact weights load or that MTP
improves their speed.

Directory-derived planning examples, **not measured runtime allocations**:

| Quant | Ordinary expert layers backed by CPU | CPU expert GiB | Remaining GPU weight GiB | Initial aggregate GPU hot-cache candidate |
|---|---:|---:|---:|---:|
| Official Q4_K_M | 30, distributed across48 | 41.06 | 29.56 | 4GiB |
| Unsloth UD-IQ3_XXS | 20, distributed across48 | 16.08 | 30.03 | 4–6GiB |

The tensor totals include the MTP layer, which stays on GPU: Q4 head1.52GiB;
IQ3 head2.50GiB. The named files really contain layer48 tensors and
`nextn_predict_layers=1`; no separate MTP download is needed for those revisions.
Their different mixed precision means head size cannot be inferred from the
filename alone. The [numeric inspection](results/ornith-122b-assessment-2026-10-21.json)
retains exact tensor counts, bytes, layer lists and revisions. These are
header-derived facts; weight checksums and numerical correctness are unverified.

At32K, ordinary BF16 attention KV alone is approximately0.75GiB; q8_0 is about
0.40GiB. At256K these become6GiB/3.19GiB respectively. Add MTP KV, recurrent
states, compute buffers, hot-cache duplication, staging and per-card reserves.
RAM and VRAM are separate pools; adding their capacities is not a fit test.
The proposed Q4 host backing also needs loader/runtime/desktop headroom beyond
its41GiB. Check actual available RAM and both cards during loading; reduce cache
or placement only through a fresh validated candidate, never lower guards.

Compare MTP off versus MTP3 on matching workloads before selecting. Test tools,
JSON/SSE, thinking controls and real agent tasks, then near-window/history and
normal launcher/API behavior. Increase32K only after memory and retrieval gates.
No tokens/s forecast, maximum usable context or quant-quality winner is claimed.
Q4 involves more expert data and CPU work than Sage; it should be evaluated for
completed-task quality and time rather than assumed to match Sage's83t/s decode.

vLLM/SGLang may support the architecture, but neither the BF16 nor FP8 base fits
this VRAM allocation as a normal GPU-resident target. Their architecture support
is not evidence of the required CPU-expert/hot-cache GGUF path. MLX/NVFP4 recipes
are not interchangeable with this Linux HIP GGUF setup. Strata and Maya have no
locally validated Ornith profile; do not replace their selected model packs.
No ROCm upgrade is needed merely to investigate the candidate.

## Community evidence and remaining uncertainty

Searches on both forums found no matched Ornith122B/dual7900XTX/64GB result.
[lcz topic1382](https://lcz.me/topic/1382/12), accessed October21 (exact dates not
exposed), contains conflicting35B-family anecdotes: Xiyu Caoying reports dual6800XT/
llama.cpp-turboquant-hip around51t/s, while others discuss quant-dependent tool
quality. Quant/context/workload are incomplete; do not transfer that rate to122B.
[Level1Techs post7](https://forum.level1techs.com/t/one-week-of-local-ai-on-strix-halo/254086/7),
lhl,August23,2026, discusses gfx1100/gfx1151 engines and Ornith35B agent evaluation
in a Strix-Halo thread. It is not a dual-XTX122B result. The
[source ledger](FORUM-OPTIMIZATION-SOURCES.md) keeps these reports separate from
locally inspected metadata and future runtime measurements.

**Recommendation:** test official Q4_K_M first if larger-model quality is the
goal; use UD-IQ3_XXS as the smaller comparison if Q4's offload cost is excessive.
Prefer the already-tested Sage as a baseline with known speed until Ornith has real
quality/time-to-answer measurements. No download or deployment is started by
this research recommendation.
