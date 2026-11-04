# Isolated AMDGPU VM page-table kernel candidate

Patched kernel booted; all four bounded P2P correctness/transport stages passed; owned cleanup verified and fault hold restored.

The retained Ubuntu source package hash matches the prior audit. All 93,128 regular source files were compared with the retained archive; only `amdgpu_vm.c` and `amdgpu_vm_pt.c` differ. The patch records page-table clear fences in `last_update` and waits for them before CPU updates. This is separate from the older six-file MES candidate.

The full kernel and 6,901 modules compiled as `7.0.14-42-vmpt1`. The retained source reports a 7.0.14 base; the custom release name distinguishes it from Ubuntu’s packaged 7.0.0-42 ABI name. Ubuntu feature settings, including Rust and BTF, are retained. Configuration differences are the unique release suffix and removal of unavailable distribution trust/revocation certificate filenames; modules use a locally generated build key. The source-only tar omits the Debian packaging signing hook, so all 6,901 staged modules were explicitly signed. AMDGPU’s detached signature was cryptographically verified against the certificate embedded in the linked kernel. Secure Boot was verified disabled.

The stock `7.0.0-42-generic` kernel is retained. Privileged validation verified its original artifact hashes and the stock persistent GRUB default; the candidate was selected for one boot and its one-shot entry is now cleared. The first unattended administrator launch could not authenticate. The subsequent owner-authenticated run installed the candidate files, generated its initramfs and GRUB entry, and pinned stock as default. It stopped at the incorrect initramfs check before arming a reboot. No installed dependency package, production setting, hold or paused schedule was changed by build preparation.

Fresh post-reboot admission requires the candidate kernel/module identity, both physical board identities, all six ACS controls at `0x11`, identity IOMMU domains, idle KFD and a clean current-boot fault scan. The new one-shot controller permits only capability, local correctness, bidirectional 16 MiB direct/IPC correctness and two-rank RCCL transport checks, preserving the existing resource, storage-health, temperature, heartbeat and cleanup guards. It refuses duplicate trials and retains the fault hold. No model startup is queued. Direct current-boot PCI reads are preferred; if administrator reads are unavailable after reboot, admission requires the privileged preboot audit, unchanged paths/selectors and all six exact current-boot ACS programming records, and records that evidence limit.

The four bounded peer stages now pass on the actual patched kernel; model startup, inference and sustained stability remain untested. A bounded pass cannot establish sustained stability or root cause. The slot change is a confounder.

[Upstream patch](https://lists.freedesktop.org/archives/amd-gfx/2026-October/154551.html). [Machine-readable validation](results/vm-page-table-kernel-2026-11-04.json). [Audited two-file patch](patches/amdgpu-vm-pending-update.patch).

## Initramfs validator repair

The image contains `/init`, the candidate module directory, `nvme.ko` and `nvme-core.ko`. Ext4 and simpledrm are built into this kernel, and Plymouth selects simpledrm. Requiring AMDGPU inside the host-only initramfs was an installer bug; the signed AMDGPU module can load from the installed root filesystem. All 6,901 installed modules match the signed payload. No kernel rebuild, forced early GPU loading or guard relaxation is needed.

The corrected [validator](kernel_initrd_validation.py) checks the actual boot path and rejects missing modular root-storage support or a mismatched kernel release. Six [regression tests](test_kernel_initrd_validation.py) pass. The same administrator entry point now resumes with validation of existing files and leaves the original backup intact. It rechecks stock and candidate hashes, the stock boot default, ACS, IOMMU and holds before arming the one-shot boot. At that repair checkpoint, privileged final validation and reboot were pending. The subsequent validated boot and bounded peer results are recorded below.

## Candidate boot and four short peer checks

`7.0.14-42-vmpt1` is running with the expected AMDGPU source identity and no module taint. The stock kernel remains the persistent default. One fresh owned queue completed exactly four stages, then stopped:

| Guarded stage | Result | Stage elapsed seconds |
|---|---|---:|
| Peer capability, three environments | Passed | 0.856 |
| Local correctness on both cards, three patterns | Passed | 0.562 |
| Bidirectional 16 MiB direct/peer-copy/HIP IPC correctness | Passed | 0.575 |
| Two-rank RCCL all-reduce/all-gather with P2P/IPC | Passed | 8.132 |

RCCL logged four P2P/IPC connections. All owned cgroups emptied and KFD is empty. No new GPU/reset/bus-loss/OOM fault was found; the prior fault hold was restored and model profiles are unchanged. Sampled peaks across 36 samples were GPU edge 25°C, junction 34°C, memory 44°C and CPU 51°C. These are sampled maxima during short checks, not guaranteed transient peaks. Owned swap and spill remained zero. Worker memory.high equaled memory.max at actual MemTotal minus 1 GiB. Existing RAM/VRAM, storage-health, thermal, heartbeat, timeout and cleanup guards remained active.

Both live IOMMU domains are identity. Postboot ACS evidence consists of six exact current-boot `0x11` programming records, unchanged bridge paths/selectors, and the privileged preboot direct-register audit; direct postboot register reads were not obtained. Actual peer integrity and logged P2P/IPC provide functional routing evidence.

PyTorch logged a nonfatal AMDSMI initialization warning 32; the collectives and transport assertions passed while independent sysfs thermal telemetry remained available. No model trial or further automatic GPU work is queued. Passing short peer checks does not validate a model-startup path or establish that the VM race patch fixes a prior failure. The concurrent slot change also limits causal attribution.

Later model checks have now run under the same patched boot. Three strict short tool checks pass; both Q1 variants and GLM stop at the retained decode guard with verified unload. PLE/Super conditional work is in progress. [Model checkpoint](PATCHED-KERNEL-MODEL-CHECKS-2026-11-04.md).
