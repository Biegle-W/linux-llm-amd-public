"""Admit sealed Strata DeepSeek profiles without changing the retained Qwen engine."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from amd_device import amd_devices
from llama_runtime import require_worker_scope
from moe_memory import host_memory
from shared_storage import STREAM_MODELS, ensure_streaming_models

ROOT=Path(__file__).resolve().parents[1]
GIB=1024**3
SOURCE=ROOT/'strata-dsv41/upstream'
PIN=ROOT/'strata-dsv41/runtime.json'


def config_fingerprint(cfg):
    ignored={'local_validation','log','installer','expert_profile_seed_sha256'}
    value={k:v for k,v in cfg.items() if k not in ignored}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def pack_fingerprint(pack):
    h=hashlib.sha256()
    for name in ('ds4.txt','tensors.txt','engram.bin'):
        h.update(name.encode()+b'\0');h.update((pack/name).read_bytes())
    return h.hexdigest()


def check_settings(cfg):
    if (cfg.get('arch')!='deepseek41' or cfg.get('backend')!='hip' or cfg.get('gpu')!=[0,1]
            or cfg.get('parallel')!=1 or cfg.get('split_skip_if_fits',False)):
        raise RuntimeError('Strata DeepSeek requires both AMD GPUs, layer groups and one request.')
    args=cfg['args']
    def value(flag):
        return args[args.index(flag)+1] if flag in args else None
    if (value('--max-context')!='32768' or value('--cpu-threads')!='24'
            or value('--tp')!='2' or value('--reserve-mib')!='8192'
            or value('--ssd-cache') not in ('0','24')):
        raise RuntimeError('Strata DeepSeek requires its validated 32K/24-thread/reserve/memory settings.')
    quant=cfg.get('installer',{}).get('quant')
    expected={'Maya-S':'none','Maya-XS':'on'}.get(quant)
    if expected is None or value('--dspark')!=expected:
        raise RuntimeError('Use the validated S/no-drafter or XS/matching-xs2 profile.')
    env=cfg.get('env',{})
    if (env.get('STRATA_DS4_PROMPT_SKIP')!='0' or env.get('DS4_YOCO')!='0'
            or env.get('STRATA_DS4_SLOT_KEEP')!='0' or env.get('STRATA_DS4_DISK_SKIP_W','0')!='0'):
        raise RuntimeError('Prompt skipping and unvalidated slot reuse must remain disabled.')
    if cfg.get('worker_swap_max_bytes')!=0 or cfg.get('startup_free_vram_gib')!=6:
        raise RuntimeError('Strata DeepSeek requires zero worker swap and 6GiB actual startup headroom.')


def require_profile(cfg,before_handover=False):
    check_settings(cfg)
    pin=json.loads(PIN.read_text())
    revision=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    if revision!=pin['source_commit'] or subprocess.run(
            ['git','-C',str(SOURCE),'diff','--quiet','HEAD','--'],check=False).returncode:
        raise RuntimeError('Strata DeepSeek source changed; validate the new revision first.')
    exe=Path(cfg['exe'])
    if exe!=SOURCE/'build-hip/strata-dsv41' or not os.access(exe,os.X_OK):
        raise RuntimeError('The separate validated Strata DeepSeek binary is unavailable.')
    valid=cfg.get('local_validation',{})
    if (valid.get('status')!='passed' or valid.get('source_commit')!=revision
            or valid.get('binary_sha256')!=hashlib.sha256(exe.read_bytes()).hexdigest()
            or valid.get('config_sha256')!=config_fingerprint(cfg)):
        raise RuntimeError('Strata DeepSeek source/binary/config validation fingerprint does not match.')
    ensure_streaming_models()
    args=cfg['args'];pack=Path(args[args.index('--pack')+1])
    if (not pack.is_relative_to(STREAM_MODELS/'Strata/DeepSeek-V4.1-Flash-1017')
            or valid.get('pack_metadata_sha256')!=pack_fingerprint(pack)
            or Path(cfg['tokenizer'])!=pack/'tokenizer'):
        raise RuntimeError('Strata DeepSeek pack/tokenizer differs from the validated shared-weight pack.')
    total,available=host_memory()
    if total<60*GIB or (not before_handover and available<52*GIB):
        raise RuntimeError('Strata DeepSeek needs 60GiB physical / 52GiB available RAM; swap is not capacity.')
    devices=amd_devices()
    if len(devices)!=2 or any(int((d/'mem_info_vram_total').read_text())<23*GIB for d in devices):
        raise RuntimeError('Strata DeepSeek requires both 24GiB AMD cards.')
    if not before_handover and any(int((d/'mem_info_vram_total').read_text())-
            int((d/'mem_info_vram_used').read_text())<16*GIB for d in devices):
        raise RuntimeError('Strata DeepSeek needs 16GiB free on each card before loading.')
    require_worker_scope()
    return cfg
