# Dual RX 7900 XTX P2P qualification — November 3, 2026

<!-- vmpt-kernel:begin -->
**November 4 isolated VM page-table kernel:** `7.0.14-42-vmpt1` and all modules built from exact retained Ubuntu source, with only the audited two source files changed. Built and staged in an isolated workspace; administrator authentication required for host installation/reboot. Stock kernel remains available; guards, holds and paused schedules remain. [Validation and pending steps](VM-PAGE-TABLE-KERNEL-2026-11-04.md).
<!-- vmpt-kernel:end -->

<!-- switch-restored-p2p:begin -->
**November 4 repeated switch/P2P-enabled crash — testing stopped:** after the owner-reported single-PSU rewiring, peer read/write, HIP IPC and RCCL P2P/IPC correctness passed. Strata Qwen MTP then passed one strict tool check (83 tokens; load 67.224 s). During the next Maya Coder startup, before readiness or any inference request, Sapphire `13:00.0` logged SMU no-response at **14:56:42 Toronto**, MES failures/reset attempts and device loss from the bus at **14:57:00**. The independent heartbeat guard fired, and an owned KFD client remained beyond cleanup. The owner reported another crash; a new reboot, idle GPUs and inactive owned queues are verified. A stop sentinel and persistent GPU-fault hold prevent continuation. P2P remains enabled in the boot configuration; no new test or automatic retry is queued. The single-PSU change did not prevent recurrence; P2P itself versus switch/routing/driver/GPU/power remains unisolated. RMA assessment: the owner confirms the Sapphire is stable alone directly in the motherboard. Do not condemn the card yet; switch branch, logical GPU role and software interaction remain unisolated. A new two-file VM race fix is absent from the exact kernel source and passes a zero-fuzz dry run; its specific fault signature is not recorded here, so it is only a software candidate. At that earlier audit boundary, no kernel change or further GPU test had been made; see the later VM kernel checkpoint above. [Failure evidence and qualification limits](results/switch-restored-p2p-2026-11-04.json).
<!-- switch-restored-p2p:end -->

**Current mode: P2P disabled.** The following bounded correctness results are historical; see [active disable verification and qualification limits](AMD-P2P-DISABLE-2026-11-03.md).

**PASS: bounded bidirectional GPU peer read/write correctness, HIP IPC and RCCL P2P/IPC correctness.** The owner-rebooted ASUS TX GAMING B760M WIFI / i5-13600KF host now uses the PEX88096 with ACS **0x11** on the four Broadcom and two AMD 1479 downstream bridges, plus **identity GPU IOMMU domains** from `iommu=pt`. Both GPUs share the Gen4 x16 upstream link; each branch includes Gen4 x8. RAM remains **30.60 GiB visible**; the planned 64 GB is still pending.

## Correctness and transport

- HIP reports peer access both ways in fresh default, fine-grain, and fine-grain/no-SDMA processes.
- GPU kernels directly read and write the other GPU's allocation: **three deterministic patterns, 16 MiB, both directions**. Full downloaded values match. Separate peer-copy correctness passes too; the GPU-kernel accesses establish direct peer-memory functionality independently of any copy API staging behavior.
- Separate fresh exec processes import HIP IPC memory handles and perform checked remote reads/writes in both directions. The exporting process verifies its allocation after child exit. Both pass.
- The retained nohostcall RCCL 2.27.7 passes two-rank all-reduce and all-gather on FP32/BF16 at 1, 4,096 and 1,048,576 elements. Logs show **P2P/IPC channels in both directions**. Only the isolated test enables P2P explicitly; existing runtime files are not edited.

## Bounded copy timings

One warmup is excluded, followed by eight checked samples per case. These are medians of synchronized, host-timed API calls, decimal GB/s; they are not sustained system benchmarks, wire-only latency or model token-rate predictions. All buffers are only 16 MiB maximum. The explicit host comparator copies through a pinned host buffer.

| Direction | 16 MiB peer copy | 16 MiB pinned-host staged copy | 4 KiB peer API elapsed |
|---|---:|---:|---:|
| GPU0 → GPU1 | **13.761 GB/s** | 5.902 GB/s | 40.078 µs |
| GPU1 → GPU0 | **13.862 GB/s** | 5.841 GB/s | 37.139 µs |

## Retained failures and limits

The earlier translated-domain boot advertised HIP peers after ACS correction, but actual remote reads returned incorrect data both directions; a same-GPU baseline passed and fine grain did not fix the peer failure. The identity-domain boot passes that same integrity test. This establishes the successful configuration change in this test sequence; no full application speedup is inferred. The initial ACS flags preserved zero firmware controls instead of intended source-validation/upstream-forwarding settings; that implementation was corrected to explicit xx100x1 and its initial outcome remains recorded.

Two attempted forced-host RCCL correctness controls also passed, but their logs still selected P2P/IPC despite `NCCL_P2P_DISABLE=1`, including with the explicit P2P-level variable removed. **They are not counted as host-transport comparisons.** The pinned-host copy measurements above are separate explicit host staging. Production retains its existing disable flag; a flag alone must not be presented as proof of the application's actual transport. Reverify logs and correctness in any later requested model trial.

PyTorch emitted AMD SMI inventory warning code 32. Device enumeration, full checked tensors and collective execution passed, while the independent controller recorded sysfs VRAM/thermal telemetry. This warning is retained as a diagnostic limitation.

## Guardrails and resulting state

Each stage used the existing GPU reservation protocol, managed scope, memory/spill guard and thermal sampling. Sampled owned swap and dedicated-VRAM spill were **zero**; all owned processes exited and reservations were released, with no remaining KFD clients. Curated results include minimum available RAM and per-card free VRAM. No inference model was loaded, no new kernel fault/reset was found in the checked interval, and no production launcher, model allocation, numerical setting, RAM hold, guard or updater schedule changed. The updater remains paused.

The successful ACS + identity-domain boot policy remains installed. `amd_p2p_support.py rollback-trial` stages restoration of the earlier ACS-only policy if the owner requests it; its previous files remain saved. Hardware-level P2P is qualified within the tested sizes/patterns; model/application transport and speed are **not** newly qualified. No further GPU test is pending for this bounded request.

[Curated results, timings and guard minima](results/amd-p2p-qualified-2026-11-03.json). [Routing installer, rollback and earlier evidence](AMD-P2P-ROUTING-SUPPORT-2026-11-03.md).
