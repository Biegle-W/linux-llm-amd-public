#!/bin/sh
# Installs coolercontrol-config.toml (max-cooling fan curves for all fans) and restarts
# CoolerControl, which applies it at every boot. Run with sudo.
# Undo: sudo cp /etc/coolercontrol/config.toml.before-max-cooling /etc/coolercontrol/config.toml && sudo systemctl restart coolercontrold
set -eu
cd "$(dirname "$0")"
systemctl stop coolercontrold
[ -f /etc/coolercontrol/config.toml.before-max-cooling ] || cp -p /etc/coolercontrol/config.toml /etc/coolercontrol/config.toml.before-max-cooling
install -m 644 coolercontrol-config.toml /etc/coolercontrol/config.toml
systemctl start coolercontrold
systemctl is-enabled coolercontrold
sleep 20
journalctl -u coolercontrold --since "-30s" --no-pager -o cat | grep -iE "applied|error|warn|fail"
echo
for h in /sys/class/hwmon/hwmon*; do
  case "$(cat "$h/name")" in nct6687|amdgpu)
    for f in "$h"/fan*_input; do printf '%s %s %s RPM\n' "$(cat "$h/name")" "$(basename "$f" _input)" "$(cat "$f")"; done;;
  esac
done
