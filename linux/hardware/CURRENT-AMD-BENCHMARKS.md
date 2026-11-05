# Current AMD results — November 5, 2026

**13 qualified normal routes are enabled.** Read the [runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) for exact selections and safeguards.

[Current model/graphics timings, realistic-budget retries and all downloaded asset groups](REALISTIC-LARGE-MODELS-2026-11-05.md) · [Curated numeric results](results/REALISTIC-LARGE-MODELS-2026-11-05.json).

[All13 short native decode statistics](AMD-DECODE-EVIDENCE-2026-11-05.md) · [New four-route native probes and three failed-model removals](AMD-NATIVE-DECODE-TESTS-2026-11-05.md). A sustained matched13-route benchmark remains missing.

Four native large-model retries passed after removing the three-second decode cutoff. Maya c167 passed all three selected profiles through the guarded updater. Llama9c9074 passed and is selected for all three llama routes. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected. Fresh owner-requested latest-guard attempts ended before inference: Flint AWQ requires unavailable FlashInfer; PLE stopped on the six-second heartbeat guard; Super stopped below the 1 GiB host reserve. PLE missed its 15-second KFD drain deadline, then drained later; that failed result remains recorded. None was promoted. The unused Strata DFlash2 source/packs were removed after pinned-hash and dependency verification; the separate SGLang drafter and all 13 selected routes remain unchanged. Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The RDNA3 fork at2314df4 built and passed native/CLI audits, but its Qwen startup warm-up failed on missing `CommonAttentionMetadata._seq_lens_cpu` before any request. The exact case is final; the fork remains isolated and unpromoted. The existing 03:00 timer is restored without catch-up. The unused Strata DFlash2 auxiliary and the explicitly named failed FlintAWQ/FP8PLE/SuperINT4 downloads were removed by owner request. 111 targeted CPU checks pass; short tests do not qualify full-window quality or sustained throughput.

[RDNA3/Radiance and true dual-card research](RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md): current gfx1100 backend coverage does not establish optimized dual-XTX TP. Existing LLM TP2, layer splitting, normal graphics component placement and isolated cached-conditioning H3 TP2 remain distinct.

[New Strata 0.2.11 Unsloth test](STRATA-0211-UNSLOTH-2026-11-05.md): Strata 0.2.11/engine+Control 0.1.57 with the already downloaded Unsloth V3.1 IQ3_XXS passed the strict tool test and completed6 quality fixtures (5/6) plus3 short timing prompts (median native 52.895 tokens/s). Owned cleanup passed with zero recorded swap/spill; production GSQ/source selections remain unchanged.

[Fresh candidate outcomes](CANDIDATE-RETESTS-2026-11-05.md) · [Numeric candidate outcomes](results/CANDIDATE-RETESTS-2026-11-05.json).

Prior evidence: [27-case campaign](ALL-MODEL-P2P-2026-11-05.md), [numeric cases](results/ALL-MODEL-P2P-2026-11-05.json), [media gallery](../graphics/results/p2p-2026-11-05/README.md), [matched Unsloth/Flint comparisons](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md). These were completed before the current update task. Use the [benchmark history](BENCHMARK-HISTORY.md) for older hardware/source/workload records.
