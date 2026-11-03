# Agent entry point

**November 2 owner-requested weight removal:** Super IQ3 and old DeepSeek Maya/Strata backing files are removed; approximately 341.6 GB reclaimed. Seven enabled routes remain. Super INT4/vLLM and latest compatible Unsloth Q1 are queued for post-RAM qualification; old weight rollback files are no longer present. Guards, other holds and paused updater remain. [Removal and preparation](linux/hardware/MODEL-WEIGHT-REMOVAL-2026-11-02.md).

**November 2 post-RAM DeepSeek Q1 queue:** replace the existing DeepSeek weight backing for both Maya and Strata with compatible latest Unsloth Q1 quants, after format/pack and RAM/VRAM admission review. Preserve rollback files; one short DSH check and verified unload per route. No current download/replacement or hold change. [Migration queue](linux/hardware/P2P-96GB-ROADMAP-2026-10-30.md).

**November 2 post-RAM Maya pin:** queue `v1.1.50` (`10e69a0eb115`) for isolated compatibility/capacity review after the RAM upgrade and owner request. Then use only short DSH tool-call checks with verified unload. Planning only; current runtime, guards, holds and paused updater remain. [Pinned queue](linux/hardware/P2P-96GB-ROADMAP-2026-10-30.md).

**November 2 Empero failure retest:** one short DSH read-tool round trip passes the strict marker-only final answer; owned unload verified. Earlier format failure retained; caps, pins, guards, held models and paused updater unchanged. [Result](linux/hardware/EMPERO-FAILURE-RETEST-2026-11-02.md).

**November 2 repeat 2 DSH checks:** fresh owner-requested checks on all eight enabled routes: **7/8 passed, 1/8 did not pass**. Each tested backend was verified unloaded before switching, including the final model. RAM/VRAM/swap and thermal observations are recorded; pins, caps, guards, holds and paused updater remain. Historical speed measurements are unchanged. [Results and guardrails](linux/hardware/DSH-ENABLED-TOOL-CHECKS-2026-11-02-REPEAT-2.md).

**November 2 enabled-model DSH checks:** fresh owner-requested checks on all eight enabled routes: **8/8 passed, 0/8 did not pass**. Each tested backend was verified unloaded before switching, including the final model. RAM/VRAM/swap and thermal observations are recorded; pins, caps, guards, holds and paused updater remain. Historical speed measurements are unchanged. [Results and guardrails](linux/hardware/DSH-ENABLED-TOOL-CHECKS-2026-11-02.md).

**November 2 future-model test plan:** one short real harness tool round trip per requested model, then verified owned unload before switching. Benchmark listings now show RAM, per-card VRAM and swap guardrails; dated speeds and historical guard evidence remain. Documentation only, no new model run. [Plan and guard catalog](linux/hardware/FUTURE-MODEL-TEST-PLAN-2026-11-02.md).

**November 2 GUI-on-connect setup:** headless boot is configured. The HDMI + USB keyboard + USB mouse detector is installed, enabled and verified running. HDMI plus DisplayPort is configured and verified; display, USB keyboard and USB mouse are detected. Nine CPU checks pass per checkout; inference is unchanged. [Install, behavior and limits](linux/network/GUI-ON-CONNECT-2026-11-02.md).

**November 1 ROCm PLE candidate:** an isolated AMD file-gather source port is prepared with 38 passing CPU checks and an exact-hash/zero-fuzz preparer. It is not installed or GPU-qualified. After RAM installation and an owner request, verify supported weights/capacity, then use only a short DSH tool-call check and unload. Existing runtime selections, holds and paused updater remain. [Source changes, package and limits](linux/hardware/PLE-ROCM-SOURCE-PORT-2026-11-01.md).

**November 1 post-RAM queue:** vLLM Flash Next disk-backed PLE is queued for reassessment after RAM installation and an owner request to proceed. ROCm support must be established first; RAM alone does not remove the reviewed CUDA-only restriction. Any later check is short DSH tool-call testing followed by unload. Daily updates and model holds stay paused. [Queue and prerequisites](linux/hardware/P2P-96GB-ROADMAP-2026-10-30.md).

**November 1 enabled-model DSH checks:** the seven remaining enabled routes each received one short harness tool-call attempt; combined with the earlier Empero result, **4/8 passed and 4/8 did not pass**. Every tested backend was unloaded. No full-context test, new throughput benchmark, context change or retry. Historical speed figures remain historical; daily updates stay paused. [Per-route results and failures](linux/hardware/DSH-ENABLED-TOOL-CHECKS-2026-11-01.md).

**November 1 DSH and testing policy:** all enabled models use one **AMD server** provider. Calculate context limits from RAM/VRAM and engine allocations; run only a short tool-call check through the harness and unload. No routine full-context, near-window or long benchmark tests. This owner instruction supersedes older routine qualification requirements below. The daily updater remains paused. [Current policy](linux/hardware/SHORT-HARNESS-TEST-POLICY-2026-11-01.md).

**November 1 daily updater paused by owner:** the 03:00 timer is inactive, not enabled for automatic startup, and has no next run. The updater service is inactive. Resume only on an explicit owner request. Selected runtimes, RAM holds and guards remain. [Pause and verification](linux/hardware/ENGINE-UPDATER-PAUSED-2026-11-01.md).

**November 1 DeepSeek test plan:** first-hand Linux gfx1100 reports support investigating the current dual 7900 XTX / 32 GB host. The staged plan tests full routing, bounded memory, actual quantized kernels, A→B→A session restoration, context growth and a stock/AtomicChat comparison. Research and plan only; no trial, download, build, runtime change or hold removal. [Sources, test sequence and gates](linux/hardware/DEEPSEEK-GSQ-32GB-TEST-PLAN-2026-11-01.md).

**October 31 normal H3 activation:** projected 8B FP8 + v3.1 projection is now the default for text-to-video. One guarded actual-normal-ComfyUI 39-frame request passes API, finite-tensor and full AV-decode checks. Exact Native32B workflows remain for image-conditioned work/rollback. Component placement, attention, guards and other runtime selections are preserved. [Activation, rollback and limits](linux/graphics/H3-PROJECTED-8B-ACTIVATION-2026-10-31.md).

**October 31 H3 projected-8B comparison:** all 12 timed generations pass guard/media checks. Before scheduled CPU preparation (four pairs), median encoder load is 31.9 s versus 49.1 s for native 32B W4A8; complete generation is 259.6 versus 270.5 s. Encoder memory falls; whole-workflow gains vary. Sampled quality, all six pairs and late scheduling overlap are recorded. This comparison used an isolated runtime; normal T2V activation is recorded separately. RAM holds and guards remain. [Measured comparison and limits](linux/graphics/H3-PROJECTED-8B-COMPARISON-2026-10-31.md).

**October 31 forum refresh:** 15 public reply pages / 206 posts reviewed. Later tiered-vLLM replies show progress but unresolved PLE/numerics; H3 projected 8B encoding is a separate quality candidate. Linked engine pins are unchanged. High-RAM/P2P results do not qualify this 32 GB host. Research only; no runtime or GPU trial. [Findings and next actions](linux/hardware/LCZ-FORUM-REFRESH-2026-10-31.md).

**October 31 Super INT4 retry:** fresh vLLM/SGLang admission is blocked at 27.6 GiB required / 22.2 GiB available; SGLang also has Super architecture and channelwise quantization blockers. No candidate worker or runtime change; llama.cpp IQ3 remains selected. [Results and next steps](linux/hardware/SUPER-INT4-ENGINES-2026-10-31.md).

**October 30 MES compatibility audit:** the workaround is absent from exact kernel source `7.0.0-42.42`; the six-file patch passes no-fuzz application, and both loaded MES versions are `0x86`. Offline source candidate, H3 inventory tools and P2P plan are prepared; no kernel build/install or GPU trial. [Audit and limits](linux/hardware/MES-SOURCE-AUDIT-2026-10-30.md).

**Planned hardware:** owner expects 96 GB total RAM and a PEX88096 switch. These are future conditions; current RAM holds and transport remain. [Conditional roadmap](linux/hardware/P2P-96GB-ROADMAP-2026-10-30.md).

**October 30 LCZ source review:** five topics checked; linked engine revisions are unchanged. Experimental MES work merits source compatibility review. No runtime changes. [Findings](linux/hardware/LCZ-UPDATE-REVIEW-2026-10-30.md).

**October 30 OpenCat search compatibility and dated news:** the actual two-function-plus-web request no longer fails HTTP400. Free RSS search supplies publication dates; the exact current-news question returns a dated answer with citations, and 69 focused checks pass per checkout. The iPhone now answers with sources, confirmed by the owner. [Fix, evidence and limits](linux/network/OPENCAT-TOOLS-DATED-NEWS-2026-10-30.md).

**October 30 Strata RDNA3/32 GB trial:** The fork loads and short replies work; conservative 8K recall passes, but its history follow-up stalls. This tested 32 GB configuration is not qualified. The isolated candidate and all three attempts are preserved; production selection and other RAM holds remain. [Measured scope and cleanup](linux/hardware/STRATA-RDNA3-32GB-TRIAL-2026-10-30.md).

**October 30 OpenCat iPhone API repair:** native `POST /v1/responses` is exposed through the authenticated, guarded API. Responses JSON/stream/history and Chat Completions pass on SGLang; 67 CPU routing checks pass per checkout. iPhone retry remains unverified. [Repair and supported scope](linux/network/OPENCAT-RESPONSES-ROUTING-2026-10-30.md).

**October 30 SGLang stream repair:** a reproduced child-exit telemetry race is fixed; five authenticated API streams and 179 CPU/ownership checks per checkout pass. Live missing counters and actual memory/eviction limits still fail closed. [Repair and limits](linux/hardware/SGLANG-TELEMETRY-EXIT-FIX-2026-10-30.md).

**October 30 DSH stream repair:** replayable HTTP activity repair is active; original failing route remains unconfirmed. Preserve timers, engine guards and RAM-test holds. [Evidence](linux/network/API-STREAM-ACTIVITY-FIX-2026-10-30.md).

**October 29 Super INT4 preflight:** the service-pause retry also fails unchanged RAM admission; all stopped services are restored. Keep the working IQ3 selection. [Completed checks and pending qualification](linux/hardware/SUPER-INT4-VLLM-PREFLIGHT-2026-10-29.md).

**Current availability — October 29:** Qwen27B/SGLang is qualified and enabled after the ROCm multicast/VRAM-guard correction; eight working profiles remain available. Ornith, both DeepSeek XS routes and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Actual spill protection and all other guards remain. [Fix and verification](linux/hardware/SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

**October 29 Strata retry / current swap policy:** Diagnostics and `loading-swap-v4` are deployed: 128 MiB/s writes / 160 MiB/s combined over complete 30-second inference windows; loading/parked swap remains allowed. All 218 CPU checks per checkout pass, including the unchanged 95% performance boundary. The Strata build and production baseline passed with zero sampler errors. Candidate launch and the restored-build load smoke hit the unchanged 25 GiB available-RAM guard; no candidate performance verdict exists. Source 7dd5cf18e68c and all three restored build files match the rollback copies. Fresh rollback loading remains unverified. The approved temporary service pause has been restored and verified; the updater is inactive with no provisional state or task GPU reservation. [Policy, diagnostics, SSD evidence and retry status](linux/hardware/STRATA-RETRY-SAMPLER-2026-10-29.md).

**October 29 split llama.cpp update:** Empero, Super and Flint now use `eb4e244be77a` after standard gates. Ornith alone retains the independent old `2280f0fd163b` source/build pin; normal RAM admission remains. [Results, durable pin and validation](linux/hardware/LLAMA-SPLIT-UPDATE-2026-10-29.md).

**October 29 updater restoration:** The 03:00 nightly engine updater is enabled; the current update is complete. Qwen/Sage now use vLLM `0.33.0rc1.dev229+g3966924d5.rocm72`; Bolt retains dev435. The llama.cpp split is recorded above; Strata rollback and remaining RAM-held engine selections remain. Earlier updater-pause notes are superseded; manual runtime pins, other holds and safety gates remain. [Restoration status and repairs](linux/hardware/ENGINE-UPDATER-RESTORED-2026-10-29.md).

**October 29 Ornith / updater audit:** Ornith has a scoped working isolated 32 GB placement; production remains held. [Placement results and limits](linux/hardware/ORNITH-VRAM-32GB-2026-10-29.md). The pre-restoration audit found five newer configured components and SGLang current; the timer is now restored and final outcomes are recorded above. [Read-only version audit](linux/hardware/ENGINE-UPDATE-AUDIT-2026-10-29.md). Other production selections, guards and unrelated paused schedules remain.

The [all-model 32 GB benchmark](linux/hardware/ALL-MODELS-32GB-2026-10-28.md) is complete within recorded scopes. Read its current grouped results, candidate limits and retained failures. All owned benchmark jobs/locks are cleaned up. Preserve completed evidence, runtime selections and guards; do not repeat GPU tests for documentation.

The [matched newer H3 comparison](linux/graphics/H3-MATCHED-32GB-2026-10-28.md) is complete on the actual 32 GB host. Read its request/sampler medians, common-input protocol, memory and sampled-quality limits. All owned work is cleaned up; preserve completed evidence, guards and the isolated candidate. No production promotion or remaining benchmark job.

[Temporary 32 GB streaming profiles](linux/hardware/SSD-STREAMING-32GB-2026-10-28.md): qualification and guarded normal API integration are complete. Read selected versus held results before changing profiles; retain exact 64 GB restoration preimages and all guards.

[AMD router admission and transport](linux/hardware/ROUTER-ADMISSION-2026-10-28.md): validated router code is active after the user-authorized idle hub/gateway restart; authenticated health passes. Keep API-only access, qualified capacity, all guards and paused schedules unchanged. See the report for verification; no activation work remains.

[AMD H3 encoder-format comparison](linux/graphics/H3-AMD-ENCODER-FORMATS-2026-10-28.md): matched format/execution, memory and quality evidence is current. Keep the tested candidate isolated; use the dated report for results, limits and preserved state.

Read [README.md](README.md) first. It is the canonical maintenance policy for
this AMD repository; this file is the discovery entry point, not a duplicate
runtime or benchmark registry.

Before work, read the [current benchmark report](linux/hardware/CURRENT-AMD-BENCHMARKS.md)
and [canonical runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md), then check
current Git status and relevant live ownership/locks. Dated results are evidence;
selected settings and candidates must remain distinguishable.

Standing user requirement, October 27: keep both maintained AMD repositories,
README, this AGENTS entry point, benchmark Markdown/results and runtime handoff
current after relevant changes so another agent can take over anytime. Preserve
history and private evidence. Before yielding, record completed verification,
actual blockers, active work/locks, unfinished steps and a concrete next action.
Review public sanitization, commit/push intended changes to both AMD repositories,
and verify synchronization; report any exact outstanding publication step.
Do not rerun completed GPU tests just to refresh documentation.

Reaffirmed October 29: reviewed commits and normal non-force pushes to both
maintained AMD repositories are automatically authorized after relevant work.
Follow the README maintenance and public sanitization rules without asking
for repeated per-change approval.

Keep private paths, credentials, logs and client state out of public exports.
Preserve unrelated user changes and existing hardware/memory/ownership guards.
The [cross-repository audit](linux/hardware/AMD-NVIDIA-GAP-AUDIT-2026-10-27.md) is read-only:
ask which proposed gaps to fill before implementing them. Do not copy AMD runtime
settings or schedules onto NVIDIA without separate authorization and qualification.

The user-requested [NVIDIA-server gap handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/AMD-PARITY-HANDOFF-20261027.md) is now published in both
NVIDIA repos. It records pending implementation work and host-specific validation;
this documentation delivery did not change runtimes or schedules.

October27 conditional vLLM qualification: [Qwen/Sage dev602 and Bolt dev435 hold](linux/hardware/VLLM-DEV602-PROMOTION-2026-10-27.md).
The installed global wheel and Bolt's explicit launcher override are separate.
Respect `manual_runtime_pin`; the updater excludes held models. Unpin only after
qualification, updating both launcher and metadata together. Keep the current owner-requested swap policy above and
all independent guards; the October29 restoration supersedes the updater pause. Current versions/results belong
in the canonical handoff/report; the API version omits the wheel packaging suffix.

Post-upgrade H3 evidence is in [the dated comparison](linux/graphics/H3-POST-UPGRADE-2026-10-28.md). Read its current RAM attribution and failures before retrying; added RAM alone does not qualify held profiles.

The [October28 correction](linux/hardware/SWAP-TASK-CONTINUITY-2026-10-28.md) records historical v3 behavior. The explicit October29 owner-requested v4 ceilings above supersede its rate behavior: sustained inference writes 128 MiB/s / combined 160 MiB/s over 30 seconds. Loading/parked swap remains allowed; PSI alone is advisory. Historical policy replay requires the second legacy-validation opt-in; never silently restore older rules. Radiance gfx1100 [preflight](linux/graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md) is a software compatibility blocker, not a swap failure.

The [fresh H3 one-card/two-card comparison](linux/graphics/H3-ONE-VS-TWO-2026-10-28.md) uses a true one-visible-GPU workflow and fresh servers per generation. Read its medians, phase timings, quality checks and attribution limits. Preserve earlier failures as historical evidence, keep this candidate isolated from production and native Radiance, and never lower guards for a comparison.
