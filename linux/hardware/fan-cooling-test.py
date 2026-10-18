#!/usr/bin/env python3
"""Temporary AMD fan test; restores the original fan mode and PWM on exit."""
import argparse
import os
from pathlib import Path
import re
import signal
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--percent', type=int, default=75, metavar='60..100')
    parser.add_argument('--seconds', type=int, default=900, metavar='30..1800')
    args = parser.parse_args()
    if not 60 <= args.percent <= 100 or not 30 <= args.seconds <= 1800:
        parser.error('Fan percentage must be 60..100 and duration 30..1800 seconds')
    if os.geteuid() != 0:
        parser.error('Administrator access is required for the kernel fan controls; run with sudo.')
    saved = []
    def stop(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for card in sorted(Path('/sys/class/drm').glob('card*')):
            if not re.fullmatch(r'card\d+', card.name):
                continue
            device = card/'device'
            if not (device/'vendor').exists() or (device/'vendor').read_text().strip() != '0x1002':
                continue
            for hwmon in (device/'hwmon').glob('hwmon*'):
                if not (hwmon/'pwm1_enable').exists():
                    continue
                old_mode = (hwmon/'pwm1_enable').read_text().strip()
                old_pwm = (hwmon/'pwm1').read_text().strip()
                if old_mode != '2':
                    raise RuntimeError('Expected automatic fan mode before the cooling test; refusing to override another controller.')
                saved.append((hwmon, old_mode, old_pwm))
                target = max(int(old_pwm), round(int((hwmon/'pwm1_max').read_text())*args.percent/100))
                (hwmon/'pwm1_enable').write_text('1')
                (hwmon/'pwm1').write_text(str(target))
                print(card.name, 'fan PWM', target, '(requested minimum', args.percent, 'percent)', flush=True)
        if len(saved) != 2:
            raise RuntimeError('Expected exactly two controllable AMD GPUs')
        print('Cooling test active; Ctrl-C or timeout restores automatic control.', flush=True)
        time.sleep(args.seconds)
    finally:
        errors = []
        for hwmon, mode, pwm in reversed(saved):
            try:
                (hwmon/'pwm1').write_text(pwm)
            except OSError as error:
                errors.append(str(error))
            finally:
                try:
                    (hwmon/'pwm1_enable').write_text(mode)
                except OSError as error:
                    errors.append(str(error))
        print('Original fan settings restored.' if not errors else 'RESTORE ERRORS: '+str(errors), flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
