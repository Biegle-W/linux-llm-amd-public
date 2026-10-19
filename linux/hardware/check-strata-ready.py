#!/usr/bin/env python3
"""Read-only Strata preparation check; never loads a model or stops another job."""
import argparse
import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIB = 1024**3
sys.path.insert(0, str(ROOT / "dsh"))
from strata_runtime import memory_blockers


def inspect(ram=32):
    mem = {line.split(':')[0]: int(line.split()[1]) * 1024
           for line in Path('/proc/meminfo').read_text().splitlines()}
    source_path = ROOT / ('dsh/strata-iq3-profile.json' if ram == 32 else 'dsh/strata-iq3-64gb-candidate.json')
    source = json.loads(source_path.read_text())
    args = source['args']
    budget = float(args[args.index('--resident-budget-gib')+1])
    problems = memory_blockers(mem['MemTotal'], mem['MemAvailable'], source['minimum_host_ram_gib'], budget)
    args = source['args']
    paths = {option: Path(args[args.index(option)+1]) for option in ('--pack', '--native', '--ple-gguf', '--mtp')}
    required = [paths['--native'], paths['--ple-gguf'], paths['--pack'] / 'dense.bin',
                paths['--pack'] / 'experts.bin', paths['--mtp'] / 'dense.bin',
                paths['--mtp'] / 'experts.bin', paths['--mtp'] / 'draft_vocab.bin']
    assets_ok = all(p.is_file() and p.stat().st_size > 0 for p in required)
    if not assets_ok:
        problems.append('Required retained Q3 pack/GGUF/MTP assets are missing or empty; check Shared mounting.')
    tokenizer = Path(source['tokenizer'])
    tokenizer_ok = tokenizer.is_dir() and any(tokenizer.iterdir())
    if not tokenizer_ok:
        problems.append('The retained tokenizer directory is missing or empty.')
    engine = ROOT / 'strata/build-hip/strata'
    engine_ok = engine.is_file() and os.access(engine, os.X_OK)
    if not engine_ok:
        problems.append('Build the separate HIP engine with hardware/build-strata-hip.sh.')
    amd = []
    for p in Path('/sys/bus/pci/devices').iterdir():
        try:
            if (p/'vendor').read_text().strip() == '0x1002' and int((p/'mem_info_vram_total').read_text()) >= 23*GIB:
                amd.append(p.name)
        except (OSError, ValueError):
            continue
    if len(amd) != 2:
        problems.append('Exactly two 24 GB AMD GPUs are required; confirm both identities with strata-device.')
    kfd_ok = os.access('/dev/kfd', os.R_OK | os.W_OK)
    if not kfd_ok:
        problems.append('KFD access is unavailable in this execution environment.')
    return {'eligible_for_manual_testing': not problems,
            'ram_total_gib': round(mem['MemTotal']/GIB,2),
            'ram_available_gib': round(mem['MemAvailable']/GIB,2),
            'assets_present': assets_ok, 'tokenizer_present': tokenizer_ok,
            'hip_engine_present': engine_ok, 'amd_pci_candidates': amd,
            'kfd_access': kfd_ok, 'blockers': problems,
            'profile_ram_gb': ram, 'expert_budget_gib': budget,
            'note': 'Read-only readiness, not a benchmark or proof of maximum context. No inference was started.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ram', type=int, choices=(32, 64), default=32)
    result = inspect(parser.parse_args().ram)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['eligible_for_manual_testing'] else 2)
