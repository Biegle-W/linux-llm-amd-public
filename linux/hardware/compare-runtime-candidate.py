#!/usr/bin/env python3
"""Compare candidate benchmark-current-amd.py records with the current baseline.

Applies the fixed promotion thresholds: prefill and code/prose decode medians
>= 95% of baseline; short TTFT <= max(1.25 x baseline, baseline + 0.05 s);
marker checks no fewer than baseline; effective swap policy and zero VRAM spill. Prints a table and exits
non-zero if any compared profile misses a threshold. It changes nothing.
"""
import argparse
import json
from pathlib import Path
import statistics
from inference_memory import worker_swap_limit_bytes, memory_failures, lifecycle_failures


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


def verdict(old, new, memory):
    failures = [name for name in ('prefill_tps', 'code_decode_tps', 'prose_decode_tps')
                if new[name] < 0.95 * old[name]]
    failures += [name for name in ('code_ttft_s', 'prose_ttft_s')
                 if new[name] > max(1.25 * old[name], old[name] + 0.05)]
    if new['markers'] < old['markers']:
        failures.append('markers')
    return failures + memory_failures(memory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates', nargs='+', type=Path)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Same-hardware baseline record from benchmark-current-amd.py (current production build)')
    parser.add_argument('--require-lifecycle-memory', action='store_true',
                        help='Also require complete launch/load/shutdown memory evidence (daily updater)')
    options = parser.parse_args()
    baseline = {p['model']: p for p in json.loads(options.baseline.read_text())['profiles']}
    if not baseline:
        parser.error('Baseline contains no model profiles; cannot establish promotion evidence')
    failed = False
    print('| Model | Metric | Baseline | Candidate | Change |\n|---|---|---:|---:|---:|')
    print(f'| policy | worker_swap_limit_bytes | | {worker_swap_limit_bytes() if worker_swap_limit_bytes() is not None else 'rate-only'} | |')
    for path in options.candidates:
        record = json.loads(path.read_text())
        if options.require_lifecycle_memory:
            failures = lifecycle_failures(record)
            memory = record.get('lifecycle_memory')
            memory = memory if isinstance(memory, dict) else {}
            for name in ('max_worker_swap_bytes', 'max_nonresident_vram_bytes'):
                print(f'| lifecycle | {name} | | {memory.get(name, "unknown")} | |')
            print(f'| lifecycle | verdict | | | {"FAIL: " + ", ".join(failures) if failures else "pass"} |')
            failed |= bool(failures)
        seen = set()
        for profile in record['profiles']:
            model = profile['model']
            if model in seen:
                print(f'| {model} | duplicate profile | | | FAIL |')
                failed = True
            seen.add(model)
            if profile.get('status') not in ('passed', 'measured_with_marker_failure') or model not in baseline:
                print(f'| {model} | status | — | {profile.get("status")} | FAIL |')
                failed = True
                continue
            old, new = metrics(baseline[model]), metrics(profile)
            for name in old:
                change = '' if name == 'markers' else f'{100 * (new[name] / old[name] - 1):+.1f}%'
                print(f'| {model} | {name} | {old[name]:.3f} | {new[name]:.3f} | {change} |')
            memory = profile.get('memory')
            for name in ('max_worker_swap_bytes', 'max_nonresident_vram_bytes'):
                value = memory.get(name, 'unknown') if isinstance(memory, dict) else 'unknown'
                print(f'| {model} | {name} | | {value} | |')
            failures = verdict(old, new, memory)
            print(f'| {model} | verdict | | | {"FAIL: " + ", ".join(failures) if failures else "pass"} |')
            failed |= bool(failures)
        for model in sorted(set(baseline) - seen):
            print(f'| {model} | missing candidate profile | | | FAIL |')
            failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
