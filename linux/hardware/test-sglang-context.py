#!/usr/bin/env python3
"""Isolated AMD KV/context trials; preserves active profiles and stops owned workers."""
import argparse, importlib.util, json, os, signal, socket, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('spec_tests', ROOT/'hardware/test-speculative.py')
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--mode', choices=['mtp','dflash'], default='mtp')
p.add_argument('--kv', choices=['bfloat16','fp8_e5m2','fp8_e4m3'], required=True)
p.add_argument('--context',type=int,required=True)
p.add_argument('--memory',type=float,default=.85)
p.add_argument('--long',action='store_true')
a=p.parse_args()
from amd_device import graphics_devices
if len(graphics_devices("0x1002")) != 1:p.error("Historical single-AMD harness; use hardware/test-dual-amd.py for the current pair")
case=f'sglang-{a.mode}-{a.kv}-{a.context}-{a.memory}'
s.OUT=ROOT/'hardware/generated/sglang-context-2026-10-16'
original_launch=s.launch
original_validate=s.validate
long_result={}
def launch(_):
 cmd,env,_=original_launch('sglang-mtp2-standard-verify' if a.mode=='mtp' else 'sglang-dflash8-standard-nocache')
 cmd+=['--kv-cache-dtype',a.kv,'--context-length',str(a.context),'--max-total-tokens',str(a.context),'--mem-fraction-static',str(a.memory)]
 return cmd,env,a.context

def capacities(value):
 if isinstance(value,dict):
  for key,item in value.items():
   if key=='max_total_num_tokens' and isinstance(item,int):yield item
   yield from capacities(item)
 elif isinstance(value,list):
  for item in value:yield from capacities(item)
def validate():
 allocated=list(capacities(s.request('/get_server_info')))
 print('CAPACITY',case,allocated,flush=True)
 if not allocated or min(allocated)<a.context:raise RuntimeError(f'Insufficient actual KV capacity: {allocated}')
 result=original_validate()
 result['allocated_token_capacity']=allocated
 if a.long and all(result[k] for k in ('arithmetic','ordered_json','tool_roundtrip')):
  from tokenizers import Tokenizer
  tok=Tokenizer.from_file(str(Path(s.TARGET)/'tokenizer.json'))
  n=max(200,(a.context-2500)//32)
  lines=[f'Record {i:05d}: location bay {i%97}, blue bolts {i%31+1}, washers {i%43+2}, boxed sets {i%19+1}.' for i in range(n)]
  codes=['ALPHA-734','BRAVO-915','CHARLIE-268']
  for index,code in zip([5,n//2,n-5],codes):lines[index]+=' Secret marker: '+code
  prompt='Read these records and return all three secret markers, exactly as written.\n'+'\n'.join(lines)
  count=len(tok.encode(prompt).ids)
  if count>a.context-512:raise RuntimeError(f'Long test too large: {count}')
  print('LONG',case,'estimated_prompt_tokens',count,flush=True)
  s.request('/flush_cache',{})
  t=time.monotonic();d=s.chat([{'role':'user','content':prompt}]);elapsed=time.monotonic()-t
  answer=d['choices'][0]['message'].get('content') or ''
  long_result.update(usage=d['usage'],seconds=elapsed,answer=answer,passed=all(c in answer for c in codes))
  print('LONG_RESULT',case,long_result,flush=True)
  assert long_result['passed'],answer
 return result
s.launch=launch;s.validate=validate
if any(s.backend_switch.is_inference(x) for x in s.backend_switch.processes().values()):p.error('Configured inference is already active; use its scoped handover first')
with socket.socket() as sock:
 sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
 sock.bind(('127.0.0.1',s.PORT))
def stop(*_):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGHUP,stop)
r=s.run(case,True)
r.update(kv=a.kv,mode=a.mode,memory_fraction=a.memory,long_retrieval=long_result)
(s.OUT/(case+'.json')).write_text(json.dumps(r,indent=2)+'\n')
raise SystemExit(0 if r['status']=='passed' else 1)
