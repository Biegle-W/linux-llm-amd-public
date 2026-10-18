# Second GPU: BIOS picture, Linux black screen — October 18, 2026

Status: **unresolved display handoff/connection issue; no repair applied**.
The owner reports a picture from the second GPU in BIOS, followed by no video
output in the OS. The currently working cable path was inspected, not a captured
failure with that cable left on the other GPU. A controlled hotplug comparison
was requested. No display-server restart, driver reinstall, firmware flash,
monitor configuration reset or display-mode change was performed.

## Observations

| Item | Observed |
| --- | --- |
| Session | GNOME/Mutter 50.1, Wayland |
| Kernel | 7.0.0-38-generic |
| Sapphire RX 7900 XTX | PCI 03:00.0, DRM card1, amdgpu loaded and active |
| PowerColor RX 7900 XTX | PCI 06:00.0, DRM card2, amdgpu loaded and active |
| Current active monitor | Sapphire DP-1, 3840x2160 at about 59.997 Hz, scale 2 |
| PowerColor connectors at inspection | DP-3, DP-4, HDMI-A-3 and HDMI-A-4 all disconnected, disabled, no mode list |
| Firmware boot-VGA designation | PowerColor/card2; GNOME also selects it as primary GPU |
| GNOME device discovery | both DRM cards added with atomic mode setting |
| Saved user monitor configurations | DP-1/2/3/4/5 entries at 3840x2160, about 60 Hz; no disabled connector entries |
| Display-related kernel parameters | no video=, nomodeset, amdgpu.*, radeon.*, drm.* or VFIO/blacklist overrides found |
| GPU reset or ring-timeout evidence | none found in the inspected current-boot messages |
| EDID error | HDMI-A-3 on PowerColor: EDID read failed during boot |

The HDMI error is not proof of the reported DisplayPort fault. Saved connector
entries do not prove a stale configuration caused it. Both GPUs are visible and
neither is generally disabled. DRM card numbers and connector names can change
after hardware changes or reboot; identify the card by PCI path/brand as well.
No raw EDID, display serials, hostnames or user display configuration are published.

## Interpretation

A 60-second read-only connector capture observed no connector-state changes;
no failed hotplug was reproduced during that window.

A BIOS picture establishes that the tested card/port/display path can produce
an image under firmware settings. It does not establish operation at the mode
or link settings selected by the OS. Loss of video when Linux starts makes the
AMDGPU kernel-mode-setting / connector detection / GNOME handoff the relevant
next investigation. A cable or adapter can still work at a firmware mode while
failing a different OS link mode. A permanently dead GPU is not established.

The observation that the currently working monitor is on Sapphire means all
PowerColor connectors being disconnected may simply reflect that the cable was
moved back. It cannot diagnose the earlier failed state. If an actually plugged-in,
powered monitor remains disconnected in sysfs during the failure, investigate
hotplug/EDID/link detection before editing GNOME layouts. If it becomes connected
with modes but remains dark, compare modes, output enablement and compositor
state. No forced resolution is justified before seeing that state.

## Useful next test

With Linux already running, move the same working DP cable/monitor to the GPU
that showed BIOS but lost OS output. Leave it long enough to capture connector
state and hotplug logs, then return to the working port if needed. The requested
short observation is read-only. Compare:

- Does the new connector change to connected and expose modes?
- Does Mutter see/enable it, and at which mode?
- Do link-training/EDID, atomic-commit or GPU-reset errors appear?

Only after the monitor is detected should a temporary supported 1920x1080/60 Hz
or 3840x2160/60 Hz test be considered. Keep the known-working connection as a
recovery path. Do not disable Display Core, blacklist a GPU or reinstall the LLM
ROCm environments based on this symptom alone. No change to inference GPU policy
or automatic shutdown targets is required by these findings.

## Sources

- [Linux DRM connector status and mode-setting semantics](https://www.kernel.org/doc/html/latest/gpu/drm-kms.html).
- [AMDGPU Display Core debug guidance](https://www.kernel.org/doc/html/latest/gpu/amdgpu/display/dc-debug.html).
- [GNOME Mutter MonitorManager](https://gnome.pages.gitlab.gnome.org/mutter/meta/class.MonitorManager.html):
  the DisplayConfig D-Bus interface supplies the live compositor state.
