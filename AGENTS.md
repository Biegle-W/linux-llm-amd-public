# Agent entry point

[Qwen3.8-Flash-Next IQ3_XXS, Unsloth vs GSQ-RCO, November 8](linux/hardware/QWEN-IQ3-UNSLOTH-VS-GSQ-2026-11-08.md): owner-requested. Quality level: both 53/54; on the harder suite GSQ 62/64, Unsloth 63/64. Unsloth reads a 5.5K-token prompt about 35% slower (512-530 vs 777-821 tok/s) and decodes about 17% slower after it; short-prompt decode is level (about 50-52 tok/s). Keep GSQ-RCO. Also fixed a Strata router bug from f332a6d that broke Qwen route readiness.

[GLM and DeepSeek RAM/reserve tuning, November 8](linux/hardware/GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md): GLM RAM 40 GB + 2 GiB reserve: 17.8-22.1 tok/s (was 2.6), 396 tok/s prompt; DeepSeek expert profile + 2 GiB reserve: 7.5-10.1 tok/s (was 4.2-6.3), 120 tok/s prompt; Maya DeepSeek route 9.5-17.1 tok/s (was 5.0-9.3).

[AMD working setup, November 7](linux/hardware/AMD-WORKING-SETUP-2026-11-07.md): card positions, device order and the tests that passed after the Sapphire switch investigation.

[All-models short tool-call benchmark, November 7](linux/hardware/AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md): all 14 routes passed in the working layout; GPU fault hold released by the owner.

[Sapphire post-crash investigation](linux/hardware/SAPPHIRE-POST-CRASH-LINK-TRAINING-2026-11-06.md): idle-power state, motherboard and switch isolation tests, P2P on/off and TP2 results.

[Headless model campaign](linux/hardware/AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.md): Headless campaign stopped on SGLang Qwen DFlash2 startup: Sapphire `0b:00.0` lost PCI/SMU access. Four model tool checks completed first (three clean guard passes; one preserved Qwen vLLM harness-path failure after successful tools/cleanup). Nine routes, including Maya DeepSeek no-store, were not run. A connected physical monitor is not required for this failure. Latest fault hold retained; no retry or further GPU work.

[No-store DeepSeek failure and persistent inference kernel](linux/hardware/MAYA-DEEPSEEK-NO-STORE-2026-11-05.md): The single no-store DeepSeek baseline also failed loading: Sapphire `0b:00.0` was reported lost from the bus, followed by SMU errors, then heartbeat/owned-cleanup failure; no requests. Patched `7.0.14-42-vmpt1` is now the owner-selected persistent inference default, with stock installed as fallback. New fault hold retained; no automatic retry or further GPU work. The current post-crash boot has no fresh peer/model qualification.

Read [README.md](README.md) for maintenance policy, then the [current runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md). Read the [current result index](linux/hardware/CURRENT-AMD-BENCHMARKS.md) only when the task needs measurements. Inspect both Git trees and actual jobs/locks before acting.

Fourteen routes are enabled. New Unsloth UD-IQ1_M passed its own short qualification; GLM RAM24 passed but remains unselected; DeepSeek36GB-store failed loading/cleanup before the later AMDGPU/CPU lockups. Persistent GPU fault hold remains; no automatic GPU work/retry/reboot/hold release. RAM40 is unrun and blocked. See [new results](linux/hardware/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md). Completed engine qualifications and daily-updater review are published; inspect actual jobs/locks and the final RDNA3 outcome. PLE/Super exact attempts are final guarded loading stops; Bolt globaldev229 passed its matching near255K check and is selected. RDNA3 build/native audits passed, but startup compatibility failed before requests; that exact case is final and no promotion occurred. No scoped qualification job remains running. Deleted XS/Super IQ3 stay retired. Preserve all guards, owner-selected persistent inference-kernel default and installed stock fallback, unrelated work and other paused schedules. Do not rerun passed checks for documentation.

[DeepSeek RAM-store comparison and scoped tuning-cache cleanup](linux/hardware/MAYA-DEEPSEEK-CACHE-COMPARISON-2026-11-05.md): live Maya Q1 tuning file removed; no persistent36GBstore or new GPU test. Hold retained.

[Full-day successful workloads and two interruptions](linux/hardware/AMD-DAY-REVIEW-2026-11-05.md) are now source-checked; baseline Maya DeepSeek passed earlier that day.

[Stock/custom crash comparison](linux/hardware/AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md): both kernel families have failed; corrected records identify Sapphire across the slot swap, still logical GPU1. Preserve the fault hold; physical-card versus runtime-role cause remains unresolved.

After authorized work, update both AMD repos and applicable current docs/results, review sanitization, normally commit/push intended files and verify both remote refs plus the exact Shared handoff. Keep private workflow and client state out of public/Shared exports.

[Older entry point and overviews](linux/hardware/history/documentation-2026-11-05/README.md) are historical references, not required startup reading. Keep this file a thin index; current state belongs in the handoff and dated evidence belongs in reports.
