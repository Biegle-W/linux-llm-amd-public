# Agent entry point

**October 29 Ornith / updater audit:** Ornith has a scoped working isolated 32 GB placement; production remains held. [Placement results and limits](linux/hardware/ORNITH-VRAM-32GB-2026-10-29.md). The overnight updater timer is absent/inactive; five configured components have newer upstreams, while SGLang matches its AMD fork. [Read-only version audit](linux/hardware/ENGINE-UPDATE-AUDIT-2026-10-29.md). Production selections, guards and paused schedules remain.

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
qualification, updating both launcher and metadata together. Keep loading-swap-v3,
all independent guards and the paused updater. Current versions/results belong
in the canonical handoff/report; the API version omits the wheel packaging suffix.

Post-upgrade H3 evidence is in [the dated comparison](linux/graphics/H3-POST-UPGRADE-2026-10-28.md). Read its current RAM attribution and failures before retrying; added RAM alone does not qualify held profiles.

The [October28 user correction](linux/hardware/SWAP-TASK-CONTINUITY-2026-10-28.md) supersedes arbitrary swap-rate stops. Never stop a task for loading/parked swap, reads, rate or PSI alone. Legacy validation needs its explicit second opt-in; frozen strict harnesses are historical. An optional write-related stop needs an explicit write budget and matched measured slowdown. Radiance gfx1100 [preflight](linux/graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md) is a software compatibility blocker, not a swap failure.

The [fresh H3 one-card/two-card comparison](linux/graphics/H3-ONE-VS-TWO-2026-10-28.md) uses a true one-visible-GPU workflow and fresh servers per generation. Read its medians, phase timings, quality checks and attribution limits. Preserve earlier failures as historical evidence, keep this candidate isolated from production and native Radiance, and never lower guards for a comparison.
