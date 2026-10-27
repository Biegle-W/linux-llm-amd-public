# Loading swap is allowed — October 27, 2026

**Standing user instruction: allow swap during model loading. Prohibit sustained
aggressive swapping during inference when it creates excessive SSD write churn
or slows inference. Parked swap pages are allowed.** This supersedes previous
blanket zero-swap rules, 64/256 MiB watchdog caps and default 4 GiB resident-swap
or cumulative-loading-write caps. Future agents must read this before testing.

## Current implementation

`loading-swap-v2` is the default for the five managed LLM routers and the maintained
benchmark/update memory collector. Loading, idle residency and active inference
are distinct phases. Loading swap volume and owned swap occupancy are recorded
without fixed byte rejection caps. Normal llama.cpp, Strata and Maya worker
scopes allow `MemorySwapMax=infinity`; VRAM-only llama.cpp profiles retain their
4 GiB `memory.high` and 5 GiB `memory.max` RAM caps. This does not enlarge RAM.
Strata profile swap limits are explicitly null, meaning no static occupancy cap.
The obsolete secondary 256 MiB and zero-worker-swap watchdog rules are removed.

The routers mark actual request forwarding as inference and return to idle on
completion. llama.cpp's empty native server health check is idle readiness;
explicit lazy model loading stays in loading until the model reports loaded.
Phase changes reset rate windows, retain latched violations and serialize with
memory/host readers. Spawn-through-shutdown accounting and cgroup ownership stay.

During a continuous active inference window of at least 30 seconds, sampled
host swap rates above **1 MiB/s swapout** or **8 MiB/s combined swap I/O** stop
the owned worker. These are conservative operational defaults for detecting
sustained churn, not measurements of SSD wear or proof of damaged hardware.
More than **10% full-memory PSI avg10 for three inference samples** also stops.
Loading/idle PSI does not trigger that inference-thrashing rule. Host counters
include unrelated tasks; they cannot attribute every swap byte to the model.
Short requests/bursts may have no complete 30-second window. Missing inference
windows never qualify a benchmark, and performance/quality checks remain needed
to show inference speed is acceptable. Existing promotion comparisons require
prefill/decode at least 95% of baseline and their existing TTFT/quality limits.

## Independent safety requirements

Physical-RAM admission and available-RAM floors still apply during loading.
The common monitor retains its <2 GiB available-RAM, three-sample stop; existing
profile-specific 3 GiB floors, RAM caps, both GPUs, GPU reserves, zero dedicated
VRAM spill, lifecycle thermal monitoring, ownership/locking and selective cleanup
remain. Swap permission does not count SSD space as resident CPU expert capacity.
No global swap partition, swapoff, swappiness, application closure, runtime pin,
context setting or paused updater schedule is changed.

Explicit `LOCAL_LLM_SWAP_POLICY=low-churn-v1` and `bounded-64mib` remain available
only to reproduce legacy **validation** behavior; do not set them for routine
loading or use them to override the standing user instruction. Evidence carries
its policy version; old records are not automatically accepted as v2. Unknown
policies, invalid/missing telemetry, ownership failures, sampling/enforcement
errors and incomplete qualification windows fail closed.

## H3 and future retries

Apply the same loading-swap permission to H3/ComfyUI. Historical private harnesses
and dated standalone validators freeze earlier zero-swap assumptions; they are
not current v2 qualification tools. Before reusing one, create a fresh harness
copy, allow worker swap in its scope, replace fixed occupancy/total-write bans
with phase-aware active-compute churn monitoring, retain the independent RAM/
VRAM/thermal guards, and identify load, warmup, denoising and decode separately.
Do not silently execute a frozen strict harness or silently remove all I/O
monitoring. Normal standalone ComfyUI is not claimed to have the five-router
LLM watcher; any H3 trial needs its own updated lifecycle monitor.

The H3 post-RAM-upgrade follow-up is updated to this policy; its actual-MemTotal
upgrade condition and quiet notification behavior remain. H3's prior 3 GiB
available-RAM stops are unchanged observations. The LLM retries stopped by the
old loading swapout cap are **not evidence that those models cannot run with
loading swap allowed**. Sage's separate Marlin HIP compile failure remains a
software blocker. Fresh guarded attempts are required for new speed results.

## Validation

**170 CPU-only tests passed in each checkout** (340 executions in the final verification suites), including
real CPU scope/orphan/fork cleanup. Policy and router regressions cover loading
swap above 4 GiB, parked
swap, phase transitions/lazy loading, inference churn, pressure, missing evidence,
preserved RAM/VRAM guards and owned-scope cleanup. Legacy fixtures explicitly
select v1 or bounded validation. No new GPU run, inference throughput, H3 video
generation, SSD endurance assessment or runtime promotion is claimed here.

## Real-model retry and systemd syntax verification — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[Measured outcomes and syntax regression](LOADING-SWAP-RETRY-2026-10-27.md).
