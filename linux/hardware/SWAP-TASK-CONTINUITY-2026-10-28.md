# Swap must not interrupt work without evidence — October 28, 2026

**Standing user instruction: allow swap while loading and computing. Do not stop a task merely because swap is used, reads are high, pages remain parked, or an arbitrary rate threshold is crossed. Only genuinely excessive SSD writes with measured inference slowdown justify a swap-related intervention.**

The earlier implementation applied that instruction too strictly. H3's 14.874 MiB/s combined-I/O stop was mostly reads, with only about 1.6 KiB/s swapout; it did not establish damaging SSD writes or quantify a matched slowdown. The original failure record remains historical evidence, not a current policy requirement.

## Current implementation

`loading-swap-v3` is the default in the shared policy, managed-worker watcher and benchmark memory collector. Loading swap, cumulative loading writes, resident/parked swap and swap reads have no fixed byte rejection caps. Normal maintained LLM scopes remain `memory.swap.max=max`; no swap partition, swappiness or OS paging setting is changed.

The earlier 1 MiB/s write, 8 MiB/s combined-I/O and 10% full-memory PSI levels are **observations/advisories only** under v3. They cannot terminate work by themselves. Router logs and numeric evidence retain these observations. A diagnostic logging failure also cannot terminate inference. Host swap counters are system-wide; they do not prove that a worker caused every byte or that an SSD is being damaged.

No automatic swap-rate stop is enabled by default. The optional stop requires **all** of:

- An explicit deployment write budget, rather than an invented universal SSD-wear limit. None is configured.
- At least 30 uninterrupted seconds of active inference with writes above that budget.
- Valid progress counts and a measured control baseline for the same workload, with throughput below 95% of that baseline. Changing/resetting counters, workloads or baselines invalidates the comparison.

The generic routers do not have matched baselines for arbitrary user prompts. They therefore continue work and report swap telemetry; pressure or read rate is never substituted for missing progress evidence. The optional structured evidence API exists for controlled comparisons. It does not claim to estimate SSD lifetime.

An old `LOCAL_LLM_SWAP_POLICY` setting alone cannot restore v2, v1 or 64 MiB stop rules. Historical validation requires a second explicit `LOCAL_LLM_LEGACY_SWAP_VALIDATION=1` opt-in. Frozen private harnesses must use the current policy and unlimited scope swap, rather than copy historical stop rules.

## Independent protections and verification

Physical-RAM admission/floors, worker resident-RAM caps, VRAM headroom, zero dedicated-VRAM spill, owned-scope containment and thermal/telemetry protections remain. These are separate from swap occupancy or rate. No active managed inference worker was present at deployment precheck; no user task or model was stopped and no router restart was needed. Existing engine pins, default model, Bolt hold and paused schedules remain.

**212 focused CPU regressions pass in each maintained AMD checkout (424 executions)**, including 24 current-policy cases, real CPU scope cleanup and loopback web tests. They cover large loading/parked swap, the read-heavy H3 counter pattern, high rates/pressure without termination, matched slowdown/write-budget evidence, baseline/counter resets, logging failures and preserved physical/VRAM/ownership failures. Historical fixtures explicitly select their actual legacy validation mode. These are CPU/controlled-counter checks, not a new H3 generation or SSD endurance benchmark.

[Numeric implementation and verification record](results/swap-task-continuity-2026-10-28.json) · [historical loading-swap policy](LOADING-SWAP-POLICY-2026-10-27.md) · [Radiance preflight](../graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md).
