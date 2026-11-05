"""Conservative campaign watchdog policy; no GPU/framework imports."""
from pathlib import Path
import json,os,time,signal,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
DEFAULT={'heartbeat_seconds':6,'load_seconds':1800,'first_token_seconds':None,'prefill_seconds':1800,'request_seconds':1800,'idle_seconds':20,'cleanup_seconds':15}
from short_test_timing import violation as timing_violation
def violation(now,heartbeat,progress,limits=DEFAULT):return timing_violation(now,heartbeat,progress,limits)
def durable(path,value):
 path=Path(path);tmp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
 with tmp.open('w') as f:json.dump(value,f);f.write('\n');f.flush();os.fsync(f.fileno())
 tmp.replace(path)
 # Also persist the rename, so a reset is less likely to lose the latest record.
 fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def start_ticks(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def main():
 directory=Path(sys.argv[1]);label=sys.argv[2];pid=int(sys.argv[3]);ticks=sys.argv[4];owner=sys.argv[5];limits=json.loads(sys.argv[6]);heartbeat=directory/(label+'.heartbeat.private.json');progress=directory/(label+'.progress.private.json');fault=directory/(label+'.watchdog-fault.private.json');stop=directory/(label+'.watchdog-stop.private.json');pinned={};boot=time.monotonic();last=None
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'dsh'));from inference_swap import OwnedScope
 base=Path('/sys/fs/cgroup/user.slice')/('user-'+str(os.getuid())+'.slice')/('user@'+str(os.getuid())+'.service')
 while not stop.exists():
  try:controller_alive=start_ticks(pid)==ticks
  except OSError:controller_alive=False
  now=time.monotonic()
  try:h=json.loads(heartbeat.read_text())
  except (OSError,ValueError):
   if not controller_alive:last='supervisor process ended or changed identity';break
   if now-boot>limits['heartbeat_seconds']:last='supervisor heartbeat never arrived';break
   time.sleep(.1);continue
  assert h['owner']==owner and h['controller_pid']==pid
  for unit in h.get('owned_units',[]):
   if unit in pinned:continue
   if not (unit.startswith('dsh-worker-') or unit==h.get('runner_unit')):raise RuntimeError('Unexpected watchdog scope')
   record=h.get('owned_scopes',{}).get(unit)
   if record is None:continue # supervisor has not published a pinned boundary yet
   cg=Path(record['directory'])
   if cg.name!=unit or not cg.is_relative_to(base):raise RuntimeError('Invalid owned cgroup path')
   try:
    scope=OwnedScope(cg,unit)
    st=os.fstat(scope.fd)
    if st.st_dev!=record['device'] or st.st_ino!=record['inode']:
     os.close(scope.kill_fd);os.close(scope.fd);scope.closed=True
     raise RuntimeError('Owned cgroup identity changed')
    # The supervisor established the task tag before pinning this unique cgroup.
    # All descendants remain owned even when a child deliberately changes env.
    pinned[unit]=scope
   except FileNotFoundError:continue
  if not controller_alive:last='supervisor process ended or changed identity';break
  try:p=json.loads(progress.read_text())
  except (OSError,ValueError):p={'phase':'loading','phase_started':boot,'request_started':boot,'last_output':boot}
  # The supervisor marks cleanup independently of a client that may be blocked in recv.
  if h.get('cleanup_started') is not None:p={'phase':'cleanup','phase_started':h['cleanup_started']}
  last=violation(now,h,p,limits)
  if last:break
  time.sleep(.1)
 if stop.exists():return
 record={'status':'latched','reason':last,'monotonic':time.monotonic(),'owner':owner,'controller_pid':pid,'owned_units':list(pinned)};durable(fault,record)
 lock=Path(__file__).resolve().parents[2]/'hardware/generated/GPU-LOCK'
 try:
  old=json.loads(lock.read_text())
  if old.get('owner')==owner:durable(lock,{'owner':'watchdog-fault-'+label,'purpose':'Persistent hold: '+str(last),'stage':label,'prior_owner':owner,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
 except OSError:pass
 try:
  if start_ticks(pid)==ticks:os.kill(pid,signal.SIGTERM)
 except OSError:pass
 time.sleep(1)
 errors=[]
 for unit,scope in pinned.items():
  try:scope.terminate();scope.close()
  except Exception as e:errors.append(unit+':'+type(e).__name__+':'+str(e))
 record['cleanup_errors']=errors;durable(fault,record)
if __name__=='__main__':main()
