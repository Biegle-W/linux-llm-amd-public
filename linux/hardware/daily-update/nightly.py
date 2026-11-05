"""Serialized daily updates using one strict tool round trip per enabled profile."""
from pathlib import Path
import argparse,datetime,fcntl,json,os,secrets,signal,subprocess,sys,time,traceback
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh')]
import daily_update as builders
from short_cases import write,run_case
import native_updates

class Llama(builders.Llama):
 def install(self,stage,revision,logfile):
  self.held_sources()
  settings=json.loads(self.pin.read_text());write(stage/'llama-before.private.json',settings)
  settings.update(source_commit=revision,source_path=str(stage/'llama.cpp'))
  settings['source_overrides']={m:r for m,r in settings.get('source_overrides',{}).items() if r.get('manual_runtime_pin')}
  write(self.pin,settings)
 def rollback(self,stage,logfile):
  if (stage/'llama-before.private.json').exists():write(self.pin,json.loads((stage/'llama-before.private.json').read_text()))

class NativeMixin:
 family=''
 def models(self):return list(native_updates.entries(self.family))
 def current(self):return native_updates.current(self.family)
 def install(self,stage,revision,logfile):
  source=stage/('source' if self.family=='maya' else 'src')
  token=native_updates.install(self.family,stage,revision,source)
  os.environ['LOCAL_LLM_UPDATE_CANDIDATE']=token
 def rollback(self,stage,logfile):native_updates.rollback(stage)
 def finalize(self,stage,revision,table):native_updates.finalize(stage,revision)
class Maya(NativeMixin,builders.Maya):family='maya'
class StrataDeepSeek(NativeMixin,builders.StrataDeepSeek):family='strata'

def engines():return {e.kind:e for e in [Llama(),builders.Vllm(),builders.Sglang(),builders.Strata(),Maya(),StrataDeepSeek()]}

def phase(stage,label,value='loading'):
 now=time.monotonic();write(stage/(label+'.progress.private.json'),{'phase':value,'phase_started':now,'last_output':now,'request_started':now})

def verify_cases(models,results):
 if not models or len(models)!=len(set(models)) or set(models)!=set(results):raise RuntimeError('Incomplete model coverage')
 for model,result in results.items():
  if (result.get('status')!='passed-one-short-DSH-check' or not result.get('owned_unload_requested')
      or len(result.get('requests',[]))!=2 or any(r.get('status')!='completed' for r in result['requests'])
      or not result.get('tool',{}).get('final_marker_correct') or not result['tool'].get('tool_call_result_ids_match')):
   raise RuntimeError('Incomplete strict tool qualification: '+model)

def changed_runtime_candidates(engine):
 if isinstance(engine,NativeMixin):
  catalog=json.loads((ROOT/'dsh'/(engine.family+'-profiles.json')).read_text())
  return ['dsh/qualified-native-profiles.json',*['dsh/'+catalog[m]['config'] for m in engine.models()]]
 return {'llama':['dsh/llama-runtime.json'],'sglang':['sglang/fork-pin.json']}.get(engine.kind,[])

def retry_publication(state):
 pending=state.get('publication_pending')
 if not pending:return True
 try:
  from publish import publish
  publish(builders.WORK,pending,builders.WORK/'publication.private.log')
 except Exception as error:
  state['publication_error']=type(error).__name__+': '+str(error);builders.save_state(state)
  print('Publication pending: '+state['publication_error'],flush=True);return False
 state.pop('publication_pending',None);state.pop('publication_error',None);builders.save_state(state);return True

def cycle(plan):
 plan=json.loads(Path(plan).read_text());stage=Path(plan['stage']);label='update';engine=engines()[plan['engine']]
 before_files={n:(ROOT/n).read_bytes() if (ROOT/n).exists() else None for n in changed_runtime_candidates(engine)}
 state=builders.load_state();result={'engine':engine.name,'kind':engine.kind,'from':plan['current'],'to':plan['latest'],'scope':'One short strict DSH read-tool round trip per enabled profile; no baseline, full-window or throughput gates','models':plan['models'],'result':'starting'}
 directory=stage/'result';directory.mkdir(exist_ok=False);installed=False;passed=False
 try:
  if engine.current()!=plan['current'] or engine.models()!=plan['models']:raise RuntimeError('Selected runtime/catalog changed since admission')
  phase(stage,label)
  if not plan.get('prepared'):engine.prepare(stage,plan['latest'],stage/'build.private.log')
  phase(stage,label);engine.check(stage,stage/'parity.private.log')
  phase(stage,label);state['provisional']={'engine':engine.kind,'stage':str(stage),'revision':plan['latest'],'policy':'short-tools-v1'};builders.save_state(state)
  installed=True;engine.install(stage,plan['latest'],stage/'install.private.log')
  results={}
  for model in plan['models']:
   phase(stage,label)
   results[model]=run_case(getattr(engine,'routing_kind',engine.kind),model,stage/('case-'+model),stage,label)
  verify_cases(plan['models'],results)
  result['cases']=results;engine.finalize(stage,plan['latest'],'Strict short-tool checks passed')
  if engine.current()!=plan['latest']:raise RuntimeError('Promoted source/version identity differs')
  state['engines'][engine.kind]={'production':plan['latest'],'promoted':datetime.date.today().isoformat(),'policy':'short-tools-v1','models':plan['models']}
  passed=True;result.update(result='promoted',detail='Every selected profile passed its strict two-step read-tool check; required per-card parity passed.')
 except BaseException as error:
  result.update(result='rejected',detail=type(error).__name__+': '+str(error));result['traceback']=traceback.format_exc()
  if installed:
   engine.rollback(stage,stage/'rollback.private.log')
   if engine.current()!=plan['current']:raise RuntimeError('Rollback identity mismatch')
   result['rollback_verified']=True
  state['engines'].setdefault(engine.kind,{}).update(rejected=plan['latest'],reason=result['detail'],date=datetime.date.today().isoformat(),policy='short-tools-v1')
 finally:
  if passed or not installed or result.get('rollback_verified'):state.pop('provisional',None)
  builders.save_state(state);os.environ.pop('LOCAL_LLM_UPDATE_CANDIDATE',None)
  result['runtime_files']=[n for n,old in before_files.items() if (ROOT/n).exists() and (ROOT/n).read_bytes()!=old]
  result['status']='passed' if passed else 'failed';write(directory/'result.private.json',result);phase(stage,label,'cleanup')
 # A cleanly rejected candidate is a completed updater operation; hardware faults are latched by the supervisor.
 return 0

def reject_failed_guard(engine,stage,plan,guard):
 """Restore only this transaction after a failed final guard; retain its hold."""
 state=builders.load_state();pending=state.get('provisional')
 if pending and (pending.get('stage')!=str(stage) or pending.get('engine')!=engine.kind):
  raise RuntimeError('Another provisional transaction exists; preserve it')
 reason='Final guard/cleanup failed; retained hardware hold requires review'
 if not guard.get('runner_pid') and not pending:
  write(stage/'outer-guard-recovery.private.json',{'status':'guard-admission-blocked-no-runtime-change','hold_released':False})
  return True
 state['provisional']={'engine':engine.kind,'stage':str(stage),'revision':plan['latest'],'policy':'short-tools-v1','outer_guard_failure':True}
 builders.save_state(state)
 if not guard.get('owned_cgroups_empty') or guard.get('remaining_KFD_clients'):
  write(stage/'outer-guard-recovery.private.json',{'status':'pending-owned-cleanup-review','reason':reason})
  return False
 if pending or engine.current()!=plan['current']:
  engine.rollback(stage,stage/'outer-rollback.private.log')
 if engine.current()!=plan['current']:raise RuntimeError('Final-guard rollback identity mismatch; provisional state retained')
 previous=json.loads((stage/'engine-before.private.json').read_text())
 state['engines'][engine.kind]=dict(previous or {},rejected=plan['latest'],reason=reason,date=datetime.date.today().isoformat(),policy='short-tools-v1')
 state.pop('provisional');builders.save_state(state)
 result_path=stage/'result/result.private.json'
 if result_path.exists():
  result=json.loads(result_path.read_text());result['inner_result']=result.get('result');result['inner_detail']=result.get('detail');result.update(result='rejected',status='failed',detail=reason,rollback_verified=True,runtime_files=[]);write(result_path,result)
 write(stage/'outer-guard-recovery.private.json',{'status':'rolled-back-and-verified','reason':reason,'hold_released':False})
 return True

def recover_pending(state):
 pending=state.get('provisional')
 if not pending:return
 if pending.get('policy')!='short-tools-v1':raise RuntimeError('Legacy provisional update requires explicit reviewed recovery; no automatic new work')
 engine=engines()[pending['engine']];stage=Path(pending['stage'])
 if pending.get('outer_guard_failure'):
  plan=json.loads((stage/'plan.private.json').read_text());guard=json.loads((stage/'update.guard.private.json').read_text())
  if not guard.get('owned_cgroups_empty') or guard.get('remaining_KFD_clients'):raise RuntimeError('Final guard cleanup remains unverified; explicit owned recovery required')
  reject_failed_guard(engine,stage,plan,guard)
  return
 engine.rollback(stage,stage/'recovery.private.log')
 state.pop('provisional');builders.save_state(state)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check',action='store_true');parser.add_argument('--engines',default=','.join(engines()))
 parser.add_argument('--no-publish',action='store_true');parser.add_argument('--recover-only',action='store_true')
 parser.add_argument('--cycle',help=argparse.SUPPRESS)
 args=parser.parse_args()
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
 if args.cycle:return cycle(args.cycle)
 selected=engines();keys=args.engines.split(',')
 if any(k not in selected for k in keys):parser.error('Unknown engine')
 builders.WORK.mkdir(parents=True,exist_ok=True)
 with (builders.WORK/'serialization.lock').open('a+') as mutex:
  try:fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:print('Skipped: another daily updater owns serialization');return 0
  state=builders.load_state()
  # Check-only is read-only; normal runs never build or recover over any task/client/hold.
  if not args.check:
   reason=builders.busy()
   if reason or (builders.GEN/'STOP').exists():print('Skipped: '+str(reason or 'STOP hold'));return 0
   from backend_switch import processes,is_inference
   if any(is_inference(p) for p in processes().values()) or list(Path('/sys/class/kfd/kfd/proc').glob('[0-9]*')):
    print('Skipped: existing inference/KFD ownership; preserve it');return 0
   recover_pending(state)
  if args.recover_only:return 0
  if not args.check and not args.no_publish and not retry_publication(state):return 1
  results=[]
  for key in keys:
   engine=selected[key]
   if not engine.models():print(key+': no enabled qualified profiles; held/retired profiles preserved');continue
   try:current,latest=engine.current(),engine.latest()
   except Exception as error:print(key+': version audit failed: '+str(error));continue
   status='current' if current==latest else 'rejected revision retained' if state['engines'].get(key,{}).get('rejected')==latest else 'update available'
   print(key+': '+current+' -> '+latest+'; '+status,flush=True)
   if args.check or status!='update available':continue
   reason=builders.busy()
   if reason:print('Skipped remaining work: '+reason);break
   stamp=datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')+'-'+secrets.token_hex(3)
   stage=builders.WORK/stamp/key;stage.mkdir(parents=True)
   models=engine.models();plan={'engine':key,'current':current,'latest':latest,'models':models,'stage':str(stage)};write(stage/'plan.private.json',plan)
   write(stage/'engine-before.private.json',state['engines'].get(key))
   now=time.monotonic();phase(stage,'update')
   from resource_policy import scope_limits
   limits=scope_limits()
   spec={'purpose':'Daily engine update '+key,'prevention':True,'timeout':43200,'runner_memory_max':str(limits['memory.max']),'minimum_available_GiB':1,
         'command':[sys.executable,'-B',str(Path(__file__).resolve()),'--cycle',str(stage/'plan.private.json')],
         'env':{'LOCAL_LLM_SWAP_POLICY':'loading-swap-v5','BUILD_JOBS':'2','PYTHONPATH':os.pathsep.join([str(ROOT/'hardware/daily-update'),str(ROOT/'hardware'),str(ROOT/'dsh')])},
         'watchdog_limits':{'heartbeat_seconds':6,'load_seconds':7200,'first_token_seconds':None,'prefill_seconds':1800,'request_seconds':1800,'idle_seconds':20,'cleanup_seconds':15}}
   write(stage/'update.stage.private.json',spec)
   rc=subprocess.run([sys.executable,'-B',str(ROOT/'hardware/daily-update/guarded_stage.py'),str(stage),'update']).returncode
   guard=json.loads((stage/'update.guard.private.json').read_text())
   if rc or guard['status']!='passed' or not guard.get('owned_cgroups_empty') or guard.get('remaining_KFD_clients'):
    try:reject_failed_guard(engine,stage,plan,guard)
    except Exception as error:print('Final guard rollback pending: '+str(error),flush=True)
    print('Stopped: guard/cleanup failure; inspect retained hold and recovery evidence');return 1
   result=json.loads((stage/'result/result.private.json').read_text());results.append(result);print(key+': '+result['result'],flush=True)
   state=builders.load_state()
   # Do not erase build/runtime evidence or retry a rejected source.
  if results:
   write(builders.WORK/'latest-short-update.private.json',{'policy':'short-tools-v1','results':results})
   if not args.no_publish:
    public_rows=[{k:r[k] for k in ['engine','kind','from','to','result','detail','runtime_files'] if k in r} for r in results]
    state['publication_pending']=public_rows;builders.save_state(state)
    if not retry_publication(state):return 1
 return 0

if __name__=='__main__':raise SystemExit(main())
