#!/usr/bin/env bash
# Prefer the first AMD card for the next GUI session; keep headless boot.
set -euo pipefail
if (( EUID != 0 )); then
    echo 'Run this reviewed installer with sudo.' >&2
    exit 1
fi
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec 9>/run/lock/local-llm-display-primary.lock
flock -n 9 || { echo 'Another display-policy installer is running.' >&2; exit 1; }
generated=$(mktemp --suffix=.rules)
trap 'rm -f -- "$generated"' EXIT
python3 "$here/desktop_primary.py" --write-rule "$generated"
udevadm verify "$generated"
target=/etc/udev/rules.d/63-local-llm-amd-primary.rules
# Refuse unknown local policy before touching any file.
for old in 61-local-llm-intel-primary.rules 62-local-llm-amd-desktop-ignore.rules; do
    if [[ -e /etc/udev/rules.d/$old ]] && ! cmp -s -- "$here/$old" "/etc/udev/rules.d/$old"; then
        echo "Local $old differs from the reviewed policy; no files changed." >&2
        exit 1
    fi
done
if [[ -e $target ]] && ! head -n 1 "$target" | grep -qx '# Managed local-llm GNOME AMD primary policy. Firmware/cabling are separate.'; then
    echo 'An unmanaged AMD preference exists; no files changed.' >&2
    exit 1
fi
backup=$(mktemp -d /var/tmp/local-llm-display-primary.XXXXXX)
chmod 0700 "$backup"
for old in 61-local-llm-intel-primary.rules 62-local-llm-amd-desktop-ignore.rules 63-local-llm-amd-primary.rules; do
    [[ ! -e /etc/udev/rules.d/$old ]] || cp -p -- "/etc/udev/rules.d/$old" "$backup/$old"
done
install -m 0644 -o root -g root -- "$generated" "$target"
rm -f -- /etc/udev/rules.d/61-local-llm-intel-primary.rules /etc/udev/rules.d/62-local-llm-amd-desktop-ignore.rules
udevadm control --reload-rules
for node in /sys/class/drm/card[0-9]* /sys/class/drm/renderD[0-9]*; do
    [[ ${node##*/} != *-* ]] || continue
    [[ -f $node/device/vendor && -f $node/device/device ]] || continue
    id="$(<"$node/device/vendor"):$(<"$node/device/device")"
    if [[ $id == 0x8086:0xa780 || $id == 0x1002:0x744c ]]; then
        udevadm trigger --action=change "$node"
    fi
done
udevadm settle --timeout=15
echo "AMD GPU0 preferred for the next GNOME session. Previous rules backed up in $backup"
echo 'No desktop restart, GPU reset, driver change, inference change or firmware write performed.'
echo 'Move the display cable to the first AMD card. Headless boot/input-trigger behavior is unchanged.'
