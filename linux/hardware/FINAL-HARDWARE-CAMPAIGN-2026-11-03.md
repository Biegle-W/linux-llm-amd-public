# Final-hardware restoration and benchmark campaign — November 3, 2026

**Authorized and in progress; the full catalog has not yet been restored or benchmarked.** The owner confirmed this as the final hardware and requested all paused LLM routes restored, all engines updated, standard LLM/diffusion benchmarks, and current forum research. This explicitly authorizes this campaign beyond the earlier short-check-only scope. Retired models remain retired. Existing memory, spill, thermal and owned-process guards remain; the paused recurring updater has not been resumed.

## Hardware and method

The installed platform is an i5-13600KF (six P cores/eight E cores, 20 logical CPUs), ASUS TX GAMING B760M WIFI, 61.55 GiB OS-visible RAM and two RX 7900 XTX 24 GB GPUs behind the owner-confirmed PEX88096. Existing scoped ACS/identity-domain configuration remains. No BIOS, kernel, system driver or firmware change is made by preparation.

The selected standard scope is one short tool check per LLM route, excluded warmups and three repeated code/prose speed and fresh prefill probes using the shared benchmark method; fixed image/video workflows use matching prompts, dimensions, steps and seeds. Cold load and warm execution are recorded separately. Workloads run sequentially, with owned unload and GPU ownership checks before switching. Results from the earlier 32 GB platform remain historical. New CPU-heavy build activity is excluded from timed GPU/CPU-offload comparisons. Some retained profiles still use 24 threads from the previous CPU; 14/20-thread choices need measurement rather than a universal tuning claim.

Twelve maintained/queued LLM routes are in scope: Empero and Flint/HIP llama; Ornith/HIP llama; retained Super INT4/vLLM replacement; Qwen27B/SGLang and vLLM; Bolt and Sage/vLLM; GLM/Maya; DeepSeek Q1/Maya and Strata; and Qwen Flash Next/Strata. Deleted Super IQ3 and other intentionally retired variants are excluded. Diffusion covers the retained Qwen-Image 2.1, H3 and FLUX 3 Klein families through fixed normal workflows, including the applicable edit/video paths.

## Preparation checkpoint

- Latest llama.cpp `0ef27309b78d054832e44a95a6fb9314d4b7363c` built in isolation; not installed or GPU-qualified yet.
- Maya 1.1.51 `3a47bbe8883f61ed4724d4b43f9dd46f7703a733` is building; both Strata components queue source `ffa80d73133ea5c548aefe57889a16e8085a938f` (0.2.10). Builds remain separate from production.
- ComfyUI 0.43.0 `ab08f7b2caa6d4007ecde3762116c6193613f43b` and its required frontend/node dependencies are staged; dependency consistency passes. The existing ROCm Torch stack is retained during this engine comparison. Generation qualification and promotion are pending.
- The current gfx1100 SGLang fork is at its latest branch head. Official 0.5.23's AOT setup explicitly exits for gfx1100; it is not a drop-in supported upgrade. Existing local fixes are preserved.
- The installed vLLM ROCm 7.2 wheel is current on that channel. Newer official releases/wheel families and the updated RDNA3 fork require compatibility review; a newer package number is not a passing hardware qualification.
- Latest Unsloth DeepSeek Q1_S source `2688c0c3c2c3b052ec4f6d10a8417b0ef7ee4eba` is downloading with per-shard SHA-256 checks. Five shards total 232,979,608,420 bytes. Header inspection identifies about 110.60 GB of PLE/Engram tables, 115.23 GB routed experts and 7.15 GB other payload; these are file totals, not RAM requirements. Conversion can use metadata packs without duplicating weights. Both engine packs and actual capacity/quality remain pending.
- An explicit **unselected** 64 GB Q1 cache tier adds sealed 42/44 GiB worker limits, a 60 GiB physical minimum, 47 GiB available-RAM admission (44 GiB cap plus 3 GiB reserve), 28 GB native expert warm cap and 1,024 MB Engram cache. Legacy tiers and all profile files remain unchanged. Thirty-two CPU admission/regression checks pass. Native format/parity checks and guarded measurements are required before selecting the new tier.

The earlier isolated RCCL candidate proved disabled-P2P shared-memory collectives and reduced 4K target-only SGLang initialization. It remains separate from the installed library. Full DFlash, generation and production qualification are still pending; the original bus-loss cause is not established. Failed candidates will retain evidence and rollback rather than be reported as upgraded.

## Current research leads

Firsthand [dual-XTX tensor/MTP measurements](https://www.reddit.com/r/ROCm/comments/1vtoux9/qwen3827b_on_llamacpp_tensor_mtp_on_dual_7900_xtx/) show a dense-Qwen decode gain with prefill/context tradeoffs. They do not establish the best split for every cached/offloaded MoE route. A separate [reproducible XTX backend study](https://github.com/hcgdw/rx-7900-xtx-llm-benchmark) reports workload-dependent ROCm/Vulkan and rocWMMA behavior, supporting matched local comparisons rather than a blanket backend switch.

[AMD's SGLang support tracking](https://github.com/sgl-project/sglang/issues/30599) distinguishes kernel enablement from working serving on consumer RDNA3. The [dual-Radeon RCCL investigation](https://github.com/cadamcat/dual-radeon-vllm) supplies source and reproducible hostcall/transport evidence; the separate local P2P-override fix remains a control correction, not an established SGLang crash remedy.

A [firsthand ComfyUI stability report](https://www.reddit.com/r/comfyui/comments/1v2iq0e/three_7900_xtx_comfyui_pitfalls_that_cost_me_a/) describes a hipBLASLt fallback on its system. An [H3/XTX discussion](https://www.reddit.com/r/StableDiffusion/comments/1vh51yv/can_amd_7900xtx_smoothly_run_minimax_h3_too/) reports separate T2V and frame-conditioned outcomes. These are leads with stack/workload limits, not locally measured results or grounds to weaken guards. Final recommendations will follow this machine's measured correctness, latency, throughput and resource evidence.

## Remaining work

Complete source/weight preparation; verify updated kernels and format support; qualify supported engine candidates with rollback; restore each paused route after admission and tool checks; run the standard sequential LLM and fixed diffusion benchmarks; publish per-route outcomes and exact remaining blockers. No whole-catalog success, latest-engine promotion or fastest-setup claim is made at this checkpoint.
