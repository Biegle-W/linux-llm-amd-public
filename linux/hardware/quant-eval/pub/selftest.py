#!/usr/bin/env python3
"""Offline design/red-team regression tests. No model requests, downloaded-code execution or host candidate execution."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import grade_pub as g
import analyze as a

ROOT=Path.cwd()
def response(text='',**kw):return dict(content=text,finish='stop',**kw)
def item(kind,answer=None,**kw):
    spec=dict(kind=kind,**kw)
    if answer is not None:spec['answer']=answer
    return dict(id='case',category=kind,tier='core',pool_key='test',stratum='all',grader=spec)

class ExtractionTests(unittest.TestCase):
    def test_mcq_precedence(self):
        for text in ('ANSWER: B', 'Final answer: (b)', 'ANSWER: A\nANSWER: B',r'\boxed{A} then \boxed{B}', 'b','Answer (B)'):
            self.assertEqual(g.extract_mcq(text,4),'B',text)
        self.assertIsNone(g.extract_mcq(r'ANSWER: A then \boxed{B}',4))
        self.assertIsNone(g.extract_mcq('ANSWER: B\nANSWER: Z',4))
        self.assertIsNone(g.extract_mcq(r'\boxed{B} ANSWER: malformed',4))
        for text in ('option b','The answer could be A or B','because bad cab','A B'):
            self.assertIsNone(g.extract_mcq(text,4),text)

    def test_math_redteam_formats(self):
        for text,gold in [('047','47'),('1,234','1234'),('0.5','1/2'),('4.7e1','47'),
            (r'ANSWER: \frac{2}{4}','1/2'),(r'ANSWER: $\dfrac{2}{4}$','1/2'),
            (r'\boxed{-\tfrac{2}{4}}','-1/2'),('ANSWER: 47th day.','47'),
            ('ANSWER: 47 days','47'),(r'ANSWER: \(\frac{1}{2}\)','1/2')]:
            self.assertEqual(g.extract_number(text),g.normalize_number(gold),text)
        for text in ('working 47','47th day','ANSWER: 47 arbitrary prose','ANSWER: 12,34','ANSWER: 1,234,56',
                     'ANSWER: 47\nANSWER: banana','ANSWER: 47 + 0',r'ANSWER: \frac{1}{0}'):
            self.assertIsNone(g.extract_number(text),text)
        self.assertEqual(g.extract_number(r'ANSWER: 47 then \boxed{48}'),None)
        self.assertEqual(g.extract_number(r'\boxed{48} ANSWER: 47'),47)

    def test_no_math_expression_or_approximate_gold(self):
        for text in ('sqrt(4)','1+1','0.5','2 meters','1,234'):
            with self.assertRaises(ValueError):g.normalize_number(text,gold=True)
        with self.assertRaises(ZeroDivisionError):g.normalize_number('1/0')

    def test_thought_tags(self):
        for text in ('<think>ANSWER: A</think>ANSWER: B','draft ANSWER: A</think>ANSWER: B'):
            self.assertEqual(g.extract_mcq(g.clean_text(text),4),'B')
        self.assertEqual(g.clean_text('<think>ANSWER: B'),'')
        data=item('mcq','B',choices=4)
        self.assertFalse(g.grade_item(data,dict(content='',reasoning='ANSWER: B',finish='stop'))['correct'])
        self.assertTrue(g.grade_item(data,response('draft</think>ANSWER: B'))['correct'])
        self.assertEqual(g.grade_item(data,response('ANSWER: B'))['extraction_path'],'explicit')

class ScoringTests(unittest.TestCase):
    def test_caps_errors_pending(self):
        data=item('numeric','47')
        capped=g.grade_item(data,dict(content='ANSWER: 47',finish='length'))
        self.assertFalse(capped['correct']);self.assertEqual(capped['status'],'capped');self.assertTrue(capped['visible_correct'])
        self.assertEqual(g.grade_item(data,None)['status'],'pending')
        self.assertEqual(g.grade_item(data,{'error':'HTTP 500'})['status'],'error')
        self.assertEqual(g.grade_item(data,dict(content='47',finish='weird'))['status'],'error')
        self.assertEqual(g.grade_item(data,response(''))['status'],'empty')
        self.assertEqual(g.grade_item(data,response('I cannot answer'))['status'],'refusal')
        self.assertEqual(g.grade_item(data,response('working: 47'))['status'],'malformed')
        self.assertEqual(g.grade_item(item('unknown'),None)['status'],'grader_error')
        self.assertEqual(g.grade_item(item('numeric','1/0'),{'error':'HTTP 500'})['status'],'grader_error')

    def test_bfcl_nested_turn_builder(self):
        import build_items as builder
        spec=next(s for s in builder.CONFIG['sources'] if s['key']=='tools_parallel_multiple')
        row={'id':'test','question':[[{'role':'user','content':'Find multiples'}]],
             'function':[{'name':'math.multiples','description':'desc','parameters':{'type':'dict','properties':{'multiples':{'type':'list','items':{'type':'int'}}},'required':['multiples']}}],
             '_gold':[{'math.multiples':{'multiples':[[3,5]]}}]}
        built=builder.make_item(spec,row,0,'testrevision','core')
        self.assertEqual(built['body']['messages'],row['question'][0])
        self.assertEqual(built['body']['tools'][0]['function']['name'],'math_multiples')
        self.assertEqual(built['gold'],[{'math_multiples':{'multiples':[[3,5]]}}])
        row['question']*=2
        with self.assertRaises(ValueError):builder.validate_tools(row)

    def test_tools_nested_and_nongreedy(self):
        def call(name,args):return {'function':{'name':name,'arguments':json.dumps(args)}}
        gold=[{'f':{'x':[1,2]}},{'f':{'x':[1]}}]
        self.assertTrue(g.tool_match([call('f',{'x':1}),call('f',{'x':2})],gold))
        gold=[{'f':{'multiples':[[3,5]],'nested':[{'a':[1,True]}]}}]
        good=[call('f',{'multiples':[3,5],'nested':{'a':[1,True]}})]
        self.assertTrue(g.tool_match(good,gold))
        bad=[call('f',{'multiples':[3,5],'nested':{'a':[True,1]}})]
        self.assertFalse(g.tool_match(bad,gold))
        self.assertFalse(g.tool_match(good+good,gold));self.assertFalse(g.tool_match([],gold))
        self.assertFalse(g.tool_match([call('f',{'multiples':[3,'5'],'nested':{'a':[1,True]}})],gold))
        self.assertFalse(g.tool_match([call('f',{'multiples':[3,5],'nested':{'a':[1,True]},'extra':1})],gold))

    def test_tools_omission_and_irrelevance(self):
        c=lambda args:[{'function':{'name':'f','arguments':args}}]
        self.assertTrue(g.tool_match(c('{}'),[{'f':{'x':['',2]}}]))
        self.assertFalse(g.tool_match(c('{}'),[{'f':{'x':[2]}}]))
        data=item('tools',ground_truth=[])
        self.assertTrue(g.grade_item(data,response('No tools are relevant'))['correct'])
        self.assertFalse(g.grade_item(data,response(''))['correct'])
        self.assertFalse(g.grade_item(data,{'error':'timeout'})['correct'])
        data=item('tools',ground_truth=[{'f':{'x':[2]}}])
        self.assertFalse(g.grade_item(data,response('f(x=2)'))['correct'])
        self.assertFalse(g.tool_match(c('[]'),[{'f':{}}]))
        self.assertFalse(g.tool_match(c('{bad'),[{'f':{}}]))

    def test_ifeval_official_semantics(self):
        checks=[('keywords:frequency',{'keyword':'cat','frequency':2,'relation':'at least'},'cat concatenate',True),
          ('keywords:forbidden_words',{'forbidden_words':['cat']},'concatenate',True),
          ('keywords:existence',{'keywords':['c.t']},'cat',True),
          ('detectable_format:number_bullet_lists',{'num_bullets':2},'-one\n*two',True),
          ('detectable_format:number_highlighted_sections',{'num_highlights':2},'**one**',False),
          ('detectable_format:number_highlighted_sections',{'num_highlights':1},'**one**',True),
          ('startend:end_checker',{'end_phrase':'Done'},'"text DONE"',True),
          ('startend:quotation',{},'  "hello"  ',True),
          ('detectable_format:title',{},'<<  >>',False),
          ('detectable_format:json_format',{},'```JSON\n{"a":1}\n```',True)]
        for name,kwargs,text,expected in checks:
            with self.subTest(name=name):self.assertEqual(g.ifeval_check(text,[name],[kwargs])[0],expected)
        raw=item('ifeval',instruction_id_list=['punctuation:no_comma'],kwargs=[{}])
        self.assertFalse(g.grade_item(raw,response('<think>draft,</think>answer'))['correct'])
        for unsupported in ('change_case:english_capital','change_case:english_lowercase'):
            self.assertEqual(g.grade_item(item('ifeval',instruction_id_list=[unsupported],kwargs=[{}]),response('hello'))['status'],'grader_error')

class CodeTests(unittest.TestCase):
    def test_child_preamble_stdlib_imports_and_denials(self):
        # Run only trusted imports, monkeypatches and the audit hook. Omit payload
        # input, /work setup, resource limits and all candidate/reference execution.
        imports, setup = g.CHILD.split('p=json.loads', 1)
        preamble = 'def deny' + setup.split('def deny', 1)[1].split("ns={", 1)[0]
        probe = r'''
import ssl, asyncio, unittest.mock, http.client, subprocess
with unittest.mock.patch('os.listdir', return_value=['mocked']):
    assert os.listdir('.') == ['mocked']
for operation, event in (
    (lambda: socket.socket(), 'socket.__new__'),
    (lambda: subprocess.run([sys.executable, '-I', '-c', 'pass']), 'subprocess.Popen'),
):
    try:
        operation()
    except PermissionError as exc:
        assert str(exc) == 'sandbox denied ' + event, str(exc)
    else:
        raise AssertionError('operation was not denied: ' + event)
print('imports_and_denials_ok')
'''
        result = subprocess.run([sys.executable, '-I', '-Werror', '-c', imports+preamble+probe],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(result.stdout.strip(), 'imports_and_denials_ok')

    def test_reference_three_runs_and_flaky_rejection(self):
        with patch.object(g,'run_code',side_effect=[(True,'ok')]*3) as run:
            ok,detail=g.validate_reference('trusted reference',{})
            self.assertTrue(ok);self.assertEqual(run.call_count,3);self.assertEqual(len(detail['runs']),3)
        with patch.object(g,'run_code',side_effect=[(True,'ok'),(False,'failed'),(True,'ok')]):
            self.assertFalse(g.validate_reference('trusted reference',{})[0])
        with patch.object(g,'run_code',return_value=(None,'isolation_unavailable')):
            self.assertIsNone(g.validate_reference('trusted reference',{})[0])

    def test_extract_complete_and_unmodified(self):
        code='def f(a,b,c):\n return a<b and c>a'
        self.assertEqual(g.extract_code('```python\n'+code+'\n```'),code)
        self.assertEqual(g.extract_code(code),code)
        with self.assertRaises(ValueError):g.extract_code('```python\nx=1\n```\n```python\nx=2\n```')

    def test_isolation_failure_refuses_before_execution(self):
        spec={'mode':'assertions','tests':'assert True'}
        with patch.object(g,'isolation_config',return_value=(None,'isolation_unavailable:test')),patch.object(g.subprocess,'Popen') as spawn:
            result=g.run_code('raise RuntimeError("MUST NOT RUN")',spec)
            self.assertIsNone(result[0]);spawn.assert_not_called()
            graded=g.grade_item(item('code',**spec),response('pass'))
            self.assertEqual(graded['status'],'ungraded');self.assertFalse(graded['correct'])

    def test_fail_closed_launch_failure(self):
        config=('bwrap','/fake/bwrap','mock isolation evidence')
        with patch.object(g,'isolation_config',return_value=(config,'')),patch.object(g.subprocess,'Popen',side_effect=OSError('cannot launch')):
            self.assertIsNone(g.run_code('pass',{'mode':'assertions','tests':'assert True'},temp_root=ROOT)[0])

    def test_no_code_cleaning_or_capped_execution(self):
        data=item('code',mode='assertions',tests='assert True')
        code='def f():\n return "<think>literal</think>"'
        with patch.object(g,'run_code',return_value=(True,'mock_execution')) as run:
            self.assertTrue(g.grade_item(data,response('```python\n'+code+'\n```'))['correct'])
            self.assertEqual(run.call_args.args[0],code)
            run.reset_mock()
            self.assertEqual(g.grade_item(data,dict(content=code,finish='length'))['status'],'capped');run.assert_not_called()

class BwrapBackendTests(unittest.TestCase):
    """All subprocesses mocked: candidate code is never executed in these tests."""
    SPEC={'mode':'assertions','tests':'assert True'}

    def setUp(self):
        self.cache=patch.object(g,'_VERIFIED',{});self.cache.start();self.addCleanup(self.cache.stop)

    def test_pure_command_exact_chair_layout(self):
        self.assertEqual(g.bwrap_command('/usr/bin/bwrap','/fresh/job','/work/probe.py','/host/home'),[
            '/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session',
            '--ro-bind','/usr','/usr','--symlink','usr/lib','/lib',
            '--symlink','usr/lib64','/lib64','--symlink','usr/bin','/bin',
            '--proc','/proc','--dev','/dev','--tmpfs','/tmp',
            '--bind','/fresh/job','/work','--chdir','/work',
            '/usr/bin/python3','-I','/work/probe.py','/host/home'])
        self.assertEqual(set(g.SANDBOX_ENV),{'PATH','LANG'})
        compile(g.CHILD,'child.py','exec');compile(g.PROBE,'probe.py','exec')
        self.assertIn("_nonce=p.pop('nonce')",g.CHILD)

    def test_nonlinux_and_missing_bwrap_never_spawn(self):
        with patch.object(g.sys,'platform','darwin'),patch.object(g.shutil,'which',return_value='/fake/bwrap'),patch.object(g.subprocess,'run') as run,patch.object(g.subprocess,'Popen') as spawn:
            self.assertIsNone(g.run_code('raise SystemExit("MUST NOT RUN")',self.SPEC,ROOT)[0])
            run.assert_not_called();spawn.assert_not_called()
        with patch.object(g.sys,'platform','linux'),patch.object(g.shutil,'which',return_value=None),patch.object(g.subprocess,'run') as run:
            self.assertIn('bwrap not found',g.isolation_config(ROOT)[1]);run.assert_not_called()

    def evidence(self):
        return {'net':'unreachable','net_errors':[101,101],'host_home_visible':False,'home_env':None,'root':sorted(g.ALLOWED_ROOT)}

    def test_probe_accepts_complete_evidence_and_caches(self):
        out=g.subprocess.CompletedProcess([],0,('PUB_PROBE:'+json.dumps(self.evidence())+'\n').encode(),b'')
        with patch.object(g.subprocess,'run',return_value=out) as run:
            self.assertTrue(g.verify_isolation('/fake/bwrap',ROOT)[0])
            self.assertTrue(g.verify_isolation('/fake/bwrap',ROOT)[0]);self.assertEqual(run.call_count,1)
            self.assertEqual(run.call_args.kwargs['env'],g.SANDBOX_ENV)

    def test_probe_failures_and_incomplete_evidence_fail_closed(self):
        changes=[{'net':'REACHABLE'},{'net_errors':[111,111]}, {'host_home_visible':True},
                 {'home_env':'/home'}, {'root':sorted(g.ALLOWED_ROOT)+['home']}, {'root':None}]
        for i,change in enumerate(changes):
            r=self.evidence();r.update(change)
            out=g.subprocess.CompletedProcess([],0,('PUB_PROBE:'+json.dumps(r)).encode(),b'')
            with patch.object(g.subprocess,'run',return_value=out):
                self.assertFalse(g.verify_isolation('/fake/bwrap'+str(i),ROOT)[0],change)
        for i,data in enumerate((b'PUB_PROBE:{}',b'PUB_PROBE:[]',b'PUB_PROBE:bad',b'')):
            with patch.object(g.subprocess,'run',return_value=g.subprocess.CompletedProcess([],0,data,b'')):
                self.assertFalse(g.verify_isolation('/missing/'+str(i),ROOT)[0])
        with patch.object(g.subprocess,'run',side_effect=OSError('probe denied')):
            self.assertFalse(g.verify_isolation('/denied',ROOT)[0])

    def fake_spawn(self,mode='pass'):
        from unittest.mock import Mock
        def spawn(command,**kwargs):
            self.assertEqual(command,g.bwrap_command('/fake/bwrap',command[command.index('--bind')+1],'/work/child.py'))
            self.assertEqual(kwargs['env'],g.SANDBOX_ENV)
            proc=Mock(returncode=0,pid=123456789)
            def communicate(payload=None,timeout=None):
                if payload is None:return
                p=json.loads(payload)
                if mode=='timeout':raise g.subprocess.TimeoutExpired(command,timeout)
                if mode=='output_limit':kwargs['stdout'].write(b'x'*g.CONFIG['code_output_bytes']);return
                if mode=='launch':kwargs['stderr'].write(b'bwrap: namespace denied');proc.returncode=1;return
                if mode=='failure':kwargs['stderr'].write(b'AssertionError: test_failed');proc.returncode=1;return
                if mode=='no_tests':kwargs['stderr'].write(b'ValueError: no tests executed');proc.returncode=1;return
                tag='PUB_VERDICT:'+p['nonce']+':'
                if mode=='spoof':tag='PUB_VERDICT:wrong:'
                value={'passed':True,'tests_run':3}
                if mode=='bad_count':value['tests_run']=True
                if mode=='bad_json':value=[]
                line=(tag+json.dumps(value)+'\n').encode()
                kwargs['stdout'].write(line * (2 if mode=='duplicate' else 1))
            proc.communicate.side_effect=communicate
            return proc
        return patch.object(g.subprocess,'Popen',side_effect=spawn)

    def test_mocked_pass_and_failure_paths(self):
        with patch.object(g,'isolation_config',return_value=(('bwrap','/fake/bwrap','bwrap:mock'),'')):
            for mode,ok,detail in [('pass',True,'passed;tests_run=3;isolation=bwrap:mock'),
                    ('spoof',False,'missing_verdict'),('duplicate',False,'missing_verdict'),
                    ('bad_json',False,'missing_verdict'),('bad_count',False,'no_tests_executed'),
                    ('output_limit',False,'output_limit'),
                    ('failure',False,'runtime_or_test_failure:AssertionError: test_failed'),
                    ('launch',None,'isolation_unavailable:launch:bwrap: namespace denied')]:
                with self.subTest(mode=mode),self.fake_spawn(mode):
                    self.assertEqual(g.run_code('x=1',self.SPEC,ROOT),(ok,detail))
            with self.fake_spawn('no_tests'),self.assertRaises(g.GraderDefect):g.run_code('pass',self.SPEC,ROOT)
            with self.fake_spawn('timeout'),patch.object(g.os,'killpg') as kill:
                self.assertEqual(g.run_code('while True: pass',dict(self.SPEC,timeout=.1),ROOT),(False,'timeout'));kill.assert_called_once()
            with patch.object(g.subprocess,'Popen') as spawn:
                self.assertEqual(g.run_code('def (:',self.SPEC,ROOT),(False,'syntax_error'));spawn.assert_not_called()
                for timeout in (0,-1,11,float('nan'),True,'1'):
                    with self.assertRaises(g.GraderDefect):g.run_code('pass',dict(self.SPEC,timeout=timeout),ROOT)

class NumberWordsTests(unittest.TestCase):
    def test_pinned_regexp_tokenizer_semantics(self):
        self.assertIn('length_constraints:number_words',g.SUPPORTED_IFEVAL)
        cases={'Hello, world!':2,"don't stop":3,'well-known fact':3,'snake_case_word x':2,
               'naïve café über':3,'日本語 テキスト':2,'3.14 and 2,000':5,
               '**bold** <<title>> - item':3,'e-mail: a@b.com':5,'résumé—CV':2,
               '!!! … 😀':0,'one\ttwo\nthree\u00a0four':4,
               'e\u0301cole':2,'中文没有空格':1,'foo_bar １２３':2}
        for text,count in cases.items():
            for relation,n,expected in [('at least',count,True),('less than',count,False),('less than',count+1,True),('at least',count+1,False)]:
                with self.subTest(text=text,relation=relation,threshold=n):
                    self.assertEqual(g.ifeval_check(text,['length_constraints:number_words'],[{'num_words':n,'relation':relation}]),(expected,[expected]))
        with self.assertRaises(g.GraderDefect):g.ifeval_check('hi',['length_constraints:number_words'],[{'num_words':1,'relation':'equal'}])

    def test_raw_response_and_instruction_conjunction(self):
        data=item('ifeval',instruction_id_list=['length_constraints:number_words','punctuation:no_comma'],
                  kwargs=[{'num_words':2,'relation':'less than'},{}])
        self.assertTrue(g.grade_item(data,response('word'))['correct'])
        self.assertFalse(g.grade_item(data,response('two words'))['correct'])
        self.assertFalse(g.grade_item(data,response('word,'))['correct'])
        # IFEval strict grading must count the original text, including leaked tags.
        self.assertFalse(g.grade_item(data,response('<think>draft</think>word'))['correct'])
        # Nonempty punctuation has zero regex words; blank responses still fail overall.
        self.assertTrue(g.grade_item(data,response('!!!'))['correct'])
        self.assertEqual(g.ifeval_check('',data['grader']['instruction_id_list'],data['grader']['kwargs']),(False,[True,True]))

class LiveIsolatedCodeTests(unittest.TestCase):
    """Hand-written execution tests only, skipped fail-closed without verified Linux bwrap."""
    @classmethod
    def setUpClass(cls):
        config,reason=g.isolation_config(ROOT)
        if config is None:raise unittest.SkipTest('FAIL-CLOSED: no candidate/reference execution: '+reason)

    def run_case(self,code,tests='assert f()==42',**kw):
        return g.run_code(code,dict(mode='assertions',tests=tests,**kw),ROOT)

    def test_pass_and_wrong(self):
        self.assertTrue(self.run_case('def f(): return 42')[0])
        self.assertFalse(self.run_case('def f(): return 0')[0])

    def test_unittest_collection(self):
        spec={'mode':'unittest','tests':'import unittest\nclass Tests(unittest.TestCase):\n def test_f(self): self.assertEqual(f(),42)'}
        self.assertTrue(g.run_code('def f(): return 42',spec,ROOT)[0])
        with self.assertRaises(g.GraderDefect):g.run_code('pass',dict(mode='unittest',tests='pass'),ROOT)

    def test_timeout_and_fork(self):
        self.assertEqual(self.run_case('while True: pass',timeout=.5),(False,'timeout'))
        ok,detail=self.run_case('import os\nos.fork()');self.assertFalse(ok);self.assertIn('PermissionError',detail)

    def test_spoof_and_visible_home(self):
        ok,detail=self.run_case('import os\nprint(\'PUB_VERDICT:{"passed":true,"tests_run":1}\',flush=True)\nos._exit(0)')
        self.assertEqual((ok,detail),(False,'missing_verdict'))
        home=str(Path.home())
        self.assertTrue(self.run_case('import os\ndef f(): return 42',tests='assert not os.path.exists('+repr(home)+')\nassert "HOME" not in os.environ')[0])


class AnalysisTests(unittest.TestCase):
    def data(self):
        x=g.grade_item(item('mcq','B',choices=4),response('B'))
        y=g.grade_item(item('mcq','B',choices=4),response('A'))
        return {'tier':'core','items_sha256':'testmanifest','item_ids':['x','y'],'routes':{'z':{'x':copy.deepcopy(x),'y':copy.deepcopy(y)},'a':{'x':copy.deepcopy(y),'y':copy.deepcopy(x)}}}

    def test_known_statistics(self):
        self.assertAlmostEqual(a.exact_mcnemar(0,5),.0625);self.assertEqual(a.exact_mcnemar(0,0),1)
        self.assertEqual(a.holm([.01,.04,.03]),[.03,.06,.06]);self.assertAlmostEqual(a.holm([.01],family_size=66)[0],.66)
        lo,hi=a.wilson(108,216);self.assertAlmostEqual((hi-lo)/2,.066094,places=5)
        self.assertEqual(a.bootstrap_pair([1,1],[1,1],['math|aime','math|math500'],100,'seed'),[0,0])
        # Two separate source strata cannot trade their quota or be bootstrapped independently.
        self.assertEqual(a.bootstrap_pair([1,0],[0,1],['s1','s2'],100,'seed'),[0,0])

    def test_seed_route_order_invariant(self):
        data=self.data();one=a.analyze(data,100)
        data['routes']=dict(reversed(list(data['routes'].items())))
        self.assertEqual(one['pairs'],a.analyze(data,100)['pairs'])
        self.assertEqual(one['pairs'][0]['bootstrap_seed'],'20261110|bootstrap|a|z|core')
        self.assertFalse(one['primary_confirmatory'])

    def test_pending_incomplete_and_defects(self):
        data=self.data();data['routes']['a']['x'].update(status='pending',correct=False,flags=['pending'])
        result=a.analyze(data,100)
        self.assertFalse(result['complete']);self.assertIsNone(result['routes']['a']['score'])
        self.assertEqual(result['pairs'][0]['n'],1);self.assertEqual(result['paired_item_ids'],['y'])
        data['routes']['a']['x']['status']='grader_error'
        with self.assertRaises(ValueError):a.analyze(data,100)
        data=self.data();data['routes']['a']['x']['stratum']='different'
        with self.assertRaises(ValueError):a.analyze(data,100)

    def test_cli_e2e_and_deadline(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='selftest-') as work:
            root=Path(work);items=[item('mcq','B',choices=4),item('numeric','47')]
            for i,row in enumerate(items):row['id']=str(i)
            path=root/'items.jsonl';path.write_text('\n'.join(map(json.dumps,items))+'\n')
            (root/'a.json').write_text(json.dumps({'0':response('B'),'1':dict(content='ANSWER: 47',finish='length')}))
            (root/'b.json').write_text(json.dumps({'0':response('A'),'1':response('47')}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main([str(root),'a,b','--items',str(path)]),0)
                self.assertEqual(a.main([str(root),'--bootstrap-samples','100']),0)
            report=json.loads((root/'analysis.json').read_text());self.assertEqual(report['routes']['a']['score'],.5)
            self.assertIn('not resolved by this test',(root/'analysis.md').read_text())
            with contextlib.redirect_stdout(io.StringIO()):g.main([str(root),'a','--items',str(path),'--deadline-monotonic','0'])
            self.assertTrue(all(r['status']=='ungraded' for r in json.loads((root/'graded.json').read_text())['routes']['a'].values()))

if __name__=='__main__':unittest.main(verbosity=2)
