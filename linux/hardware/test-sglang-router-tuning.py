#!/usr/bin/env python3
"""Load the saved production profiles through the router and check live settings."""
import importlib.util
import json
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

base=load('context_checks',ROOT/'hardware/test-sglang-dual-context.py')
router=load('production_router',ROOT/'dsh/sglang-router.py')

def interrupted(*_):
 raise KeyboardInterrupt

if __name__=='__main__':
 if any(base.backend_switch.is_inference(p) for p in base.backend_switch.processes().values()):
  raise SystemExit('Another configured worker is active')
 signal.signal(signal.SIGTERM,interrupted)
 signal.signal(signal.SIGHUP,interrupted)
 base.checks.PORT=30001
 rows=[]
 try:
  for model,cfg in router.PROFILES.items():
   if not cfg.get('enabled',True):continue
   print('INTEGRATION',model,flush=True)
   router.ensure_worker(model)
   base.checks.MODEL=model
   info=router.get_worker('/server_info')
   capacities=list(router.cache_capacities(info))
   assert capacities and min(capacities)>=cfg['context']
   quality=base.checks.validate()
   assert all(quality[k] for k in ('arithmetic','ordered_json','tool_roundtrip'))
   if cfg.get('mtp'):
    assert info['speculative_num_steps']==cfg['mtp_steps']
   with Path(f'/proc/{router.worker.pid}/environ').open('rb') as envfile:
    env=dict(part.split(b'=',1) for part in envfile.read().split(b'\0') if b'=' in part)
   assert env[b'SGLANG_RDNA_VLLM_VERIFY']==b'1'
   assert env[b'SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX']==b'1'
   tree=base.backend_switch.processes();ids={router.worker.pid}
   for _ in range(8):ids.update(p.pid for p in tree.values() if p.parent in ids)
   spill=sum(base.checks.gpu.amd_residency(pid)['nonresident_vram_bytes'] for pid in ids)
   assert spill==0
   used=[int((d/'mem_info_vram_used').read_text()) for d in base.amd_devices()]
   assert min(used)>2*1024**3
   rows.append(dict(model=model,context=cfg['context'],reported_cache_capacities=capacities,
                    speculative_algorithm=info.get('speculative_algorithm'),mtp_steps=info.get('speculative_num_steps'),
                    quality={k:v for k,v in quality.items() if isinstance(v,bool)},repaired_verifier=True,
                    vram_bytes=used,nonresident_vram_bytes=spill))
   print('PASSED',model,flush=True)
 finally:
  router.stop_worker()
 out=ROOT/'hardware/generated/dual-tuning-2026-10-17/router-integration.json'
 out.write_text(json.dumps(dict(status='passed',profiles=rows),indent=2)+'\n')
