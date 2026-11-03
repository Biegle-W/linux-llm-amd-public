# New PCIe switch: HIP peer access check — November 3, 2026

**Result: direct P2P is not available in the current configuration.** Both RX 7900 XTX cards are below the installed, owner-confirmed Broadcom/PLX PEX88096 switch fabric on the ASUS TX GAMING B760M WIFI / i5-13600KF host, but HIP reports no peer access in either direction. This is a tested capability failure, not a bandwidth measurement or a verdict that the switch hardware cannot support P2P.

| Fresh isolated process environment | GPU0 → GPU1 | GPU1 → GPU0 |
|---|---|---|
| Default HIP | No peer access | No peer access |
| `HSA_FORCE_FINE_GRAIN_PCIE=1` | No peer access | No peer access |
| Fine grain + `HSA_ENABLE_SDMA=0` | No peer access | No peer access |

GPU0 maps to **0b:00.0** and GPU1 to **13:00.0**. `hipDeviceCanAccessPeer` itself returns success with capability false. A separate fresh diagnostic called `hipDeviceEnablePeerAccess` both ways: both returned **101 / `hipErrorInvalidDevice` / “invalid device ordinal”**, despite two devices being enumerated and each source being selected successfully. That error is recorded as observed; it is not reinterpreted as a different HIP error code. Neither diagnostic allocated data buffers or dereferenced peer memory.

The current boot log prints amdgpu’s generic “not supported by the chipset” message in both directions. **That wording does not identify the motherboard chipset as the cause:** both GPUs are confirmed behind the PEX88096 switch. In the [upstream amdgpu implementation](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/amdgpu/amdgpu_device.c), the message is emitted when the PCI peer-route check fails; it does not mean the GPUs are directly attached to separate motherboard ports. KFD exposes no GPU-to-GPU peer links. The amdgpu `pcie_p2p` parameter is already `Y`, kernel P2PDMA/HSA-P2P support is built, both cards have 32 GiB BAR0 apertures and full driver-visible VRAM. The common switch uplink is Gen4 x16, with x8 segments in each branch. RAM remains 30.60 GiB visible; the 64 GB installation is pending.

## Test gates and diagnosis

Direct peer-copy correctness, direct kernel loads/stores, HIP IPC and RCCL P2P stages were **blocked at their peer-capability prerequisite**, not marked as passed or as completed transfers. No direct bandwidth, host-comparator speed, model speedup or application qualification is claimed. Two guarded diagnostic stages completed normally; their successful process exit does not mean P2P passed.

The existing reservation protocol, memory/spill guards, thermal samples and owned-process cleanup were used. Both diagnostic process trees exited, reservations were released and no KFD clients remained. Owned swap and dedicated-VRAM spill were zero in all samples. No inference backend was loaded. A controller setup attempt initially rejected the systemd unlimited-swap spelling before HIP launch; the spelling was corrected to `infinity`, leaving the existing unlimited swap setting intact.

The precise routing blocker is still under investigation. Additional current-boot messages show that Linux consults the host-bridge P2PDMA allowlist and rejects host ID `8086:a704`. That records the kernel’s route decision, not the physical GPU placement or proof that switch-local forwarding is impossible. Non-root PCI access cannot inspect extended ACS capability controls, and the current IOMMU domain is translated. **ACS redirect is a hypothesis, not yet a measured cause.** Linux's [P2PDMA routing logic](https://github.com/torvalds/linux/blob/v7.0/drivers/pci/p2pdma.c) checks ACS redirection along the path; with redirection clear a shared-switch bus-address route can avoid the host allowlist, while redirection can force its use. This makes the switch-port ACS controls relevant even with the confirmed common-switch topology. Compare that policy with the actual privileged capability dump before proposing any scoped configuration change. The [HIP peer-access API](https://rocm.docs.amd.com/projects/HIP/en/docs-7.1.0/doxygen/html/group___peer_to_peer.html) documents the capability and enable calls used here.

Existing `NCCL_P2P_DISABLE=1` host transport, runtime pins, guards, RAM holds and updater pause remain. No ACS override, IOMMU/boot change, firmware write, kernel/driver replacement or automatic model trial occurred. Next action: inspect the read-only privileged switch/bridge ACS report; propose a scoped, reviewable fix only if its evidence supports one. Repeat direct qualification only after peer capability becomes available.

[Curated observations and guard minima](results/pcie-switch-p2p-check-2026-11-03.json).
