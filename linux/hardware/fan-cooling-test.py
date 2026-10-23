#!/usr/bin/env python3
"""Temporary AMD fan test; restores automatic fan control on exit.

RDNA3 (RX 7000) rejects the legacy pwm1 manual mode with EINVAL. Its fans are set through
OverDrive: gpu_od/fan_ctrl/fan_minimum_pwm takes a minimum percentage, 'c' commits and 'r'
resets to the firmware default. Zero-RPM mode parks the fans below its stop temperature
regardless of that minimum, so fan_zero_rpm_enable is also set to 0 for the test. The 7900 XTX
firmware ignored both at idle (0 RPM), so the custom fan_curve is also set to at least the
requested percentage at every point, which switches the firmware to manual-curve mode.
OverDrive needs bit 0x4000 in amdgpu.ppfeaturemask.
"""
import argparse
import os
from pathlib import Path
import re
import signal
import time


def amd_cards():
    for card in sorted(Path('/sys/class/drm').glob('card*')):
        device = card/'device'
        if re.fullmatch(r'card\d+', card.name) and (device/'vendor').exists() \
                and (device/'vendor').read_text().strip() == '0x1002':
            yield card.name, device


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--percent', type=int, default=75, metavar='60..100')
    parser.add_argument('--seconds', type=int, default=900, metavar='30..1800')
    args = parser.parse_args()
    if not 60 <= args.percent <= 100 or not 30 <= args.seconds <= 1800:
        parser.error('Fan percentage must be 60..100 and duration 30..1800 seconds')
    if os.geteuid() != 0:
        parser.error('Administrator access is required for the kernel fan controls; run with sudo.')
    cards = list(amd_cards())
    if len(cards) != 2:
        raise SystemExit('Expected exactly two AMD GPUs')
    fan_ctrl = {name: device/'gpu_od/fan_ctrl' for name, device in cards}
    missing = [name for name, path in fan_ctrl.items() if not (path/'fan_minimum_pwm').exists()]
    if missing:
        mask = Path('/sys/module/amdgpu/parameters/ppfeaturemask').read_text().strip()
        raise SystemExit(f'No OverDrive fan control on {", ".join(missing)}: amdgpu.ppfeaturemask is {mask}. '
                         'Add amdgpu.ppfeaturemask=0xfff7ffff (sets bit 0x4000) to the kernel command line and reboot. '
                         'Nothing was changed.')
    def stop(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    changed = []
    try:
        for name, ctrl in fan_ctrl.items():
            curve = [f'{point} {temp} {max(args.percent, speed)}'
                     for point, (temp, speed) in enumerate(((25, 0), (45, 0), (65, 0), (80, 90), (95, 100)))]
            for setting, values in (('fan_zero_rpm_enable', ['0']), ('fan_minimum_pwm', [str(args.percent)]),
                                    ('fan_curve', curve)):
                path = ctrl/setting
                changed.append(path)
                for value in values:
                    path.write_text(f'{value}\n')
                path.write_text('c\n')
                print(name, setting, ':', ' '.join(path.read_text().split()), flush=True)
        print('Cooling test active; Ctrl-C or timeout restores automatic control.', flush=True)
        time.sleep(min(10, args.seconds))
        for name, device in cards:
            rpm = [fan.read_text().strip() for fan in device.glob('hwmon/hwmon*/fan1_input')]
            print(name, 'fan speed after 10 s:', ', '.join(rpm) or 'unknown', 'RPM', flush=True)
        time.sleep(max(0, args.seconds - 10))
    finally:
        errors = []
        for path in reversed(changed):
            try:
                path.write_text('r\n')
                path.write_text('c\n')
            except OSError as error:
                errors.append(f'{path}: {error}')
        print('Firmware fan defaults restored.' if not errors else 'RESTORE ERRORS: '+str(errors), flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
