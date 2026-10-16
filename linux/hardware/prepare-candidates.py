#!/usr/bin/env python3
"""Generate inactive AMD candidates from retained model paths; never activate/run them."""
import configparser
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def strata_candidate(source):
    cfg = copy.deepcopy(source)
    args = cfg['args']
    for option, value in {'--max-context': '32768', '--kv-resident': '32768',
                          '--prefill': '512', '--vram-reserve-mib': '3072',
                          '--conversation-cache-mib': '0'}.items():
        args[args.index(option) + 1] = value
    for option in ('--remote-expert-opt', '--trim-stage-weights'):
        if option in args:
            args.remove(option)
    args += ['--mmap-experts', '--resident-cpu-experts', '--adapt-every', '0',
             '--pcie-frac', '0', '--pool-workers', '6']
    cfg.update(backend='hip', gpu=[0], gpus_asked=True, layer_split='auto',
               exe=str(ROOT / 'strata/build-hip/strata'),
               log=str(ROOT / 'dsh/logs/strata-amd-candidate.log'),
               port=18030, lib_dirs=[],
               env={'STRATA_PREFILL_MMQ': '1', 'STRATA_NO_ARENA_THP': '1'})
    # lib_dirs and the optional hipBLASLt table must match the SDK used to build HIP.
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
    cfg = strata_candidate(json.loads((ROOT / 'dsh/strata-iq3-profile.json').read_text()))
    (dest / 'strata-7900xtx-candidate.json').write_text(json.dumps(cfg, indent=2) + '\n')
    (dest / 'llama-7900xtx-candidate.ini').write_text(llama_candidate((ROOT / 'dsh/models.ini').read_text()))
    print('Wrote inactive candidates to', dest)
    print('No launchers, API catalogs, runtimes or model files changed.')


if __name__ == '__main__':
    main()
