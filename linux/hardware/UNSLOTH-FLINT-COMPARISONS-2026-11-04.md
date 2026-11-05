# Unsloth IQ3 and Flint Mix-24G comparisons

A1 and A2 are current-weight controls; B is the candidate. Two isolated A1 → B → A2 comparisons used the current pinned engines and retained guards. The selected production models remain unchanged. These are short local probes, with one bracket per comparison; they are not broad benchmark scores or sustained stability qualifications.

| Run | Load (s) | Strict tool | Local quality | Median speed TTFT (s) | Native decode (tokens/s) | Client estimate (tokens/s) |
|---|---:|---|---:|---:|---:|---:|
| gsq-a1 | 69.335 | Pass | 5/6 | 0.518 | 55.944 | 56.103 |
| unsloth-b | 75.590 | Pass | 5/6 | 0.563 | 52.481 | 52.630 |
| gsq-a2 | 71.081 | Pass | 5/6 | 0.588 | 56.042 | 34.347 |
| flint-a1 | 15.757 | Pass | 6/6 | 0.105 | 65.690 | 65.923 |
| flint-b | 17.038 | Pass | 5/6 | 0.102 | 61.693 | 61.893 |
| flint-a2 | 17.275 | Pass | 6/6 | 0.106 | 65.792 | 66.014 |

Qwen result: all three runs passed the strict tool check and scored 5/6, each missing the same arithmetic fixture. Native speed medians were approximately 55.9 and 56.0 tokens/s for GSQ controls and 52.5 for Unsloth (about 6% lower in this small sample). Candidate loading took 75.590 s versus 69.335/71.081 s. The candidate adds about 10.3% GGUF storage without a fixture-quality gain here; retain the current GSQ selection. These measurements do not establish broad quality equivalence.

Each run used the same six fixed quality cases (JSON arithmetic, Python, SQL, logic, retrieval and history) and three fixed speed prompts within its bracket. Quality is fixture correctness, not a general model ranking. Prompt hashes, actual token counts and individual timings are in the numeric evidence. Client decode estimates use `(completion_tokens−1)/(last emitted token−first emitted token)` and can reflect SSE batching; they are not native prefill rates. Loading is excluded from request TTFT. OS page caches were not deliberately cleared; loading times describe these bracket runs rather than controlled cold-cache measurements. Flint native timings use the engine-provided predicted_per_second value from each final SSE record; the reported generated-token counts are checked against API completion counts. Its native rate excludes the first generated token, while Qwen uses the engine’s generated-token count divided by its logged decode time. Its visible-answer latency is recorded separately from first-emitted-token latency because reasoning is enabled. Output caps and reasoning differ between the Qwen and Flint brackets, so their throughput figures are not a controlled cross-family ranking. Qwen native decode is generated tokens divided by the engine’s logged decode milliseconds; every native entry is matched in request order and checked against the API token counts. Client measurements include collection/delivery overhead. The GSQ return run had stable native throughput despite substantially lower client estimates, so client throughput alone is unsuitable for ranking this bracket.

The Qwen bracket kept the same Strata engine, MTP module, expert profile, 26-layer split, 256K configured context, 32K resident INT8 KV, 12 GiB resident expert budget, tokenizer and template. Both model copies were on the same NVMe drive; the original GSQ files were untouched. Unsloth’s four GGUF shards total 83,626,438,426 bytes, versus 75,839,998,528 bytes for the current GSQ GGUFs. All source files and the control copy passed SHA-256 verification. The candidate pack retains original expert and PLE-table bytes. Its standard compatibility conversions include 196 rounded tensors (195 BF16 compatibility conversions plus one loader F32→F16 narrowing); the packer reports maximum absolute conversion error 0.0204. Those conversions are a qualification limit, not a claim of fully bit-identical projections. All four selected routed expert format pairs and Q6_K/Q8_0 dense diagnostics passed on both cards.

The Flint bracket kept the current llama.cpp engine, dual AMD layer split 1:1, 32K configured context, Q8_0 KV, Flash Attention, DIO loading, 4096 batch/ubatch, zero CPU experts and reasoning budget 128. Both weights used the same NVMe drive. Raw headers differ in optional clean_spaces and eog_token_ids metadata; the pinned engine defaults and derives these equivalently. The loaded EOG sets and four fixed tokenize/detokenize probes must match before inference. Scoped log verbosity 4 is common to both arms to capture those diagnostics. An earlier control loaded but stopped before any inference because default verbosity 3 omitted EOG details; that instrumentation failure and its clean unload are retained separately and excluded from timed inference results. The abliterated candidate changes the weights and quantization; these tests cannot isolate abliteration from quantization or establish refusal behavior. Speed requests allow up to 384 total generated tokens so reasoning and visible answers fit; actual counts and answer completion are recorded. No full-32K retrieval qualification is inferred from configuration alone.

Flint result: the current UD-Q4_K_XL controls passed the strict tool test and all six fixtures, with native medians 65.690/65.792 tokens/s. Mix-24G passed the tool test but scored 5/6 and 61.693 tokens/s (about 6.2% lower). Its arithmetic values were correct; the JSON-only fixture failed because it added explanatory prose before the JSON. Mix-24G uses 23,993,808,416 bytes versus 25,054,688,704 bytes for the current GGUF, saving 1,060,880,288 bytes (about 4.2%). This sample supports retaining the current Flint selection; it does not isolate the effects of abliteration versus quantization.

| Run | Minimum available RAM (GiB) | Minimum per-card free VRAM (GiB) | Maximum owned swap (GiB) | CPU sampled peak (°C) | Thermal samples / largest gap (s) |
|---|---:|---|---:|---:|---|
| gsq-a1 | 49.231 | 0.577 / 1.790 | 0.000 | 69.000 | 408 / 0.396 |
| unsloth-b | 42.182 | 0.550 / 0.969 | 0.000 | 75.000 | 470 / 0.481 |
| gsq-a2 | 49.234 | 0.577 / 1.789 | 0.000 | 68.000 | 415 / 0.475 |
| flint-a1 | 56.956 | 9.673 / 11.220 | 0.000 | 61.000 | 201 / 0.349 |
| flint-b | 56.886 | 10.956 / 10.855 | 0.000 | 60.000 | 219 / 0.370 |
| flint-a2 | 56.961 | 9.674 / 11.221 | 0.000 | 62.000 | 209 / 0.449 |

GPU edge/junction/memory sampled peaks and sample coverage are recorded per run in the numeric evidence. Sampled peaks are not continuous physical maxima; raw SMU throttle flags are not treated as proof of current overheating or measured speed loss.

All attempts retained 100°C CPU/GPU/SSD software ceilings, independent hardware/SMART protections, 1 GiB available RAM and 128 MiB free VRAM per card, zero dedicated spill, current swap policy, equal isolated memory high/hard caps, six-second heartbeat, three-second decode-stall, 30-second output-from-first-token, 20-second idle and 15-second owned cleanup limits. There was no separate TTFT cutoff; 210-second loading and 240-second model stage budgets remained. Heavy transfers, packing and GPU stages were serialized.

Final verification found empty owned scopes and KFD, preserved runtime/source/profile/schedule files and service states, retained the fault hold and historical STOP files, and no new kernel fault-pattern matches. Verified temporary byte-identical control copies were removed after final checks; original models, downloaded candidates, their packs and private evidence were retained. The stock persistent boot default remains. No PLE/Super retry, model promotion, service change or schedule change was made.

Sources: [pinned Unsloth GGUF](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/tree/d96201194f103c906994f283f504209dc8d2a10c), [pinned Flint Mix-24G](https://huggingface.co/orcarouter/Flint-abliterated-GGUF/tree/4d618d1cb1d7782d4b08762fb664487bf5e4d3c4), [Strata source](https://github.com/Niko1221/Strata/tree/ffa80d73133ea5c548aefe57889a16e8085a938f), [llama.cpp source](https://github.com/ggml-org/llama.cpp/commit/0ef27309b78d054832e44a95a6fb9314d4b7363c).

[Curated numeric evidence](results/unsloth-flint-comparisons-2026-11-04.json).

Boot verification limit: the readable final GRUB drop-in still selects stock, the one-shot entry is empty, and the generated GRUB timestamp predates these comparisons. A fresh content read of the administrator-only generated file was unavailable because noninteractive sudo required authentication; no boot configuration was modified.
