#!/usr/bin/env python3
"""Fetch public benchmark data and build a locked, reproducible local suite (stdlib)."""
import argparse
import ast
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from fractions import Fraction
import importlib.util
import grade_pub
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
# All design-dependent source choices, counts (core, additional extended), filters,
# prompts, and token budgets live here. Changing this table changes the suite hash.
CONFIG = {
    'seed': 20261110,
    'system': 'Solve the task carefully. Follow the requested final-answer format.',
    'mcq_prompt': '{question}\n\n{options}\n\nReturn your final answer as ANSWER: X, where X is the correct option letter.',
    'numeric_prompt': '{question}\n\nReturn your final answer as ANSWER: <number>, using an integer or an exact fraction.',
    'code_prompt': 'Implement the following Python task using only the standard library. Return the complete implementation in a single Python code block, with no tests.\n\n{question}',
    'version': 'design-v1-sha256-sampler-5',
    'code_candidate_multiplier': 2,
    # Chair exclusions after review: gold accepts item/quantity pairings that are wrong.
    'excluded': {'tools_parallel_multiple': ['parallel_multiple_165']},
    # English case rules require language detection and are not eligible.
    'sources': [
        dict(key='mmlu', repo='TIGER-Lab/MMLU-Pro', config='default', split='test', license='MIT', category='knowledge', grader='mcq', counts=[60,20], max_tokens=2048, domains={'physics':[10,4],'chemistry':[10,4],'engineering':[10,4],'computer science':[10,4],'law':[10,2],'economics':[10,2]}),
        dict(key='math', repo='HuggingFaceH4/MATH-500', config='default', split='test', raw='test.jsonl', license='MIT (upstream MATH); mirror license unset', category='math', grader='numeric', counts=[24,20], max_tokens=3072, levels=[4,5]),
        dict(key='aime24', repo='math-ai/aime24', config='default', split='test', license='Apache-2.0', category='math', grader='numeric', counts=[8,0], max_tokens=4096),
        dict(key='aime25', repo='math-ai/aime25', config='default', split='test', raw='test.jsonl', license='Apache-2.0', category='math', grader='numeric', counts=[8,0], max_tokens=4096),
        dict(key='code', repo='bigcode/bigcodebench', config='default', split='v0.1.4', license='Apache-2.0', category='code', grader='code', counts=[20,8], max_tokens=3072),
        dict(key='ifeval', repo='google/IFEval', config='default', split='train', raw='ifeval_input_data.jsonl', license='Apache-2.0', category='instruction', grader='ifeval', counts=[32,12], max_tokens=2048, rules=sorted(grade_pub.SUPPORTED_IFEVAL - {'change_case:english_capital', 'change_case:english_lowercase'})),
        dict(key='musr_object', repo='TAUR-Lab/MuSR', config='default', split='object_placements', license='CC-BY-4.0', category='reasoning', grader='mcq', counts=[16,6], max_tokens=2048),
        dict(key='musr_team', repo='TAUR-Lab/MuSR', config='default', split='team_allocation', license='CC-BY-4.0', category='reasoning', grader='mcq', counts=[16,6], max_tokens=2048),
        dict(key='tools_parallel_multiple', repo='ShishirPatil/gorilla', github=True, split='parallel_multiple', license='Apache-2.0', category='tools', grader='tool', counts=[16,4], max_tokens=2048),
        dict(key='tools_multiple', repo='ShishirPatil/gorilla', github=True, split='multiple', license='Apache-2.0', category='tools', grader='tool', counts=[8,4], max_tokens=2048),
        dict(key='tools_irrelevance', repo='ShishirPatil/gorilla', github=True, split='irrelevance', license='Apache-2.0', category='tools', grader='tool', counts=[8,4], max_tokens=2048),
    ],
}
MAX_DOWNLOAD = 49_000_000


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    """Retry only transient failures; never hide auth/schema/source drift failures."""
    for attempt in range(7):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'public-local-quality-harness/1.0'})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read(MAX_DOWNLOAD + 1)
            if len(data) > MAX_DOWNLOAD:
                raise RuntimeError(f'Download exceeds {MAX_DOWNLOAD} bytes: {url}')
            return data
        except urllib.error.HTTPError as exc:
            if exc.code != 429 and not 500 <= exc.code < 600:
                raise
            if attempt == 6:
                raise
            delay = min(60, 2 ** attempt)
            retry_after = exc.headers.get('Retry-After', '')
            if retry_after.isdigit():
                delay = max(delay, min(120, int(retry_after)))
            print(f'HTTP {exc.code}; retry in {delay}s: {url}', file=sys.stderr, flush=True)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 6:
                raise
            time.sleep(min(60, 2 ** attempt))


def revision(spec):
    if spec.get('github'):
        obj = json.loads(fetch('https://api.github.com/repos/' + spec['repo'] + '/commits/main'))
    else:
        obj = json.loads(fetch('https://huggingface.co/api/datasets/' + spec['repo']))
        if obj.get('gated'):
            raise RuntimeError(f'Gated source: {spec["repo"]}')
    return obj['sha']


def rows_url(spec, offset):
    return 'https://datasets-server.huggingface.co/rows?' + urllib.parse.urlencode(dict(
        dataset=spec['repo'], config=spec['config'], split=spec['split'], offset=offset, length=100))


def download_rows(spec, rev):
    if spec.get('raw'):
        url = f'https://huggingface.co/datasets/{spec["repo"]}/resolve/{rev}/{spec["raw"]}'
        return [json.loads(line) for line in fetch(url).splitlines() if line.strip()], [url]
    if spec.get('github'):
        root = f'https://raw.githubusercontent.com/{spec["repo"]}/{rev}/berkeley-function-call-leaderboard/bfcl_eval/data/'
        name = 'BFCL_v4_' + spec['split'] + '.json'
        data = [json.loads(line) for line in fetch(root + name).splitlines() if line.strip()]
        if spec['split'] == 'irrelevance':
            return data, [root + name]
        answers = [json.loads(line) for line in fetch(root + 'possible_answer/' + name).splitlines() if line.strip()]
        gold = {r['id']: r['ground_truth'] for r in answers}
        if len(gold) != len(answers) or set(gold) != {r['id'] for r in data}:
            raise RuntimeError('BFCL question/answer ID mismatch')
        for row in data:
            row['_gold'] = gold[row['id']]
        return data, [root + name, root + 'possible_answer/' + name]
    first = json.loads(fetch(rows_url(spec, 0)))
    total = first['num_rows_total']
    def unpack(page, offset):
        rows = page['rows']
        if len(rows) != min(100, total-offset):
            raise RuntimeError(f'Incomplete source page at {spec["key"]}:{offset}')
        if any(row['row_idx'] != offset+i or row.get('truncated_cells') for i,row in enumerate(rows)):
            raise RuntimeError(f'Truncated or reordered source page at {spec["key"]}:{offset}')
        return [row['row'] for row in rows]
    result = unpack(first, 0)
    offsets = list(range(100, total, 100))
    def page(offset):
        obj = json.loads(fetch(rows_url(spec, offset)))
        if obj['num_rows_total'] != total:
            raise RuntimeError('Source count changed during fetch')
        return unpack(obj, offset)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for block in pool.map(page, offsets):
            result.extend(block)
    return result, [rows_url(spec, offset) for offset in range(0,total,100)]


def numeric_answer(value):
    s = str(value).strip()
    for left, right in (('$$','$$'),('$','$'),('\\(','\\)'),('\\[','\\]')):
        if s.startswith(left) and s.endswith(right):
            s = s[len(left):-len(right)].strip()
            break
    if s.startswith('\\boxed{') and s.endswith('}'):
        s = s[7:-1].strip()
    s = re.sub(r'\s+', '', s).replace('\\dfrac','\\frac').replace('\\tfrac','\\frac')
    match = re.fullmatch(r'\\frac\{([+-]?\d+)\}\{([+-]?\d+)\}', s)
    if match:
        try:
            return str(Fraction(int(match[1]), int(match[2])))
        except ZeroDivisionError:
            return None
    if not re.fullmatch(r'[+-]?\d+(?:/[+-]?\d+)?', s):
        return None
    try:
        terms = s.split('/')
        return str(Fraction(int(terms[0]), int(terms[1]))) if len(terms)==2 else str(Fraction(int(s)))
    except (ValueError, ZeroDivisionError):
        return None


def list_field(value):
    return ast.literal_eval(value) if isinstance(value, str) else value


def code_static_reason(row):
    allowed = sys.stdlib_module_names | {'__future__'}
    libs = list_field(row['libs'])
    if any(lib.split('.')[0] not in allowed for lib in libs):
        return 'declared_nonstdlib_library'
    # Conservative exclusion before any execution; imports must be available here too.
    banned = {'socket','http','urllib','requests','subprocess','multiprocessing','pty','tkinter','turtle','webbrowser','ftplib','smtplib','telnetlib','ctypes'}
    for label, source in [('reference', reference_source(row)), ('tests', row['test'])]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return label + '_syntax_error'
        for node in ast.walk(tree):
            modules = [n.name for n in node.names] if isinstance(node, ast.Import) else ([node.module or ''] if isinstance(node, ast.ImportFrom) else [])
            for module in modules:
                root = module.split('.')[0]
                if root not in allowed or root in banned:
                    return label + '_unsafe_or_nonstdlib_import:' + module
                try:
                    if importlib.util.find_spec(root) is None:
                        return label + '_unavailable_import:' + root
                except (ValueError, ImportError):
                    return label + '_unavailable_import:' + root
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name in {'__import__','eval','exec','input','os.system','os.popen','os.fork','os.forkpty','os.posix_spawn'}:
                    return label + '_unsafe_call:' + name
    text = (row['instruct_prompt'] + '\n' + row['test']).lower()
    if re.search(r'https?://|ftp://|external file|internet|network connection|gui |interactive input', text):
        return 'external_service_or_interactive_task'
    return None


def reference_source(row):
    # Dataset canonical_solution is a completion of complete_prompt, not a standalone module.
    return row['complete_prompt'] + row['canonical_solution']


def eligible(spec, row):
    key = spec['key']
    if key == 'mmlu':
        return row['category'] in spec['domains']
    if key == 'math':
        level = int(str(row['level']).replace('Level ',''))
        return level in spec['levels'] and numeric_answer(row['answer']) is not None
    if key == 'code':
        return code_static_reason(row) is None
    if key == 'ifeval':
        return 2 <= len(row['instruction_id_list']) <= 3 and set(row['instruction_id_list']) <= (set(spec['rules']) & grade_pub.SUPPORTED_IFEVAL)
    if key.startswith('tools_'):
        try:
            validate_tools(row)
        except (ValueError, KeyError, TypeError):
            return False
    return True


def original_id(spec, row, index):
    for field in ('question_id','task_id','id','key','unique_id'):
        if field in row:
            return str(row[field])
    return str(index)


def tool_schema(value):
    if isinstance(value, list):
        return [tool_schema(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in {'properties', '$defs', 'definitions'} and isinstance(v, dict):
                out[k] = {name: tool_schema(schema) for name, schema in v.items()}
            elif k in {'enum', 'default', 'examples'}:
                out[k] = v  # literal values, never schema-convert parameter names or enums
            else:
                out[k] = tool_schema(v)
        if 'type' in out:
            mapping = {'dict':'object','float':'number','int':'integer','str':'string','bool':'boolean','tuple':'array','list':'array'}
            t = out['type']
            if not isinstance(t,str) or t not in set(mapping) | {'object','number','integer','string','boolean','array','null'}:
                raise ValueError('Unknown/ambiguous tool schema type: ' + repr(t))
            out['type'] = mapping.get(t,t)
        return out
    return value


def validate_tools(row):
    if not isinstance(row['question'], list) or len(row['question']) != 1 or not isinstance(row['question'][0],list):
        raise ValueError('BFCL requires exactly one outer turn')
    if not row['question'][0] or any(not isinstance(m,dict) or not isinstance(m.get('content'),str) or m.get('role') not in {'user','system','assistant'} for m in row['question'][0]):
        raise ValueError('Invalid BFCL messages')
    names = [f['name'].replace('.','_') for f in row['function']]
    if len(set(names)) != len(names) or any(not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',n) for n in names):
        raise ValueError('Invalid or colliding tool names')
    for f in row['function']:
        tool_schema(f)


def make_item(spec, row, index, rev, tier):
    key, grader = spec['key'], spec['grader']
    meta = {}
    if key == 'mmlu':
        question, options, gold = row['question'], row['options'], row['answer']
        meta['domain'] = row['category']
    elif key.startswith('musr_'):
        question = row['narrative'] + '\n\n' + row['question']
        options = list_field(row['choices'])
        gold = chr(65 + int(row['answer_index']))
    elif key in ('math','aime24','aime25'):
        question = row.get('problem', row.get('question'))
        gold = numeric_answer(row.get('answer', row.get('solution')))
        if gold is None:
            raise ValueError(f'Non-numeric gold in {key}: {row.get('answer', row.get('solution'))!r}')
    elif key == 'code':
        question = row.get('instruct_prompt') or row['complete_prompt']
        gold = {'test':row['test'], 'entry_point':row['entry_point'], 'mode':'unittest'}
        meta['complete_prompt'] = row['complete_prompt']
        meta['libs'] = list_field(row['libs'])
    elif key == 'ifeval':
        question = row['prompt']
        gold = {'instruction_id_list':row['instruction_id_list'], 'kwargs':row['kwargs']}
    elif key.startswith('tools_'):
        question = None
        gold = [{f.replace('.', '_'): args for f, args in call.items()} for call in row.get('_gold', [])]
        names = {f['name']: f['name'].replace('.','_') for f in row['function']}
        if len(set(names.values())) != len(names):
            raise ValueError('Tool-name normalization collision')
        tools = []
        for function in row['function']:
            f = tool_schema(function)
            f['name'] = names[function['name']]
            tools.append({'type':'function', 'function':f})
        meta.update(functions=row['function'], tool_name_map=names)
    else:
        raise ValueError(key)
    if grader == 'mcq':
        if not 0 <= ord(gold)-65 < len(options):
            raise ValueError('Invalid MCQ gold')
        meta['choices'] = options
        prompt = CONFIG['mcq_prompt'].format(question=question, options='\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(options)))
    elif grader == 'numeric':
        prompt = CONFIG['numeric_prompt'].format(question=question)
    elif grader == 'code':
        prompt = CONFIG['code_prompt'].format(question=question)
    else:
        prompt = question
    messages = [{'role':'system','content':CONFIG['system']}, {'role':'user','content':prompt}]
    if grader == 'ifeval':
        messages = [{'role':'user','content':prompt}]
    body = dict(messages=messages, max_tokens=spec['max_tokens'], temperature=0, stream=False, chat_template_kwargs={'enable_thinking':False,'thinking':False})
    if grader == 'tool':
        if len(row['question']) != 1:
            raise ValueError('Only single-turn BFCL supported')
        body.update(messages=row['question'][0], tools=tools, tool_choice='auto')
    meta['problem_text'] = question if question is not None else canonical(row['question'][0]).decode()
    oid = original_id(spec,row,index)
    return dict(id=f'{key}:{oid}', category=spec['category'], tier=tier, source=spec['repo'], source_revision=rev,
                license=spec['license'], pool=key, sampler_version=CONFIG['version'], original_id=oid, grader='tools' if grader == 'tool' else grader, body=body, gold=gold, meta=meta)


def build(args):
    args.cache.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    old_lock = json.loads(args.lock.read_text()) if args.lock.exists() else None
    if old_lock is None and not args.update_lock:
        raise RuntimeError(f'Missing source lock {args.lock}; use --update-lock ONLY to approve initial/new source content')
    lock = dict(old_lock or {'schema_version':2}, sources={})
    items = []
    audit = {'schema_version':3, 'config_sha256':sha(canonical(CONFIG)), 'code':[], 'draft':True}
    pending = ['reference_validation']
    for spec in CONFIG['sources']:
        key = spec['key']
        expected = (old_lock or {}).get('sources',{}).get(key)
        if args.offline:
            if not expected:
                raise RuntimeError(f'No locked source: {key}')
            rev = expected['revision']
        else:
            rev = expected['revision'] if expected and not args.update_lock else revision(spec)
            current = revision(spec)
            if expected and not args.update_lock and current != rev:
                raise RuntimeError(f'SOURCE CHANGED upstream: {key}: {rev} -> {current}')
        if not args.update_lock and (not expected or rev != expected['revision']):
            raise RuntimeError(f'SOURCE CHANGED: {key}: expected {expected and expected["revision"]}, got {rev}. Review source before --update-lock.')
        cache = args.cache / f'{key}-{rev}.json'
        if cache.exists() and not args.refresh:
            rows = json.loads(cache.read_bytes())
            if expected:
                urls = expected['urls']
            elif spec.get('github'):
                root = f'https://raw.githubusercontent.com/{spec["repo"]}/{rev}/berkeley-function-call-leaderboard/bfcl_eval/data/'
                name = 'BFCL_v4_' + spec['split'] + '.json'
                urls = [root + name, root + 'possible_answer/' + name]
            elif spec.get('raw'):
                urls = [f'https://huggingface.co/datasets/{spec["repo"]}/resolve/{rev}/{spec["raw"]}']
            else:
                urls = [rows_url(spec, offset) for offset in range(0, len(rows), 100)]
        else:
            if args.offline:
                raise RuntimeError(f'Missing offline cache: {cache}')
            rows, urls = download_rows(spec,rev)
            if not spec.get('github') and revision(spec) != rev:
                raise RuntimeError(f'SOURCE CHANGED during download: {key}')
            cache.write_bytes(canonical(rows))
        digest = sha(canonical(rows))
        entry = dict(repo=spec['repo'], config=spec.get('config'), split=spec['split'], revision=rev,
                     sha256=digest, rows=len(rows), urls=urls, license=spec['license'])
        if expected and not args.update_lock and any(entry[k] != expected[k] for k in ('repo','config','split','revision','sha256','rows','license')):
            raise RuntimeError(f'SOURCE CHANGED: hash/schema/identity mismatch for {key}; expected {expected["sha256"]}, got {digest}')
        lock['sources'][key] = entry
        fields = {'mmlu':{'question','options','answer','category'},'math':{'problem','level','answer'},'aime24':{'problem','solution'},'aime25':{'problem','answer'},'code':{'libs','complete_prompt','canonical_solution','test','entry_point','instruct_prompt'},'ifeval':{'prompt','instruction_id_list','kwargs'}}
        required = fields.get(key, {'question','function','id'} if key.startswith('tools_') else {'narrative','question','choices','answer_index'})
        if any(not isinstance(r,dict) or not required <= set(r) for r in rows):
            raise RuntimeError('Unexpected source schema: ' + key)
        ids = [original_id(spec,r,i) for i,r in enumerate(rows)]
        if len(set(ids)) != len(ids):
            raise RuntimeError('Duplicate original IDs: ' + key)
        pool = []
        for i, row in enumerate(rows):
            if ids[i] in CONFIG['excluded'].get(key, ()):
                continue
            if key == 'code':
                reason = code_static_reason(row)
                result = dict(original_id=ids[i], reference_sha256=sha(reference_source(row).encode()), tests_sha256=sha(row['test'].encode()))
                if reason:
                    result.update(eligible=False, reason=reason)
                else:
                    result.update(eligible=True, reason='candidate_static_eligibility_only')
                audit['code'].append(result)
                args.audit.write_bytes(canonical(audit)+b'\n')
                if not result['eligible']:
                    continue
            elif not eligible(spec,row):
                continue
            pool.append((i,row))
        strata = spec.get('domains', {'all':spec['counts']})
        for stratum, (ncore,nextra) in strata.items():
            candidates = [(i,r) for i,r in pool if stratum == 'all' or r['category'] == stratum]
            candidates.sort(key=lambda ir:(sha(f'{CONFIG["seed"]}|{key}|{stratum}|{original_id(spec,ir[1],ir[0])}'.encode()), original_id(spec,ir[1],ir[0])))
            if len(candidates) < ncore+nextra:
                raise RuntimeError(f'{key}/{stratum}: need {ncore+nextra}, have {len(candidates)}')
            limit = min(len(candidates), CONFIG['code_candidate_multiplier'] * (ncore+nextra)) if key == 'code' else ncore+nextra
            for pos,(index,row) in enumerate(candidates[:limit]):
                item = make_item(spec,row,index,rev,'candidate' if key == 'code' else ('core' if pos<ncore else 'extended'))
                if key == 'code':
                    item['reference_source'] = reference_source(row)
                    item['candidate_rank'] = pos
                items.append(item)
        print(f'{key}: {len(rows)} source rows, {len(pool)} eligible; core={spec["counts"][0]}, extended={spec["counts"][1]}', flush=True)
    texts = {}
    for item in items:
        body = item['body']
        problem = item['meta']['problem_text']
        normalized = ' '.join(problem.replace('\r\n','\n').split())
        if normalized in texts:
            raise RuntimeError(f'Duplicate normalized problem: {texts[normalized]}, {item["id"]}')
        texts[normalized] = item['id']
    items.sort(key=lambda item:(item['tier'] != 'core', sha(f'{CONFIG["seed"]}|order|{item["id"]}'.encode()), item['id']))
    # Eligibility-affecting checker parity must be explicitly advertised by the aligned grader.
    supported = set(getattr(grade_pub, 'SUPPORTED_IFEVAL', []))
    required = set(next(s for s in CONFIG['sources'] if s['key']=='ifeval')['rules'])
    if not required <= supported:
        pending.append('ifeval_official_parity:' + ','.join(sorted(required-supported)))
    audit['pending'] = sorted(set(pending))
    args.audit.write_bytes(canonical(audit)+b'\n')
    manifest = write_artifact(args.output, items, lock, audit, frozen=False)
    if args.update_lock:
        args.lock.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n')
    if args.examples:
        args.examples.mkdir(parents=True,exist_ok=True)
        args.examples.joinpath('manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        buckets = defaultdict(list)
        for item in items:
            if len(buckets[item['category']]) < 3:
                buckets[item['category']].append(item)
        args.examples.joinpath('items.examples.jsonl').write_bytes(b''.join(canonical(i)+b'\n' for cat in sorted(buckets) for i in buckets[cat]))
    print(json.dumps(manifest['counts'],sort_keys=True))
    return manifest


def write_artifact(output, items, lock, audit, *, frozen, **extra):
    if len({i['id'] for i in items}) != len(items):
        raise RuntimeError('Duplicate item IDs')
    items.sort(key=lambda item:(item['tier'] != 'core', sha(f'{CONFIG["seed"]}|order|{item["id"]}'.encode()), item['id']))
    data = b''.join(canonical(item)+b'\n' for item in items)
    tiers = ('core','extended') if frozen else ('core','extended','candidate')
    manifest = dict(schema_version=3, frozen=frozen, pending=audit['pending'],
                    sampler_version=CONFIG['version'], build_audit_sha256=sha(canonical(audit)),
                    seed=CONFIG['seed'], config_sha256=sha(canonical(CONFIG)),
                    items_sha256=sha(data), item_count=len(items), source_lock_sha256=sha(canonical(lock)),
                    counts={t:dict(Counter(i['category'] for i in items if i['tier']==t)) for t in tiers},
                    pool_counts={t:dict(Counter(i['pool'] for i in items if i['tier']==t)) for t in tiers},
                    sources=lock['sources'], **extra)
    output.parent.mkdir(parents=True, exist_ok=True)
    # A mismatched old manifest fails closed if interrupted between these renames.
    tmp = output.with_name(output.name+'.tmp')
    tmp.write_bytes(data)
    os.replace(tmp, output)
    path = output.with_suffix('.manifest.json')
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    os.replace(tmp, path)
    return manifest


def validate_code(args):
    """Freeze a self-contained candidate artifact; never download or run code directly."""
    if args.input.resolve() == args.output.resolve():
        raise RuntimeError('Candidate input and frozen output must be separate paths')
    data = args.input.read_bytes()
    manifest = json.loads(args.input.with_suffix('.manifest.json').read_text())
    if manifest.get('frozen') is not False or manifest.get('schema_version') != 3:
        raise RuntimeError('Expected a schema-3 unfrozen candidate draft')
    if sha(data) != manifest['items_sha256'] or manifest['config_sha256'] != sha(canonical(CONFIG)):
        raise RuntimeError('Candidate content/config changed; rebuild draft')
    if manifest.get('pending') != ['reference_validation']:
        raise RuntimeError('Draft has unresolved non-code preflight requirements')
    lock = json.loads(args.lock.read_text())
    if sha(canonical(lock)) != manifest['source_lock_sha256']:
        raise RuntimeError('Source lock changed; rebuild draft')
    items = [json.loads(line) for line in data.splitlines() if line.strip()]
    if len(items) != manifest['item_count'] or len({i['id'] for i in items}) != len(items):
        raise RuntimeError('Invalid candidate count/IDs')
    candidates = [i for i in items if i['grader'] == 'code']
    selected = [i for i in items if i['grader'] != 'code']
    spec = next(s for s in CONFIG['sources'] if s['key'] == 'code')
    ncore, nextra = spec['counts']
    quota = ncore+nextra
    candidates.sort(key=lambda i:(sha(f'{CONFIG["seed"]}|code|all|{i["original_id"]}'.encode()), i['original_id']))
    if not quota <= len(candidates) <= CONFIG['code_candidate_multiplier'] * quota:
        raise RuntimeError('Invalid code candidate quota')
    for rank, item in enumerate(candidates):
        if item['tier'] != 'candidate' or item['candidate_rank'] != rank or not item.get('reference_source'):
            raise RuntimeError('Invalid candidate rank/tier/reference')
    audit = dict(schema_version=3, draft=False, config_sha256=sha(canonical(CONFIG)),
                 candidates_sha256=sha(data), code=[], pending=['reference_validation'])
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    def save_audit():
        args.audit.write_bytes(canonical(audit)+b'\n')
    save_audit()
    args.cache.mkdir(parents=True, exist_ok=True)
    # Probe once before timing references, so its startup cost is not an exclusion.
    isolation, reason = grade_pub.isolation_config(args.cache)
    if isolation is None:
        audit['pending'] = ['reference_isolation_unavailable']
        audit['failure'] = reason
        save_audit()
        raise RuntimeError('Reference isolation unavailable: '+reason)
    passed = 0
    for item in candidates:
        record = dict(original_id=item['original_id'], candidate_rank=item['candidate_rank'],
                      reference_sha256=sha(item['reference_source'].encode()),
                      tests_sha256=sha(item['gold']['test'].encode()))
        try:
            ok, detail = grade_pub.validate_reference(item['reference_source'], item['gold'], temp_root=args.cache)
        except grade_pub.GraderDefect as exc:
            record.update(eligible=False, reason='grader_defect', detail=str(exc))
            audit['code'].append(record)
            audit['pending'] = ['reference_grader_defect']
            save_audit()
            raise RuntimeError('Reference grader defect: '+str(exc)) from exc
        record.update(eligible=ok is True, **detail)
        audit['code'].append(record)
        if ok is None:
            audit['pending'] = ['reference_isolation_unavailable']
            save_audit()
            raise RuntimeError('Reference isolation unavailable: '+str(detail))
        if ok:
            record['selected'] = passed < quota
            if passed < quota:
                frozen_item = dict(item)
                del frozen_item['reference_source']
                del frozen_item['candidate_rank']
                frozen_item['tier'] = 'core' if passed < ncore else 'extended'
                selected.append(frozen_item)
            passed += 1
        else:
            record['selected'] = False
        save_audit()
        print(f'code rank={item["candidate_rank"]} {item["id"]}: {record["reason"]}', flush=True)
    if passed < quota:
        audit['pending'] = ['code_quota_shortfall']
        save_audit()
        raise RuntimeError(f'code: need {quota} passing candidates, have {passed}; review exclusions before rebuilding')
    # Verify every pool and stratum before publishing a frozen artifact.
    for source in CONFIG['sources']:
        for stratum, counts in source.get('domains', {'all':source['counts']}).items():
            for tier, count in zip(('core','extended'), counts):
                actual = sum(i['pool'] == source['key'] and i['tier'] == tier and
                             (stratum == 'all' or i['meta'].get('domain') == stratum) for i in selected)
                if actual != count:
                    raise RuntimeError(f'Final quota mismatch: {source["key"]}/{stratum}/{tier}: {actual} != {count}')
    audit['pending'] = []
    save_audit()
    result = write_artifact(args.output, selected, lock, audit, frozen=True,
                            candidates_sha256=sha(data), reference_validation_runs=3)
    print(json.dumps(result['counts'],sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Default: candidates.jsonl for build; items.jsonl for validation')
    parser.add_argument('--validate-code',action='store_true',help='Validate draft references in bwrap on Linux and freeze')
    parser.add_argument('--input',type=Path,default=Path('candidates.jsonl'),help='Self-contained draft for --validate-code')
    parser.add_argument('--cache',type=Path,default=Path('.pub-cache'))
    parser.add_argument('--lock',type=Path,default=HERE/'sources.lock.json')
    parser.add_argument('--update-lock',action='store_true',help='Explicitly approve source snapshots after reviewing changes')
    parser.add_argument('--offline',action='store_true',help='Use verified local caches; no network access')
    parser.add_argument('--refresh',action='store_true',help='Download sources again, validating against lock')
    parser.add_argument('--examples',type=Path)
    parser.add_argument('--draft',action='store_true',help='Compatibility alias: builds always emit unvalidated candidates')
    parser.add_argument('--audit',type=Path,help='Default: build.audit.json or validate.audit.json')
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error('--offline and --refresh are incompatible')
    args.output = args.output or Path('items.jsonl' if args.validate_code else 'candidates.jsonl')
    args.audit = args.audit or Path('validate.audit.json' if args.validate_code else 'build.audit.json')
    if args.validate_code and (args.update_lock or args.refresh or args.examples or args.draft):
        parser.error('--validate-code cannot update/rebuild sources or examples')
    if args.validate_code:
        validate_code(args)
    else:
        build(args)

if __name__ == '__main__':
    main()
