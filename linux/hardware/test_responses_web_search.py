"""CPU/HTTP/SDK contracts for genuine local Responses search execution."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dsh'),str(ROOT/'hardware')]
import responses_web_search as w
import test_router_admission as fixture
try:
 from openai.types.responses import Response, ResponseCompletedEvent
except ImportError:
 Response=ResponseCompletedEvent=None
def validate_response(value, event=False):
 # Run with the existing vLLM venv for strict SDK schema checks; CPU routing
 # regressions also remain runnable without installing an SDK globally.
 cls=ResponseCompletedEvent if event else Response
 if cls is not None:
  return cls.model_validate_json(value) if isinstance(value,(str,bytes)) else cls.model_validate(value)

SOURCE={'url':'https://www.python.org/downloads/release/python-3140/','title':'Python release','snippet':'Python3.14.0 was released October7,2025.','date':'2025-10-07'}
def reply(output):
 return {'status':'completed','output':output,'usage':{'input_tokens':20,'output_tokens':20,'total_tokens':40}}
def call():
 return {'type':'function_call','name':w.FUNCTION,'arguments':'{"query":"Python3.14 official release date"}','call_id':'c1','id':'fc1','status':'completed'}
def answer():
 return {'id':'msg1','type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':'It was released October7,2025.[1]','annotations':[],'logprobs':[]}]}
def request(**values):
 return {'model':'sage-a1.5','input':'Search the official Python release date.','tools':[{'type':'web_search'}],'max_output_tokens':256,**values}

class Contracts(unittest.TestCase):
 def setUp(self):
  self.cache=patch.object(w,'HISTORY',w.History());self.cache.start();self.addCleanup(self.cache.stop)
 def test_real_search_loop_preserves_query_result_provenance_and_sdk_response(self):
  backend=Mock(side_effect=[reply([call()]),reply([answer()])]);provider=Mock(return_value=[SOURCE]);s=w.Session(request(),backend,provider)
  final,output=s.run();validate_response(final)
  provider.assert_called_once();self.assertEqual(provider.call_args.args[0],'Python3.14 official release date')
  payload=backend.call_args_list[-1].args[0];self.assertEqual(payload['input'][-1]['type'],'function_call_output')
  self.assertIn(SOURCE['url'],payload['input'][-1]['output']);self.assertNotIn('web_search',str(payload['tools'][0]['type']))
  self.assertEqual(final['output'][0]['type'],'web_search_call');self.assertEqual(final['usage']['output_tokens'],40)
  part=output[0]['content'][0];a=part['annotations'][0];self.assertEqual(part['text'][a['start_index']:a['end_index']],'[1]');self.assertEqual(a['url'],SOURCE['url'])
 def test_forced_web_choice_normalizes_to_sdk_compatible_required(self):
  s=w.Session(request(tool_choice={'type':'web_search'}),Mock(side_effect=[reply([call()]),reply([answer()])]),lambda *_:[SOURCE])
  final,_=s.run();self.assertEqual(final['tool_choice'],'required');validate_response(final)
 def test_stream_events_form_sdk_final_with_increasing_sequence_and_no_fake_done(self):
  events=[];s=w.Session(request(),Mock(side_effect=[reply([call()]),reply([answer()])]),lambda *_:[SOURCE],emit=lambda k,v:events.append((k,v)))
  s.start();final,output=s.run();s.finish(final,output)
  self.assertEqual([v['sequence_number'] for _,v in events],list(range(len(events))))
  self.assertIn('response.web_search_call.searching',[k for k,_ in events]);validate_response(events[-1][1],event=True)
  self.assertEqual(events[-1][1]['response']['id'],events[0][1]['response']['id'])
  self.assertEqual([v['delta'] for k,v in events if k=='response.output_text.delta'],[answer()['content'][0]['text']])
 def test_required_search_cannot_silently_turn_into_a_plain_answer(self):
  provider=Mock();s=w.Session(request(tool_choice='required'),lambda _:reply([answer()]),provider)
  with self.assertRaises(w.SearchError) as error:s.run()
  self.assertEqual(error.exception.code,'required_search_not_called');provider.assert_not_called()
 def test_auto_without_search_does_not_claim_a_search(self):
  provider=Mock();s=w.Session(request(),lambda _:reply([answer()]),provider);final,_=s.run();provider.assert_not_called()
  self.assertNotIn('web_search_call',[x['type'] for x in final['output']]);self.assertEqual(final['output'][0]['content'][0]['annotations'],[])
 def test_none_never_enables_search_and_keeps_native_tools_empty(self):
  backend=Mock(return_value=reply([answer()]));provider=Mock();w.Session(request(tool_choice='none'),backend,provider).run()
  self.assertEqual(backend.call_args.args[0]['tools'],[]);provider.assert_not_called()
 def test_previous_response_continues_ephemerally_without_inheriting_instructions(self):
  first=w.Session(request(instructions='Oldinstruction'),Mock(side_effect=[reply([call()]),reply([answer()])]),lambda *_:[SOURCE]);final,_=first.run()
  backend=Mock(return_value=reply([answer()]));s=w.Session(request(previous_response_id=final['id'],tools=[],instructions='Newinstruction',input='What source was that?'),backend);s.run()
  p=backend.call_args.args[0];self.assertIn('function_call_output',str(p['input']));self.assertNotIn('Oldinstruction',p['instructions']);self.assertIn('Newinstruction',p['instructions']);self.assertNotIn('previous_response_id',p)
 def test_store_false_does_not_retain_chain(self):
  s=w.Session(request(store=False),lambda _:reply([answer()]));final,_=s.run()
  with self.assertRaises(w.SearchError):w.HISTORY.get(final['id'])
 def test_native_previous_response_id_is_kept_upstream(self):
  b=Mock(return_value=reply([answer()]));w.Session(request(previous_response_id='resp_native'),b).run();self.assertEqual(b.call_args.args[0]['previous_response_id'],'resp_native')
 def test_cache_expiry_size_and_detached_values(self):
  clock=[0];h=w.History(limit=256,ttl=1,clock=lambda:clock[0]);self.assertTrue(h.put('a',{'v':'one'}));x=h.get('a');x['v']='changed';self.assertEqual(h.get('a')['v'],'one')
  self.assertFalse(h.put('big',{'v':'x'*500}));clock[0]=2
  with self.assertRaises(w.SearchError):h.get('a')
 def test_search_round_limit_does_not_make_extra_provider_calls(self):
  b=Mock(side_effect=[reply([call()]),reply([call()])]);p=Mock(return_value=[SOURCE]);s=w.Session(request(max_tool_calls=1),b,p)
  with self.assertRaises(w.SearchError):s.run()
  p.assert_called_once();self.assertEqual(b.call_args.args[0]['tool_choice'],'none')
 def test_unsupported_controls_fail_before_query(self):
  for tool in [{'type':'web_search','external_web_access':False},{'type':'web_search','search_content_types':['image']},{'type':'web_search','filters':{'allowed_domains':['https://bad/']}}]:
   with self.subTest(tool=tool),self.assertRaises(w.SearchError):w.Session(request(tools=[tool]),Mock(),Mock())
 def test_approximate_location_guides_only_the_local_query_planner(self):
  b=Mock(return_value=reply([answer()]));w.Session(request(tools=[{'type':'web_search','user_location':{'type':'approximate','city':'Toronto','country':'CA'}}]),b).run();self.assertIn('Toronto',b.call_args.args[0]['instructions'])
 def test_cancelled_client_never_starts_search(self):
  p=Mock();check=Mock(side_effect=ConnectionResetError());s=w.Session(request(),Mock(),p,check=check)
  with self.assertRaises(ConnectionResetError):s.run()
  p.assert_not_called()
 def test_disconnect_after_search_does_not_generate_a_followup(self):
  cancelled=[False]
  def search(*_):cancelled[0]=True;return [SOURCE]
  def check():
   if cancelled[0]:raise ConnectionResetError()
  backend=Mock(return_value=reply([call()]));session=w.Session(request(),backend,search,check=check)
  with self.assertRaises(ConnectionResetError):session.run()
  self.assertEqual(backend.call_count,1);self.assertEqual(w.HISTORY.size,0)
 def test_provider_sends_only_query_and_filters_unsafe_or_outside_urls(self):
  from unittest.mock import MagicMock
  response=MagicMock();response.__enter__.return_value=response
  response.read.return_value=json.dumps({'results':[SOURCE,{**SOURCE,'url':'http://127.0.0.1/private'},{**SOURCE,'url':'https://other.example/page'}]}).encode()
  opener=Mock();opener.open.return_value=response
  options=w.settings(request(tools=[{'type':'web_search','filters':{'allowed_domains':['python.org']}}]))
  with patch.dict(w.os.environ,{'DEEPSEEK_API_KEY':'fixture-provider-key'}),patch.object(w.urllib.request,'build_opener',return_value=opener):
   results=w.provider_search('Python release',options)
  self.assertEqual([x['url'] for x in results],[SOURCE['url']])
  sent=opener.open.call_args.args[0];self.assertEqual(sent.full_url,'https://api.deepseek.com/v1/tools/search')
  body=json.loads(sent.data);self.assertEqual(set(body),{'query','count','need_content'});self.assertIn('site:python.org',body['query']);self.assertNotIn('fixture-provider-key',str(body))
 def test_provider_error_is_not_relabelled_as_a_completed_search(self):
  s=w.Session(request(),lambda _:reply([call()]),Mock(side_effect=w.SearchError(503,'Providerfailed')))
  with self.assertRaises(w.SearchError):s.run()
  self.assertNotEqual(s.web[0]['status'],'completed')
 def test_public_url_rejects_local_and_credential_urls(self):
  for value in ['http://127.0.0.1/x','http://localhost/x','http://10.0.0.2/x','http://user:pass@example.com/','file:///tmp/a']:
   self.assertFalse(w.public_url(value),value)
  self.assertTrue(w.public_url(SOURCE['url']))

class HTTP(unittest.TestCase):
 setUp=fixture.HttpTests.setUp
 server=fixture.HttpTests.server
 request=fixture.HttpTests.request
 def prepare(self):
  owner=self;self.calls=[]
  class Backend(BaseHTTPRequestHandler):
   def log_message(*_):pass
   def do_POST(inner):
    d=json.loads(inner.rfile.read(int(inner.headers['Content-Length'])));owner.calls.append((d,dict(inner.headers)))
    native=reply([answer()]) if any(x.get('type')=='function_call_output' for x in d['input']) else reply([call()])
    body=json.dumps(native).encode();inner.send_response(200);inner.send_header('Content-Type','application/json');inner.send_header('Content-Length',str(len(body)));inner.end_headers();inner.wfile.write(body)
  self.backend.RequestHandlerClass=Backend
 def test_gateway_executes_and_returns_sdk_valid_search_response(self):
  self.prepare()
  with patch.object(w,'provider_search',return_value=[SOURCE]) as provider:
   status,_,body=self.request(path='/v1/responses',data=request())
  self.assertEqual(status,200);validate_response(body);provider.assert_called_once();self.assertEqual(len(self.calls),2)
  self.assertTrue(all('Authorization' not in headers for _,headers in self.calls));self.assertEqual(json.loads(body)['output'][0]['type'],'web_search_call')
 def test_stream_has_real_search_and_citation_events(self):
  self.prepare()
  with patch.object(w,'provider_search',return_value=[SOURCE]):status,_,body=self.request(path='/v1/responses',data=request(stream=True))
  self.assertEqual(status,200);self.assertIn(b'response.web_search_call.completed',body);self.assertIn(b'url_citation',body);self.assertNotIn(b'[DONE]',body)
  events=[json.loads(l[6:]) for l in body.decode().splitlines() if l.startswith('data: ')];validate_response(events[-1],event=True)
 def test_auth_and_held_model_validation_precede_search(self):
  with patch.object(w,'provider_search') as provider:
   self.assertEqual(self.request(path='/v1/responses',data=request(),auth=False)[0],401)
   self.assertEqual(self.request(path='/v1/responses',data=request(model='qwen3.8-flash-next-iq3_xxs'))[0],404)
  provider.assert_not_called()
 def test_gpu_reservation_rejection_never_runs_search(self):
  with patch.object(fixture.mh.hub,'serving',return_value=False),patch.object(w,'provider_search') as provider:
   status,_,body=self.request(path='/v1/responses',data=request())
  self.assertEqual(status,503);provider.assert_not_called();self.assertIn(b'local_response_error',body)
 def test_provider_failures_are_errors_with_no_false_completed(self):
  self.prepare()
  with patch.object(w,'provider_search',side_effect=w.SearchError(503,'Providerunavailable','web_search_provider_error')):
   status,_,body=self.request(path='/v1/responses',data=request(stream=True))
  self.assertEqual(status,200);self.assertIn(b'response.failed',body);self.assertNotIn(b'event: response.completed',body)

if __name__=='__main__':unittest.main()
