"""Admit separately qualified native profiles while retaining legacy source pins."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time
import resource_policy
from amd_device import amd_devices
from llama_runtime import require_worker_scope
from moe_memory import host_memory
from shared_storage import STREAM_MODELS,ensure_streaming_models

ROOT=Path(__file__).resolve().parent.parent
GIB=2**30
_VERIFIED_BACKING_CONTENT=set()

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def filesystem_uuid(path):
    """Block-device numbers can change across boots; filesystem UUIDs do not."""
    value=subprocess.check_output(['findmnt','-rn','-T',str(Path(path).resolve()),'-o','UUID'],
                                  text=True,timeout=5).strip()
    if not re.fullmatch(r'[0-9A-Fa-f-]{8,128}',value):
        raise RuntimeError('Cannot verify qualified backing filesystem UUID')
    return value

def backing_digest(path):
    """Keep thermal/storage monitoring active during a large identity recheck."""
    sys.path.insert(0,str(ROOT/'hardware'))
    from storage_health import StorageHealthMonitor
    from gpu_telemetry import snapshot
    from temperature_policy import temperature_failure,TEMPERATURE_LIMIT_C
    if TEMPERATURE_LIMIT_C!=100:raise RuntimeError('Qualified native temperature policy changed')
    monitor=StorageHealthMonitor()
    def health():
        monitor.check();reason=temperature_failure(snapshot())
        if reason:raise RuntimeError(reason)
    health();last=time.monotonic();h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(8*1024*1024):
            h.update(block)
            if time.monotonic()-last>=5:health();last=time.monotonic()
    health();return h.hexdigest()

def config_fingerprint(cfg):
    ignored={'local_validation','log','installer','expert_profile_seed_sha256','upstream_expert_profile_seed_sha256'}
    return hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ignored},sort_keys=True).encode()).hexdigest()

def admitted_status(record):
    if record.get('status')=='passed':return True
    token=os.environ.get('LOCAL_LLM_UPDATE_CANDIDATE')
    if record.get('status')!='candidate' or not token or token!=record.get('candidate_owner'):return False
    try:
        lock=json.loads((ROOT/'hardware/generated/GPU-LOCK').read_text())
        return lock['owner'].startswith('daily-update-') and Path('/proc',str(int(lock['pid']))).is_dir()
    except (OSError,ValueError,KeyError,TypeError):return False

def record_for(cfg,family=None):
    path=ROOT/'dsh/qualified-native-profiles.json'
    if not path.exists():return None
    data=json.loads(path.read_text())
    if data.get('schema_version')!=1:raise RuntimeError('Unknown native qualification registry version')
    record=data.get('profiles',{}).get(cfg.get('model_name'))
    if record is None:return None
    if not admitted_status(record) or family is not None and record.get('family')!=family:
        raise RuntimeError('Native qualification is held or belongs to another backend')
    return record

def require_profile(cfg,record,before_handover=False):
    from inference_kernel import require_inference_kernel
    require_inference_kernel()
    if not admitted_status(record) or record.get('family') not in ['maya','strata']:
        raise RuntimeError('Native qualification must pass for a known backend family')
    if (cfg.get('backend')!='hip' or cfg.get('gpu')!=[0,1] or cfg.get('parallel')!=1
            or cfg.get('split_skip_if_fits',False)):
        raise RuntimeError('Qualified native profiles require both AMD cards and one request')
    if config_fingerprint(cfg)!=record['config_sha256']:
        raise RuntimeError('Native profile differs from its independently sealed qualification')
    source=Path(record['source']);revision=record['source_commit']
    if not source.is_absolute() or not re.fullmatch('[0-9a-f]{40}',revision):
        raise RuntimeError('Invalid qualified native source pin')
    actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
    if actual!=revision or subprocess.run(['git','-C',str(source),'diff','--quiet','HEAD','--'],timeout=10).returncode:
        raise RuntimeError('Qualified native source changed')
    binary=Path(record['binary']);expected=source/record['binary_relative']
    if (record['binary_relative'] not in ['build-hip/maya','build-hip/maya-ds4','build-hip/strata-dsv41']
            or Path(cfg['exe'])!=binary or binary!=expected or Path(cfg['cwd'])!=source
            or not os.access(binary,os.X_OK) or digest(binary)!=record['binary_sha256']):
        raise RuntimeError('Qualified native executable identity changed')
    args=cfg['args']
    def value(flag):return args[args.index(flag)+1] if flag in args else None
    if value('--max-context')!='32768':raise RuntimeError('Native context must remain the tested 32K')
    glm='--glm-pack' in args
    if glm:
        ram_gb=record.get('glm_ram_gb',8)
        if (record['family']!='maya' or record['binary_relative']!='build-hip/maya'
                or cfg.get('layer_split')!='auto' or value('--tp') is not None
                or value('--vram-reserve-mib')!='8192' or value('--vram-reserve-later-mib')!='8192'
                or cfg.get('env',{}).get('MAYA_GLM_PREFILL_FUSED')!='0'
                or type(ram_gb) is not int or ram_gb not in (8,24,40)
                or cfg.get('env',{}).get('MAYA_GLM_RAM_GB')!=str(ram_gb)):
            raise RuntimeError('GLM must retain its tested dual-card placement, RAM tier and disabled fused prefill')
    elif value('--tp')!='2':raise RuntimeError('Native placement must retain both tested layer groups')
    reserves=[int(value(flag)) for flag in ['--reserve-mib','--vram-reserve-mib','--vram-reserve-later-mib'] if flag in args]
    if not reserves or min(reserves)<8192:
        raise RuntimeError('Qualified normal profile must retain its 8 GiB requested reserve')
    for key,env_value in cfg.get('env',{}).items():
        if key.endswith(('DISK_SKIP_W','DS4_PROMPT_SKIP','DS4_SLOT_KEEP','DS4_YOCO')) and float(env_value)!=0:
            raise RuntimeError('Quality-changing expert/prompt skipping must remain disabled')
        if key.endswith('GLM_DISK_SKIP_FROM') and int(env_value)>=0:
            raise RuntimeError('Quality-changing GLM expert skipping must remain disabled')
    flag='--glm-pack' if '--glm-pack' in args else '--pack';pack=Path(value(flag))
    family_root=STREAM_MODELS/('Maya' if record['family']=='maya' else 'Strata')
    if pack!=Path(record['pack']) or not pack.is_relative_to(family_root):
        raise RuntimeError('Qualified native backing location changed')
    for relative,expected_hash in record['pack_metadata_sha256'].items():
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts or digest(pack/path)!=expected_hash:
            raise RuntimeError('Qualified pack metadata changed')
    if not record['pack_metadata_sha256']:raise RuntimeError('Native pack metadata must be sealed')
    for path,identity in record.get('backing_identity',{}).items():
        stat=Path(path).stat()
        actual={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'inode':stat.st_ino,'device':stat.st_dev}
        expected={k:identity[k] for k in actual}
        if actual!=expected:
            # A UUID must have been recorded from reviewed filesystem provenance.
            # It admits only a device-number alias: inode, size and mtime still match.
            if (all(actual[k]==expected[k] for k in ['bytes','mtime_ns','inode'])
                    and identity.get('filesystem_uuid')
                    and filesystem_uuid(path)==identity['filesystem_uuid']):
                continue
            # exFAT assigns a fresh inode number after cache eviction. An inode-only
            # change requires the original content hash, never a blind re-seal.
            expected_hash=identity.get('sha256','')
            key=(path,*actual.values(),expected_hash)
            if (any(actual[k]!=expected[k] for k in ['bytes','mtime_ns','device'])
                    or not re.fullmatch('[0-9a-f]{64}',expected_hash)):
                raise RuntimeError('Qualified native backing identity changed')
            if key not in _VERIFIED_BACKING_CONTENT:
                if backing_digest(path)!=expected_hash:raise RuntimeError('Qualified native backing content changed')
                _VERIFIED_BACKING_CONTENT.add(key)
    if Path(cfg['tokenizer'])!=Path(record['tokenizer']) or not Path(cfg['tokenizer']).is_dir():
        raise RuntimeError('Qualified tokenizer identity changed')
    if cfg.get('worker_swap_max_bytes') is not None or cfg.get('startup_free_vram_gib')!=0.125:
        raise RuntimeError('Retain current phase-aware swap and per-card resource guard')
    if not resource_policy.active():raise RuntimeError('This qualification requires the current owner resource policy')
    ensure_streaming_models()
    total,available=host_memory()
    if total<60*GIB or not before_handover and available<52*GIB:
        raise RuntimeError('Qualified native loading requires 60 GiB physical / 52 GiB available RAM')
    devices=amd_devices()
    if len(devices)!=2 or any(int((d/'mem_info_vram_total').read_text())<23*GIB for d in devices):
        raise RuntimeError('Qualified native profiles require both 24 GiB AMD cards')
    if not before_handover and any(int((d/'mem_info_vram_total').read_text())-int((d/'mem_info_vram_used').read_text())<16*GIB for d in devices):
        raise RuntimeError('Qualified native loading requires 16 GiB free per card')
    require_worker_scope()
    return cfg
