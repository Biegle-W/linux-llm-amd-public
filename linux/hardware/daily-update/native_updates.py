"""Provisional updates only for enabled, independently qualified native profiles."""
from pathlib import Path
import json,os,secrets,shutil,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dsh'))
from qualified_native_runtime import config_fingerprint,digest
from short_cases import write

def entries(family):
 registry=json.loads((ROOT/'dsh/qualified-native-profiles.json').read_text())
 catalog=json.loads((ROOT/'dsh'/(family+'-profiles.json')).read_text())
 return {model:record for model,record in registry['profiles'].items() if record['family']==family and record['status']=='passed' and catalog.get(model,{}).get('enabled',family!='maya')}

def current(family):
 revisions={r['source_commit'] for r in entries(family).values()}
 return next(iter(revisions)) if len(revisions)==1 else 'mixed:'+','.join(sorted(revisions))

def install(family,stage,revision,source):
 registry_path=ROOT/'dsh/qualified-native-profiles.json';catalog=json.loads((ROOT/'dsh'/(family+'-profiles.json')).read_text());registry=json.loads(registry_path.read_text())
 selected=entries(family)
 if not selected:raise RuntimeError('No independently qualified enabled native profiles')
 rollback=stage/'native-rollback';rollback.mkdir();snapshots={}
 for path in [registry_path,*[ROOT/'dsh'/catalog[m]['config'] for m in selected]]:
  snapshots[str(path)]=path.read_text()
 write(rollback/'files.private.json',snapshots)
 token=secrets.token_hex(24)
 for model,record in selected.items():
  path=ROOT/'dsh'/catalog[model]['config'];cfg=json.loads(path.read_text())
  binary=source/record['binary_relative']
  if not binary.is_file():raise RuntimeError('Candidate lacks qualified binary '+str(binary))
  cfg.update(cwd=str(source),exe=str(binary));cfg['local_validation']={'status':'candidate','source_commit':revision,'binary_sha256':digest(binary),'scope':'Provisional short-tool qualification; public callers are rejected until finalization.'}
  write(path,cfg)
  updated=dict(record,status='candidate',candidate_owner=token,source=str(source),source_commit=revision,binary=str(binary),binary_sha256=digest(binary),config_sha256=config_fingerprint(cfg))
  registry['profiles'][model]=updated
 write(registry_path,registry)
 return token

def finalize(stage,revision):
 registry_path=ROOT/'dsh/qualified-native-profiles.json';registry=json.loads(registry_path.read_text());snapshots=json.loads((stage/'native-rollback/files.private.json').read_text())
 for model,record in registry['profiles'].items():
  if record.get('status')!='candidate':continue
  if record['source_commit']!=revision:raise RuntimeError('Unexpected candidate revision')
  family=record['family'];catalog=json.loads((ROOT/'dsh'/(family+'-profiles.json')).read_text());path=ROOT/'dsh'/catalog[model]['config']
  if str(path) not in snapshots:raise RuntimeError('Unexpected provisional native profile')
  cfg=json.loads(path.read_text());cfg['local_validation'].update(status='passed',config_sha256=config_fingerprint(cfg),evidence=str(stage.relative_to(ROOT)),scope='One strict two-step DSH read-tool round trip and required per-card parity; no full-window or sustained-performance claim.')
  write(path,cfg);record.update(status='passed',evidence=str(stage.relative_to(ROOT)));record.pop('candidate_owner',None)
 write(registry_path,registry)

def rollback(stage):
 path=stage/'native-rollback/files.private.json'
 if not path.exists():return False
 for name,text in json.loads(path.read_text()).items():
  target=Path(name);temporary=target.with_name(target.name+'.restore');temporary.write_text(text);temporary.replace(target)
 return True
