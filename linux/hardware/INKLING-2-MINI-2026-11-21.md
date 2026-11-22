# Inkling 2 Mini on llama.cpp — November 21, 2026

The owner asked for the backend to be updated so the server can run Thinking Machines' Inkling 2 Mini (released November 20). Production llama.cpp was updated to an upstream revision that supports the model, and the model was added as the hub route `inkling-2-mini-q8`. Every figure below is from a short guarded check or the 216-item suite; none is a sustained benchmark.

## Result

| | |
|---|---|
| Route | `inkling-2-mini-q8`, llama.cpp `19bc41dbb41e`, both cards, 131,072-token context |
| File | Unsloth `Inkling-2-Mini-UD-Q8_K_XL`, upstream ("Mainline_Support") layout, 22.9 GB; original 4-bit expert weights, the rest in BF16 |
| Strict tool check | passed three times out of three (bare marker) |
| Decode | 25.9 tok/s on the tool-check answer; 26.7 tok/s on a 400-token answer |
| Prompt read | 615 tok/s (7,594-token tool prompt, cold) |
| Load | 49 s |
| VRAM | 9.2 GB on the display card, 20.2 GB on the second card, flat under load |
| Public suite | 149 of 216 (69.0%, 95% interval 62.5–74.8%); 45 answers cut off by the token limit |

On this suite the model does not beat the Qwen3.8 routes here (151 to 169). It reasons before every answer even at reasoning effort `none`, and 45 answers ran into the suite's 2,048–4,096-token limit and were scored wrong, so 149 is a lower bound, as with Ripple. By category: code 8 of 20, instructions 26 of 32, knowledge 41 of 60, math 33 of 40, reasoning 19 of 32, tools 22 of 32. The vendor's own comparison against Qwen3.8-27B uses software-engineering benchmarks that this suite does not contain.

## What changed

1. **llama.cpp `9581154a2250` → `19bc41dbb41e` (159 commits).** Researched before install. Relevant: support for the looped Inkling 2 Mini layout and its fix (merged November 20 and 21), automatic handling of per-expert scale tensors, a fix for a NaN that could persist in recurrent state, a 64-bit offset fix in the quantized matrix multiply, a rewritten expert-selection kernel (no RX 7900 figures upstream), and server fixes. Pre-flight on both cards: the backend op tests for the gated-delta and expert matrix-multiply ops passed (84 of 84 and 1,077 of 1,077), including the case that fails in upstream's CI on another Radeon. Guarded install: `empero` loaded in 47 s, tool steps 2.5 s and 0.3 s, unchanged. Promoted.
2. **Route `inkling-2-mini-q8`.** All 48 layer passes run on the second card. The four large expert blocks (20–23) and the output layer sit on the display card, which leaves about 4 GB free on the second card at 131,072 tokens of context. KV cache is f16; quantized KV is unmeasured for this model. Sampling follows the vendor (temperature 1.0, top-p 1.0, top-k 0, min-p 0). Vision is not enabled.
3. **Placement guard.** A VRAM-only plan may now declare its own two-card layout (card order, split, on-card tensor placement). It must still name both cards and may never place a tensor on the CPU; every other preset check is unchanged.
4. **Graph capture off for this route.** New per-model list `no_graph_models` in the llama runtime settings sets `GGML_CUDA_DISABLE_GRAPHS=1` for the listed model only.

## The memory growth, and the earlier crash

With graph capture on (llama.cpp's default), VRAM on the card running the model rose about 22 MiB per minute under load and never fell: 20.2 GB at load, 23.3 GB at the end of the 136-minute suite. The cause is in the ROCm 7.2.3 runtime: every time llama.cpp updates a captured graph (each 256 tokens of position and each request), the runtime allocates fresh kernel-argument memory on the card and frees it only when the graph is destroyed. Inkling's graph is several times larger than a normal model's, so the growth is fast enough to matter. This very likely also explains the crash in the first trial that morning (the rate matches): one card, about 1 GB free, and the server died after 47 minutes with a null-pointer fault inside the ROCm runtime.

Confirmed on the server with the same 17 requests each time:

| Setting | VRAM growth over the 17 requests | Decode tok/s |
|---|---:|---:|
| Default (graph capture on) | +343 MiB at the peak | 30.8 |
| `GGML_CUDA_DISABLE_GRAPHS=1` | +18 MiB, all in the first requests | 26.8 |
| ROCm packet capture off (`DEBUG_CLR_GRAPH_PACKET_CAPTURE=0`) | +18 MiB | 26.7 |

Both switches stop the growth and cost the same 13% of decode speed. The route uses llama.cpp's own switch. Through the hub with the switch on: 20,180 → 20,186 MiB across the same requests. ROCm.s development branch is reported to carry a fix; 7.2.3 does not. The `empero` route keeps graph capture on; its graph is much smaller and its growth was not measured.

The suite was run before the switch was added, at the 30 tok/s setting. The switch changes speed, not the computation, so the score was not rerun.

## Not done

- **Unsloth's own llama.cpp build and its DSpark drafter were not installed.** The release tag does not contain the code that the binaries were built from; it is assembled by CI from about 30 pull requests, most of them unreviewed, and its drafter revision has since been rewritten upstream. It also reads only Unsloth's own file layout. Upstream's drafter support is still under review.
- **No 4-bit file was downloaded.** The 8-bit file fits with the two-card layout.
- An RX 7900 XTX owner reports 64 tok/s from a private, unreviewed branch of llama.cpp; not tested.
- Strict gate note: `empero` answered with the correct marker in all six checks that day, and wrapped it in a sentence in two of them, which the strict gate counts as a failure. The requests were identical apart from the marker; the route samples at temperature 0.6.

Evidence: `hardware/generated/daily-update/2026-11-21T-inkling/` and `2026-11-21T-inkling-gate*/` (not in Git), and [results](results/inkling-2-mini-2026-11-21.json).
