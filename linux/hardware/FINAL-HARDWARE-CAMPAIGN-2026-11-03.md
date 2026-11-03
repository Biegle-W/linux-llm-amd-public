# Final-hardware restoration and benchmark campaign — November 3, 2026

**Authorized and in progress; the full catalog has not yet been restored or benchmarked.** The owner confirmed this as the final hardware and requested all paused LLM routes restored, all engines updated, standard LLM/diffusion benchmarks, and current forum research. This explicitly authorizes this campaign beyond the earlier short-check-only scope. Retired models remain retired. Existing memory, spill, thermal and owned-process guards remain; the paused recurring updater has not been resumed.

## Hardware and method

The installed platform is an i5-13600KF (six P cores/eight E cores, 20 logical CPUs), ASUS TX GAMING B760M WIFI, 61.55 GiB OS-visible RAM and two RX 7900 XTX 24 GB GPUs behind the owner-confirmed PEX88096. Existing scoped ACS/identity-domain configuration remains. No BIOS, kernel, system driver or firmware change is made by preparation.

The selected standard scope is one short tool check per LLM route, excluded warmups and three repeated code/prose speed and fresh prefill probes using the shared benchmark method; fixed image/video workflows use matching prompts, dimensions, steps and seeds. Cold load and warm execution are recorded separately. Workloads run sequentially, with owned unload and GPU ownership checks before switching. Results from the earlier 32 GB platform remain historical. New CPU-heavy build activity is excluded from timed GPU/CPU-offload comparisons. Some retained profiles still use 24 threads from the previous CPU; 14/20-thread choices need measurement rather than a universal tuning claim.

Twelve maintained/queued LLM routes are in scope: Empero and Flint/HIP llama; Ornith/HIP llama; retained Super INT4/vLLM replacement; Qwen27B/SGLang and vLLM; Bolt and Sage/vLLM; GLM/Maya; DeepSeek Q1/Maya and Strata; and Qwen Flash Next/Strata. Deleted Super IQ3 and other intentionally retired variants are excluded. Diffusion covers the retained Qwen-Image 2.1, H3 and FLUX 3 Klein families through fixed normal workflows, including the applicable edit/video paths.

## Preparation checkpoint

- Latest llama.cpp `0ef27309b78d054832e44a95a6fb9314d4b7363c` built in isolation; not installed or GPU-qualified yet.
- Maya 1.1.51 `3a47bbe8883f61ed4724d4b43f9dd46f7703a733` and both Strata components at `ffa80d73133ea5c548aefe57889a16e8085a938f` (0.2.10) built in isolation. The DeepSeek local test adapter needed a test-only kernel-symbol rename for a new header definition; no engine objects, mathematical code or tolerances were changed. All remain separate from production.
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

## Llama production baselines completed

These are **old-runtime baselines before the new llama.cpp candidate**, at source `eb4e244be77a906a183cd4a00fd51d9ad3200955` on the final hardware. They are not new-engine or full-catalog results.

| Route | Median code decode | Median prose decode | Fresh retrieval probes |
|---|---:|---:|---:|
| Empero | 160.84 tokens/s | 102.26 tokens/s | 3/3 pass |
| Flint | 71.98 tokens/s | 71.64 tokens/s | 3/3 pass |

The shared method excludes workload warmups and retains three timed code/prose trials plus three fresh approximately8K marker probes. The owned campaign download was frozen during timing and thawed afterward. The outer guard recorded zero owned swap/spill and no new GPU/bus/OOM fault; owned cgroups emptied, KFD clients were absent and the reservation was released. Candidate comparison and promotion remain pending. [Curated baseline record](results/final-hardware-baseline-2026-11-03.json).

## Additional qualification evidence and blockers

Maya's established per-card gate ran36cases:34passed, while the known fused-prefill case failed on each card. That path remains disabled and is not claimed qualified. Five native CPU format/path/RAM/pack/IQ tests also passed. The latest separate Strata DeepSeek API suite ran 64 tests: 63 passed and one real-tokenizer test was skipped pending the restored pack.

The broad DeepSeek GPU gate failed **IQ3_XXS WMMA-versus-scalar output:3.14e-3 against the unchanged3e-3 tolerance**, on both cards; the two devices were bit-identical and no GPU/bus fault occurred. Broad promotion is held. Exact header review shows the selected Unsloth Q1 uses IQ1_S and IQ2_XXS, including IQ1_S gate/up with IQ2_XXS down. That exact mixed-format path still needs its own validation; the unselected IQ3 failure is retained and no tolerance is relaxed.

A newer vLLM `0.33.0rc1.dev573+g40941f2c4.rocm100` is now dependency-staged for gfx1100 only, with matching Torch2.13.0/ROCm10.0.0 and Triton3.8. Its228packages pass dependency consistency. It is neither selected nor GPU-qualified, and system drivers are unchanged. Its SDK uses external `.kpack` device images, so RCCL/device-image and runtime-isolation preflights are pending before a guarded GPU probe. The supported gfx1100 SGLang fork, selected runtimes and paused model profiles remain unchanged at this checkpoint.

## November 3 qualified llama split and Q1 progress

Flint now uses global llama.cpp `0ef27309b78d`. Its standard comparison and strict DSH read-tool round trip pass. Empero retains independent `eb4e244be77a` code: the newer candidate completed the read tool and two model steps but added explanatory text/code fences to the required marker-only final answer. That strict failure is retained. Ornith's independent old pin and pause remain pending its restoration qualification.

| Route | Baseline code / prose | Candidate code / prose | Fresh probes | Strict DSH result | Selection |
|---|---:|---:|---:|---|---|
| Empero | 160.84 / 102.26 t/s | 160.83 / 104.90 t/s | 3/3 | Final-format failure; tool completed | Prior source held |
| Flint | 71.98 / 71.64 t/s | 72.62 / 72.18 t/s | 3/3 | Pass | Latest source |

Both candidates pass the unchanged shared-method speed/retrieval and complete native lifecycle gates. A final supervisor empty-scope race triggered rollback after the complete candidate record; the saved results were reused after correcting that race. A compiler internal error at eight jobs was followed by a successful two-job build. No successful GPU benchmark was repeated. Controlled split activation passes; the old Empero library cohort is verified, its code/constants/device images are unchanged after localizing library search paths, and owned scopes/KFD clients/reservation are clear. No new GPU fault or owned swap/spill was observed. Sampled thermal coverage and limits are in the [curated progress record](results/final-hardware-progress-2026-11-03.json).

All five Unsloth Q1 backing shards are now fully hash-verified. Two metadata-only packs reference the same232,979,608,420-byte GGUF payload. Maya's selected Q1 tests pass on both cards, including IQ4_NL Engram, Q5_K/Q6_K dense tensors and the exact IQ1_S/IQ2_XXS role combinations. Strata's corresponding selected tests also pass. A newly added K-quant fixture initially placed scales at the wrong offsets, producingNaNs in both GPU and reference; legal test data corrected from upstreamMaya/GGML passes with unchanged engine math and thresholds. The earlier unselectedIQ3_XXS numerical failure remains. These are format/kernel results: model capacity, explicit admission, normal tools and restored-profile benchmarks remain pending.

The staged ROCm10 vLLM's stock RCCL archive has37gfx1100 device images and13hidden-hostcall declarations; required PyTorch exports are present. A matchingSDK10 RCCL build is in progress, preserving explicit user P2P controls and NDEBUG in all191compilecommands. It is unselected and has not been GPU-tested. Maya GLM comparison and the rest of the restoration/LLM/diffusion campaign continue; the recurring updater remains paused.

### Additional research decisions

- [vLLM Engram source](https://github.com/vllm-project/vllm/blob/main/vllm/config/engram.py): the exact staged validator restricts `disk_offload` to Qwen4Exp on CUDA; it does not admit the AMD DeepSeek route.
- [LSA paper](https://arxiv.org/abs/2610.42147): the headline speedups concern an attention layer at ultra-long context; the proposed variants require distillation or native training. AMD whole-engine performance is unverified here.
- [tandem.cpp](https://github.com/ewhacc/tandem.cpp): its documented CUDA-tested path is a research lead, not an AMD runtime selection.
- [AtomicChat GSQ-RCO](https://huggingface.co/AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF):121/138/155GB backbones also require shared110GBEngram; total sizes are231/249/266GB. Its modified-weight and limited benchmark claims do not establish universal zero refusals or zero quality loss.
- [GSQ-RCO Coder](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF): it removes half the routed experts; its effective1.05bpw uses the original transformer denominator.72.12GB backbone plus110.60GBEngram is182.72GB on disk. It remains a separate optional model, not a replacement for the completed Q1 restoration.

## November 3 Maya fault containment and revised queue

The old production Maya GLM baseline (`cbaaec5d70fd`) stalled at 62 of 256 warmup tokens, then encountered MES queue removal failure, SMU nonresponse and a failed reset sequence. The latest Maya candidate was never installed. This is a failed baseline, with no comparative pass or speed result. The guard reported no owned OOM/swap/spill trigger; the underlying cause is unresolved.

All campaign GPU work is stopped. GLM is disabled with an explicit owner-instruction requirement for resumption, and a persistent GPU fault reservation remains latched. No retry, framework GPU import, communicator probe, manual reset or automatic reboot is authorized by this checkpoint. Existing independent holds, rollback, guards and recurring updater pause remain.

Read-only boot-journal audit confirms a restart at 14:32 UTC (09:32 Toronto), after the 12:50 UTC Maya fault. The hold was created after this restart; matching its boot identifier does not prove the machine remained on the fault boot. No KFD compute clients or matching new kernel fault signatures were observed in the current boot. These observations alone do not qualify recovery or authorize a GPU workload.

The CPU-only ROCm10 RCCL build was interrupted: its scope is inactive, recorded controller/worker processes are absent, the stale job record says building, and the log ends at 513/1925 with no completed library. Existing Ninja outputs are preserved. An incremental CPU-only continuation needs an ownership audit and a distinct continuation record, never deletion of the old record or a duplicate build.

Completed llama comparisons, independent Empero/Ornith selections, all five Q1 shard hashes, both metadata packs and selected Q1 kernel gates remain valid completed evidence and must not be repeated for documentation. Q1 admission/capacity/tools/profile benchmarks remain pending; the unselected Strata IQ3 numerical failure remains recorded.

After crash containment and verified readiness, the owner's new priority is:

1. Strata 0.2.10 Qwen DFlash2 versus MTP versus Off on the dual-XTX/64 GB system.
2. vLLM disk-backed PLE eligibility and AMD compatibility, followed by a controlled comparison only if supported. The reviewed staged Qwen4Exp CUDA-only validator does not establish AMD DeepSeek support.
3. Prepare and benchmark the additional ISTA-DASLab DeepSeek GSQ-RCO Coder candidate, preserving the completed Q1 restoration. Its 182.72 GB total includes 110.60 GB shared Engram; reuse requires verified identical hashes.

Use the authorized standard tool checks and repeated speed protocol, recording correctness, TTFT, prefill, decode, end-to-end time, RAM/VRAM, disk I/O, cold/warm behavior and spread. Unsupported paths and failures receive explicit outcomes. Remaining model restorations, engine qualifications and six fixed diffusion/edit workflows are still unfinished. Next action: preserve the fault hold, finish read-only recovery/transport review and CPU-only preparation before any bounded, separately reviewed GPU stage.

### CPU-only continuation and Strata preparation

The interrupted RCCL build has now resumed incrementally under a distinct owned CPU-only continuation: two compile jobs, four logical CPU quota, 24 GiB memory maximum and nice 10, with GPU visibility disabled. The old record/log and partial outputs remain intact. It is still building, unselected and unqualified; no completed-library or runtime-pass claim is made. Freeze only this verified owned continuation during future timed comparisons and thaw it in cleanup.

The matching pinned Strata DFlash2 source (revision `a22a1744e85c`) is downloaded and fully SHA-256 verified. NumPy-only conversion produced the exact pinned 522,458,112-byte Q4_0 pack and 339,694,592-byte Q4_0 selector pack, each hash-verified. These are staged artifacts, with no production installation or GPU execution. Three isolated DFlash2/MTP/Off configurations preserve the same target quant, layer split, context/KV, memory tier and three-token verification window. DFlash2 explicitly forbids MTP fallback. Strata Off removes the neural drafter but retains suffix/prompt lookup; native IQ packs reject a verification window below two, so Off must not be described as completely speculation-free.

Static Maya review finds host-staged decode residual transfer and an opt-in native peer-prefill path. Source comments describe prior pageable-transfer wedges, but do not prove this fault's cause; changing RCCL or enabling a bounce option is not an established remedy. GPU work and GLM remain held. PLE disk offload is unsupported by the reviewed staged Qwen4Exp CUDA-only validator; no AMD timing is claimed. The additional Coder download/benchmark remains queued after the requested Strata and PLE stages.

## New NVMe placement and CPU clarification

**November 3 new streaming storage:** new SSD-streaming weights now use the newly mounted NVMe through UUID-checked placement, with the existing 90% capacity limit. GPU-led inference may use CPU expert offload; fully CPU inference is excluded. The isolated Strata comparison is in progress. [Verified placement and interrupted-trial attribution](NEW-NVME-STREAMING-2026-11-03.md). No new GPU fault was observed in the owner-stopped first Strata trial; the continuation remains guarded and unqualified.

## Repeat freeze update

**November 3 repeat hard freeze:** the isolated dual-GPU Strata Qwen Off trial froze the system; the owner manually reset it. DFlash2 was not loaded and the compiler was frozen. The exact cause is unresolved. All GPU campaign work is stopped under a fresh persistent hold. [Evidence and containment](STRATA-HARD-FREEZE-2026-11-03.md).
