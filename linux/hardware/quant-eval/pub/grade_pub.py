#!/usr/bin/env python3
"""Frozen-design v1 offline grader; generated code requires verified Linux bubblewrap isolation."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from fractions import Fraction

VERSION = 'design-v1-bwrap-3'
CONFIG = {'default_items': str(Path(__file__).with_name('items.jsonl')), 'tier': 'core',
          'code_timeout': 10, 'code_cpu_seconds': 5, 'code_memory_mb': 512,
          'code_output_bytes': 1048576}
IFEVAL_REVISION = 'e6890f85757dd84e27ca6df2dd30651dafad28e0'
SUPPORTED_IFEVAL = frozenset(('punctuation:no_comma', 'keywords:existence',
    'keywords:forbidden_words', 'keywords:frequency', 'detectable_format:json_format',
    'startend:end_checker', 'startend:quotation', 'detectable_format:title',
    'detectable_format:number_bullet_lists', 'detectable_format:number_highlighted_sections',
    'length_constraints:number_words'))
# Frozen, intentionally small: applied only to explicit scalar answers.
NUMERIC_UNITS = ('day', 'days', 'hour', 'hours', 'minute', 'minutes', 'second', 'seconds',
                 'meter', 'meters', 'metre', 'metres', 'cm', 'm', 'km', 'dollar', 'dollars')

class GraderDefect(ValueError): pass


def clean_text(value, preserve_code=False):
    """Only MCQ/math use this; never alter code interiors or IFEval content."""
    if not isinstance(value, str): return ''
    text = re.sub(r'<think\b[^>]*>.*?</think\s*>', '', value, flags=re.I | re.S)
    # Orphan closing tag denotes a reasoning prefix, not a candidate final answer.
    if re.search(r'</think\s*>', text, re.I):
        text = re.split(r'</think\s*>', text, flags=re.I)[-1]
    text = re.sub(r'<think\b[^>]*>.*\Z', '', text, flags=re.I | re.S)
    return text.strip()


def boxed_values(text):
    out = []
    for m in re.finditer(r'\\(?:boxed|fbox)\s*\{', text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text[i] == '{': depth += 1
            if text[i] == '}': depth -= 1
            i += 1
        if not depth: out.append((m.start(), text[m.end():i-1]))
    return out


def explicit_payload(text):
    markers = list(re.finditer(r'\b(?:final\s+answer|answer)\s*:\s*', text, re.I))
    if not markers: return None
    return text[markers[-1].end():].strip()


def extract_mcq(text, choices=10, audit=False):
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:choices] if isinstance(choices, int) else ''.join(choices).upper()
    value = explicit_payload(text); path = 'explicit'
    if value is not None:
        # Frozen red-team rule: explicit payload must be exactly one option letter.
        m = re.fullmatch(r'\(?([A-Za-z])\)?', value)
        pred = m.group(1).upper() if m and m.group(1).upper() in letters else None
    else:
        boxes = boxed_values(text)
        if boxes:
            value = boxes[-1][1].strip(); path = 'boxed'
        else:
            value = re.sub(r'^answer\s+', '', text.strip(), flags=re.I); path = 'bare'
        m = re.fullmatch(r'\(?([A-Za-z])\)?[.]?', value)
        pred = m.group(1).upper() if m and m.group(1).upper() in letters else None
    return (pred, path if pred is not None else path + '_malformed') if audit else pred


def normalize_number(value, gold=False):
    """Exact scalar parser. Gold accepts integers/rationals only; no expressions."""
    text = str(value).strip().replace('−', '-')
    for _ in range(3):
        if text.startswith('\\(') and text.endswith('\\)'): text = text[2:-2].strip()
        elif text.startswith('\\[') and text.endswith('\\]'): text = text[2:-2].strip()
        elif text.startswith('$$') and text.endswith('$$'): text = text[2:-2].strip()
        elif text.startswith('$') and text.endswith('$'): text = text[1:-1].strip()
        elif re.fullmatch(r'\\(?:boxed|fbox)\s*\{.*\}', text, re.S):
            boxes = boxed_values(text)
            if len(boxes) != 1: raise ValueError('ambiguous boxed scalar')
            text = boxes[0][1].strip()
        else: break
    text = re.sub(r'\s+', '', text)
    if len(text) > 256: raise ValueError('number too long')
    m = re.fullmatch(r'([+-]?)\\(?:frac|dfrac|tfrac)\{([+-]?\d+)\}\{([+-]?\d+)\}', text)
    if m: return (-1 if m[1] == '-' else 1) * Fraction(int(m[2]), int(m[3]))
    if ',' in text:
        if gold or not re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+', text): raise ValueError('invalid comma grouping')
        text = text.replace(',', '')
    if re.fullmatch(r'[+-]?\d+/[+-]?\d+', text):
        a, b = text.split('/'); return Fraction(int(a), int(b))
    pattern = r'[+-]?\d+' if gold else r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?'
    if not re.fullmatch(pattern, text): raise ValueError('not an exact scalar')
    return Fraction(text)


def extract_number(text, audit=False):
    payload = explicit_payload(text); explicit = payload is not None; path = 'explicit'
    if not explicit:
        boxes = boxed_values(text)
        if boxes: payload = boxes[-1][1]; path = 'boxed'
        else: payload = text.strip(); path = 'bare'
    if explicit:
        payload = payload.rstrip().rstrip('.!;').rstrip()
        payload = re.sub(r'\s+(?:' + '|'.join(NUMERIC_UNITS) + r')$', '', payload, flags=re.I)
        payload = re.sub(r'(?<=\d)(?:st|nd|rd|th)$', '', payload, flags=re.I)
        payload = payload.rstrip().rstrip('.!;').rstrip()
    try: pred = normalize_number(payload)
    except (ValueError, ZeroDivisionError): pred = None
    return (pred, path if pred is not None else path + '_malformed') if audit else pred


def ifeval_check(text, ids, kwargs):
    r"""Exact stdlib check_following semantics from pinned official revision.

    Only the two English case IDs are excluded (langdetect dependency).
    number_words uses the pinned upstream RegexpTokenizer(r"\w+") semantics.
    """
    if len(ids) != len(kwargs) or not ids: raise GraderDefect('IFEval kwargs/IDs mismatch')
    checks = []
    for name, k in zip(ids, kwargs):
        if name not in SUPPORTED_IFEVAL: raise GraderDefect('unsupported IFEval rule: ' + name)
        if name == 'punctuation:no_comma': ok = not re.search(r'\,', text)
        elif name == 'keywords:existence': ok = all(re.search(w, text, re.I) for w in k['keywords'])
        elif name == 'keywords:forbidden_words': ok = not any(re.search(r'\b'+w+r'\b', text, re.I) for w in k['forbidden_words'])
        elif name == 'keywords:frequency':
            n = len(re.findall(k['keyword'].strip(), text, re.I)); rel = k['relation']
            if rel not in ('less than', 'at least'): raise GraderDefect('invalid relation')
            ok = n < k['frequency'] if rel == 'less than' else n >= k['frequency']
        elif name == 'length_constraints:number_words':
            if k.get('relation') not in ('less than', 'at least') or type(k.get('num_words')) is not int:
                raise GraderDefect('invalid number_words kwargs')
            # Pinned instructions_util.count_words uses RegexpTokenizer(r'\w+').
            # Keep Unicode regex semantics; split(), ASCII, and normalization differ.
            n = len(re.findall(r'\w+', text))
            ok = n < k['num_words'] if k['relation'] == 'less than' else n >= k['num_words']
        elif name == 'detectable_format:json_format':
            value = text.strip().removeprefix('```json').removeprefix('```Json').removeprefix('```JSON').removeprefix('```').removesuffix('```').strip()
            try: json.loads(value); ok = True
            except ValueError: ok = False
        elif name == 'startend:end_checker': ok = text.strip().strip('"').lower().endswith(k['end_phrase'].strip().lower())
        elif name == 'startend:quotation':
            v = text.strip(); ok = len(v) > 1 and v[0] == '"' and v[-1] == '"'
        elif name == 'detectable_format:title': ok = any(v.lstrip('<').rstrip('>').strip() for v in re.findall(r'<<[^\n]+>>', text))
        elif name == 'detectable_format:number_bullet_lists':
            ok = len(re.findall(r'^\s*\*[^\*].*$', text, re.M)) + len(re.findall(r'^\s*-.*$', text, re.M)) == k['num_bullets']
        elif name == 'detectable_format:number_highlighted_sections':
            n = sum(bool(v.strip('*').strip()) for v in re.findall(r'\*[^\n\*]*\*', text))
            n += sum(bool(v.removeprefix('**').removesuffix('**').strip()) for v in re.findall(r'\*\*[^\n\*]*\*\*', text))
            ok = n >= k['num_highlights']
        checks.append(bool(ok))
    return bool(text.strip()) and all(checks), checks


def typed_equal(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, dict): return set(a) == set(b) and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(typed_equal(x,y) for x,y in zip(a,b))
    return a == b


def validate_gold_tools(expected):
    if not isinstance(expected, list): raise GraderDefect('BFCL gold must be a list')
    for e in expected:
        if not isinstance(e, dict) or len(e) != 1: raise GraderDefect('invalid BFCL gold call')
        params = next(iter(e.values()))
        if not isinstance(params, dict) or any(not isinstance(v, list) or not v for v in params.values()):
            raise GraderDefect('invalid BFCL parameter alternatives')


def tool_match(calls, expected):
    validate_gold_tools(expected)
    if calls is None: calls = []
    if not isinstance(calls, list): return False
    actual = []
    for c in calls:
        try:
            f = c['function']; args = f['arguments']
            if isinstance(args, str): args = json.loads(args, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
            if not isinstance(args, dict) or not isinstance(f['name'], str): return False
            actual.append((f['name'], args))
        except (KeyError, TypeError, ValueError): return False
    if len(actual) != len(expected): return False
    def matches(a, e):
        name, params = next(iter(e.items()))
        if a[0] != name or set(a[1]) - set(params): return False
        return all((key not in a[1] and any(type(v) is str and v == '' for v in allowed)) or
                   (key in a[1] and any(typed_equal(a[1][key], v) for v in allowed))
                   for key, allowed in params.items())
    def search(i, remaining):
        if i == len(actual): return True
        return any(matches(actual[i], expected[j]) and search(i+1, remaining - {j}) for j in sorted(remaining))
    return search(0, set(range(len(expected))))


def extract_code(text):
    blocks = re.findall(r'```([^\n]*)\n(.*?)```', text, re.S)
    if blocks:
        if len(blocks) != 1 or blocks[0][0].strip().lower() not in ('', 'python', 'py'):
            raise ValueError('ambiguous_or_non_python_fences')
        return blocks[0][1].strip()
    if '```' in text: raise ValueError('unbalanced_fence')
    return text.strip()

# Trusted bootstrap runs ONLY after the bubblewrap isolation probe succeeds.
# Python limits/audit hooks supplement, never substitute for, the namespace boundary.
CHILD = r'''
import sys, os, json, resource, socket, unittest, ast, trace
from pathlib import Path
p=json.loads(sys.stdin.read())
_nonce=p.pop('nonce')
os.chdir('/work')
resource.setrlimit(resource.RLIMIT_CPU,(5,5))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def deny(*a,**k): raise PermissionError('sandbox denied')
os.fork=deny
if hasattr(os,'forkpty'): os.forkpty=deny
# Keep socket.socket a class so ssl (and asyncio/unittest.mock) can import.
# The audit hook denies socket operations; bwrap also isolates the network.
def audit(event,args):
    if event.startswith(('socket.','subprocess.','os.exec','os.spawn','ctypes.')) or event in ('os.fork','os.forkpty','os.system','os.posix_spawn'):
        raise PermissionError('sandbox denied '+event)
sys.addaudithook(audit)
ns={'__name__':'__candidate__'}
exec(compile(p['code'],'candidate.py','exec'),ns)
if p['mode']=='unittest':
    exec(compile(p['tests'],'tests.py','exec'),ns)
    suite=unittest.TestSuite()
    for v in list(ns.values()):
        if isinstance(v,type) and issubclass(v,unittest.TestCase) and v is not unittest.TestCase:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(v))
    count=suite.countTestCases()
    if not count: raise ValueError('no tests collected')
    result=unittest.TextTestRunner().run(suite)
    count=result.testsRun-len(result.skipped)
    if not count: raise ValueError('no tests executed')
    if not result.wasSuccessful(): raise AssertionError('test_failed')
else:
    counter={'n':0}
    class CountAssertions(ast.NodeTransformer):
        def visit_Assert(self,node):
            return [ast.Expr(ast.Call(ast.Name('_count_assert',ast.Load()),[],[])),node]
    def increment(): counter['n']+=1
    ns['_count_assert']=increment
    tree=CountAssertions().visit(ast.parse(p['tests'])); ast.fix_missing_locations(tree)
    exec(compile(tree,'tests.py','exec'),ns)
    if p.get('entry_point') and 'check' in ns: ns['check'](ns[p['entry_point']])
    count=counter['n']
    if not count: raise ValueError('no tests executed')
print('\nPUB_VERDICT:'+_nonce+':'+json.dumps({'passed':True,'tests_run':count}),flush=True)
'''


ALLOWED_ROOT = {'usr', 'lib', 'lib64', 'bin', 'proc', 'dev', 'tmp', 'work'}
_VERIFIED = {}  # bwrap path -> (ok, reason); verified once per grader process

PROBE = r'''
import errno, json, os, socket, sys
host_home = sys.argv[1]
res = {'root': sorted(os.listdir('/')), 'home_env': os.environ.get('HOME'),
       'host_home_visible': bool(host_home) and os.path.exists(host_home), 'net': 'unreachable', 'net_errors': []}
for addr in (('1.1.1.1', 53), ('8.8.8.8', 53)):
    try:
        s = socket.create_connection(addr, timeout=2); s.close(); res['net'] = 'REACHABLE'; break
    except OSError as e:
        res['net_errors'].append(e.errno)
        if e.errno != errno.ENETUNREACH: res['net'] = 'UNVERIFIED'
print('PUB_PROBE:' + json.dumps(res), flush=True)
'''


def bwrap_command(bwrap, jobdir, script, *args):
    """Exact chair-verified command; jobdir is bound read-write at /work (fresh per item)."""
    return [bwrap, '--unshare-all', '--die-with-parent', '--new-session',
            '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib',
            '--symlink', 'usr/lib64', '/lib64', '--symlink', 'usr/bin', '/bin',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            '--bind', str(jobdir), '/work', '--chdir', '/work',
            '/usr/bin/python3', '-I', script, *args]


SANDBOX_ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}  # no HOME, no credentials, no tokens


def verify_isolation(bwrap, temp_root=None):
    """Run PROBE inside the sandbox. Returns (ok, reason). Never raises."""
    if bwrap in _VERIFIED:
        return _VERIFIED[bwrap]
    try:
        with tempfile.TemporaryDirectory(dir=temp_root, prefix='sandbox-probe-') as job:
            Path(job, 'probe.py').write_text(PROBE)
            out = subprocess.run(bwrap_command(bwrap, job, '/work/probe.py', str(Path.home())),
                                 capture_output=True, timeout=20, env=SANDBOX_ENV, stdin=subprocess.DEVNULL)
        line = [l for l in out.stdout.decode(errors='replace').splitlines() if l.startswith('PUB_PROBE:')]
        if out.returncode or len(line) != 1:
            result = (False, 'isolation_unverified:probe_failed:rc=%s:%s' % (out.returncode, out.stderr.decode(errors='replace')[-300:]))
        else:
            r = json.loads(line[-1][len('PUB_PROBE:'):])
            if not isinstance(r, dict): raise ValueError('probe evidence is not an object')
            problems = []
            if r.get('net') != 'unreachable' or r.get('net_errors') != [101, 101]: problems.append('network_reachable')
            if r.get('host_home_visible') is not False: problems.append('host_home_visible')
            if r.get('home_env', 'MISSING') is not None: problems.append('HOME_set')
            root = r.get('root')
            if not isinstance(root, list) or not all(isinstance(v, str) for v in root):
                raise ValueError('invalid probe root')
            if set(root) != ALLOWED_ROOT: problems.append('unexpected_root_layout')
            extra = set(root) - ALLOWED_ROOT
            if extra: problems.append('unexpected_root_entries:' + ','.join(sorted(extra)))
            result = (False, 'isolation_unverified:' + ';'.join(problems)) if problems else \
                     (True, 'bwrap:net=unreachable;home=absent;root=' + ','.join(r['root']))
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        result = (False, 'isolation_unavailable:probe_error:' + str(e))
    _VERIFIED[bwrap] = result
    return result


def isolation_config(temp_root=None):
    """(('bwrap', path, evidence), '') if verified, else (None, reason). macOS => None."""
    if sys.platform != 'linux':
        return None, 'isolation_unavailable: Linux bwrap required (code stays ungraded on '+sys.platform+')'
    bwrap = shutil.which('bwrap')
    if not bwrap:
        return None, 'isolation_unavailable: bwrap not found (expected on macOS; code stays ungraded)'
    ok, reason = verify_isolation(bwrap, temp_root)
    if not ok:
        return None, reason
    return ('bwrap', bwrap, reason), ''



def run_code(code, spec, temp_root=None):
    """Never executes without a verified bwrap sandbox. Unverifiable => (None, reason) => ungraded."""
    config, reason = isolation_config(temp_root)
    if config is None:
        return None, reason
    mode = spec.get('mode', 'unittest'); tests = spec.get('tests', spec.get('test'))
    if mode not in ('assertions', 'unittest') or not isinstance(tests, str) or not tests.strip():
        raise GraderDefect('invalid code test mode/source')
    try:
        compile(code, 'candidate.py', 'exec', dont_inherit=True)  # parse only; never executed here
    except (SyntaxError, ValueError):
        return False, 'syntax_error'
    _, bwrap, evidence = config
    nonce = secrets.token_hex(16)
    payload = json.dumps({'code': code, 'tests': tests, 'mode': mode, 'nonce': nonce,
                          'entry_point': spec.get('entry_point')}).encode()
    limit = CONFIG['code_output_bytes']
    timeout = spec.get('timeout', CONFIG['code_timeout'])
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 10:
        raise GraderDefect('code timeout must be a finite number in (0, 10]')
    try: ast.parse(tests)
    except SyntaxError as e: raise GraderDefect('invalid code test source') from e
    try:
        with tempfile.TemporaryDirectory(dir=temp_root, prefix='grade-job-') as job, \
             tempfile.TemporaryDirectory(dir=temp_root, prefix='grade-output-') as outdir:
            Path(job, 'child.py').write_text(CHILD)
            with open(Path(outdir, 'stdout'), 'wb') as out, open(Path(outdir, 'stderr'), 'wb') as err:
                p = subprocess.Popen(bwrap_command(bwrap, job, '/work/child.py'), stdin=subprocess.PIPE,
                                     stdout=out, stderr=err, env=SANDBOX_ENV, start_new_session=True,
                                     preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit)))
                try:
                    p.communicate(payload, timeout=timeout)
                except subprocess.TimeoutExpired:
                    try: os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    p.communicate(); return False, 'timeout'
            stdout = Path(outdir, 'stdout').read_bytes(); stderr = Path(outdir, 'stderr').read_bytes()
    except (OSError, subprocess.SubprocessError) as e:
        return None, 'isolation_unavailable:' + str(e)
    if len(stdout) + len(stderr) >= limit:
        return False, 'output_limit'
    if b'ValueError: no tests collected' in stderr or b'ValueError: no tests executed' in stderr:
        raise GraderDefect('supplied test source did not execute any tests')
    if p.returncode and (stderr.startswith(b'bwrap:') or b"can't open file '/work/child.py'" in stderr):
        return None, 'isolation_unavailable:launch:' + stderr.decode(errors='replace')[-500:]
    if p.returncode:
        return False, 'runtime_or_test_failure:' + stderr.decode(errors='replace')[-500:]
    tag = 'PUB_VERDICT:' + nonce + ':'
    lines = [l for l in stdout.decode(errors='replace').splitlines() if l.startswith(tag)]
    if len(lines) != 1:
        return False, 'missing_verdict'
    try: verdict = json.loads(lines[0][len(tag):])
    except ValueError: return False, 'missing_verdict'
    if not isinstance(verdict, dict): return False, 'missing_verdict'
    if verdict.get('passed') is not True or type(verdict.get('tests_run')) is not int or verdict['tests_run'] < 1:
        return False, 'no_tests_executed'
    return True, 'passed;tests_run=%d;isolation=%s' % (verdict['tests_run'], evidence)


def validate_reference(code, spec, temp_root=None):
    """Pre-freeze helper: three fresh runs; never treats missing isolation as exclusion."""
    records=[]
    for _ in range(3):
        started=time.monotonic()
        ok,detail=run_code(code,spec,temp_root)
        records.append({'passed':ok,'detail':detail,'seconds':time.monotonic()-started})
        if ok is None:return None,{'reason':'reference_isolation_unavailable','runs':records}
    eligible=all(r['passed'] is True and r['seconds']<8 for r in records)
    return eligible,{'reason':'reference_three_passes' if eligible else 'reference_failed_flaky_or_wall_borderline','runs':records}


def grading_spec(item):
    spec = item.get('grader', item.get('grading', {}))
    if isinstance(spec,str): spec={'kind':spec}
    spec=dict(spec)
    gold=item.get('gold')
    if isinstance(gold,dict):
        for k,v in gold.items(): spec.setdefault(k,v)
    elif gold is not None: spec.setdefault('answer',gold)
    for k in ('answer','tests','test','entry_point','ground_truth','instruction_id_list','kwargs','choices','mode'):
        if k not in spec and k in item: spec[k]=item[k]
    if 'choices' not in spec and 'choices' in item.get('meta',{}):
        v=item['meta']['choices'];spec['choices']=len(v) if isinstance(v,list) else v
    spec.setdefault('kind',item.get('answer_type'))
    if spec['kind']=='code':
        spec.setdefault('mode','unittest' if 'test' in spec else 'assertions')
        if 'test' in spec: spec.setdefault('tests',spec['test'])
    return spec


def validate_spec(spec):
    kind=spec.get('kind')
    if kind in ('mcq','choice'):
        choices=spec.get('choices',10)
        letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:choices] if isinstance(choices,int) else ''.join(choices)
        if str(spec.get('answer','')).upper() not in letters or len(str(spec.get('answer',''))) != 1:
            raise GraderDefect('invalid MCQ gold')
    elif kind in ('numeric','integer','number','rational'): normalize_number(spec['answer'],gold=True)
    elif kind in ('tools','bfcl'): validate_gold_tools(spec.get('ground_truth',spec.get('answer')))
    elif kind=='ifeval':
        if not set(spec['instruction_id_list']) <= SUPPORTED_IFEVAL: raise GraderDefect('unsupported IFEval IDs')
        if len(spec['instruction_id_list']) != len(spec['kwargs']): raise GraderDefect('IFEval metadata lengths')
    elif kind=='code':
        tests=spec.get('tests')
        if not isinstance(tests,str) or not tests.strip(): raise GraderDefect('empty code test source')
        try: ast.parse(tests)
        except SyntaxError as e: raise GraderDefect('invalid code tests') from e
    else: raise GraderDefect('unknown grader kind '+str(kind))


def grade_item(item,row,temp_root=None):
    meta=item.get('meta',{})
    pool=item.get('pool_key',meta.get('pool_key',meta.get('pool',item.get('pool',item.get('source','')))))
    stratum=item.get('stratum',meta.get('stratum',meta.get('domain','all')))
    base={'category':item.get('category',item.get('cat','unknown')),'tier':item.get('tier','core'),
          'source':item.get('source',''),'stratum':str(pool)+'|'+str(stratum),'correct':False,'status':'wrong','flags':[]}
    try: spec=grading_spec(item);validate_spec(spec)
    except (KeyError,TypeError,ValueError,ZeroDivisionError) as e: return dict(base,status='grader_error',detail=str(e))
    if row is None: return dict(base,status='pending',flags=['pending'])
    if not isinstance(row,dict): return dict(base,status='error',flags=['error'],detail='malformed_result')
    raw=row.get('content');raw='' if raw is None else raw
    calls=row.get('tool_calls');kind=spec['kind'];flags=[]
    if row.get('error'): flags.append('error')
    if row.get('finish')=='length': flags.append('capped')
    if not isinstance(raw,str): return dict(base,status='error',flags=flags+['error'],detail='non_string_content')
    if not raw.strip() and not calls: flags.append('empty')
    if row.get('refusal') or re.match(r'^\s*(?:I (?:cannot|can\'t|am unable)|Sorry[, ])',raw,re.I): flags.append('refusal')
    if 'error' in flags: return dict(base,status='error',flags=flags,detail=str(row['error']))
    if row.get('finish') not in ('stop','tool_calls','length'):
        return dict(base,status='error',flags=flags+['error'],detail='invalid_finish:'+str(row.get('finish')))
    if row.get('finish')=='tool_calls' and kind not in ('tools','bfcl'):
        return dict(base,status='error',flags=flags+['error'],detail='unexpected_tool_finish')
    if 'refusal' in flags and 'capped' not in flags: return dict(base,status='refusal',flags=flags)
    try:
        pred=None;detail='';path=None
        if kind in ('mcq','choice'):
            pred,path=extract_mcq(clean_text(raw),spec.get('choices',10),True);ok=pred==str(spec['answer']).upper()
        elif kind in ('numeric','integer','number','rational'):
            pred,path=extract_number(clean_text(raw),True);ok=pred is not None and pred==normalize_number(spec['answer'],gold=True)
            pred=str(pred) if pred is not None else None
        elif kind in ('tools','bfcl'):
            pred=calls;gold=spec.get('ground_truth',spec.get('answer'));ok=tool_match(calls,gold)
            if not gold: ok=ok and bool(raw.strip()) and row.get('finish')=='stop'
        elif kind=='ifeval': ok,detail=ifeval_check(raw,spec['instruction_id_list'],spec['kwargs'])
        else:
            # Never spend code-execution budget on capped candidates.
            if 'capped' in flags: return dict(base,status='capped',flags=flags)
            try: code=extract_code(raw)
            except ValueError as e: return dict(base,status='malformed',flags=flags+['malformed'],detail=str(e))
            ok,detail=run_code(code,spec,temp_root)
            if ok is None: return dict(base,status='ungraded',flags=flags+['ungraded'],detail=detail)
            if not ok: flags.append('test_failure')
        if path and path.endswith('_malformed'): flags.append('malformed')
        if 'capped' in flags:
            return dict(base,status='capped',flags=flags,prediction=pred,extraction_path=path,visible_correct=bool(ok),detail=detail)
        status='correct' if ok else 'empty' if 'empty' in flags else 'malformed' if 'malformed' in flags else 'wrong'
        return dict(base,status=status,flags=flags,correct=bool(ok),prediction=pred,extraction_path=path,detail=detail)
    except Exception as e:
        return dict(base,status='grader_error',flags=flags,detail=type(e).__name__+':'+str(e))


def load_items(path,tier='all'):
    rows=[];seen=set()
    for line in Path(path).read_text().splitlines():
        if not line.strip():continue
        item=json.loads(line);key=item.get('id',item.get('item_id'))
        if not isinstance(key,str) or not key or key in seen:raise ValueError('missing/duplicate item id:'+str(key))
        seen.add(key)
        if tier=='all' or item.get('tier','core')==tier:rows.append((key,item))
    if not rows:raise ValueError('no selected items')
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results_dir',type=Path);p.add_argument('routes')
    p.add_argument('--items',default=os.environ.get('PUB_ITEMS',CONFIG['default_items']))
    p.add_argument('--tier',choices=['core','extended','all'],default=os.environ.get('PUB_TIER','core'))
    p.add_argument('--temp-root',type=Path);p.add_argument('--deadline-monotonic',type=float,help='fleet deadline on this boot; no grading starts afterward')
    args=p.parse_args(argv);items=load_items(args.items,args.tier)
    fleet_path=args.results_dir/'fleet.json'
    if fleet_path.exists():
        fleet=json.loads(fleet_path.read_text())
        elapsed=max(0.,time.time()-float(fleet['fleet_start']),float(fleet.get('max_elapsed_seen',0)))
        fleet_deadline=time.monotonic()+max(0.,20*3600-elapsed)
        args.deadline_monotonic=min(args.deadline_monotonic,fleet_deadline) if args.deadline_monotonic is not None else fleet_deadline
    manifest_path=Path(args.items).with_suffix('.manifest.json')
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    items_sha=hashlib.sha256(Path(args.items).read_bytes()).hexdigest()
    if manifest is not None and (not manifest.get('frozen') or manifest.get('items_sha256')!=items_sha):
        raise GraderDefect('unfrozen or mismatching item manifest')
    temp=args.temp_root or args.results_dir/'.sandbox';temp.mkdir(parents=True,exist_ok=True)
    sandbox_config, sandbox_reason = isolation_config(str(temp.resolve()))
    if sandbox_config is None:
        print('WARNING: CODE EXECUTION DISABLED; code items remain UNGRADED: '+sandbox_reason, file=sys.stderr)
    else:
        print('Code isolation verified: '+sandbox_config[2], file=sys.stderr)
    result={'schema_version':2,'grader_version':VERSION,'tier':args.tier,
            'items_sha256':hashlib.sha256(Path(args.items).read_bytes()).hexdigest(),
            'item_ids':[k for k,_ in items],'routes':{},'manifest_verified':manifest is not None,'manifest':manifest,'route_metadata':{},
            'isolation_verified':sandbox_config is not None,'isolation_detail':sandbox_reason if sandbox_config is None else sandbox_config[2],
            'run_date_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'timeout_policy':{'wall_seconds':10,'cpu_seconds':5,'fleet_hours':20},
            'isolation_policy':'verified Linux bwrap: no network, no host home, read-only /usr; otherwise ungraded'}
    for route in args.routes.split(','):
        if not route or Path(route).name!=route:p.error('unsafe route name')
        path=args.results_dir/(route+'.json');raw=json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(raw,dict):raise ValueError('route JSON must be object')
        metadata=raw.get('_meta',{})
        if metadata.get('items_sha256') not in (None,items_sha):raise GraderDefect('route manifest mismatch:'+route)
        result['route_metadata'][route]=metadata
        records={}
        for key,item in items:
            expired=args.deadline_monotonic is not None and time.monotonic()>=args.deadline_monotonic
            if expired:
                record=grade_item(item,None,str(temp.resolve()));record.update(status='ungraded',flags=['ungraded'],detail='fleet_grading_deadline')
            else:
                # Reserve full 10 s execution plus cleanup before launching a code grader.
                spec=grading_spec(item)
                if spec.get('kind')=='code' and args.deadline_monotonic is not None and time.monotonic()+50>=args.deadline_monotonic:
                    record=grade_item(item,None);record.update(status='ungraded',flags=['ungraded'],detail='insufficient_grading_budget')
                else:record=grade_item(item,raw.get(key),str(temp.resolve()))
            row=raw.get(key)
            if isinstance(row,dict):record.update(seconds=row.get('seconds'),usage=row.get('usage'))
            records[key]=record
        result['routes'][route]=records
        print(route,json.dumps({s:sum(r['status']==s for r in records.values()) for s in sorted({r['status'] for r in records.values()})}))
        (args.results_dir/'graded.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(args.results_dir/'graded.json')
    return int(any(r['status']=='grader_error' for rows in result['routes'].values() for r in rows.values()))

if __name__=='__main__':raise SystemExit(main())
