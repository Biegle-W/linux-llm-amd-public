# AMD PEX88096 routing support — November 3, 2026

**Status: administrator audit confirms ACS control 0x1d on four Broadcom bridges and two AMD 1479 bridges directly above the GPUs. The revised six-bridge installer passes 25 CPU checks; administrator staging/reboot remain pending. No boot setting or live PCI register changed; P2P is not fixed or qualified.** The owner requested installation of the support needed for the installed PEX88096 and dual RX 7900 XTX. Linux already binds the switch ports to `pcieport`; no additional generic PLX driver is indicated. The working NVIDIA configuration had a scoped ACS correction, while current AMD HIP peer access is false both ways. [Measured result and working NVIDIA comparison](PCIE-SWITCH-P2P-CHECK-2026-11-03.md).

The prepared `amd_p2p_support.py` uses the existing kernel's documented `pci=config_acs` support before amdgpu initializes. It does not replace amdgpu, ROCm, the kernel or firmware. No NVIDIA-specific driver is installed.

## Scope and admission

The administrator installer reads extended PCI configuration and rediscovers exactly two 24 GB amdgpu Navi31 graphics functions with a common approved Broadcom PEX880xx ancestor. It selects **exactly four Broadcom downstream bridges plus exactly two AMD 1479 downstream parents, one directly above each GPU** along their paths, excluding CPU root ports, GPU endpoints, other AMD bridges, empty branches and unrelated devices. Its expected controls are the known-working-reference values **0x1d / 0x11**. Any other control or an additional redirecting bridge refuses installation for separate review. If the request/completion redirect bits are already clear, it refuses an unnecessary repair.

For admitted paths, kernel flags `xxx00xx` clear only ACS bits 2/3 (mask **0x0c**), preserving all other controls. Hierarchical device/function path selectors tolerate secondary bus renumbering and avoid a vendor-wide match. The configuration applies to normal and recovery Ubuntu kernel entries. Exact token quoting, generated kernel entries and GRUB syntax are checked; existing boot options remain. The change permits peer forwarding within those selected branches and can alter their IOMMU grouping. No global ACS override or IOMMU-mode change is staged. The current translated-domain difference can be assessed separately if peer access remains unavailable.

The installer writes one managed root-owned GRUB drop-in plus root-private state and backups. Existing conflicting/unmanaged ACS policy, symlinks, unknown state or active GPU reservations cause refusal. A staging/generation/verification failure restores the prior GRUB configuration and removes the new managed files. Installation performs **no live PCI register write, GPU driver unload/reset, display restart or reboot**. Because KFD peer topology is established during device initialization, a boot-time correction is used instead of assuming a live register write would update the cached peer graph.

## Installation and verification

From the operational checkout, with administrator authentication:

```bash
sudo python3 hardware/amd_p2p_support.py audit
sudo python3 hardware/amd_p2p_support.py install
```

The install action performs its own audit; the separate audit is optional. It stops without staging anything if actual controls do not meet admission. A successful result explicitly says that the policy is staged for reboot. **Reboot remains owner-controlled.** Do not call preparation or staging a working-P2P result.

After reboot:

```bash
sudo python3 hardware/amd_p2p_support.py verify
```

Then repeat the existing guarded HIP capability check, followed only on success by direct peer read/write correctness, HIP IPC and bounded RCCL qualification. Production `NCCL_P2P_DISABLE=1`, model holds/guards and updater pause stay until separately qualified. No model test or profile restoration is part of this installer.

To remove the managed next-boot policy:

```bash
sudo python3 hardware/amd_p2p_support.py rollback
```

Rollback regenerates and verifies GRUB; the current boot remains unchanged. The retained root-private backup records the original generated boot file. Reaudit the selectors after moving the switch or changing the motherboard/root slot.

## Validation

**25 CPU tests pass per checkout**, using synthetic PCI capability/topology records and temporary boot files. The audit retains all bridge controls and admission errors even when installation is refused. Tests cover six-bridge discovery and exact AMD parent identity, root/endpoint/unrelated-path exclusion, preservation of ACS bits outside 0x0c, hierarchy selectors, malformed/truncated/cyclic capabilities, unexpected controls, other redirecting bridges, shell/GRUB token quoting, existing-policy/symlink refusal, no-op refusal, transactional staging rollback and safe removal rollback. These are installation-logic checks; no administrator stage, reboot or new GPU test occurred during preparation.

Sources: [Linux 7.0 kernel parameters](https://www.kernel.org/doc/html/v7.0/admin-guide/kernel-parameters.html), [PCI path selector and ACS implementation](https://github.com/torvalds/linux/blob/v7.0/drivers/pci/pci.c), [working NVIDIA ACS reference](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/PEX-ACS-PAIR-20261031.md).

[Curated preparation state](results/amd-p2p-routing-support-2026-11-03.json).
