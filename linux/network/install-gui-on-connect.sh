#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
    echo 'Run this installer with sudo.' >&2
    exit 1
fi
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
install -d -m 0755 /usr/local/libexec
install -o root -g root -m 0755 "$ROOT/gui_on_connect.py" /usr/local/libexec/local-llm-gui-on-connect.py
for unit in local-llm-gui-on-connect.service local-llm-gui-on-connect.timer; do
    install -o root -g root -m 0644 "$ROOT/$unit" "/etc/systemd/system/$unit"
done
if [[ ! -e /etc/default/local-llm-gui-on-connect ]]; then
    install -o root -g root -m 0644 "$ROOT/gui-on-connect.conf" /etc/default/local-llm-gui-on-connect
fi
systemctl daemon-reload
systemctl set-default multi-user.target
systemctl enable --now local-llm-gui-on-connect.timer
echo 'Enabled display + USB keyboard + USB mouse detection; existing desktop/inference left running.'
