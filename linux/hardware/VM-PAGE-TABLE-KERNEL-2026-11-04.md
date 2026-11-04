# Isolated AMDGPU VM page-table kernel candidate

Built and staged in an isolated workspace; administrator authentication required for host installation/reboot.

The retained Ubuntu source package hash matches the prior audit. All 93,128 regular source files were compared with the retained archive; only `amdgpu_vm.c` and `amdgpu_vm_pt.c` differ. The patch records page-table clear fences in `last_update` and waits for them before CPU updates. This is separate from the older six-file MES candidate.

The full kernel and 6,901 modules compiled as `7.0.14-42-vmpt1`. The retained source reports a 7.0.14 base; the custom release name distinguishes it from Ubuntu’s packaged 7.0.0-42 ABI name. Ubuntu feature settings, including Rust and BTF, are retained. Configuration differences are the unique release suffix and removal of unavailable distribution trust/revocation certificate filenames; modules use a locally generated build key. The source-only tar omits the Debian packaging signing hook, so all 6,901 staged modules were explicitly signed. AMDGPU’s detached signature was cryptographically verified against the certificate embedded in the linked kernel. Secure Boot was verified disabled.

The stock `7.0.0-42-generic` kernel is retained. The prepared installer verifies original artifact hashes, pins stock as the persistent GRUB default, and selects the candidate only with a one-shot boot. It requires administrator authentication. The attempted administrator launch stopped with `No authentication agent found`; the installer did not execute. No host installation, boot setting or reboot was performed. No installed dependency package, production setting, hold or paused schedule was changed by build preparation.

Fresh post-reboot admission requires the candidate kernel/module identity, both physical board identities, all six ACS controls at `0x11`, identity IOMMU domains, idle KFD and a clean current-boot fault scan. The new one-shot controller permits only capability, local correctness, bidirectional 16 MiB direct/IPC correctness and two-rank RCCL transport checks, preserving the existing resource, storage-health, temperature, heartbeat and cleanup guards. It refuses duplicate trials and retains the fault hold. No model startup is queued. Direct current-boot PCI reads are preferred; if administrator reads are unavailable after reboot, admission requires the privileged preboot audit, unchanged paths/selectors and all six exact current-boot ACS programming records, and records that evidence limit.

Build/source validation only; no patched-kernel P2P/inference qualification. A bounded pass cannot establish sustained stability or root cause. The slot change is a confounder.

[Upstream patch](https://lists.freedesktop.org/archives/amd-gfx/2026-October/154551.html). [Machine-readable validation](results/vm-page-table-kernel-2026-11-04.json). [Audited two-file patch](patches/amdgpu-vm-pending-update.patch).
