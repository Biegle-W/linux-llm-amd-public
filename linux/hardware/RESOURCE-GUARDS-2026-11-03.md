# Resource guard policy — November 3, 2026

The owner selected these resource thresholds. They supersede earlier default headroom and swap-rate limits; historical results keep their original settings and are not requalified by this change.

| Setting | Current policy |
| --- | --- |
| Minimum available system RAM | **1 GiB** |
| Minimum free VRAM | **128 MiB on each card** |
| Worker soft RAM limit | **Disabled** (`memory.high=max`) |
| Worker hard RAM ceiling | Recomputed at launch as OS-visible `MemTotal − 1 GiB` |
| Swap capacity | Existing system swap unchanged; the inspected host has **33.53 GiB** |
| Worker swap ceiling | Current `SwapTotal`; no swapfile/partition expansion |
| Swap I/O throughput | **No software rate ceiling**; actual throughput depends on the SSD/workload |
| SSD checks | Cached SMART health plus live NVMe temperatures; no self-test or write-speed benchmark |

The user explicitly accepted normal SSD wear. Maximum device throughput is not a wear-free rate, and these checks cannot guarantee SSD lifetime. [Crucial's P3 Plus datasheet](https://www.crucial.com/content/dam/crucial/ssd-products/p3-plus/flyers/b2c/crucial-p3plus-productflyer-consumer.pdf) specifies finite write endurance and a 0–70°C operating range. The guard uses a **70°C stop threshold**, not a promise that operation below it cannot fail.

## Runtime behavior

`dsh/resource_policy.py` supplies the shared RAM/VRAM thresholds and scope limits. `spawn_owned` replaces old profile-era `MemoryHigh`, `MemoryMax` and `MemorySwapMax` properties with the current policy before releasing its gated command. It verifies the effective kernel cgroup values. Other scope properties and the exact owned cgroup boundary remain intact. A global headroom watcher is still necessary because unrelated applications and some driver allocations are outside a worker's memory charge.

The inspected host resolves the ceiling to **65,016,582,144 bytes (60.55 GiB)** and its unchanged swap ceiling to **36,000,755,712 bytes (33.53 GiB)**. These are observations of that host; launchers derive values locally rather than using those numbers as universal settings. The old 20/22 GiB limits no longer govern managed workers. [Linux's cgroup documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html) distinguishes the reclaim boundary from the hard limit and separate swap limit.

Native Strata/Maya reserve arguments and actual startup checks use 128 MiB per card. Their model contexts, caches, weights, numerical settings and catalog enablement remain unchanged. Resource-policy validation is CPU-only and does not qualify a changed model configuration for GPU use. Model placement, runtime identity and capacity requirements remain separate checks.

`loading-swap-v5` is the current swap policy. It retains measured swap occupancy/rates as telemetry but removes the old 128 MiB/s write and 160 MiB/s combined throughput stops. Inherited older policy names do not silently restore old limits. Explicit historical replay requires the existing legacy swap-validation opt-in; resource-policy replay has its own explicit validation opt-in. Those modes are for historical checks, not the normal service environment.

`WorkerSwapGuard` checks SSD health before spawning and while its owned worker runs. The reader obtains cached UDisks SMART properties without privileged refreshes. SMART data older than **20 minutes**, missing coverage/counters, reported critical/failing health, NVMe media errors or spare below threshold fail closed. Live NVMe temperatures are read each watch sample; cached SMART records are reread every 30 seconds. SATA temperature comes from the SMART cache. UDisks itself controls refresh frequency; the reader does not claim a fresh device read on every call. [UDisks source](https://github.com/storaged-project/udisks/blob/master/src/udiskslinuxnvmecontroller.c) documents this cached SMART path. Normal wear percentages and lifetime error-log entry counts alone do not stop a worker.

RAM/VRAM telemetry loss, actual dedicated VRAM eviction, owned-process containment and existing fault/thermal protections remain. A resource change does not clear a device-fault reservation, enable a held model, restart an inference worker or resume a paused updater.

The managed ComfyUI CLI uses the shared owned resource/SSD guard and a 0.125 GiB native VRAM reserve. Its hold check runs before framework initialization. The existing desktop application's native reserve is also 0.125 GiB; its direct native launch is not represented as having the CLI wrapper's SSD/cgroup monitor. Use the managed CLI when those checks are required. No ComfyUI workload or application restart was performed for this change.

## November 18, 2026: one free-RAM floor for loading (owner decision)

The owner asked for a plain free-RAM floor for every model, as on the NVIDIA server, instead of a per-model figure. Before a model loads, the only available-RAM requirement is now the **1 GiB host reserve** above (`free_ram_blocker` in `dsh/resource_policy.py`). Nothing is added for expert budgets, host KV copies or CPU expert bytes.

| Route | Available RAM needed before loading, until November 17 | Now |
|---|---:|---:|
| Flash-Next on Strata (`64gb-qwen-v1`) | 28.4 GiB (24 counted + 3.35 host KV + 1) | 1 GiB |
| DeepSeek Q1 on Maya (qualified native) | 52 GiB | 1 GiB |
| GLM on Maya | 52 GiB | 1 GiB |
| DeepSeek Q1 on Strata | 52 GiB | 1 GiB |
| `64gb-q1-v1` tier | 29 GiB | 1 GiB |
| `32gb-v1` tier | expert budget + 1 GiB (Qwen), 9 GiB (GLM, DeepSeek) | 1 GiB |
| llama.cpp MoE with CPU experts (none enabled) | CPU expert bytes + 1 GiB | 1 GiB |
| llama.cpp VRAM-only, vLLM, SGLang | 1 GiB or no RAM figure | unchanged |

Unchanged: the physical-RAM floors (60 GiB installed for the large profiles), the layout checks of each tier, every VRAM check, the worker hard ceiling of `MemTotal − 1 GiB`, and the running guards, which stop only the owned worker when available RAM falls below 1 GiB. What this means in practice: a load that used to be refused up front when other programs held the RAM is now started, and if the RAM does run out it is the running guard that stops that worker (a router-local fault, not a GPU hold).

Checked with the unit tests (hardware: 662 run, 2 skipped; dsh: 62) and one short request per affected model through the hub: Flash-Next, DeepSeek Q1 on Maya, GLM on Maya and DeepSeek Q1 on Strata all loaded and answered ([result](results/ram-floor-load-check-2026-11-18.json)). Those loads began with 15–58 GiB available, so the 1 GiB boundary itself is covered by unit tests only.

Found during the check, not caused by it, and fixed the same day (owner OK): switching straight from a loaded Flash-Next to a Maya model was refused with "16 GiB free per card", twice out of two. Maya, the qualified native path and Strata DeepSeek read free VRAM once, right after the previous backend stops. They now poll for up to 15 s (`free_vram_short` in `dsh/amd_device.py`, tests in `hardware/test_vram_release_wait.py`); the 16 GiB requirement is unchanged. In the retest the cards reported the memory free 0.6 s after Flash-Next stopped, the check passed and Maya began loading 3 s later. That load then ended on a different, unchanged check, "whole-card startup headroom is below 1 GiB": a game on the display card was holding about 850 MiB more VRAM than during the earlier successful load, and DeepSeek Q1 on Maya leaves about 1 GiB free on that card. The switch was not retested at that point, so as not to load the cards under the owner's game. Later the same day, with the display card free (140 MiB in use), it was verified through the hub: Flash-Next loaded and answered in 98 s, a request for DeepSeek Q1 on Maya then switched, loaded and answered in 77 s, and a request for Flash-Next switched back and answered in 148 s. No refusal, no hold, no kernel fault.

## Validation and activation

Eight new CPU-only tests exercise inclusive headroom boundaries, legacy-environment normalization, high-rate swap, storage warnings/freshness, ordinary wear and owned shutdown. Historical replay checks cover 12 streaming-memory cases and nine earlier rate-policy cases. The ownership/lifecycle suite passes 32 CPU-only cases on the host user bus; a stale SGLang fixture was corrected to mock storage preflight consistently with its VLLM counterpart.

An actual CPU sleep worker verified that even old 20/22 GiB launch arguments produce the new cgroup values; cleanup emptied only its scope while preserving an unrelated process and the existing GPU reservation. Four native profiles pass CPU resource-policy validation, and model-placement validation remains intact. Read-only live SSD health checks pass. No inference run, synthetic swap traffic, sustained-write benchmark or new GPU qualification is claimed.

Idle hub/API service reload and repository synchronization are recorded in the task completion record. A running model would require an owned unload and subsequent launch to acquire new cgroup limits; changing source alone cannot rewrite an existing worker's scope.
