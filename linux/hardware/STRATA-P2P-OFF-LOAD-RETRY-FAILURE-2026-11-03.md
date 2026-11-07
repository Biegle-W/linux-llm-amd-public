# Strata P2P-off loading-timeout retry failure — November 3, 2026

**The owner-authorized retry loaded in 71.327 seconds, then failed during its first request with GPU `13:00.0` MES/reset and “device lost from bus” messages. The owner reported another crash; a subsequent reboot is verified. P2P was off. No complete response or tool round trip exists. GPU work remains held; the owner plans to remove the PCIe switch while powered off.**

## Authorized change and failure stage

Only the isolated loading deadline increased, from 150 to **210 seconds**. Both existing overall/worker runtime caps stayed **240 seconds**; first-output 20 s, request 30 s, decode stall 3 s, thermal, RAM/VRAM, SSD, swap/spill, heartbeat, cleanup and ownership controls were unchanged. The planned 300 s loading allowance was narrowed to 210 s to retain those overall caps. A fresh workspace and label were used, and the prior evidence was preserved. Model arguments/environment/source executable matched the prior short profile apart from diagnostic destinations. No engine upgrade, service restart or schedule change occurred.

Both P2P driver flags remained `N` / `0`; the same-boot protected six-bridge ACS/IOMMU/KFD verification was retained. Three fresh HIP processes again reported zero peer capability in both directions and refused peer enables before model load. The first GPU cache prefill completed in 29.5 s. Readiness occurred at **71.3268 s**, well before either the old or increased loading deadline. Direct-I/O activation and the expected O_DIRECT expert-file handle were verified before the first request. Thus the loading timeout was not the point of failure in this retry.

The first DSH request began with 25,081 input bytes, three messages, 25 tools and a 256-token maximum. No complete reply was captured. The engine log ends with `rocblaslt error: Could not initialize Tensile host: unordered_map::at`. The saved live kernel log records GPU `13:00.0` MES `REMOVE_QUEUE` failure, failed queue eviction, reset start, worker segfault, device lost from bus and SMU errors. The Tensile initialization error keeps a software path in scope; neither it nor these logs proves the original causal order or identifies a failed physical component.

## Evidence and containment limits

The supervisor recorded **266 samples**; **264 complete sampler records** survive, plus one torn final JSONL line. The last complete record is at 73.962 s. Guard-recorded minima were **51.172 GiB available host RAM** and **1,898.996 / 307.066 MiB free VRAM**. Owned swap and spill stayed zero. Last retained worker high/max/OOM event counters were zero. Sampled GPU memory peaks were **43/28°C**, junction peaks **33/33°C**, and CPU package peak **51°C**. These are retained pre-failure samples, not a complete thermal or memory record through the crash.

The fault was detected and owned termination attempted, but the failed boot's cleanup could not empty the GPU worker scope: KFD client `32630` remained. Do not describe that cleanup as successful. The owner-reported reboot changed the boot ID; current checks find both old task scopes inactive/dead and KFD empty. No new GPU workload was launched after the crash report. The existing persistent hold is `watchdog-fault-strata-p2p-off-short-validated`, with this retry recorded as its last failed stage.

The prior boot's persisted journal stops before the final fault window. The live supervisor's saved `kernel.private.log` and fault-lock messages preserve the actual errors; zero matching faults in the truncated persisted journal is not contrary evidence. Raw engine, proxy, guard, sampler, live-kernel, boot-journal and direct-I/O evidence remain private.

The 1 GiB RAM / 128 MiB-per-card VRAM reserves, `MemoryHigh=max`, installed RAM minus 1 GiB worker ceiling, existing 33.53 GiB swap, v5 SSD-health checks and all other guards remain. P2P-off did **not** prevent this incident; sustained stability and expert streaming remain unqualified. The switch, card, driver/runtime, host-memory and power paths are not distinguished by this one failed run.

## Next action

Honor the owner's planned powered-off switch removal. Shut down fully and disconnect AC before changing PCIe hardware. Keep GPU work held after the move until the actual bypass/bifurcation topology, link widths, device identities, installed RAM and P2P-off state are read back. The current six-bridge switch-specific verifier must not be blindly reused as a bypass admission gate. Do not auto-resume models, restore P2P, change guards or run another trial from this report. A separate controlled workload scope is needed after the hardware comparison is ready.

[Current P2P-off state and earlier bounded attempt](AMD-P2P-DISABLE-2026-11-03.md). Personal crash evidence is private; the public reference records only the failed qualification status and unchanged controls.
