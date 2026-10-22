#!/usr/bin/env bash
# Keep every GNOME session (local or remote-desktop) on the Intel iGPU; never restart a session.
set -euo pipefail
if [[ $EUID != 0 ]]; then
    printf '%s\n' 'Run this reviewed installer with sudo or pkexec.' >&2
    exit 1
fi
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
for rule in 61-local-llm-intel-primary.rules 62-local-llm-amd-desktop-ignore.rules; do
    udevadm verify "$here/$rule"
    install -m 0644 -o root -g root -- "$here/$rule" "/etc/udev/rules.d/$rule"
done
udevadm control --reload-rules
# Re-tag only the Intel and RX 7900 XTX DRM nodes; no driver reload or GPU reset.
for device in /sys/class/drm/card[0-9]* /sys/class/drm/renderD[0-9]*; do
    [[ ${device##*/} != *-* ]] || continue
    [[ -f $device/device/vendor && -f $device/device/device ]] || continue
    id="$(<"$device/device/vendor"):$(<"$device/device/device")"
    if [[ $id == 0x8086:0xa780 || $id == 0x1002:0x744c ]]; then
        udevadm trigger --action=change "$device"
    fi
done
udevadm settle --timeout=15
printf '%s\n' 'Installed. Log out and back in (or reconnect remote desktop after logout) for GNOME to use only the Intel iGPU.'
