# Agent entry point

Read [README.md](README.md) for maintenance policy, then the [current runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md). Read the [current result index](linux/hardware/CURRENT-AMD-BENCHMARKS.md) only when the task needs measurements. Inspect both Git trees and actual jobs/locks before acting.

Fourteen routes are enabled. New Unsloth UD-IQ1_M passed its own short qualification; GLM RAM24 passed but remains unselected; DeepSeek36GB-store failed loading/cleanup before the later AMDGPU/CPU lockups. Persistent GPU fault hold remains; no automatic GPU work/retry/reboot/hold release. RAM40 is unrun and blocked. See [new results](linux/hardware/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md). Completed engine qualifications and daily-updater review are published; inspect actual jobs/locks and the final RDNA3 outcome. PLE/Super exact attempts are final guarded loading stops; Bolt globaldev229 passed its matching near255K check and is selected. RDNA3 build/native audits passed, but startup compatibility failed before requests; that exact case is final and no promotion occurred. No scoped qualification job remains running. Deleted XS/Super IQ3 stay retired. Preserve all guards, stock boot default, unrelated work and other paused schedules. Do not rerun passed checks for documentation.

[Stock/custom crash comparison](linux/hardware/AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md): both kernel families have failed; corrected records identify Sapphire across the slot swap, still logical GPU1. Preserve the fault hold; physical-card versus runtime-role cause remains unresolved.

After authorized work, update both AMD repos and applicable current docs/results, review sanitization, normally commit/push intended files and verify both remote refs plus the exact Shared handoff. Keep private workflow and client state out of public/Shared exports.

[Older entry point and overviews](linux/hardware/history/documentation-2026-11-05/README.md) are historical references, not required startup reading. Keep this file a thin index; current state belongs in the handoff and dated evidence belongs in reports.
