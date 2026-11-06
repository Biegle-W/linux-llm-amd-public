# Repeated GPU crashes: stock versus custom kernel — November 5, 2026

**The custom kernel is not the sole explanation, and returning to stock is not a demonstrated repair.** An earlier stock boot already recorded SMU nonresponse, MES queue-removal failure and attempted GPU recovery. The latest custom boot shows a similar initial sequence followed by a display/vblank interrupt hard lockup and multiple CPU soft lockups. Recovered board-placement records identify the same physical Sapphire card in both failures, on different switch branches but still logical GPU1 in the model runtime. This supersedes the earlier incorrect claim that different physical cards failed. It raises a Sapphire-specific or retained-runtime-role interaction and weakens a single fixed-branch explanation; it does not establish a defective card or clear the wider driver/firmware/PCIe/power environment.

**Keep inference held. The next comparison must separate the physical Sapphire card from its retained runtime GPU1 role, preferably on a separate diagnostic machine.** A previous direct CPU/bifurcated connection with the switch bypassed remains a topology comparison if the current hardware supports it, not an established repair. The owner reports Sapphire is stable alone. No hardware, software, boot or runtime setting was changed in this investigation.

## What the read-only comparison establishes

Seven recent boot journals were inspected. The table compares the earlier failed stock boot, the latest failed custom boot, and the current stock boot. Workloads and exposure differ; this is not a controlled kernel A/B.

| Item | Earlier stock failure | Latest custom failure | Current stock boot |
|---|---|---|---|
| Kernel | `7.0.0-42-generic` | `7.0.14-42-vmpt1` | `7.0.0-42-generic` |
| Relevant failure time, EST | Nov 4, 14:56:42 onward | Nov 5, 18:45:06 onward | No comparable GPU failure recorded during this inspection; no new GPU load |
| First GPU symptoms | SMU queries stop responding; MES REMOVE_QUEUE/reset trouble follows | SMU queries stop responding; MES REMOVE_QUEUE/reset trouble follows | Both cards enumerate; KFD observed empty |
| Later host failure | Journal ends during attempted GPU recovery | DMCUB/display error, vblank timeout, CPU19 hard lockup in `amdgpu_device_rreg`, multiple soft lockups | Idle enumeration is not a loaded stability qualification |
| Boot arguments apart from kernel image | Same six physical ACS selectors, `iommu=pt`, OverDrive feature mask | Same | Same |
| Recorded ACS programming | Same six bridges programmed to `0x0011` | Same | Same |
| SMU/DMUB firmware and BIOS/microcode version strings | Same reported versions | Same reported versions | Same reported versions |
| Persisted GPU VM/IOMMU fault, PCIe AER error or OOM | None found | None found | None found |

## Physical card versus runtime number
+
+| Compared failure | Physical board | Switch location | Model runtime role |
+|---|---|---|---|
+| Earlier stock boot, before the recorded slot swap | Sapphire | Original branch | Logical GPU1 |
+| Latest custom boot, after the slot swap | Sapphire | Other branch | Logical GPU1 |
+
+PCI addresses and monitoring indices are location/order labels, not permanent card identities. The comparison now uses contemporaneous pre-swap records, the recorded post-swap subsystem identities, and the qualified runtime order. The earlier review incorrectly applied an old board-to-address mapping to the later crash. It therefore mislabeled the latest failing device as PowerColor and incorrectly inferred that both physical cards had failed. Those claims are withdrawn.
+
+These two events followed Sapphire across the recorded branch swap, while its runtime role stayed the same. They do not establish “always the first GPU.” Card, retained runtime role, any power connections that moved with the card, and a multi-GPU software interaction remain confounded. Stable-alone history argues against declaring the card generally defective or recommending RMA from these records alone.
+
+The current loaded amdgpu source-version matches the installed stock module. Saved custom-boot evidence identifies the expected custom module. The two kernel configs differ only in local version and trusted/revocation certificate paths. The retained source audit limits custom source changes to the two VM page-table synchronization files. That patch addresses a specific update-ordering issue; its presence and four passing peer checks do not qualify every allocation, copy, model-loading or GPU-recovery path. Earlier stock failure means reverting that patch alone cannot be presented as a general fix; differing workloads also prevent clearing the patch of any role in the latest failure.

Both branches currently report Gen4 links with matching x8 segments behind a shared x16 uplink. All exposed current-boot AER counter lines were zero. These post-reboot observations do not establish link reliability during the failed boot. Linux documents AER reporting and its firmware-control requirements in the [AER guide](https://docs.kernel.org/PCI/pcieaer-howto.html).

## Why RAM, temperatures and warning labels do not explain it

The latest case has 49 completed saved samples over 13.79 seconds. Minimum available host RAM was 52.57 GiB and minimum free VRAM was 7.71 GiB per card. Recorded owned swap/spill and cgroup OOM events were zero. Sampled maxima were 53°C CPU and 46°C across GPU sensors. The last completed sample preceded the first SMU error by about 3 seconds; these readings do not exclude an unsampled transient or measurements lost after the device stopped responding.

The engine never reported ready, accepted no inference requests, and did not log completion of expert loading or RAM-store initialization. Its last sampled worker memory was about 8.05 GiB. The intended 36 GB cache is therefore not evidence of a completed 36 GB allocation or a RAM-capacity failure. The guard was interrupted during its telemetry snapshot; its traceback does not identify which kernel operation first wedged. The original six-second heartbeat and 15-second cleanup failures remain failed. Raising either timeout cannot guarantee recovery from a kernel/PCIe/MMIO lockup.

Two warnings require careful interpretation:

- **`CPU_OUT_OF_SPEC` does not establish a CPU defect.** The selected amdgpu source explicitly sets this taint when the OverDrive enable bit is present. The boot mask enables adjustment; it does not prove active overclocking or undervolting. Existing fan control depends on this enablement, so removing it requires a reviewed cooling plan. See the [upstream amdgpu initialization](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c).
- **The SMU interface-version warning is not proof of an incompatible or defective GPU firmware.** Both kernels/cards report it, and [SMU13 source](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/pm/swsmu/smu13/smu_v13_0.c) treats this mismatch as nonfatal because the interface is designed for backward compatibility. It does not justify flashing a VBIOS.

The current stock boot's out-of-tree/unsigned-module taints are associated in its journal with the motherboard sensor module. The custom failure already occurred without those two taint flags. This does not prove that module harmless, but its absence did not prevent the custom failure. Current firmware boot-error notification alone does not identify the original failing component; no new protected firmware-region capture was performed.

## Safest route before another model attempt

1. **Keep the existing persistent GPU fault hold.** Retain stock as the persistent default, GLM RAM8 and Maya DeepSeek without the candidate store. RAM40 remains prepared, unrun and blocked. All selected routes, prior final results and guards remain intact.
2. **Separate physical-card identity from the retained runtime role.** First audit placement and per-card loading behavior from saved source/logs. A future matched role comparison belongs on a separate diagnostic setup or in an explicitly authorized maintenance window because another kernel wedge can freeze this workstation. Track card, branch, power connection and runtime rank independently. A powered-off switch bypass/direct CPU connection is another comparison if supported by the current hardware; do not present it as a proved fix or repeat an unchanged full model load.
3. **Use a documented software baseline as a separate comparison.** The installed Ubuntu 26.04/kernel 7.0 stack is absent from the installed ROCm 7.2.3 [compatibility matrix](https://rocm.docs.amd.com/en/docs-7.2.3/compatibility/compatibility-matrix.html). The [Radeon matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html) lists Ubuntu 24.04.4/HWE 6.17 for its 7.2.1 release. An alternate boot device or bench host can provide a documented matched OS/kernel/driver/firmware/userspace baseline without replacing production. Exact engine compatibility must be reviewed before preparing it; a container alone does not replace the host driver.
4. **Avoid mixing the diagnostic workload with the workstation desktop.** AMD documents resets with some mixed graphics/compute workloads in its [multi-GPU guidance](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/native_linux/mgpu.html). The latest recovery failure involves the display IRQ path, but that does not prove the initially unresponsive card was the active display card or that this known issue caused the event. The current KF CPU has no integrated display fallback; motherboard video output is not a solution. Any later small single-card allocation/copy check, then dual-card check and finally model qualification needs separate authorization and the unchanged safeguards.

`iommu=pt` is already present in all compared boots, so [AMD's missing-IOMMU-setting remedy](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/install-faq.html#issue-5-application-hangs-on-multi-gpu-systems) is already applied. Reapplying it, repeating short peer tests unchanged, enlarging RAM caches, weakening guards, disabling display/MES with speculative flags, or flashing firmware is not an evidence-backed repair. Change one diagnostic variable at a time and retain the original failed outcomes.

## Limits and outcome

No GPU runtime, sensor query, workload, reset, unbind, reboot, hold release or configuration write was used for this comparison. Inspection used saved application/guard records, kernel journals, ordinary PCI sysfs identity/link/AER files, module metadata, configs and source. New privileged extended PCI capability/BERT reads were unavailable without terminal authentication; no privilege workaround or new live firmware extraction was attempted. Zero AER reports and cool samples cannot clear hardware or power delivery.

The supported conclusion is recurring loss of GPU responsiveness and failed recovery that can escalate into host lockup. **No single software fix or failed component is proved.** The next direction is to distinguish the physical-card and retained-runtime-role hypotheses outside the active workstation session, with topology and matched software comparisons kept separate. The GPU hold remains in place.

[Curated comparison](results/AMD-CRASH-KERNEL-COMPARISON-2026-11-05.json) · [Latest case and original cleanup failure](STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md) · [Runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)
