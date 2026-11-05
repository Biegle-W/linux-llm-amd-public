"""Prepare exactly one isolated normal-router tool check from current profiles."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
GIB=2**30

def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def prepare_case(kind,model,directory,progress_path):
 directory=Path(directory);directory.mkdir(exist_ok=False)
 filenames={'llama':'models.json','vllm':'vllm-profiles.json','sglang':'sglang-profiles.json','maya':'maya-profiles.json','strata':'strata-profiles.json'}
 path=ROOT/'dsh'/filenames[kind];data=json.loads(path.read_text())
 row=next(x for x in data if x['id']==model) if isinstance(data,list) else data[model]
 if not row.get('enabled',kind!='maya'):raise RuntimeError('Disabled profiles are never automatically qualified')
 cfg={'backend':kind,'model_name':model,'context':row['context'],'max_model_len':row['context']}
 if kind in ['maya','strata']:
  native=ROOT/'dsh'/row['config'];cfg['worker_memory_limits']=json.loads(native.read_text()).get('worker_memory_limits')
  cfg['normal_native_startup']=kind=='maya' or row.get('family')=='deepseek41'
 write(directory/'profile.private.json',cfg)
 sealed={str(path):digest(path)}
 if row.get('config'):sealed[str(native)]=digest(native)
 write(directory/'input-seal.private.json',{'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),'files':sealed})
 spec={'timeout':9120,'watchdog_limits':{'heartbeat_seconds':6,'load_seconds':1800,'first_token_seconds':None,'prefill_seconds':1800,'request_seconds':1800,'idle_seconds':20,'cleanup_seconds':15}}
 write(directory/'short-check.stage.private.json',spec)
 return cfg

def check_case(cfg,directory):
 seal=json.loads((directory/'input-seal.private.json').read_text())
 if hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()!=seal['config_sha256']:raise RuntimeError('Short-check input changed')
 for path,expected in seal['files'].items():
  if digest(path)!=expected:raise RuntimeError('Normal managed profile changed during qualification: '+path)

def run_case(kind,model,directory,stage,label,env=None):
 progress=Path(stage)/(label+'.progress.private.json');prepare_case(kind,model,directory,progress)
 write(Path(stage)/'active-terminal.private.json',{'path':str(Path(directory)/'result/result.private.json')})
 child_env=dict(os.environ,**(env or {}),LOCAL_LLM_PROGRESS_PATH=str(progress))
 child_env['PYTHONPATH']=os.pathsep.join([str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh'),child_env.get('PYTHONPATH','')])
 with (Path(directory)/'controller.private.log').open('w') as log:
  proc=subprocess.run([sys.executable,'-B',str(ROOT/'hardware/daily-update/short_trial.py'),str(directory)],env=child_env,stdout=log,stderr=subprocess.STDOUT)
 result=json.loads((Path(directory)/'result/result.private.json').read_text())
 if proc.returncode or result.get('status')!='passed-one-short-DSH-check' or not result.get('owned_unload_requested'):
  raise RuntimeError('Short DSH qualification failed for '+model+': '+str(result.get('error',result.get('status'))))
 return result
