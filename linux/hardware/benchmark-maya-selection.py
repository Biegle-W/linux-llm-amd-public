#!/usr/bin/env python3
"""Matched 8K DeepSeek Maya selection probes on an already guarded worker. No model launches or settings changes."""
import argparse,importlib.util,json,statistics,time
from pathlib import Path
p=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('bench',p/'hardware/benchmark-current-amd.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.PORTS['maya']=(18195,18195)
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);ap.add_argument('--warmups',type=int,default=3);ap.add_argument('--port',type=int,default=18195);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--context',type=int,default=8192,help='Expected served max_context (production DeepSeek: 32768)');a=ap.parse_args();out=a.output;assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);b.PORTS['maya']=(a.port,a.port);health=b.request(a.port,'/health');assert health['model']=='deepseek-v4.1-flash-1017-maya' and health['max_context']==a.context and not health['unloaded']
r={'status':'running','tag':a.tag,'context':a.context,'model':'deepseek-v4.1-flash-1017-maya','method':'Three sequential timed requests per short code/prose workload after excluded warmups (count retained); temperature .6, top_p .95, seed42, thinking off, 128-output cap; external SSE plus native timing retained. Cache warm; compare complete profile, not an isolated causal effect.','warmups_per_task':a.warmups,'tasks':{}}
def save():out.write_text(json.dumps(r,indent=2)+'\n')
save()
try:
 for task,prompt in b.PROMPTS.items():
  warms=[]
  for _ in range(a.warmups):
   warm,_=b.stream('maya',r['model'],prompt,limit=128);warms.append(warm)
  r['tasks'][task]={'warmup_trials':warms}
  trials=[]
  for n in range(3):
   t,_=b.stream('maya',r['model'],prompt,limit=128);assert t['usage']['completion_tokens']>=64;trials.append(t);r['tasks'][task]['trials']=trials;save();print(a.tag,task,n,round(t['decode_tps_sse'],2),flush=True)
  r['tasks'][task]['median_decode_tps']=statistics.median(t['decode_tps_sse'] for t in trials)
 r['status']='passed'
except Exception as e:r.update(status='failed',error_type=type(e).__name__);raise
finally:save()
