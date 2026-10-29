"""Admit only validated, bounded Maya profiles on both AMD cards."""
import hashlib
import json
from pathlib import Path
import subprocess
from amd_device import amd_devices
from moe_memory import host_memory
from streaming_memory import check_32gb
from shared_storage import STREAM_MODELS, ensure_streaming_models
from llama_runtime import require_worker_scope

ROOT=Path(__file__).resolve().parent.parent
GIB=1024**3


def profiles():
    return {k:v for k,v in json.loads((ROOT/'dsh/maya-profiles.json').read_text()).items() if v.get('enabled',False)}


def config_fingerprint(cfg):
    # Bind all engine/serving settings, including vision and MCP. Logging and
    # provenance do not alter inference; the validation record cannot hash itself.
    ignored={'local_validation','log','installer','expert_profile_seed_sha256','upstream_expert_profile_seed_sha256'}
    return hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ignored},sort_keys=True).encode()).hexdigest()


def pack_metadata_fingerprint(pack):
    digest=hashlib.sha256()
    for name in ('ds4.txt','tensors.txt','engram.bin'):
        path=pack/name
        if not path.is_file():raise RuntimeError('DeepSeek pack metadata is missing; prepare the Linux pack again.')
        digest.update(name.encode()+b'\0');digest.update(path.read_bytes())
    return digest.hexdigest()


def check_config(cfg, before_handover=False, require_validated=True):
    if cfg.get('backend')!='hip' or cfg.get('gpu')!=[0,1] or cfg.get('split_skip_if_fits',False):
        raise RuntimeError('Maya requires both configured AMD GPUs; single-card fallback is disabled.')
    if cfg.get('parallel',1)!=1:
        raise RuntimeError('Only the validated single-request Maya configuration is admitted.')
    expected=json.loads((ROOT/'maya/runtime.json').read_text())['source_commit']
    source=ROOT/'maya/upstream'
    actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if actual!=expected or subprocess.run(['git','-C',str(source),'diff','--quiet','HEAD','--'],check=False).returncode:
        raise RuntimeError('Maya source changed; validate the new revision before activation.')
    allowed={source/'build-hip/maya',source/'build-hip/maya-ds4'}
    exe=Path(cfg['exe'])
    if exe not in allowed or not exe.is_file():
        raise RuntimeError('The separate Maya HIP engine is missing or outside the configured installation.')
    validation=cfg.get('local_validation',{})
    if require_validated and (validation.get('status')!='passed' or
            validation.get('binary_sha256')!=hashlib.sha256(exe.read_bytes()).hexdigest() or
            validation.get('config_sha256')!=config_fingerprint(cfg)):
        raise RuntimeError('This Maya binary/profile has not passed the local dual-GPU activation checks.')
    args=cfg['args'];glm='--glm-pack' in args
    def value(flag):return args[args.index(flag)+1]
    pack=Path(value('--glm-pack' if glm else '--pack')).resolve()
    if not pack.is_relative_to(STREAM_MODELS/'Maya') or not pack.is_dir():
        raise RuntimeError('Maya model packs must use the configured shared NVMe model folder.')
    if int(value('--max-context'))<=0:
        raise RuntimeError('Maya context must be explicitly bounded.')
    if int(value('--vram-reserve-mib' if glm else '--reserve-mib'))<6144:
        raise RuntimeError('Keep at least 6 GiB startup reserve per GPU for Maya.')
    if require_validated:
        required=8192
        if int(value('--vram-reserve-mib' if glm else '--reserve-mib'))<required or (glm and int(value('--vram-reserve-later-mib'))<8192):
            raise RuntimeError('Use the validated desktop reserves: 8 GiB native on each card, then verify 6 GiB whole-card free.')
    env=cfg.get('env',{})
    for k,v in env.items():
        if (k.endswith('DS4_DISK_SKIP_W') or k.endswith('GLM_MISS_SKIP_W')) and float(v)!=0:
            raise RuntimeError('Quality-changing disk expert skipping is not a validated optimization.')
        if k.endswith('GLM_DISK_SKIP_FROM') and int(v)>=0:
            raise RuntimeError('Quality-changing disk expert skipping is not a validated optimization.')
    if not glm:
        index=pack/'tensors.txt'
        types={line.split()[2] for line in index.read_text().splitlines() if line.startswith('t ')}
        xs='IQ1_S' in types
        if xs:
            # Admit only the exact tested XS/matching-drafter profile; keep all
            # source/binary/config/metadata fingerprints and memory gates below.
            if (cfg.get('installer',{}).get('ds4_quant')!='maya-xs' or
                    pack.parent.name!='Maya-XS' or
                    '--dspark' not in args or value('--dspark')!='on' or
                    int(value('--max-context'))!=32768 or
                    '--cpu-threads' not in args or int(value('--cpu-threads'))!=24 or
                    types - {'BF16','F32','IQ1_S','IQ2_XXS','Q6_K','Q8_0'}):
                raise RuntimeError('Use the validated Maya-XS pack with its matching DSpark drafter and retained32K/24threads.')
        if not types or types - {'IQ1_S','BF16','F32','IQ2_S','IQ2_XXS','IQ3_S','IQ3_XXS','MXFP4','Q6_K','Q8_0'}:
            raise RuntimeError('DeepSeek is admitted only for the tested format set; Q4_K/IQ4_XS parity remains unresolved.')
        if require_validated and validation.get('pack_metadata_sha256')!=pack_metadata_fingerprint(pack):
            raise RuntimeError('DeepSeek pack metadata changed; regenerate and validate Linux paths before loading.')
    if glm:
        cap=float(env.get('MAYA_GLM_RAM_GB',env.get('STRATA_GLM_RAM_GB','0')))
        if not 0<cap<=40:
            raise RuntimeError('Use an explicit bounded whole-machine GLM expert RAM tier, at most 40 GiB.')
    total,available=host_memory()
    bounded = check_32gb(cfg,total,available,'glm' if glm else 'deepseek',check_available=not before_handover)
    if not bounded and (total<60*GIB or (not before_handover and available<52*GIB)):
        raise RuntimeError('Maya needs 60 GiB physical / 52 GiB available RAM before loading; swap is not capacity.')
    if len(amd_devices())!=2 or any(int((d/'mem_info_vram_total').read_text())<23*GIB for d in amd_devices()):
        raise RuntimeError('Maya requires both 24 GB AMD cards.')
    require_worker_scope()
    if not before_handover and any(int((d/'mem_info_vram_total').read_text())-int((d/'mem_info_vram_used').read_text())<16*GIB for d in amd_devices()):
        raise RuntimeError('Maya needs 16 GiB free VRAM on each card before loading.')


def require_maya(model=None,before_handover=False):
    ensure_streaming_models()
    active=profiles()
    if not active or (model is not None and model not in active):
        raise RuntimeError('No validated Maya profile is enabled for this selection.')
    selected=[(model,active[model])] if model else list(active.items())
    for model_id,item in selected:
        cfg=json.loads((ROOT/'dsh'/item['config']).read_text())
        if cfg['model_name'] != model_id or int(cfg['args'][cfg['args'].index('--max-context')+1])!=item['context']:
            raise RuntimeError('Maya catalog and validated worker context/model must match.')
        check_config(cfg,before_handover=before_handover)
