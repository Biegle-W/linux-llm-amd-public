# Planned ASUS DDR5 / 13600KF / 64 GB platform with an active PCIe switch — November 3, 2026

The owner plans to return this machine to **ASUS TX B760M DDR5, Intel Core i5-13600KF and 64 GB DDR5**, and clarified that both AMD GPUs will connect through an **active PCIe switch**, rather than motherboard lane bifurcation. The CPU spelling and DDR5 variant were confirmed. The matched ASUS reference is TX GAMING B760M WIFI, not its D4 variant; verify the installed board's exact DMI/model after the swap. The earlier PEX88096 proposal remains the reference switch candidate; the complete switch board, firmware and port configuration still need to be checked when installed.

The CPU, motherboard and switch are now installed; RAM remains pending. See the [post-reboot observations](ASUS-PCIE-SWITCH-INSTALLED-2026-11-03.md) for current hardware, link widths and display-rule installation status. The original plan below records intent; no runtime, CPU affinity, memory profile, driver, kernel, boot setting or model hold is changed by this documentation.

## Intended topology

```text
13600KF CPU PCIe graphics root port
    └── ASUS CPU-connected x16 slot
          └── active transparent PCIe switch
                ├── RX 7900 XTX GPU0
                └── RX 7900 XTX GPU1
```

Both GPU links must come from that same switch. The switch presents downstream PCIe bridges; the motherboard host slot remains one upstream link. A passive bifurcation adapter is a different arrangement. The board's chipset-connected secondary GPU slot is outside this intended path.

The [ASUS DDR5 manual](https://dlcdnets.asus.com/pub/ASUS/mb/LGA1700/TX_GAMING_B760M_WIFI/C21825_TX_GAMING_B760M_WIFI_UM_12P_WEB.pdf) identifies a CPU PCIe 5.0 x16 slot, a chipset PCIe 4.0 physical-x16 slot operating at x4, and CPU-attached M.2_1. Use the CPU x16 slot for the switch; the planned common-switch GPU path bypasses that chipset x4 slot. The upstream negotiated generation/width is limited by the actual switch board and link. CPU transfers share its upstream bandwidth; local peer traffic may remain inside the switch. This is topology intent, not a measured speedup or established GPU peer capability.

[Linux's P2PDMA explanation](https://docs.kernel.org/driver-api/pci/p2pdma.html) motivates a common-switch route rather than unsupported cross-root forwarding. The actual HIP/RCCL behavior is a separate verification. [Broadcom's PEX88000 brief](https://docs.broadcom.com/doc/BC-0484EN) documents the earlier candidate switch family; a chip name alone does not establish the complete expansion board's wiring/firmware, transparent-port mode or ACS/BAR behavior.

## CPU, RAM and display implications

- Intel lists the [13600KF as lacking processor graphics](https://cdrdv2-public.intel.com/841760/Intel-Core-i5-HD-GFX.pdf). Keep the monitor on an AMD card; motherboard HDMI/DisplayPort is not a fallback with this CPU. The current AMD-primary policy matches that requirement.
- **64 GB total is the next planned RAM capacity.** Earlier 96 GB planning is conditional future work, not capacity available for this swap. Recalculate physical/available RAM, engine allocations and conservative context/cache limits against actual installed memory.
- Saved 64 GB profiles require at least 60 GiB visible physical RAM and sufficient idle available memory. Restore only retained-model settings after owner confirmation/request and actual admission. More RAM does not enable retired/missing Super IQ3 or old DeepSeek weights; replacement candidates require their separate preparation and short qualification.
- CPU thread counts/affinity and sensors must be checked on the installed CPU/board. Current 13900KS placement is not assumed appropriate for the changed CPU. Kernel, source/runtime pins and numerical settings remain until an authorized adjustment is justified.
- PCI/DRM numbering can change behind the new board/switch. Re-discover both AMD cards and re-run `sudo bash hardware/install-amd-desktop-primary.sh` to regenerate its exact PCI-parent match. Do not copy the old GPU address into the new platform. The GUI still starts only on actual keyboard/mouse activity; boot remains headless.

## After the owner reports installation

First perform read-only admission: actual CPU/DMI, DIMM type/usable capacity, negotiated link widths/speeds, common-switch ancestry (`lspci -t`), GPU identities/driver/VRAM, BAR mappings, mounts/model paths and device/sensor discovery. Keep the system streaming NVMe on the intended CPU-attached M.2 path where available; ordinary resident weights remain on SATA. Recheck local/remote access and the selected display card.

Inspect the complete switch's power/firmware/upstream/downstream configuration, Above-4G/ReBAR availability and ACS routing. No blanket ACS override, IOMMU change, firmware flash or kernel/driver replacement is authorized by this note. Keep the known-working host-transport fallback until actual peer access and correctness are established.

Only with an owner request to execute GPU work: verify peer capability both ways, real bidirectional data integrity/direct access and HIP IPC, then bounded RCCL correctness and logs showing the chosen transport. A copy API success can hide host staging; a shared PCI ancestor alone is not sufficient proof. Test P2P in an isolated process before changing the normal `NCCL_P2P_DISABLE=1` fallback. Any persistent transport change must have its own evidence.

After transport/capacity admission and requested profile restoration, use only one short real DSH harness tool-call check per requested model, with verified owned unload before switching. No automatic held-model resume, long/full-context benchmark, repeated performance matrix, candidate promotion or updater restart is queued.

The original planning update performed no installation or GPU work. The subsequent owner-installed platform has now received read-only discovery; see the observations linked above. Complete RAM installation and requested admission before profile/transport changes.

[Curated planning state](results/asus-64gb-switch-plan-2026-11-03.json).
