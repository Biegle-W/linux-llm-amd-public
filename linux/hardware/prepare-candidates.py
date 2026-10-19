#!/usr/bin/env python3
"""Generate inactive AMD candidates from retained model paths; never activate/run them."""
import configparser
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def strata_candidate(source, ram_gib=32):
    if ram_gib not in (32, 64):
        raise ValueError('Choose the 32 GB profile or the gated 64 GB candidate')
    cfg = copy.deepcopy(source)
    args = cfg['args']
    # Preserve the validated placement, KV window, desktop reserves and overlap.
    # RAM restoration must not regenerate the obsolete 32K/128K presets.
    if ram_gib == 64:
        args[args.index('--max-context') + 1] = '262144'
        args[args.index('--resident-budget-gib') + 1] = '20'
    cfg.update(log=str(ROOT / 'dsh/logs/strata-amd-candidate.log'), port=18030)
    # Candidates never activate automatically when memory capacity changes.
    cfg['minimum_host_ram_gib'] = 29 if ram_gib == 32 else 60
    cfg['worker_swap_max_bytes'] = 0
    cfg['validation_status'] = 'inactive: dual-HIP inference and long context unvalidated'
    # lib_dirs and any optional hipBLASLt table must match the SDK used to build HIP.
    return cfg


def llama_candidate(source):
    cfg = configparser.ConfigParser(interpolation=None)
    # models.ini has a version preamble, which ConfigParser does not accept.
    cfg.read_string(source[source.index('[*]'):])
    model = cfg['qwen3.8-27b-q4']['model']
    return f'''# INACTIVE: replace AMD_VULKAN_DEVICE after --list-devices; never guess ordinal.
version = 1

[*]
device = AMD_VULKAN_DEVICE
split-mode = none
n-gpu-layers = 99
parallel = 1
jinja = true
reasoning = off
flash-attn = on
cache-type-k = q8_0
cache-type-v = q8_0

[qwen3.8-27b-q4]
model = {model}
ctx-size = 32768
batch-size = 512
ubatch-size = 128
fit = off
spec-type = draft-mtp
spec-draft-n-max = 3
'''


def main():
    dest = ROOT / 'hardware/generated'
    dest.mkdir(parents=True, exist_ok=True)
    source = json.loads((ROOT / 'dsh/strata-iq3-profile.json').read_text())
    for ram in (32, 64):
        cfg = strata_candidate(source, ram)
        (dest / f'strata-{ram}gb-candidate.json').write_text(json.dumps(cfg, indent=2) + '\n')
        (dest / f'strata-{ram}gb-candidate.shared-settings.json').write_text('{"reasoning_effort":"none"}\n')
    (dest / 'llama-7900xtx-candidate.ini').write_text(llama_candidate((ROOT / 'dsh/models.ini').read_text()))
    print('Wrote inactive candidates to', dest)
    print('No launchers, API catalogs, runtimes or model files changed.')


if __name__ == '__main__':
    main()
