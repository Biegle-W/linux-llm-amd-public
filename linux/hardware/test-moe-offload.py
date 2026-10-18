#!/usr/bin/env python3
"""Bounded two-AMD CPU-expert/cache validation; stops only configured inference backends."""
from pathlib import Path
import sys,os,json,time,subprocess,signal,threading,urllib.request,re,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dsh'))
from llama_runtime import launch_spec,require_amd_headroom
from backend_switch import startup_handover,clear_owner
from amd_device import amd_devices
from moe_memory import worker_memory
OUT=ROOT/'hardware/generated/moe-offload-2026-10-18';OUT.mkdir(parents=True,exist_ok=True)
CAT={m['id']:m for m in json.loads((ROOT/'dsh/models.json').read_text())}
PORT=18030;GIB=1024**3

def request(path,data=None,timeout=600):
 req=urllib.request.Request('http://127.0.0.1:'+str(PORT)+path,None if data is None else json.dumps(data).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as res:return json.load(res)
def mem():
 m={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
 ds=amd_devices();return {'available':m['MemAvailable'],'vram':[int((d/'mem_info_vram_used').read_text()) for d in ds],'swap_used':m['SwapTotal']-m['SwapFree']}
def pswap(pid):
 try:return int(re.search(r'^VmSwap:\s+(\d+)',(Path('/proc')/str(pid)/'status').read_text(),re.M)[1])*1024
 except (OSError,TypeError):return 0
def stop(p):
 if p and p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(20)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def run(model,context=65536,cache=8192,backend='vulkan',long_tokens=8000,no_host=False,half_cpu=False):
 binary,preset,env,_=launch_spec()
 if backend=='hip':
  result=subprocess.run(['bash','-c','source "$1"; env -0','bash',str(ROOT/'hardware/rocm-env.sh')],capture_output=True,check=True)
  env=dict(x.decode().split('=',1) for x in result.stdout.split(b'\0') if x);env['LD_LIBRARY_PATH']+=':'+str(ROOT/'llm-tools/cuda-build/lib');binary=ROOT/'llama.cpp/build-hip/bin/llama-server'
 devices='ROCm0,ROCm1' if backend=='hip' else 'Vulkan0,Vulkan1';dev0=devices.split(',')[0]
 ncmoe=88 if model=='nemotron-3.5-bolt' else 40
 name=model+'-'+backend+'-c'+str(context)+'-cache'+str(cache)+('-plain-host' if no_host else '')+('-half-cpu' if half_cpu else '')
 cmd=[str(binary),'--model',CAT[model]['path'],'--alias',model,'--host','127.0.0.1','--port',str(PORT),'--device',devices,'--n-gpu-layers','99','--split-mode','layer','--tensor-split','1,1','--override-tensor','token_embd.*='+dev0,'--n-cpu-moe',str(ncmoe),'--moe-cache-mib',str(cache),'--load-mode','none','--ctx-size',str(context),'--parallel','1','--batch-size','512','--ubatch-size','128','--threads','6','--threads-batch','6','--flash-attn','on','--cache-type-k','q8_0','--cache-type-v','q8_0','--cache-ram','0','--ctx-checkpoints','0','--jinja','--reasoning','off','--chat-template-kwargs','{"enable_thinking":false}','--log-colors','off','-lv','4','--spec-type','draft-mtp' if CAT[model].get('mtp') else 'none']
 if CAT[model].get('mtp'):cmd+=['--spec-draft-n-max','3','--spec-draft-type-k','q8_0','--spec-draft-type-v','q8_0']
 if no_host:cmd+=['--no-host','--no-repack']
 if half_cpu:
  policy=ROOT/'dsh/moe-offload.json'
  if policy.exists():
   layers=json.loads(policy.read_text())['models'][model]['cpu_expert_layers']
  else:
   meta=next(x for x in json.loads((OUT/'model-metadata.json').read_text()) if x['id']==model)
   layers=sorted(int(x) for x in meta['expert_layer_bytes'] if int(x)<ncmoe)[::2]
  pattern=r'^blk\.(?:'+'|'.join(map(str,layers))+r')\.ffn_.*_exps\.weight$=CPU'
  cmd[cmd.index('--n-cpu-moe')+1]='0'
  cmd[cmd.index('--override-tensor')+1]+=','+pattern
 logpath=OUT/(name+'.log');p=None;done=threading.Event();samples=[];alerts=[];record={'model':model,'backend':backend,'context':context,'cache_mib_total':cache,'n_cpu_moe':0 if half_cpu else ncmoe,'cpu_expert_layers':layers if half_cpu else list(range(ncmoe)),'command':cmd,'checks':{},'started':time.time()}
 def watch():
  low=0
  while not done.wait(1):
   m=mem();m['process_swap'],m['nonresident_vram']=worker_memory(p.pid);samples.append(m)
   low=low+1 if m['available']<3*GIB else 0
   if low>=3 or m['process_swap']>256*1024**2 or max(m['vram'])>23*GIB or m['nonresident_vram']>256*1024**2:
    alerts.append(m);stop(p);return
 try:
  require_amd_headroom()
  with logpath.open('w') as log:
   p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   threading.Thread(target=watch,daemon=True).start();deadline=time.monotonic()+600
   while time.monotonic()<deadline:
    if p.poll() is not None:raise RuntimeError('worker exited '+str(p.returncode))
    try:
     if request('/health',timeout=1).get('status')=='ok':break
    except Exception:pass
    time.sleep(1)
   else:raise TimeoutError('startup >600 sec')
   record['ready_seconds']=round(time.time()-record['started'],3)
   def chat(messages,**extra):
    data={'model':model,'messages':messages,'max_tokens':96,'temperature':0,'chat_template_kwargs':{'enable_thinking':False},'cache_prompt':False,**extra};start=time.monotonic();res=request('/v1/chat/completions',data,timeout=900);return res,round(time.monotonic()-start,3)
   a,elapsed=chat([{'role':'user','content':'Calculate 37 + 48. Reply with only the integer.'}]);text=a['choices'][0]['message'].get('content','');assert text.strip()=='85',text;record['checks']['arithmetic']=True
   a,elapsed=chat([{'role':'user','content':'Return only valid JSON: an object with key numbers and the integers 1 through 8 in order as its array.'}],response_format={'type':'json_object'});text=a['choices'][0]['message']['content'];assert json.loads(text)['numbers']==list(range(1,9)),text;record['checks']['json']=True
   tool={'type':'function','function':{'name':'get_inventory','description':'Look up stock for a product.','parameters':{'type':'object','properties':{'sku':{'type':'string'}},'required':['sku']}}}
   messages=[{'role':'user','content':'Use get_inventory to check stock for SKU ABC-123.'}]
   a,elapsed=chat(messages,tools=[tool],tool_choice='required');msg=a['choices'][0]['message'];call=msg['tool_calls'][0];assert call['function']['name']=='get_inventory';assert json.loads(call['function']['arguments'])['sku']=='ABC-123'
   messages+=[msg,{'role':'tool','tool_call_id':call['id'],'content':'{"sku":"ABC-123","quantity":17}'}]
   a,elapsed=chat(messages,tools=[tool]);assert '17' in (a['choices'][0]['message'].get('content') or '');record['checks']['tools_roundtrip']=True
   a,elapsed=chat([{'role':'user','content':'Write a short Python function that returns the sum of squares of the integers in a list, with a short explanation.'}],max_tokens=128);record['decode_sample']={'elapsed_seconds':elapsed,'usage':a.get('usage'),'timings':a.get('timings'),'text':a['choices'][0]['message'].get('content')}
   if long_tokens:
    prefix='The access codes are START=amber-731.\n';middle='\nMIDDLE=cedar-482.\n';tail='\nEND=river-956.\nReturn only the three access code values in START, MIDDLE, END order.'
    noise='Ordinary inventory record with no access code.\n'
    count=1000
    for _ in range(3):
     text=prefix+noise*(count//2)+middle+noise*(count-count//2)+tail;n=len(request('/tokenize',{'content':text})['tokens']);count=int(count*(long_tokens-100)/n)
    text=prefix+noise*(count//2)+middle+noise*(count-count//2)+tail;actual=len(request('/tokenize',{'content':text})['tokens'])
    a,elapsed=chat([{'role':'user','content':text}],max_tokens=64);response=a['choices'][0]['message'].get('content') or '';assert all(x in response for x in ['amber-731','cedar-482','river-956']),response
    record['checks']['retrieval']=True;record['long_probe']={'raw_text_tokens':actual,'usage':a.get('usage'),'elapsed_seconds':elapsed,'timings':a.get('timings'),'text':response}
   record['passed']=True
 except Exception as e:
  record['passed']=False;record['error']=str(e);record['traceback']=traceback.format_exc()
 finally:
  done.set();stop(p);time.sleep(1)
  text=logpath.read_text(errors='replace');record['cache_lines']=[line for line in text.splitlines() if ('MoE cache size' in line or 'llama_moe_cache:' in line or 'CPU' in line and 'model buffer size' in line)][-20:]
  record['cache_both_gpus']=all((('ROCm'+str(i)) if backend=='hip' else ('Vulkan'+str(i)))+' MoE cache size' in text for i in range(2))
  record['passed']=record['passed'] and record['cache_both_gpus'] and not alerts
  if samples:record['telemetry']={'min_available_gib':round(min(m['available'] for m in samples)/GIB,3),'peak_vram_gib':[round(max(m['vram'][i] for m in samples)/GIB,3) for i in range(2)],'max_worker_swap_mib':round(max(m['process_swap'] for m in samples)/1024**2,2),'max_nonresident_vram_mib':round(max(m['nonresident_vram'] for m in samples)/1024**2,2)}
  record['alerts']=alerts;record['completed']=time.time();(OUT/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
  print(json.dumps({k:v for k,v in record.items() if k not in ['command','traceback']},indent=2),flush=True)
 return record
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--model',default='qwen3.6-35b-a3b');ap.add_argument('--context',type=int,default=65536);ap.add_argument('--cache',type=int,default=8192);ap.add_argument('--backend',default='vulkan');ap.add_argument('--long',type=int,default=8000);ap.add_argument('--plain-host',action='store_true');ap.add_argument('--half-cpu',action='store_true');a=ap.parse_args()
 with startup_handover('llama') as state:state.register()
 try:rec=run(a.model,a.context,a.cache,a.backend,a.long,a.plain_host,a.half_cpu)
 finally:clear_owner()
 sys.exit(0 if rec['passed'] else 1)
