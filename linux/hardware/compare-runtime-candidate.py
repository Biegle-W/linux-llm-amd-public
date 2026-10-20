#!/usr/bin/env python3
"""Compare candidate benchmark-current-amd.py records with the current baseline.

Applies the fixed promotion thresholds: prefill and code/prose decode medians
>= 95% of baseline; short TTFT <= max(1.25 x baseline, baseline + 0.05 s);
marker checks no fewer than baseline; zero VRAM spill. Prints a table and exits
non-zero if any compared profile misses a threshold. It changes nothing.
"""
import argparse
import json
from pathlib import Path
import statistics


def prefill(profile):
    if 'summary' in profile:
        return profile['summary']['prefill_tps']
    values = [t.get('prefill_native_tps') or t.get('prefill_phase_tps') for t in profile['prefill']]
    return statistics.median(v for v in values if v)


def metrics(profile):
    short = profile['short']
    return {'prefill_tps': prefill(profile),
            'code_decode_tps': short['code']['median_decode_tps'],
            'prose_decode_tps': short['prose']['median_decode_tps'],
            'code_ttft_s': short['code']['median_ttft_seconds'],
            'prose_ttft_s': short['prose']['median_ttft_seconds'],
            'markers': sum(bool(t.get('markers_passed')) for t in profile['prefill'])}


def verdict(old, new, spill):
    failures = [name for name in ('prefill_tps', 'code_decode_tps', 'prose_decode_tps')
                if new[name] < 0.95 * old[name]]
    failures += [name for name in ('code_ttft_s', 'prose_ttft_s')
                 if new[name] > max(1.25 * old[name], old[name] + 0.05)]
    if new['markers'] < old['markers']:
        failures.append('markers')
    if spill:
        failures.append('vram_spill')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates', nargs='+', type=Path)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Same-hardware baseline record from benchmark-current-amd.py (current production build)')
    options = parser.parse_args()
    baseline = {p['model']: p for p in json.loads(options.baseline.read_text())['profiles']}
    failed = False
    print('| Model | Metric | Baseline | Candidate | Change |\n|---|---|---:|---:|---:|')
    for path in options.candidates:
        for profile in json.loads(path.read_text())['profiles']:
            model = profile['model']
            if profile.get('status') not in ('passed', 'measured_with_marker_failure') or model not in baseline:
                print(f'| {model} | status | — | {profile.get("status")} | FAIL |')
                failed = True
                continue
            old, new = metrics(baseline[model]), metrics(profile)
            for name in old:
                change = '' if name == 'markers' else f'{100 * (new[name] / old[name] - 1):+.1f}%'
                print(f'| {model} | {name} | {old[name]:.3f} | {new[name]:.3f} | {change} |')
            failures = verdict(old, new, profile['memory']['max_nonresident_vram_bytes'])
            print(f'| {model} | verdict | | | {"FAIL: " + ", ".join(failures) if failures else "pass"} |')
            failed |= bool(failures)
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
