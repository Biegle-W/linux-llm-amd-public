#!/usr/bin/env bash
# Install only the matching Intel desktop preference; never restart a session.
set -euo pipefail
if [[ $EUID != 0 ]]; then
    printf '%s\n' 'Run this reviewed installer with sudo or pkexec.' >&2
    exit 1
fi
source_rule="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/61-local-llm-intel-primary.rules"
target_rule=/etc/udev/rules.d/61-local-llm-intel-primary.rules
if [[ -e $target_rule ]] && ! cmp -s -- "$source_rule" "$target_rule"; then
    printf '%s\n' 'A different Intel desktop rule already exists; review it before replacing it.' >&2
    exit 1
fi
udevadm verify "$source_rule"
install -m 0644 -o root -g root -- "$source_rule" "$target_rule"
udevadm control --reload-rules
# Trigger just the Intel display device; no driver reload or GPU reset.
for device in /sys/class/drm/card[0-9]*; do
    [[ ${device##*/} != *-* ]] || continue
    [[ -f $device/device/vendor && -f $device/device/device ]] || continue
    if [[ $(<"$device/device/vendor") == 0x8086 && $(<"$device/device/device") == 0xa780 ]]; then
        udevadm trigger --action=change "$device"
    fi
done
udevadm settle --timeout=15
printf '%s\n' 'Intel UHD 770 is preferred for the next GNOME desktop session. No session has been restarted.'
