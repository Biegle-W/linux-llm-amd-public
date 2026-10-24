#!/usr/bin/env python3
"""Validate a running native Maya or Strata DeepSeek worker; tools are synthetic."""
import argparse,hashlib,importlib.util,json,re,sys,time,uuid
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
from amd_device import amd_devices
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--port',type=int,required=True);ap.add_argument('--model',required=True);ap.add_argument('--context',type=int,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--long-tokens',type=int);ap.add_argument('--prompt-seed',help='Fixed synthetic record salt for matched comparisons; default is fresh random salt')
ap.add_argument('--token-count-path',choices=['/api/tokens','/v1/messages/count_tokens'],default='/api/tokens',help='Native token-count route; Strata DeepSeek uses the Anthropic route')
a=ap.parse_args();assert not a.output.exists(),'Preserve the previous validation record'
spec=importlib.util.spec_from_file_location('benchmark',ROOT/'hardware/benchmark-current-amd.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.PORTS['maya']=(a.port,a.port)
record={'model':a.model,'context':a.context,'status':'running','tests':{},'method':'Functional checks with thinking off and greedy sampling; synthetic tool results only; not a throughput benchmark'}
def save():a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(record,indent=2)+'\n')
def request(path,body=None):return b.request(a.port,path,body,timeout=1200)
def chat(messages,**extra):return request('/v1/chat/completions',dict(model=a.model,messages=messages,max_tokens=128,temperature=0,chat_template_kwargs={'enable_thinking':False},**extra))
save()
try:
 h=request('/health');assert h['model']==a.model and h['max_context']==a.context and h.get('loaded',not h.get('unloaded',True))
 math,text=b.stream('maya',a.model,'What is 17 times 19? Reply with only the integer.',limit=64,sampled=False);assert re.search(r'\b323\b',text);record['tests']['arithmetic_streaming']={'passed':True,**math};save()
 result=chat([{'role':'user','content':'Return only a JSON object with key answer and integer value 137. No markdown.'}]);message=result['choices'][0]['message'];assert json.loads(message['content'])['answer']==137;record['tests']['json']={'passed':True,'usage':result['usage'],'answer_sha256':hashlib.sha256(message['content'].encode()).hexdigest()};save()
 tools=[{'type':'function','function':{'name':'lookup_inventory','description':'Look up stock for a SKU','parameters':{'type':'object','properties':{'sku':{'type':'string'}},'required':['sku']}}}]
 history=[{'role':'user','content':'Call lookup_inventory for SKU BOLT-42, then report the returned stock.'}]
 message=chat(history,tools=tools,tool_choice={'type':'function','function':{'name':'lookup_inventory'}})['choices'][0]['message'];call=message['tool_calls'][0];assert call['function']['name']=='lookup_inventory' and json.loads(call['function']['arguments'])=={'sku':'BOLT-42'}
 response=chat(history+[message,{'role':'tool','tool_call_id':call['id'],'content':'{"sku":"BOLT-42","stock":137}'}],tools=tools,tool_choice='none');text=response['choices'][0]['message']['content'];assert '137' in text;record['tests']['tool_roundtrip']={'passed':True,'usage':response['usage'],'answer_sha256':hashlib.sha256(text.encode()).hexdigest()};save()
 if a.long_tokens:
  assert a.long_tokens<a.context-256
  salt=a.prompt_seed or uuid.uuid4().hex
  def prompt(n):
   rows=[f'Record {i:05d}: bay {i%97}, blue bolts {i%31+1}, washers {i%43+2}, sets {i%19+1}.' for i in range(n)]
   for i,marker in zip((5,n//2,n-5),('ALPHA-734','BRAVO-915','CHARLIE-268')):rows[i]+=' Secret marker: '+marker
   return salt+'\nRead these records. Return the three secret markers in order, and nothing else.\n'+'\n'.join(rows)
  lo,hi=20,a.long_tokens
  while lo+1<hi:
   mid=(lo+hi)//2;req={'model':a.model,'messages':[{'role':'user','content':prompt(mid)}],'chat_template_kwargs':{'enable_thinking':False}}
   count_req={**req,'thinking':{'type':'disabled'}} if a.token_count_path=='/v1/messages/count_tokens' else req
   counts=request(a.token_count_path,count_req)
   if counts.get('tokens',counts.get('input_tokens'))<=a.long_tokens:lo=mid
   else:hi=mid
  history=[{'role':'user','content':prompt(lo)}];long,text=b.stream('maya',a.model,'',limit=64,sampled=False,messages=history);long['markers_passed']=all(m in text for m in ('ALPHA-734','BRAVO-915','CHARLIE-268'));assert long['markers_passed'] and long['cached_tokens']==0
  record['long_context']=long;save()
  follow,text=b.stream('maya',a.model,'',limit=64,sampled=False,messages=history+[{'role':'assistant','content':text},{'role':'user','content':'Repeat the same three secret markers in order, nothing else.'}]);follow['markers_passed']=all(m in text for m in ('ALPHA-734','BRAVO-915','CHARLIE-268'));assert follow['markers_passed'];record['long_follow_up']=follow
 record['gpu_used_bytes']=[int((d/'mem_info_vram_used').read_text()) for d in amd_devices()];assert len(record['gpu_used_bytes'])==2 and min(record['gpu_used_bytes'])>2*1024**3
 record['status']='passed';save();print(a.model,'functional PASS',record.get('long_context',{}).get('usage'))
except Exception as error:
 record.update(status='failed',error_type=type(error).__name__);save();raise
