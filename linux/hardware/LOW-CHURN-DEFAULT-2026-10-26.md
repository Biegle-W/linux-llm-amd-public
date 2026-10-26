# Default low-churn inference swap — October 26, 2026

The user authorized the existing `low-churn-v1` policy as the default, conditional
on bounded swap activity rather than using SSD swap as model/expert RAM. This is
a policy/runtime-guard change, not a runtime upgrade or real-model qualification.

## Limits retained

- At most **4 GiB aggregate owned-worker swap**, not 4 GiB per process.
- At most **4 GiB cumulative host swapout per monitored lifecycle**. The baseline
  is captured before the router spawns its worker; readiness does not reset it.
- After readiness, sampled continuous-inference windows of at least **30 seconds**
  must stay at or below **1 MiB/s swapout** and **8 MiB/s combined swap I/O**.
- Three consecutive observations below **2 GiB host MemAvailable**, or above
  **10% full-memory PSI avg10**, reject. **Dedicated VRAM spill remains zero.**
- Missing/invalid telemetry, unavailable ownership, sample errors and incomplete
  qualification windows fail closed. An old record without activity evidence is
  not retrospectively promoted by relaxing the default.

Host swap counters are system-wide, not worker-attributed: unrelated swapping can
conservatively trigger a stop. These are sampled stop conditions, not kernel I/O
rate limits. Bursts and enforcement delays can overshoot them. They cannot prove
zero inference slowdown, SSD remaining endurance, or absence of every transient.
Settled low-churn swap is allowed; sustained paging is not intended as capacity.

## Normal inference enforcement

All five managed routers (llama.cpp, vLLM, SGLang, Strata and Maya) start an owned
worker watch at spawn, mark actual readiness, and invalidate the watcher before
normal stop/switch. Every payload is gated in a uniquely named user-systemd
scope until writable `cgroup.kill` containment is verified and pinned. Worker
memory includes only that cgroup subtree, surviving parent exit, reparenting and
`setsid()`. Shutdown tries identity-checked TERM, then kernel subtree KILL if
needed, and verifies refreshed `cgroup.events populated=0` before retirement.
DSH, hub, gateway and unrelated workers are excluded. Existing engine scope
properties are preserved without nesting a second scope.

This requires working user systemd, cgroup v2 and writable `cgroup.kill` in the
owned scope; unsupported containment refuses payload execution. It is ownership
containment for cooperative inference programs, not a sandbox against malicious
same-UID code deliberately migrating itself through systemd.

A violation latches a router-restart-required fault and requests owned-worker
shutdown. Repeated model requests cannot implicitly clear that fault. Stale
watch callbacks cannot stop replacement workers. Sampling and termination errors
remain faulted. The llama model server can load models lazily after readiness;
those later loads conservatively retain serving-rate checks.

**Stricter existing engine restrictions take precedence:** no-swap cgroups,
256 MiB watchdogs, physical-RAM admission, GPU reserves and sealed model-profile
fingerprints are not loosened. The general 4 GiB ceiling does not make a model
admissible on insufficient physical RAM. Direct unmanaged vendor-binary launches
bypass these router hooks and are not claimed as covered by this deployment.

## Validation and update collection

The default hardware monitor/validator selects `low-churn-v1` when no override is
set. Explicit `LOCAL_LLM_SWAP_POLICY=bounded-64mib` retains the stricter validation
option. Comparator output prints the effective limit, not a fixed legacy value.

Each benchmark profile now serializes actual `MemoryMonitor` activity and the
same monitor's swap/spill peaks. Its original post-readiness warmup/timed scope,
request counts, measured timing methods and thermal scope are retained. The
updater's lifecycle collector marks loading, successful prewarm/inference, model
changes and shutdown explicitly. Failed readiness/prewarm cannot establish an
inference window. Workload success alone is not memory-policy qualification;
short observations remain unqualified without padding or invented evidence.

## CPU-only verification

- **210 hardware regression tests and 31 DSH tests pass in each checkout**
  (241 per private/public checkout).
- The 68-test focused policy/collector suite passes, covering default/override,
  limits, invalid or missing activity, phase transitions and collector cleanup.
- Runtime coverage exercises all five router hooks, latch/reentry, scoped
  sampling, PID reuse, switches, readiness and a real CPU-only sleep-worker stop
  with unrelated children surviving. Real CPU probes cover a detached/reparented
  child after parent exit and a detached child forked during TERM; both boundaries
  were verified empty after cleanup. A deterministic concurrent stop/callback
  regression verifies fault latching before replacement. Router-stop regressions
  verify bounded parent reaping without numeric PID/PGID signal fallbacks after
  cgroup cleanup, including already-reaped parents and cleanup/reap failures.
  No LLM inference or deliberate SSD swap
  load was generated by this verification.
- Existing socket-test `ResourceWarning` messages remain in the broader hardware
  suite; the suite passes. New runtime tests emit no such warnings.

[Curated numeric evidence](results/low-churn-default-2026-10-26.json). Full CPU
logs and pre-change configuration hashes remain in private scratch evidence.
Independent collector and runtime reviews passed after correcting the detected
stop/switch fault race, orphan/fork containment gaps and redundant numeric
process-group shutdown signals. The final four shutdown regressions were
independently rechecked. Original findings and corrections remain in private
review evidence.

## Unchanged / not claimed

Nightly updates stay paused. No reduced-16-GB GPU trial, candidate installation,
model movement, model/context change, swap enlargement, swappiness change or
OS/driver/ROCm modification is part of this task. No throughput or SSD-health/
endurance measurement was performed. Earlier benchmark and qualification results
keep their original policy, date and hardware attribution.
