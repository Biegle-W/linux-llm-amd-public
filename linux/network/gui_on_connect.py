#!/usr/bin/env python3
"""Start the graphical login screen only when a local USB workstation is present."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def properties(path):
    try:
        return dict(line[2:].split('=', 1) for line in path.read_text().splitlines()
                    if line.startswith('E:') and '=' in line)
    except OSError:
        return {}


def detect(drm=Path('/sys/class/drm'), inputs=Path('/sys/class/input'),
           udev=Path('/run/udev/data'), connectors=('HDMI-A',)):
    displays = []
    for status in drm.glob('card*-*/status'):
        try:
            if any(f'-{kind}-' in status.parent.name for kind in connectors) and status.read_text().strip() == 'connected':
                displays.append(status.parent.name)
        except OSError:
            continue
    keyboard = mouse = False
    for event in inputs.glob('event*'):
        try:
            device = event.joinpath('dev').read_text().strip()
        except OSError:
            continue
        props = properties(udev / ('c' + device))
        if props.get('ID_BUS') == 'usb':
            keyboard |= props.get('ID_INPUT_KEYBOARD') == '1'
            mouse |= props.get('ID_INPUT_MOUSE') == '1'
    return {'display': bool(displays), 'usb_keyboard': keyboard, 'usb_mouse': mouse,
            'ready': bool(displays) and keyboard and mouse}


def activate(state, run=subprocess.run):
    if not state['ready']:
        return False
    if run(['systemctl', 'is-active', '--quiet', 'display-manager.service']).returncode == 0:
        return False
    run(['systemctl', 'start', 'display-manager.service'], check=True)
    print('Local display, USB keyboard and USB mouse detected; graphical login started.', flush=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Print detection state without changing any service')
    args = parser.parse_args()
    connectors = tuple(os.environ.get('LOCAL_LLM_GUI_CONNECTORS', 'HDMI-A').split(','))
    if not connectors or not set(connectors) <= {'HDMI-A', 'DP'}:
        parser.error('LOCAL_LLM_GUI_CONNECTORS must contain HDMI-A and/or DP, comma separated')
    state = detect(connectors=connectors)
    if args.check:
        print(json.dumps(state))
    else:
        activate(state)


if __name__ == '__main__':
    main()
