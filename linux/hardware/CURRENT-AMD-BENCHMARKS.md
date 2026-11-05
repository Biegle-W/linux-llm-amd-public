# Current AMD results — November 5, 2026

**13 qualified normal routes are enabled.** Read the [runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) for exact selections and safeguards.

[Current model/graphics timings, realistic-budget retries and all downloaded asset groups](REALISTIC-LARGE-MODELS-2026-11-05.md) · [Curated numeric results](results/REALISTIC-LARGE-MODELS-2026-11-05.json).

Four native large-model retries passed after removing the three-second decode cutoff. Maya c167 passed all three selected profiles through the guarded updater. Llama9c9074 passed and is selected for all three llama routes. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected. PLE stopped during loading on the unchanged heartbeat guard, with clean owned teardown and no promotion. Super also stopped during loading under that guard, with clean owned cleanup and no promotion. Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The corrected isolated RDNA3 CPU build is running with matching MIOpen and hipSPARSELt7.2.3 dependency overlays; runtime qualification remains pending and no production promotion occurred. The existing 03:00 timer is restored without catch-up. Nothing was deleted. 111 targeted CPU checks pass; short tests do not qualify full-window quality or sustained throughput.

[RDNA3/Radiance and true dual-card research](RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md): current gfx1100 backend coverage does not establish optimized dual-XTX TP. Existing LLM TP2, layer splitting, normal graphics component placement and isolated cached-conditioning H3 TP2 remain distinct.

Prior evidence: [27-case campaign](ALL-MODEL-P2P-2026-11-05.md), [numeric cases](results/ALL-MODEL-P2P-2026-11-05.json), [media gallery](../graphics/results/p2p-2026-11-05/README.md), [matched Unsloth/Flint comparisons](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md). These were completed before the current update task. Use the [benchmark history](BENCHMARK-HISTORY.md) for older hardware/source/workload records.
