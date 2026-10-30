"""CPU-only native Responses routing and typed SSE/error regressions."""
import http.client
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'hardware'), str(ROOT/'dsh')]
import test_router_admission as fixture


def event(kind, **values):
    return ('event: '+kind+'\ndata: '+json.dumps({'type':kind, **values})+'\n\n').encode()


class ResponsesTransportTests(unittest.TestCase):
    def relay(self, data, split=1):
        out=[]
        fixture.tr.relay_sse(fixture.Response([data[i:i+split] for i in range(0,len(data),split)]),out.append,('TOPSECRET',),responses=True)
        return b''.join(out)

    def test_native_text_and_tool_events_preserved_at_every_boundary(self):
        data=(b': loading\n\n'+event('response.created',response={'id':'resp_1','status':'in_progress'})+
              event('response.output_item.added',output_index=0,item={'type':'function_call','call_id':'call_1'})+
              event('response.function_call_arguments.delta',item_id='fc_1',delta='{"x":1}')+
              event('response.output_text.delta',item_id='msg_1',delta='Hello')+
              event('response.completed',response={'id':'resp_1','status':'completed','output':[]}))
        for split in range(1,len(data)+1):
            self.assertEqual(self.relay(data,split),data)

    def test_incomplete_finishes_without_being_relabelled_completed(self):
        data=event('response.incomplete',response={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'}})
        self.assertEqual(self.relay(data),data)

    def test_failed_envelope_redacts_error_without_inventing_done(self):
        out=self.relay(event('response.failed',response={'status':'failed','error':{'code':'limit','message':'TOPSECRET /home/person/file'}}))
        self.assertIn(b'response.failed',out);self.assertIn(b'limit',out)
        self.assertNotIn(b'TOPSECRET',out);self.assertNotIn(b'/home/',out);self.assertNotIn(b'[DONE]',out)

    def test_protocol_error_is_typed_and_redacted(self):
        out=self.relay(b'event: error\ndata: {"message":"TOPSECRET","code":"limit","status":429}\n\n')
        self.assertIn(b'event: error',out);self.assertIn(b'"type": "error"',out);self.assertIn(b'429',out)
        self.assertNotIn(b'TOPSECRET',out);self.assertNotIn(b'[DONE]',out)

    def test_eof_or_chat_done_without_responses_terminal_fails(self):
        for data in [event('response.created',response={'status':'in_progress'}), b'data: [DONE]\n\n']:
            with self.assertRaises(http.client.HTTPException):self.relay(data)

    def test_chat_stream_still_requires_its_own_done(self):
        with self.assertRaises(http.client.HTTPException):
            fixture.tr.relay_sse(fixture.Response([event('response.completed',response={'status':'completed'})]),lambda _:None)


class ResponsesHttpTests(unittest.TestCase):
    setUp=fixture.HttpTests.setUp
    server=fixture.HttpTests.server
    request=fixture.HttpTests.request

    def test_native_nonstream_request_and_response_pass_through_both_hops(self):
        outer=self;original=self.backend.RequestHandlerClass
        class Backend(original):
            def do_POST(inner):
                outer.backend_path=inner.path
                super().do_POST()
        self.backend.RequestHandlerClass=Backend
        self.payload=json.dumps({'object':'response','id':'resp_1','status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Hi'}]}]}).encode()
        data={'model':'sage-a1.5','input':[{'role':'user','content':'Hi'}],'instructions':'Be brief','previous_response_id':'resp_previous','store':False,'max_output_tokens':32}
        status,headers,body=self.request(path='/v1/responses',data=data)
        self.assertEqual(status,200);self.assertEqual(body,self.payload)
        self.assertEqual(self.backend_path,'/v1/responses');self.assertEqual(json.loads(self.body),data)
        self.assertNotIn('Authorization',self.headers)

    def test_native_stream_terminal_passes_twice_without_extra_error(self):
        self.backend_type='text/event-stream'
        self.payload=(event('response.created',response={'status':'in_progress'})+
                      event('response.output_text.delta',delta='Hi')+
                      event('response.completed',response={'status':'completed','output':[]}))
        status,headers,body=self.request(path='/v1/responses',data={'model':'sage-a1.5','input':'Hi','stream':True})
        self.assertEqual(status,200);self.assertEqual(body,self.payload);self.assertNotIn(b'[DONE]',body)

    def test_responses_require_authentication_and_enabled_model(self):
        self.assertEqual(self.request(path='/v1/responses',auth=False)[0],401)
        self.assertEqual(self.request(path='/v1/responses',data={'model':'not-enabled','input':'Hi'})[0],404)

    def test_reservation_failure_uses_typed_error_and_never_launches(self):
        with patch.object(fixture.mh.hub,'serving',return_value=False),patch.object(fixture.mh.hub,'launch') as launch:
            status,_,body=self.request(path='/v1/responses',data={'model':'sage-a1.5','input':'Hi','stream':True})
            self.assertEqual(status,200);self.assertIn(b'gpu_reserved',body);self.assertIn(b'"type": "error"',body)
            self.assertNotIn(b'[DONE]',body);launch.assert_not_called()

    def test_backend_http_error_keeps_status_and_redacts_body(self):
        self.backend_status=422;self.payload=b'{"error":{"message":"/home/person/model Bearer fixture-external-secret","code":"bad_input"}}'
        status,_,body=self.request(path='/v1/responses',data={'model':'sage-a1.5','input':'Hi'})
        self.assertEqual(status,422);self.assertIn(b'bad_input',body);self.assertNotIn(b'/home/',body)
        self.assertNotIn(b'fixture-external-secret',body)

    def test_truncated_native_stream_surfaces_typed_failure(self):
        self.backend_type='text/event-stream';self.payload=event('response.created',response={'status':'in_progress'})
        _,_,body=self.request(path='/v1/responses',data={'model':'sage-a1.5','input':'Hi','stream':True})
        self.assertIn(b'backend_unavailable',body);self.assertIn(b'"type": "error"',body);self.assertNotIn(b'[DONE]',body)

    def test_maya_responses_uses_same_guarded_native_route(self):
        self.payload=b'{"id":"resp_maya","object":"response","output":[]}'
        with patch.dict(fixture.mh.BACKENDS,{'maya':('maya-profiles.json',self.backend.server_port,'Maya')}):
            status,_,body=self.request(path='/v1/responses',data={'model':'glm-5.3-flash-maya','input':'Hi'})
        self.assertEqual(status,200);self.assertEqual(body,self.payload)


if __name__=='__main__':unittest.main()
