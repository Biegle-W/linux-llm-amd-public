"""Strict two-step read-tool result gate; no model or framework imports."""
import json

def events(path):
 out=[]
 if path.exists():
  for line in path.read_text().splitlines():
   try:out.append(json.loads(line))
   except ValueError:pass
 return out

def parse_result(result,path,marker):
 e=events(path);calls=[x for x in e if x.get('type')=='tool_call'];outputs=[x for x in e if x.get('type')=='tool_result'];steps=[x for x in e if x.get('type')=='status' and x.get('phase')=='step_end'];final=next((x.get('text','') for x in reversed(e) if x.get('type')=='final'),'')
 tokens=[x.get('usage',{}).get('outputTokens') for x in steps]
 result.update(tool_calls=len(calls),tool_names=[x.get('tool') for x in calls],tool_result_statuses=[x.get('status') for x in outputs],model_steps=len(steps),generated_tokens=sum(tokens) if tokens and all(isinstance(t,int) for t in tokens) else None,initial_input_tokens=steps[0].get('usage',{}).get('inputTokens') if steps else None,usage_per_step=[x.get('usage') for x in steps],final_marker_correct=final.strip()==marker,tool_call_result_ids_match=len(calls)==len(outputs)==1 and calls[0].get('callId')==outputs[0].get('callId'))
 return result.get('exit_code')==0 and len(calls)==1 and calls[0].get('tool')=='read' and len(outputs)==1 and result['tool_call_result_ids_match'] and outputs[0].get('status')=='completed' and marker in str(outputs[0].get('result')) and final.strip()==marker and len(steps)==2
