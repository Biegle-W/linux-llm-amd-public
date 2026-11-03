# Installed ASUS / 13600KF / switched dual AMD topology — November 3, 2026

**Subsequent P2P check:** peer capability and enable fail both ways; direct/IPC/RCCL stages remain blocked. [Measured result](PCIE-SWITCH-P2P-CHECK-2026-11-03.md).

Read-only post-reboot discovery confirms **ASUS TX GAMING B760M WIFI (BIOS 1836), Core i5-13600KF (14 cores / 20 threads)** and both RX 7900 XTX cards behind a common Broadcom/LSI PEX880xx Gen4 switch fabric, identified by the owner as PEX88096. The PEX88096 identification is owner-confirmed; the expansion-board model and firmware are not established by its generic PCI ID. **RAM installation remains pending: 32,084,672 KiB / 30.60 GiB is currently visible; 64 GB is the planned capacity.** Earlier benchmark timings retain their original CPU, RAM and topology attribution.

## Observed topology and allocation

| Item | Post-reboot observation |
|---|---|
| CPU root / common switch upstream | 00:01.0 → 01:00.0; PCIe 4.0 x16 negotiated at the switch uplink |
| First AMD graphics function | 0b:00.0, amdgpu, card1/renderD128 |
| Second AMD graphics function | 13:00.0, amdgpu, card2/renderD129 |
| First GPU branch | 02:04.0 → 07:00.0 → 08:00.0 → 09:00.0 → 0a:00.0 → 0b:00.0 |
| Second GPU branch | 02:08.0 → 0f:00.0 → 10:00.0 → 11:00.0 → 12:00.0 → 13:00.0 |
| Branch limits | 08:00.0 and 10:00.0 each negotiate PCIe 4.0 x8; both GPU endpoint links report PCIe 4.0 x16 |
| Per-card memory | 25,753,026,560 bytes VRAM, all CPU-visible through the driver; 32 GiB BAR0 aperture |
| Storage | System NVMe and shared SATA model volume mounted; migrated Sabrent device absent |

The x8 bridge segments limit each branch even though the endpoint reports x16. No new bandwidth or latency result is claimed. Shared ancestry and large BARs do not prove HIP peer access, direct data correctness, HIP IPC or RCCL transport. ACS/firmware details remain unverified. Existing host transport and `NCCL_P2P_DISABLE=1` remain selected; P2P execution requires the separate owner-requested isolated checks in the [installation plan](ASUS-64GB-PCIE-SWITCH-PLAN-2026-11-03.md).

## Desktop and runtime state

GNOME's current boot journal selects **card2 / 13:00.0** as boot-VGA primary, matching the connected DisplayPort monitor. The pre-swap AMD-primary preference matched the old 03:00.0 graphics address, which is now a switch bridge. The regenerated rule is now installed and selects the first validated AMD at **0b:00.0**. Nine existing CPU checks, udev rule verification and dry runs on all four current AMD card/render nodes pass. **Owner installation and post-install verification are complete:** installed bytes match the reviewed generated rule, the file is root-owned with mode 0644, and live card/render tags select only 0b:00.0 without ignoring either AMD card. The existing reviewed installer regenerates the rule from live sysfs; no source change is needed. It affects a later graphical session and does not restart the desktop. The current cable is on the second card; moving it to the first card aligns it with the standing first-card preference.

Headless default remains `multi-user.target`; the input-triggered GUI service is enabled/running and the old presence timer disabled/inactive. Hub/API and mount-preflight services are active. The daily updater timer/service remain inactive with no next run. No inference backend or task GPU reservation was observed. No model, peer test, inference benchmark, firmware write, kernel/driver change, transport change, RAM-profile restoration or hold removal occurred. RAM floors and all guards remain.

Next actions: observe the first-AMD renderer preference after the next graphical session; complete the planned RAM installation, then rediscover physical/available RAM before any requested capacity/profile work. P2P remains unqualified until separately requested direct-access/IPC/RCCL checks succeed.

[Curated observations](results/asus-pcie-switch-installed-2026-11-03.json).
