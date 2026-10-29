# Remaining models on actual 32 GB RAM — started October 28, 2026

**Running; no final all-model result yet.** The user requested fresh results for the remaining LLM profiles and confirmed inclusion of Qwen-Image 2.1 and FLUX 3 Klein. Maximize GPU-resident weights within the existing guards; keep quantization, configured context, engine pins and production profiles unless a separately qualified placement is selected.

Actual host: i9-13900KS, 30.56 GiB OS-visible physical RAM, two RX 7900 XTX cards. Existing Qwen/Strata and GLM/Maya 32 GB measurements, the DeepSeek native 32 GB trials and the completed H3 comparison are retained rather than repeated.

Resident series: Empero/Flint, Sage/Qwen/Bolt vLLM and Qwen SGLang, through the normal guarded launchers. One excluded warmup per code/prose task, three timed trials/task and three fresh approximately 8K marker-prefill probes. Full lifecycle memory, swap, thermals and owned shutdown are recorded. Natural file caches are retained.

Empero and Flint have completed the series on 32 GB. A missing client-side tokenizers dependency interrupted framework prefill setup after completed short decode trials. Those valid trials are saved; only missing prefill/continuous stages are queued through the existing client environment with that dependency. This is a harness dependency issue, not a model/RAM failure. Do not discard or repeat completed decode trials.

Next, test Super's current GPU-heavy placement and any measured safe cache headroom. Ornith's original CPU expert backing is about 41.06 GiB, so test an explicit file-backed placement with a bounded 32 GB working set and increased GPU cache where safe. Metadata-only inspection finds 55.65 GiB Super weights and 70.62 GiB Ornith weights; both exceed combined VRAM before KV/compute reserves. A file-backed candidate remains distinct from the retained CPU-resident profile. Keep all original profiles and evidence.

Then run Qwen-Image base 512×512/40 steps, FLUX text-to-image 1024×1024/16 steps and the saved approximately 1 MP FLUX reference edit. Each has one excluded fresh-server warmup and three timed fresh-server generations. The isolated source uses the same weights/workflows/precision with GPU-initialized encoders to reduce extra CPU staging; complete image timings include encoder/upsampler/model loading, sampling, decode and saving. Source inventory is checked before launch; production ComfyUI is unchanged.

All LLM host/VRAM floors, zero dedicated-VRAM spill, loading-swap-v3, engine pins, contexts, coordinators and paused schedules remain. Swap occupancy, reads, rates and PSI do not independently stop a task. Native placement candidates use explicit bounded 18/20 or 20/22 GiB scopes with phase-aware swap; no fake physical-RAM readings. Image tests keep the 3 GiB host floor, existing 2 GiB/four-sample free-VRAM soft floor, 1.5 GiB hard floor, zero spill and physical-MemTotal scope cap. No unrelated work is stopped.

The exact saved 64 GB profile preimages remain. **Restoration requires an explicit new user instruction; detecting more RAM does not authorize restoration. No restoration reminder/monitor/automation should be created.**

Pending: finish queued stages and any necessary scoped repairs; assess image outputs; merge only valid current measurements, retain setup/guard/compatibility failures with accurate attribution; publish final grouped tables with dates, timing scope, context, storage and active versus candidate status to both AMD repositories and the exact Shared handoff. No blanket production promotion or maximum-capacity claim is authorized by benchmark completion.

[Current benchmark listing](CURRENT-AMD-BENCHMARKS.md), [completed SSD-streaming trials](SSD-STREAMING-32GB-2026-10-28.md), [completed H3 matched comparison](../graphics/H3-MATCHED-32GB-2026-10-28.md).
