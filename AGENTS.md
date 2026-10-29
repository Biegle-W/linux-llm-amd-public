# Agent entry point

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
