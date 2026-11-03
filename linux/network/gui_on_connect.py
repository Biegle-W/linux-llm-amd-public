#!/usr/bin/env python3
"""Start graphical login on fresh local input, never on device presence alone."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import time

EVENT = struct.Struct('@llHHi')  # Linux input_event, native timeval ABI.
EVIOCSCLOCKID = 0x400445a0
ARM_SECONDS = 2.0


def properties(path):
    try:
        return dict(line[2:].split('=', 1) for line in path.read_text().splitlines()
                    if line.startswith('E:') and '=' in line)
    except OSError:
        return {}


def input_devices(inputs=Path('/sys/class/input'), udev=Path('/run/udev/data'),
                  devices=Path('/dev/input')):
    found = {}
    for event in inputs.glob('event*'):
        try:
            device = event.joinpath('dev').read_text().strip()
        except OSError:
            continue
        props = properties(udev / ('c' + device))
        keyboard = props.get('ID_INPUT_KEYBOARD') == '1'
        mouse = props.get('ID_INPUT_MOUSE') == '1'
        if props.get('ID_BUS') == 'usb' and (keyboard or mouse):
            found[devices / event.name] = {'keyboard': keyboard, 'mouse': mouse}
    return found


def detect(drm=Path('/sys/class/drm'), inputs=Path('/sys/class/input'),
           udev=Path('/run/udev/data'), connectors=('HDMI-A',)):
    displays = []
    for status in drm.glob('card*-*/status'):
        try:
            if any(f'-{kind}-' in status.parent.name for kind in connectors) and status.read_text().strip() == 'connected':
                displays.append(status.parent.name)
        except OSError:
            continue
    devices = input_devices(inputs, udev)
    keyboard = any(d['keyboard'] for d in devices.values())
    mouse = any(d['mouse'] for d in devices.values())
    return {'display': bool(displays), 'usb_keyboard': keyboard, 'usb_mouse': mouse,
            'ready': bool(displays) and keyboard and mouse}


def desktop_active(run=subprocess.run):
    try:
        # Unknown/error state fails closed; only an inactive manager may start.
        return run(['systemctl', 'is-active', '--quiet', 'display-manager.service'],
                   timeout=5).returncode != 3
    except (OSError, subprocess.SubprocessError):
        return True


def input_activity(data, device, armed_at):
    """Return a boolean only; never retain or print input codes or content."""
    for offset in range(0, len(data) - EVENT.size + 1, EVENT.size):
        sec, usec, kind, code, value = EVENT.unpack_from(data, offset)
        if sec + usec / 1_000_000 < armed_at:
            continue
        if kind == 1 and value == 1:  # EV_KEY press; ignore release/repeat.
            if device['keyboard'] and 1 <= code < 0x100:
                return True
            if device['mouse'] and 0x110 <= code <= 0x117:
                return True
        if kind == 2 and device['mouse'] and code in (0, 1, 6, 8, 11, 12) and value:
            return True  # EV_REL X/Y or normal/high-resolution wheel movement.
    return False


def activate(state, run=subprocess.run, *, activity=False):
    if not state['ready'] or not activity:
        return False
    if desktop_active(run):
        return False
    run(['systemctl', 'start', 'display-manager.service'], check=True, timeout=30)
    print('Local keyboard/mouse activity detected; graphical login started.', flush=True)
    return True


class InputWatch:
    def __init__(self):
        self.handles = {}

    def close(self):
        for fd, _, _ in self.handles.values():
            os.close(fd)
        self.handles.clear()

    def sync(self, devices):
        for path in list(self.handles):
            if path not in devices or self.handles[path][1] != devices[path]:
                os.close(self.handles.pop(path)[0])
        for path, device in devices.items():
            if path in self.handles:
                continue
            fd = None
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
                # Event timestamps and arming deadline must share a monotonic clock.
                fcntl.ioctl(fd, EVIOCSCLOCKID, struct.pack('@i', time.CLOCK_MONOTONIC))
                self.handles[path] = (fd, device, time.monotonic() + ARM_SECONDS)
            except OSError:
                if fd is not None:
                    os.close(fd)

    def poll(self, timeout=1.0):
        by_fd = {row[0]: (path, row[1], row[2]) for path, row in self.handles.items()}
        if not by_fd:
            time.sleep(timeout)
            return False
        ready, _, _ = select.select(list(by_fd), [], [], timeout)
        for fd in ready:
            path, device, armed_at = by_fd[fd]
            try:
                data = os.read(fd, EVENT.size * 64)
                if not data:
                    os.close(self.handles.pop(path)[0])
                elif input_activity(data, device, armed_at):
                    return True
            except BlockingIOError:
                continue
            except OSError:
                os.close(self.handles.pop(path)[0])
        return False


def watch_once(watcher, connectors):
    # Do not open/read input devices during desktop/login sessions.
    if desktop_active():
        watcher.close()
        time.sleep(1)
        return
    state = detect(connectors=connectors)
    if not state['ready']:
        watcher.close()
        time.sleep(1)
        return
    watcher.sync(input_devices())
    if watcher.poll():
        # Recheck display/device readiness after the event and before activation.
        activate(detect(connectors=connectors), activity=True)
        watcher.close()


def watch(connectors):
    watcher = InputWatch()
    print('Headless boot: waiting for fresh local keyboard/mouse activity.', flush=True)
    try:
        while True:
            watch_once(watcher, connectors)
    finally:
        watcher.close()


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
        watch(connectors)


if __name__ == '__main__':
    main()
