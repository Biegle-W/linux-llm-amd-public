# Monitor/display contribution investigation — November 5, 2026

**A connected monitor is a plausible contributing variable, but the available evidence does not establish it as the crash trigger.** The most specific recorded failure is loss of PCI/SMU access to Sapphire during loading. No GPU test, hold release or runtime change was made for this investigation. [Structured findings](results/MAYA-DISPLAY-MONITOR-INVESTIGATION-2026-11-05.json).

The owner reports that the successful early DeepSeek run had no physical monitor attached, whereas a monitor was connected to watch the later failures. That is a relevant difference to isolate. Historical connector/EDID/CRTC state was not saved at the successful 04:14 test, and the exact plug-in time/earlier port is not independently recorded.

## What the evidence establishes

| Question | Finding |
|---|---|
| Where is the monitor connected now? | PowerColor `13:00.0`, HDMI-A-4, enabled with DPMS On. |
| Which GPU first failed? | Sapphire `0b:00.0`, logical model GPU1. The monitor is currently on the other physical GPU. |
| Which GPU provided the kernel framebuffer on the failed boot? | PowerColor `13:00.0`. This is a framebuffer assignment, not a saved connector snapshot at the instant of failure. |
| Was Display Core absent on the successful boot? | No. Both successful and failed boots initialized Display Core3.2.369/DCN3.2 on both cards and a PowerColor framebuffer. A later unplugged monitor does not imply unloaded display code. |
| Was an ordinary desktop compositor required? | Current display-manager is inactive with no compositor process observed; the failed boot has no saved GNOME Shell records. The kernel display/console path remains relevant. |
| Does the latest fault prove physical card removal? | No. The exact kernel helper prints lost-from-bus when a `PCI_COMMAND` configuration read fails or returns a PCI error value, after an unexpected SMU response. This proves failed access at that point, not why it failed. |

The earlier 18:45 failure began with a Sapphire SMU no-response message. Sapphire DMCUB errors followed **30.686s later**, PowerColor vblank timeout **34.851s later**, and the CPU hard-lockup report **58.368s later**. Its stack included display/vblank register-reading functions; the exact GPU associated with that stack is not established. Display activity could have contributed to escalation into a host freeze, but the ordering does not establish it as the initiating event. The latest saved kernel journal ends at the initial lost-bus/SMU fault, so it cannot establish that later sequence again.

The first complete sample of the reported-headless successful load recorded Sapphire12W/PowerColor8W, compared with53W/10W before the failed load progressed. Clock ranges and preceding work also differed. Those measurements are clues about different runtime states, not a controlled monitor comparison: fresh peer work and cold Lt tuning are confounders. There is no saved separate PCIe AER/DPC/link-error record in the latest trial window; the incomplete journal prevents ruling a link/power-state problem out.

## Why the monitor remains plausible

Kernel documentation treats display as a separate AMDGPU subsystem and describes display/power-management interactions and methods to isolate Display Core. DMCUB belongs to the display subsystem. This supports investigating display state; it does not identify a matching bug on this machine. [Display debugging](https://docs.kernel.org/gpu/amdgpu/display/dc-debug.html), [DCN architecture](https://docs.kernel.org/gpu/amdgpu/display/dcn-overview.html).

A physical monitor can alter the active display and clock/power-management conditions. Here, its location on PowerColor while Sapphire first loses access weakens a direct same-card display explanation. A multi-GPU interaction or display-related escalation remains possible. The patched kernel changed VM page-table code, not the Display Core source; its selection never established a display fix.

The useful next comparison, if separately authorized after fault review, is one guarded headless run with remote durable logs, matching kernel, source, weights, placement, cache state and protections. Do not combine that comparison with changed clocks, power caps, PCIe settings or display-driver parameters. Physical unplugging and disabling Display Core are different experiments. **No such trial is prepared or running.** The latest fault hold and all41 prior failure-evidence pins remain unchanged; root cause remains unresolved.
