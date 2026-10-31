# Current benchmark results

## MES source audit and offline preparation — October 30

Exact `7.0.0-42.42` source lacks the workaround; no-fuzz applicability and a separate offline candidate reverse check pass. Loaded MES is `0x86` on both GPUs. Eleven CPU-only preparation checks pass; the H3 W4A8 runner/assets remain unqualified. Kernel, runtime selections, guards, holds and schedules remain; no GPU trial or active audit job. [Audit, prepared tools and next action](../MES-SOURCE-AUDIT-2026-10-30.md).

## Planned P2P and 96 GB — October 30

[Planning metadata](p2p-96gb-roadmap-2026-10-30.json), not measured upgrade results. [Roadmap](../P2P-96GB-ROADMAP-2026-10-30.md).

## LCZ source update review — October 30

[Curated source metadata](lcz-update-review-2026-10-30.json) and [review](../LCZ-UPDATE-REVIEW-2026-10-30.md). Author-reported results remain distinct from local qualification.

## OpenCat mixed tools and dated news — October 30

[Request compatibility and dated answers](../../network/OPENCAT-TOOLS-DATED-NEWS-2026-10-30.md), with [curated evidence](opencat-tools-dated-news-2026-10-30.json): 69 focused checks per checkout; exact current-news streaming answer with dated sources passes. The owner confirms the iPhone now answers with sources; actual searched responses completed with citation annotations and no refusal parts.

## Free OpenCat search service — October 30

[Keyless service verification](../../network/OPENCAT-FREE-SEARCH-2026-10-30.md) and [curated checks](opencat-free-search-2026-10-30.json): 39 focused checks per checkout and live vLLM JSON/SSE/citation/history checks pass. A new iPhone retry remains unconfirmed.

## OpenCat Responses web search — October 30

[Executed search/citation verification](../../network/OPENCAT-RESPONSES-WEB-SEARCH-2026-10-30.md) and [curated checks](opencat-responses-web-search-2026-10-30.json): live JSON/SSE and history pass on Qwen/vLLM, 90 CPU/HTTP/SDK checks per checkout. No confirmed iPhone retry.

## Strata RDNA3/32 GB trial — October 30

[Scoped trial and retained failures](../STRATA-RDNA3-32GB-TRIAL-2026-10-30.md) and [curated results](strata-rdna3-32gb-trial-2026-10-30.json). The fork loads and short replies work; conservative 8K recall passes, but its history follow-up stalls. This tested 32 GB configuration is not qualified. No production promotion or new held-model queue.

## OpenCat native Responses routing — October 30

[Endpoint repair](../../network/OPENCAT-RESPONSES-ROUTING-2026-10-30.md) and [curated verification](opencat-responses-routing-2026-10-30.json): SDK JSON/stream/history plus Chat Completions on enabled SGLang, 67 CPU checks per checkout. iPhone retry remains unverified.

## SGLang telemetry stream repair — October 30

[Functional repair](../SGLANG-TELEMETRY-EXIT-FIX-2026-10-30.md) and [curated evidence](sglang-telemetry-exit-fix-2026-10-30.json): five completed authenticated streams, 179 CPU/ownership checks per checkout and 3,600 race-reproduction samples. No new performance qualification.

## DSH stream activity repair — October 30

GPU-free client adapter and transport validation only. [Report](../../network/API-STREAM-ACTIVITY-FIX-2026-10-30.md) and [curated checks](api-stream-activity-fix-2026-10-30.json). The original real conversation remains unverified.

## Super INT4 preflight — October 29

Super INT4 small-kernel/UVA checks pass; a temporary nonessential-service pause still fails full-model RAM admission (26.9 GiB required / 23.5 GiB available, before cache/workspace overhead). All three services are restored. No full-model benchmark or promotion; working Super IQ3 remains selected. [Report](../SUPER-INT4-VLLM-PREFLIGHT-2026-10-29.md) and [numeric preflight evidence](super-int4-vllm-preflight-2026-10-29.json).

## All models on actual 32 GB — October 29

[Grouped report](../ALL-MODELS-32GB-2026-10-28.md) and [numeric trials](all-models-32gb-2026-10-29.json): resident measurements, scoped native/file-backed candidates, reused SSD/H3 results, fresh-server Qwen/FLUX images, memory/thermal summaries and retained failures. Timing scopes, configured context, storage and active versus candidate status remain explicit.

[AMD H3 encoder-format comparison](../../graphics/H3-AMD-ENCODER-FORMATS-2026-10-28.md): Tested W4A8 on the same H3 encoder against corrected NVFP4. Native HIP INT8 encoding was 5.91–8.11× faster across three prompts after warmup; separate cold-file load times, RAM/VRAM, nine paired TP2 clips and quality limits are recorded. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. Both host floors remain 1 GiB; other guards and production selection remain.

## Fresh H3 one-card versus two-card test — October28

Fresh tests completed on one physical 7900 XTX and on two 7900 XTX cards: one excluded warmup plus three timed 39-frame generations per arm, with a new isolated server for every generation. Full-request medians are 270.098 s on one card and 146.603 s on two (45.7% shorter on the two-card path). Sampler medians are 30.237/59.749 s. This establishes the measured fresh-server workflow result; loader/storage/noise/source differences limit attribution to GPU count alone. All independent guards and loading-swap-v3 remained. No production promotion or native Radiance run. [Fresh protocol, individual samples and limits](../../graphics/H3-ONE-VS-TWO-2026-10-28.md).

## October28 policy and compatibility records

[Swap continuity numeric evidence](swap-task-continuity-2026-10-28.json) and [policy report](../SWAP-TASK-CONTINUITY-2026-10-28.md); [Radiance preflight numeric evidence](radiance-h3-preflight-2026-10-28.json) and [report](../../graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md). CPU/compiler checks only, with no new GPU performance claim.

## Post-upgrade H3 record — October 28

Linux now exposes **30.56 GiB RAM**, up from **14.83 GiB** before the reboot. This is a physical MemTotal increase; the prior measurements retain their original hardware attribution. The full matched comparison did not complete. Keep the saved production workflow. Partial successful generations and failed attempts are retained; no SP2 speedup or production qualification is claimed. [Report](../../graphics/H3-POST-UPGRADE-2026-10-28.md). LLM selections and historical speeds are unchanged.

October27 reporting correction: current tables now include exact selected engine versions and use the [October25 Strata Qwen promoted-build samples](strata-qwen-selected-2026-10-25.json). Older October24 tuning evidence is preserved; no GPU test or runtime setting changed.

## Conditional vLLM promotion — October27

Qwen/Sage qualify on dev602; Bolt remains explicitly on dev435 after two near255K
inference-churn stops, despite its earlier successful8K performance gates. The
updater excludes `manual_runtime_pin` profiles and remains paused. Completed speed
samples are reused; new installed functionality/mixed routing, all failures and
188 CPU regressions per checkout are recorded. Guards/contexts remain unchanged.
[Selected results, qualification and recovery](../VLLM-DEV602-PROMOTION-2026-10-27.md).

## Current Sage INT4 selection — October27

Sage now uses native W4A16 INT4 on the installed vLLMdev435 runtime under the
same `sage-a1.5` ID,64K/TP2/MTP3. Normal API/tools/JSON/SSE/history and
62,009-token markers pass. Selected benchmark: engine-phase prefill
4142.6t/s, fresh TTFT2.001s, code/prose148.04/138.33t/s,
20.33GB SATA1. Native image checks failed on both tested vLLM builds; the replacement is text-only. The slower Sage GGUF and
exclusive projector are removed (22.61GB reclaimed); all other GGUFs remain.
Twelve profiles remain; DSH default, remaining engine pins, current swap policy,
independent guards and paused updater remain. Earlier same-day snapshots below
retain their original status; this selection supersedes their Sage GGUF state.
[Comparison, compatibility results and removal](../SAGE-INT4-REPLACEMENT-2026-10-27.md).

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](../LOADING-SWAP-RETRY-2026-10-27.md).


## Current-RAM retest — October27

After verified inactive compiler temps were retained on disk, both H3 and blocked
vLLM/SGLang/native INT4 profiles were retried with more free RAM and unchanged
guards. H3 advanced to text-encoder loading, then hit its RAM floor; LLM loading
still hit the swapout budget, with an additional Sage auto-Marlin HIP compile
failure. No new model/engine promotion or retirement; no new inference medians.
[All attempts, memory counters and thermals](../CURRENT-RAM-RETEST-2026-10-27.md).


## VRAM engine refresh — October27

Qualified llama.cpp19cce691 for Empero/Sage/Flint with profile-specific source
pins; CPU profiles retain2280f0fd. New vLLM dev602 and Sage/Flint native INT4
trials remain held by current-host loading guards; production staysdev435.
Required SGLang f84475cc is already latest. All current guards/settings and the
paused updater remain. [Full fields, paired medians, source pins and failed attempts](../VRAM-ENGINE-UPDATE-2026-10-27.md).


- [H3 guarded SP2 attempt](h3-sp2-2026-10-27.json), [report](../../graphics/H3-SP2-2026-10-27.md): stock ComfyUI0.42 API incompatibility, reduced-RAM control/communication guard stops and isolated compatibility pilot; no completed matched generation speedup.

- [Earlier October27 Flint reasoning128](flint-reasoning128-2026-10-27.json), [report](../FLINT-REASONING128-2026-10-27.md): normal-launcher median prefill 6034.8, TTFT 1.396 s (visible answer 4.436s), code/prose 46.63/46.57 tokens/s; 32K, 25.06 GB SATA1; three trials/task, zero worker swap/spill.

- [VRAM-only defaults and selectable Flint](vram-defaults-2026-10-27.json), [report](../VRAM-DEFAULTS-2026-10-27.md): normal launch/auth API, tools, long markers/history and Sage vision; strict owned staging caps; 12 profiles, default preserved.
- [October27 backup cleanup and all-VRAM candidates](storage-vram-2026-10-27.json), [report](../STORAGE-VRAM-2026-10-27.md): 156.47GB reclaimed; Strata Qwen reclassified SSD stream; Empero/Sage/Flint isolated GPU-only text probes pass, production profiles unchanged.
- [October27 model storage inventory](model-storage-2026-10-27.json): three user-requested categories, per-model allocated/logical bytes, shared assets and extra copies.
- [DeepSeek-S removal and retained XS dependencies](deepseek-s-retirement-2026-10-26.json), [report](../DEEPSEEK-S-RETIREMENT-2026-10-26.md): 186.18 GB reclaimed, shared Engram retained; storage/CPU/API validation only, no inference.

- [Default low-churn swap policy](low-churn-default-2026-10-26.json), [report](../LOW-CHURN-DEFAULT-2026-10-26.md): CPU-only policy/runtime verification, 241 regressions per checkout; bounded host swap I/O and owned-worker guards for all five engines. No fresh LLM inference, SSD endurance measurement, engine update or updater activation.

- [Bolt SATA2-to-SATA1 relocation](bolt-storage-move-2026-10-26.json), [report](../BOLT-STORAGE-MOVE-2026-10-26.md): storage-only verification, 33 SHA-256-matched files / 43,645,320,930 bytes; original model removed, active paths updated, 16 CPU storage tests per checkout. Administrator unmount/fstab cleanup still pending; no new inference or NAS service.

- [Reduced-RAM GPU-resident loading qualification](vram-qualification-2026-10-26.json), [report](../VRAM-QUALIFICATION-2026-10-26.md): 14.83 GiB OS RAM, bounded worker units; all three scoped profiles guard-stopped during loading at the cumulative host swapout budget. None qualified; no inference throughput/correctness result, no runtime promotion. Exact memory/thermal coverage retained; historical 64 GB results unchanged.

- [Fresh engine tests after the 64 MiB swap allowance](fresh-engine-tests-2026-10-25.json), [report](../FRESH-ENGINE-TESTS-2026-10-25.md): llama.cpp promoted; Maya rejected/rollback verified; Strata DeepSeek rejected on dual-card kernel parity. All trials/counts, memory and thermal coverage retained; no new full-window claim.

- [October25 minor worker swap policy](../daily-update/README.md#minor-worker-swap-allowance--october-25): **validation only**, 64 MiB aggregate cap, 18 CPU regressions and saved-record replay; no fresh throughput test or runtime promotion.

- [Ten-minute idle unload and inference-only swap scope](model-idle-2026-10-24.json), [policy/report](../MODEL-HUB-2026-10-22.md#ten-minute-idle-power-saving--october24): **functional only**, full live vLLM idle cycle, preserved DSH/gateway/catalog, CPU safety/reload tests; no new throughput or power benchmark.

- [Strata table/prefill selection](strata-tuning-2026-10-24.json), [report](../STRATA-TUNING-2026-10-24.md): same8183c6b6 binary, repeated table controls, rejected4096 admission, independent repeat and normal near256K/history/UI/authenticated host-self API; every trial and lifecycle thermal summary.

- [Strata DeepSeek reusing Maya weights](strata-deepseek-2026-10-24.json), [report](../STRATA-DEEPSEEK-2026-10-24.md): independent S/XS profiles, exact tested gfx1100/HIP7.2.3 binary, RAM-store selection, all trials/counts/thermals, selected-kernel parity, unused-format failures and normal near32K/UI/authenticated API proof.

- [All eleven active profiles re-measured](all-models-2026-10-23.json), [report](../ALL-MODELS-2026-10-23.md): production launchers, shared method, every trial/count/thermal summary, whole-run fan peaks after the October23 fan-control changes; all eleven passed.

- [Maya-S DSpark1.1.24 retest](maya-s-dspark-2026-10-23.json), [report](../MAYA-S-DSPARK-2026-10-23.md): matched A1off-Bon-A2off, all timed trials/nativePP/SSE TTFT+decode, thermal/memory/functional/context gates; S DSpark not selected; production S remains off.

- [Both DeepSeek quants deployed](maya-dual-deepseek-2026-10-23.json), [report](../MAYA-DUAL-DEEPSEEK-2026-10-23.md): S restored as independent selection alongside unchanged XS; three Maya / eleven total profiles, full six-file S SHA256 and normal selector/API proof; no throughput rerun.

- [Maya-XS production integration](maya-xs-production-2026-10-23.json), [report](../MAYA-XS-PRODUCTION-2026-10-23.md): same1.1.24/SDK7 binary, XS+matchingDSpark now selected; normalDesktop/UI/authAPI/GLM↔XS passed. Functional only; earlier XS benchmark rates remain attributed to its experiment.

- [Maya-XS/matching DSpark dual-AMD test](maya-xs-dspark-2026-10-23.json), [report](../MAYA-XS-DSPARK-2026-10-23.md): source1.1.24/SDK7.2.3,32K, off/on three-trial and1024-output probes, format/memory/thermal/context checks. Test only; production Maya-S unchanged.

- [Maya1.1.24 update — October23](maya-update-2026-10-23.json): four matched source19/24 arms, all trials/native PP/SSE TTFT+decode, near31.5K/history, guards/thermals/known kernel failures and normal integration; [report](../MAYA-UPDATE-2026-10-23.md).

- [Ornith122B metadata/tensor inspection](ornith-122b-assessment-2026-10-21.json), [assessment](../ORNITH-122B-ASSESSMENT-2026-10-21.md): research-only memory/quant candidates, **no inference or throughput measurements**.

- [llama.cpp batch sweep](llama-batch-sweep-2026-10-22.json), [report](../LLAMA-BATCH-SWEEP-2026-10-22.md): all five llama.cpp profiles: Ornith/Qwen3.6/Empero/Sage 4096/4096, Super 2048/1024; prefill 4.6–13.6×, decode within 2%; Ornith 8192 and Super ≥2048 break the 3 GiB/card guard.
- [Slow-model optimization research](../SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md): community sources only; top lead is llama.cpp ubatch (128 today) × op-offload threshold for CPU-expert MoE prefill.
- [Model hub live validation](model-hub-2026-10-22.json), [report](../MODEL-HUB-2026-10-22.md): any model via 127.0.0.1:30100 or the gateway starts/switches its backend on demand; waits for in-flight replies; refuses under GPU-LOCK.
- [ROCm 7.2.4 / 7.14.1 vs 7.2.3](rocm-724-7141-2026-10-22.json), [report](../ROCM-724-7141-2026-10-22.md): vLLM Qwen, llama Qwen3.6/Sage, Ornith; all within ±3% (Sage 7.14.1 seed-confirmation −0.05%); retain 7.2.3.
- [Bolt vLLM vs llama.cpp](bolt-vllm-2026-10-21.json), [report](../BOLT-VLLM-2026-10-21.md): AutoRound W4A16 on vLLM TP2 38.0/37.9 decode (+3%), 2,910 t/s prefill vs 224 (13×), 262K window with 255K retrieval pass; **promoted** as `nemotron-3.5-bolt-vllm` (router checks and production benchmark 37.32/37.21, 2,959 PP).
- [vLLM alternatives for Bolt/Sage](../VLLM-ALTERNATIVES-BOLT-SAGE-2026-10-21.md): research only; Bolt AutoRound W4A16 is the one test candidate, Sage has no ready 4-bit vLLM build, FP8 not recommended on RDNA3.
- [Ornith122B Q4 test](ornith-122b-test-2026-10-21.json), [report](../ORNITH-122B-TEST-2026-10-21.md): test-only, both GPUs/32K; MTP off 11.43/13.34/52.68, MTP3 rejected (−27.3%); 31K retrieval/history/vision pass.
- [Sage-A1.5 three-arm tests](sage-a15-2026-10-21.json), [report](../SAGE-A15-2026-10-21.md): test-only Q4/MTP/SDK7-vs-10.1, 64K retrieval/history, vision and full thermal coverage; ten production profiles unchanged.

- [ROCm10.1 six-engine trials](rocm101-2026-10-21.json), [decision and methods](../ROCM101-2026-10-21.md): fresh exact-stack controls, reverse-order/seed confirmation, normal graphics and all failed/partial arms.

- [Maya web switching and DSH reuse](maya-web-switching-2026-10-21.json), [report](../MAYA-WEB-SWITCHING-2026-10-21.md): functional-only UI/SSE/reload/security checks; no new throughput rates.
- [Other-engine ROCm10/table comparison](rocm10-other-engines-2026-10-20.json), [method and decision](../ROCM10-OTHER-ENGINES-2026-10-20.md): fresh exact-production SDK7 controls plus isolated SDK10/Strata-table candidates, all trials/temperatures; production unchanged.

- [Maya v1.1.19/ROCm comparison](maya-rocm10-2026-10-20.json), [decision](../MAYA-ROCM10-2026-10-20.md): SDK7 retained, both NVMe Maya-S packs tested; six GLM /three DeepSeek trials, near32K and normal UI/API/switchback pass. SDK10 negative/stalled arms retained.

- [Strata user-selected 5 GiB startup floor](../STRATA-STARTUP5-2026-10-20.md): 0.1.46.1 promoted; all candidate/near256K and actualDesktop/nativeUI/API gates pass. Fresh912.2PP,9.015s freshTTFT,75.28/50.31decode; [all trials](strata-startup5-2026-10-20.json). Former6GiB failures remain historical.

Current hardware: i9-13900KS,64 GB RAM, two RX 7900 XTX 24 GB. Thirteen selectable
profiles remain after Muse Q4 and Super Q4 retirement: nine shared-method profiles and Super IQ3 with its separate fixed-8K workload. Historical batches keep all original results.

- [Strata Linux app/update admission evidence](strata-linux-update-2026-10-20.json), [scope and limits](../STRATA-LINUX-UPDATE-2026-10-20.md): app0.2.1 installed; Intel primary rendering verified after login; former6GiB startup rule failed twice (exact loaded5.388/6.269GiB free). These historical failures are superseded by the passed5GiB rollout above; old0.1.45 measurements remain dated.

- [Normal launchers and native frontend checks](launcher-validation-2026-10-20.json): functional-only proofs for SGLang/vLLM160K, Strata Q3 and both Maya models, original UI assets and managed runtime controls.
- [GLM Maya-S/S24 ABBA results](maya-s-vs-s24-2026-10-20.json), [decision and method](../MAYA-S-VS-S24-2026-10-20.md): six samples/task/quant at32K; selected Maya-S. DeepSeek measurements are unchanged.
- [DeepSeek DSpark production retest](deepseek-dspark-production-2026-10-20.json), [decision](../DEEPSEEK-DSPARK-2026-10-20.md):
  32K, 24 threads; DSpark −20.4% geometric mean (code −33%, prose −22%) despite 85% draft acceptance. Rejected.
- [Super IQ3 NVMe load and SSD-streaming trial](super-nvme-load-2026-10-20.json), [decision](../SUPER-NVME-LOAD-2026-10-20.md):
  NVMe load 42.2 s vs 112.1 s, with identical inference (−0.12% geometric mean); mmap streaming rejected (forced tool-call failure).
- [Requested model retirement](model-retirement-2026-10-20.json): four exact GGUF files, 95.726 GiB, retained dependency checks.
- [Qwen INT4 context candidates and selected trials](qwen-int4-context-2026-10-20.json), [selection report](../QWEN-INT4-CONTEXT-2026-10-20.md): actual long inputs, full-history follow-ups, three-trial short/8K timings and rejected guard case.
- [Current report](../CURRENT-AMD-BENCHMARKS.md) and [CPU/RAM/pool validation](../CPU-RAM-PROFILES-2026-10-20.md).
- [Original eleven-profile numeric batch](dual-amd-i9-64gb-2026-10-20.json): all trials, exact measured source revisions, actual counts, timing definitions, memory, both Strata pools and normal functional proofs.
- [Maya added two-profile batch](maya-dual-amd-2026-10-20.json) and [Maya report](../MAYA-2026-10-20.md): final RAM/GPU reserves, exact inputs/outputs, all trials, screening controls, numerical limits and normal API/switchback proofs.
- [Earlier i9 baseline/selection evidence](dual-amd-i9-baseline-2026-10-20.json):31288c9, old SATA Strata pack; separate from corrected-NVMe tests.
- [Verified model storage](streaming-storage-2026-10-20.json): checksums and asset scope, no model weights.
- [October 19 i5/32 GB report](../AMD-BENCHMARKS-2026-10-19.md), [nine-profile numeric batch](current-amd-2026-10-19.json) and [Super IQ3 batch](nemotron-super-2026-10-19.json).
- [Complete dated history](../BENCHMARK-HISTORY.md), including NVIDIA/Windows and older capacity tests.

Use [benchmark-current-amd.py](../benchmark-current-amd.py) against one already
running normal backend at a time. It does not launch models or disable guards.
Use `--kind llama|sglang|vllm|strata|maya`, `--model API_ID` for one profile, and an
output beneath ignored `hardware/generated/`. Run with the existing vLLM Python
for its tokenizer dependency. The legacy Muse `--allow-marker-failure` option is for historical replay only;
it does not restore the retired profile. Raw logs and generated answers remain private.
Functional normal-launcher proofs are validation only, not throughput results.
Configured context is separate from actual tested input; phase PP is separate
from external SSE TTFT and input/TTFT proxies.
