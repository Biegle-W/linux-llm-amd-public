"""Single-stream SSE timings; generated prompts only, no user data."""
import argparse
import json
import statistics
import time
import urllib.request
import urllib.error
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--base', default='http://127.0.0.1:18020')
p.add_argument('--label', default='hyperqwen-mtp')
p.add_argument('--repeats', type=int, default=3)
p.add_argument('--long-tokens', type=int, nargs='*', default=[4096, 16384, 60000])
args = p.parse_args()
deadline = time.monotonic() + 1200
while True:
    try:
        with urllib.request.urlopen(args.base + '/health', timeout=5) as response:
            if response.status == 200:
                break
    except (OSError, urllib.error.URLError):
        pass
    if time.monotonic() > deadline:
        raise TimeoutError('Server did not become healthy within 20 minutes')
    time.sleep(3)
root = Path(__file__).parent / 'research' / 'raw'
root.mkdir(parents=True, exist_ok=True)
rows = []

def request(route, body):
    req = urllib.request.Request(args.base + route, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    return urllib.request.urlopen(req, timeout=1800)

def run(name, prompt, count=256, **extra):
    body = {'model': 'qwen3.8-27b', 'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': count, 'temperature': 0.6, 'top_p': 0.95, 'seed': 42,
            'chat_template_kwargs': {'enable_thinking': False},
            'stream': True, 'stream_options': {'include_usage': True}}
    body.update(extra)
    started = time.monotonic()
    first = None
    text = ''
    usage = {}
    metrics = {}
    calls = []
    with request('/v1/chat/completions', body) as response:
        for line in response:
            if not line.startswith(b'data: ') or line.strip() == b'data: [DONE]':
                continue
            item = json.loads(line[6:])
            usage = item.get('usage') or usage
            metrics.update(item.get('metrics') or {})
            for choice in item.get('choices', []):
                delta = choice.get('delta') or {}
                piece = delta.get('content') or ''
                if piece or delta.get('tool_calls'):
                    first = first or time.monotonic()
                text += piece
                calls += delta.get('tool_calls') or []
    finished = time.monotonic()
    n = usage.get('completion_tokens', 0)
    row = {'name': name, 'ttft_s': None if first is None else first - started,
           'elapsed_s': finished - started,
           'decode_tps_external': None if first is None else (n-1)/max(.001, finished-first),
           'usage': usage, 'metrics': metrics, 'text': text, 'tool_calls': calls}
    rows.append(row)
    (root / (args.label + '.json')).write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps({k:v for k,v in row.items() if k != 'text'}), flush=True)
    return row

run('warmup', 'List ten practical ways to organize a bookshelf.', 96)
prompts = {
    'code': 'Write a Python function that merges two sorted lists. Explain its time and space complexity.',
    'prose': 'Write a short story about a lighthouse keeper finding a letter.'}
for i in range(args.repeats):
    for name, prompt in prompts.items():
        run(f'{name}-{i+1}', prompt)
tools = [{'type':'function','function': {'name':'get_test_value','description':'Get a test value',
           'parameters':{'type':'object','properties':{'key':{'type':'string'}},'required':['key']}}}]
tool = run('tool', 'Call get_test_value with key alpha.', 96, tools=tools, tool_choice='required')
assert tool['tool_calls'], 'No structured tool call'
merged = {}
for piece in tool['tool_calls']:
    index = piece['index']
    call = merged.setdefault(index, {'id':'', 'type':'function', 'function':{'name':'','arguments':''}})
    if piece.get('id'): call['id'] = piece['id']
    for key in ('name','arguments'):
        call['function'][key] += piece.get('function', {}).get(key, '')
call = merged[0]
assert call['function']['name'] == 'get_test_value'
assert json.loads(call['function']['arguments']) == {'key':'alpha'}
result = run('tool-result', '', 96, temperature=0, messages=[
    {'role':'user','content':'Call get_test_value with key alpha, then report the returned value.'},
    {'role':'assistant','content':None,'tool_calls':[call]},
    {'role':'tool','tool_call_id':call['id'],'content':'{"value":"HYPERQWEN_TOOL_OK_742"}'}])
assert 'HYPERQWEN_TOOL_OK_742' in result['text'], 'Tool result was not used'
for target in args.long_tokens:
    chunks = []
    for i in range(target // 12):
        chunks.append(f'Record {i}: sample archive entry contains ordinary descriptive words.\n')
    middle = len(chunks)//2
    chunks.insert(middle, 'The middle access code is CEDAR-529.\n')
    prompt = f'Archive size target: {target} tokens.\nThe first access code is MAPLE-173.\n' + ''.join(chunks)
    suffix = '\nThe last access code is BIRCH-864.\nReturn the three access codes from the beginning, middle and end. Then write a detailed 500-word explanation of how archive records can be indexed and searched.'
    prompt += suffix
    with request('/tokenize', {'model':'qwen3.8-27b', 'messages':[{'role':'user','content':prompt}],
                              'chat_template_kwargs':{'enable_thinking':False}}) as response:
        token_count = json.load(response)['count']
    # Keep enough room for the reply, even when the tokenizer differs from estimates.
    if token_count > target:
        keep = max(1, int(len(chunks) * (target-512) / token_count))
        half = keep//2
        selected = chunks[:half] + ['The middle access code is CEDAR-529.\n'] + chunks[-half:]
        prompt = f'Archive size target: {target} tokens.\nThe first access code is MAPLE-173.\n' + ''.join(selected)
        prompt += suffix
    row = run(f'context-{target}', prompt, 256, temperature=0)
    row['retrieval_passed'] = all(code in row['text'] for code in ('MAPLE-173','CEDAR-529','BIRCH-864'))
    (root / (args.label + '.json')).write_text(json.dumps(rows, indent=2) + '\n')
    print('retrieval', target, row['retrieval_passed'], flush=True)
summary = {}
for name in prompts:
    group = [r for r in rows if r['name'].startswith(name+'-')]
    summary[name] = {'median_decode_tps_external':statistics.median(r['decode_tps_external'] for r in group),
                     'median_ttft_s':statistics.median(r['ttft_s'] for r in group)}
(root / (args.label + '-summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary), flush=True)
