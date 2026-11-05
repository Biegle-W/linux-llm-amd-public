"""Guard a tagged task and its sibling worker cgroups; never terminate unrelated work."""
import sys,os,json,time,signal,subprocess,uuid,re,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(R/'dsh'),str(R/'hardware')]
from backend_switch import processes,is_inference
from strata_memory import MemoryGuard,vram_snapshot,startup_vram_blocker
from moe_memory import host_memory
from gpu_telemetry import snapshot
from temperature_policy import temperature_failure
from inference_swap import OwnedScope,sample_owned_memory
label=sys.argv[2];spec=json.loads((W/(label+'.stage.private.json')).read_text());owner='daily-update-'+uuid.uuid4().hex[:12];lock=R/'hardware/generated/GPU-LOCK';proc=None;locked=False;owned={};frozen=[];watchdog=None
result={'label':label,'owner':owner,'controller_pid':os.getpid(),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'starting','samples':0,'max_owned_swap_bytes':0,'max_owned_spill_bytes':0,'min_available_bytes':2**63,'min_free_VRAM_bytes':[2**63]*2}
def save():
 target=W/(label+'.guard.private.json');temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(target)
 if spec.get('prevention'):
  from prevention_guard import durable
  durable(W/(label+'.heartbeat.private.json'),{'monotonic':time.monotonic(),'owner':owner,'controller_pid':os.getpid(),'owned_units':list(owned),'owned_scopes':{unit:{'directory':str(scope.directory),'device':os.fstat(scope.fd).st_dev,'inode':os.fstat(scope.fd).st_ino} for unit,scope in owned.items() if not scope.closed},'runner_unit':result.get('runner_unit'),'cleanup_started':result.get('cleanup_started')})
def interrupt(*a):
 if not globals().get('cleanup_active',False):raise KeyboardInterrupt
cleanup_active=False
for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,interrupt)
def discover():
 from known_scope import in_known_scope
 boundaries=['/'+str(s.directory.relative_to('/sys/fs/cgroup')) for s in owned.values() if not s.closed and s.populated()]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   membership=(p/'cgroup').read_text().strip()
   if in_known_scope(membership,boundaries):continue
   if ('LOCAL_LLM_TASK_OWNER='+owner).encode() not in (p/'environ').read_bytes().split(b'\0'):continue
   membership=(p/'cgroup').read_text().strip();assert membership.startswith('0::/user.slice/'),membership
   rel=membership.split('::',1)[1];directory=Path('/sys/fs/cgroup')/rel.lstrip('/');unit=directory.name
   if unit not in owned and unit.endswith('.scope') and (unit.startswith('dsh-worker-') or unit==result.get('runner_unit')):
    owned[unit]=OwnedScope(directory,unit)
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 result['owned_units']=list(owned)
def check_kernel():
 text=subprocess.check_output(['journalctl','-k','--after-cursor='+result['kernel_start_cursor'],'--no-pager','-o','cat'],text=True,timeout=3)
 (W/(label+'.kernel.private.log')).write_text(text)
 errors=[l for l in text.splitlines() if re.search(r'device lost from bus|GPU reset|GPU fault|ring .*timeout|SMU.*(error|failed|no response|timeout)|MES.*(error|failed|respond)|amdgpu.*(page fault|VM fault)|Out of memory|oom-kill',l,re.I)]
 if errors:result['new_kernel_faults']=errors;raise RuntimeError('New GPU/bus/OOM kernel fault')
def cleanup():
 failures=[]
 try:discover()
 except Exception as e:failures.append('discover:'+str(e))
 for unit,scope in list(owned.items()):
  try:scope.terminate();scope.close()
  except Exception as e:failures.append(unit+':'+str(e))
 if proc is not None and proc.poll() is None:
  try:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
  except ProcessLookupError:proc.wait(timeout=3)
 result['owned_cgroups_empty']=all(not o.populated() for o in owned.values());result['runner_exited']=proc is None or proc.poll() is not None
 if failures:raise RuntimeError('Owned cleanup failure: '+';'.join(failures))
def freeze_sources():
 for item in spec.get('freeze_downloads', [])+spec.get('freeze_tasks', []):
  unit=item['unit'];pid=item['pid']
  active=subprocess.check_output(['systemctl','--user','show',unit,'-p','ActiveState','--value'],text=True).strip()
  if active!='active':continue
  rel=subprocess.check_output(['systemctl','--user','show',unit,'-p','ControlGroup','--value'],text=True).strip()
  cg=Path('/sys/fs/cgroup')/rel.lstrip('/')
  assert str(pid) in (cg/'cgroup.procs').read_text().split(),'Download ownership changed'
  cmd=[x.decode() for x in Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0') if x]
  cwd=Path('/proc',str(pid),'cwd').resolve()
  if 'argv_prefix' in item:
   assert cmd[:len(item['argv_prefix'])]==item['argv_prefix'],'Background task identity changed'
  else:
   assert any((cwd/x).resolve()==Path(item['script']) for x in cmd[1:]),'Download script ownership changed'
  if (cg/'cgroup.freeze').read_text().strip()=='1':continue
  frozen.append(item)
  subprocess.run(['systemctl','--user','freeze',unit],check=True,timeout=10)
 result['frozen_owned_downloads']=frozen
 save()
def thaw_sources():
 for item in frozen:
  subprocess.run(['systemctl','--user','thaw',item['unit']],check=True,timeout=10)
 result['owned_downloads_thawed']=True
try:
 assert not (R/'hardware/generated/STOP').exists(),'Persistent STOP hold; preserve it'
 claim={'owner':owner,'pid':os.getpid(),'purpose':spec.get('purpose',label),'expected_end':'bounded daily updater stage'}
 fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644);locked=True;os.write(fd,(json.dumps(claim)+'\n').encode());os.close(fd)
 assert not any(is_inference(p) for p in processes().values()),'Unrelated inference active; preserve it'
 assert not list(Path('/sys/class/kfd/kfd/proc').glob('[0-9]*')),'Existing KFD client; preserve it'
 freeze_sources()
 reason=startup_vram_blocker(vram_snapshot());assert not reason,reason
 assert host_memory()[1]>=spec.get('minimum_available_GiB',3)*2**30,'Insufficient host headroom'
 cur=subprocess.check_output(['journalctl','-k','-n','0','--show-cursor','--no-pager'],text=True);result['kernel_start_cursor']=cur.split('-- cursor: ')[-1].strip();assert result['kernel_start_cursor'].startswith('s=')
 env=os.environ.copy();env.update(spec.get('env',{}));env['LOCAL_LLM_TASK_OWNER']=owner
 result['runner_unit']='llm-update-run-'+uuid.uuid4().hex+'.scope'
 command=['systemd-run','--user','--scope','--quiet','--unit='+result['runner_unit'],'-p','MemoryMax='+spec['runner_memory_max'],'-p','MemoryHigh=infinity',*spec['command']]
 from storage_health import StorageHealthMonitor
 storage_health=StorageHealthMonitor();storage_health.check()
 guard=MemoryGuard();start=time.monotonic();last_kernel=0;last_discover=0
 if spec.get('prevention'):
  from prevention_guard import start_ticks,DEFAULT
  save();watchdog_log=(W/(label+'.watchdog.private.log')).open('w')
  watchdog=subprocess.Popen([sys.executable,str(R/'hardware/daily-update/prevention_guard.py'),str(W),label,str(os.getpid()),start_ticks(os.getpid()),owner,json.dumps(spec.get('watchdog_limits',DEFAULT))],stdout=watchdog_log,stderr=subprocess.STDOUT,start_new_session=True)
  result['watchdog_pid']=watchdog.pid
 if spec.get('graphics_policy'):
  from swap_activity import SwapActivity,read_host_activity
  swap_activity=SwapActivity();phase='loading';phase_offset=0;graphics_low=0;last_graphics_sample=0

 with (W/(label+'.private.log')).open('w') as log,(W/(label+'.samples.private.jsonl')).open('w') as samples:
  proc=subprocess.Popen(command,cwd=spec.get('cwd',str(R)),env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);result['runner_pid']=proc.pid;save()
  while proc.poll() is None:
   if watchdog is not None:
    fault=W/(label+'.watchdog-fault.private.json')
    if fault.exists():result['watchdog_fault']=json.loads(fault.read_text());raise RuntimeError('Independent prevention watchdog stopped the stage')
    if watchdog.poll() is not None:raise RuntimeError('Independent prevention watchdog unavailable')
   storage_health.check()
   readings=vram_snapshot();available=host_memory()[1];thermal=snapshot();now=time.monotonic()
   if now-last_discover>=.5:discover();last_discover=now
   totals={'swap':0,'spill':0,'processes':0}
   for scope in owned.values():
    if scope.populated():
     reading=sample_owned_memory(scope)
     if reading is None:
      if not scope.populated():continue # worker exited between population check and sample
      from cleanup_boundary import drain_completed_scope
      progress=json.loads((W/(label+'.progress.private.json')).read_text())
      terminal_path=Path(json.loads((W/'active-terminal.private.json').read_text())['path']) if (W/'active-terminal.private.json').exists() else W/'result/result.private.json'
      terminal=json.loads(terminal_path.read_text())
      drain_completed_scope(scope,progress,terminal)
      result.setdefault('owned_cleanup_drains',[]).append(scope.unit)
      continue # only after pinned termination proved this scope empty; no synthetic reading
     for k in totals:totals[k]+=reading[k]
   result['samples']+=1;result['max_owned_swap_bytes']=max(result['max_owned_swap_bytes'],totals['swap']);result['max_owned_spill_bytes']=max(result['max_owned_spill_bytes'],totals['spill']);result['min_available_bytes']=min(result['min_available_bytes'],available);result['min_free_VRAM_bytes']=[min(x,y['free']) for x,y in zip(result['min_free_VRAM_bytes'],readings)]
   scope_stats={}
   for unit,scope in owned.items():
    fields={}
    for field in ['memory.current','memory.peak','memory.high','memory.max','memory.events','memory.stat','memory.pressure','memory.swap.current','memory.swap.peak']:
     try:fields[field]=(scope.directory/field).read_text().strip()
     except (AttributeError,OSError):pass
    scope_stats[unit]=fields
   gtt={}
   for card in readings:
    device=Path('/sys/bus/pci/devices')/card['device']
    gtt[card['device']]={key:(device/key).read_text().strip() for key in ['mem_info_gtt_total','mem_info_gtt_used']}
   samples.write(json.dumps({'elapsed':now-start,'host_available':available,'owned_memory':totals,'VRAM':readings,'thermal':thermal,'scope_stats':scope_stats,'GTT':gtt})+'\n');samples.flush()
   reason=guard.check(available,totals['swap'],totals['spill'],readings)
   if spec.get('prevention'):
    if available<1*2**30:reason='Owner host reserve below 1 GiB'
    if min(r['free'] for r in readings)<128*2**20:reason='Owner GPU reserve below 128 MiB'
    if result['samples']%4==0:os.fsync(samples.fileno())
   if spec.get('graphics_policy'):
    # Existing graphics reserve policy: soft2GiB for4samples; hard1.5GiB. Host3GiB remains.
    free=min(r['free'] for r in readings)
    if now-last_graphics_sample>=1:
     graphics_low=graphics_low+1 if free<2*2**30 else 0;last_graphics_sample=now
    reason='Graphics headroom guard' if free<1.5*2**30 or graphics_low>=4 or available<3*2**30 else None
    event_path=Path(spec['phase_events'])
    if event_path.exists():
     with event_path.open() as ef:
      ef.seek(phase_offset)
      for line in ef:
       event=json.loads(line);phase=event['phase'];swap_activity.set_phase(phase)
      phase_offset=ef.tell()
    swap_activity.observe(read_host_activity(),phase,totals['swap']);result['swap_activity']=swap_activity.summary()
    if swap_activity.failures():reason='Inference swap activity: '+str(swap_activity.failures())
   if totals['spill']:reason='Dedicated VRAM spill'
   reason=temperature_failure(thermal,check_cpu=bool(spec.get('prevention'))) or reason
   if reason:raise RuntimeError(reason)
   if now-last_kernel>=.5:check_kernel();last_kernel=now;save()
   if now-start>spec.get('timeout',10800):raise TimeoutError('Daily updater stage deadline')
   time.sleep(.25)
  result['runner_exit_code']=proc.returncode;result['elapsed_seconds']=time.monotonic()-start;assert proc.returncode==0,'Stage runner exit '+str(proc.returncode);result['status']='passed'
except BaseException as e:result.update(status='failed',error=type(e).__name__+': '+str(e),traceback=traceback.format_exc())
finally:
 cleanup_active=True
 result['cleanup_started']=time.monotonic();save()
 try:
  cleanup()
  # Keep the original 15-second independent cleanup deadline active while
  # waiting for KFD's asynchronous client registration to disappear.
  while list(Path('/sys/class/kfd/kfd/proc').glob('[0-9]*')):
   if time.monotonic()-result['cleanup_started']>=15:raise RuntimeError('KFD clients remain after owned cleanup deadline')
   time.sleep(.05)
  if 'kernel_start_cursor' in result:check_kernel()
 except BaseException as e:result.update(status='failed',cleanup_error=type(e).__name__+': '+str(e))
 if watchdog is not None:
  from prevention_guard import durable
  durable(W/(label+'.watchdog-stop.private.json'),{'monotonic':time.monotonic()})
  watchdog.terminate()
  try:watchdog.wait(timeout=3)
  except subprocess.TimeoutExpired:watchdog.kill();watchdog.wait(timeout=3)
  fault=W/(label+'.watchdog-fault.private.json')
  if fault.exists():result['watchdog_fault']=json.loads(fault.read_text());result['status']='failed'
 try:thaw_sources()
 except BaseException as e:result.update(status='failed',thaw_error=type(e).__name__+': '+str(e))
 result['remaining_KFD_clients']=[p.name for p in Path('/sys/class/kfd/kfd/proc').glob('[0-9]*')]
 if locked and json.loads(lock.read_text()).get('owner')==owner:
  if result.get('new_kernel_faults') or result.get('watchdog_fault') or ((spec.get('resume_fault_hold') or spec.get('prevention')) and result['status']!='passed') or result['remaining_KFD_clients']:
   hold=result.get('prior_fault_hold',{'owner':'daily-update-fault-'+label,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
   hold.update(purpose='Persistent fault hold after guarded daily updater failure; review before any GPU continuation',last_failed_stage=label,new_kernel_faults=result.get('new_kernel_faults',[]))
   temp=lock.with_name('GPU-LOCK.'+owner+'.tmp');temp.write_text(json.dumps(hold,indent=2)+'\n');temp.replace(lock);result['fault_hold_latched']=True
  elif result.get('owned_cgroups_empty') and result.get('runner_exited'):
   # One bounded trial is not permission to resume the held task.
   if 'prior_fault_hold' in result:
    hold=dict(result['prior_fault_hold'])
    hold['last_bounded_trial']={'label':label,'status':result['status'],'campaign_resumed':False}
    from prevention_guard import durable
    durable(lock,hold);result['prior_hold_restored']=True
   else:
    lock.unlink();result['owned_lock_released']=True
 result['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save();print(json.dumps(result),flush=True)
sys.exit(0 if result['status']=='passed' else 1)
