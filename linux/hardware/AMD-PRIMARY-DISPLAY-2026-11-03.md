# First AMD GPU preferred for graphical sessions — November 3, 2026

**Post-swap update:** PCI addresses changed. Current GNOME uses card2 / 13:00.0; regenerated first-card preference targets 0b:00.0 and is installed with root ownership/mode, exact bytes and all four live AMD tags verified. The original verification below is pre-swap evidence. [Current observation and pending step](ASUS-PCIE-SWITCH-INSTALLED-2026-11-03.md).

The owner requested moving default video output from Intel to the first AMD GPU because inference will run headless. The first validated AMD GPU (the same first card used by the dual-card inference device discovery) is now the GNOME/Mutter preferred primary device. The owner moved the monitor cable, and the connected DisplayPort connector is verified on that same AMD card. The installed preference and removal of the old Intel-only policy are verified. **Live renderer selection still needs a new graphical session; no session was restarted.**

## Selection and installation

`desktop_primary.py` discovers the two expected amdgpu Navi31 24 GB cards and selects the first in PCI order. It refuses missing/extra/unexpected cards or a different driver/capacity. It generates a rule with that exact PCI parent, since both cards have identical vendor/device IDs; it does not depend on changing DRM card numbers. Re-run the installer after a PCIe topology change so the selected PCI parent is refreshed.

The rule clears the superseded Intel-primary and AMD-ignore tags on card/render nodes, then marks only AMD GPU0 preferred. Intel remains available as a fallback; no GPU is blacklisted or unbound. The old `61-local-llm-intel-primary.rules` and `62-local-llm-amd-desktop-ignore.rules` are backed up and removed from the active rules directory. The new root-owned `63-local-llm-amd-primary.rules` matches the reviewed generated rule and has no group/other write permission.

From the repository root:

```sh
sudo bash hardware/install-amd-desktop-primary.sh
```

The installer verifies generated udev syntax and refuses conflicting unmanaged policy before editing. It records a root-owned backup directory, reloads udev rules and re-tags only the Intel/AMD DRM nodes. It does not restart GNOME/GDM, reset a GPU, reload a driver, change model configuration or write firmware. Legacy Intel-only installers/rules remain historical rollback material; they are not the current setup. Any deliberate reversion must remove the new policy before restoring the old one.

The implementation uses [GNOME's documented primary-GPU preference](https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md). The preference applies when Mutter creates a renderer for a new graphical session. The existing session journal still identifies its old Intel renderer; logging out/in or rebooting is needed to validate a fresh AMD renderer. The physical monitor is already connected to the selected AMD card.

## Headless inference and firmware boundary

Default boot remains `multi-user.target`. The existing keyboard/mouse-activity watcher remains running and starts graphical login only on fresh input with the required local devices present. No GUI auto-start-on-presence policy was restored. Both AMD cards remain available to inference, with identical ROCm device selection, source/runtime pins, RAM holds, VRAM/swap/thermal guards and paused updater.

When the desktop runs on AMD GPU0 it uses some of that card's VRAM. The owner plans to infer headless; the unchanged guards still admit or refuse loads based on real headroom. No guard was relaxed to accommodate an active desktop, and no inference was started for this display-policy change.

Firmware/BIOS/pre-OS boot video is a separate primary-adapter setting. The firmware currently identifies Intel as boot VGA; this installer does not change that. If pre-OS output is also required on the AMD ports, select the PCIe graphics adapter in firmware setup. Linux graphical output and firmware boot-video selection must not be reported as the same setting.

## Verification

- Nine CPU checks pass per checkout: selection order, ignoring non-graphics functions, missing/extra/wrong-driver/wrong-model/low-VRAM rejection, exact single-card preference, old exclusion clearing and invalid PCI input refusal.
- Shell syntax and `udevadm verify` pass. Dry runs against all six Intel/AMD card/render nodes give preference only to AMD GPU0, with neither AMD card ignored.
- Installed rule bytes, root ownership/mode, removed legacy rules and actual `CURRENT_TAGS` on all six nodes are verified. The monitor connector maps to the selected AMD GPU0.
- Headless default and running input watcher are verified. The existing display manager has the same activation time; no display/inference service restart or GPU model test occurred.

Remaining verification: after the owner's next graphical login/reboot, inspect the GNOME journal for AMD primary-renderer selection. No remaining installer job or task GPU reservation.

[Curated verification](results/amd-primary-display-2026-11-03.json).
