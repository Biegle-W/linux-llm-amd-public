# Agent entry point

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
qualification, updating both launcher and metadata together. Keep loading-swap-v2,
all independent guards and the paused updater. Current versions/results belong
in the canonical handoff/report; the API version omits the wheel packaging suffix.
