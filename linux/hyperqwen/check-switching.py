#!/usr/bin/env python3
"""Synthetic switching regression: real launcher/router, SSE, tools and 64K profile."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = 'http://127.0.0.1:18020'
IDS = {mode: 'qwen3.8-27b-hyperqwen-' + mode for mode in ('dflash2', 'mtp')}
TOOLS = [{'type': 'function', 'function': {'name': 'get_test_value',
    'description': 'Get the synthetic test value.', 'parameters': {'type': 'object',
    'properties': {'key': {'type': 'string'}}, 'required': ['key']}}}]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--label', default='switching-2026-10-07')
parser.add_argument('--long-tokens', type=int, default=61000)
parser.add_argument('--quick', action='store_true', help='Skip long prompts and tools.')
parser.add_argument('--queue-only', action='store_true', help='Test a switch queued behind active generation, then restore DFlash2.')
args = parser.parse_args()
output = ROOT / 'hyperqwen/research' / (args.label + '.json')
result = {'date': '2026-10-07', 'purpose': 'switching and functional regression, not speed benchmark',
          'stages': [], 'passed': False}

def save():
    output.write_text(json.dumps(result, indent=2) + '\n')

def get(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return json.load(response)

def gpu():
    raw = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.total',
                                   '--format=csv,noheader,nounits'], text=True)
    return [[int(x.strip()) for x in line.split(',')] for line in raw.splitlines()]

def owned_pids():
    raw = subprocess.check_output(['ss', '-lntp', 'sport = :18021'], text=True)
    match = re.search(r'pid=(\d+)', raw)
    if not match:
        return []
    group = os.getpgid(int(match.group(1)))
    found = []
    for path in Path('/proc').iterdir():
        if path.name.isdecimal():
            try:
                if os.getpgid(int(path.name)) == group:
                    found.append(int(path.name))
            except ProcessLookupError:
                pass
    return sorted(found)

def verify_spec(mode, pids):
    for pid in pids:
        try:
            argv = Path('/proc', str(pid), 'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if b'--speculative-config' in argv:
            value = json.loads(argv[argv.index(b'--speculative-config') + 1])
            expected = 'dflash' if mode == 'dflash2' else 'mtp'
            assert value['method'] == expected
            assert value['num_speculative_tokens'] == (7 if mode == 'dflash2' else 3)
            return {'method': value['method'], 'num_speculative_tokens': value['num_speculative_tokens']}
    raise AssertionError('No worker speculative config found')

def chat(mode, prompt=None, messages=None, base=ROUTER, key=None, first_event=None, **extra):
    body = {'model': IDS[mode], 'messages': messages or [{'role': 'user', 'content': prompt}],
            'temperature': 0, 'seed': 42, 'max_tokens': 256, 'stream': True,
            'stream_options': {'include_usage': True},
            'chat_template_kwargs': {'enable_thinking': False}}
    body.update(extra)
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    request = urllib.request.Request(base + '/v1/chat/completions', json.dumps(body).encode(), headers)
    start = time.monotonic()
    text, usage, calls, done, model, finish = '', {}, {}, False, None, None
    with urllib.request.urlopen(request, timeout=1200) as response:
        for line in response:
            if not line.startswith(b'data: '):
                continue
            data = line[6:].strip()
            if data == b'[DONE]':
                done = True
                continue
            item = json.loads(data)
            if item.get('error'):
                raise RuntimeError(str(item['error']))
            model = item.get('model', model)
            usage = item.get('usage') or usage
            for choice in item.get('choices', []):
                finish = choice.get('finish_reason') or finish
                delta = choice.get('delta') or {}
                text += delta.get('content') or ''
                if first_event is not None and delta.get('content'):
                    first_event.set()
                for fragment in delta.get('tool_calls') or []:
                    call = calls.setdefault(fragment['index'], {'id': '', 'type': 'function',
                                                  'function': {'name': '', 'arguments': ''}})
                    if fragment.get('id'):
                        call['id'] = fragment['id']
                    for field in ('name', 'arguments'):
                        call['function'][field] += fragment.get('function', {}).get(field) or ''
    assert done, 'Stream missing [DONE]'
    assert model == IDS[mode], 'Incorrect served model ID: ' + str(model)
    assert finish, 'Missing finish reason'
    assert usage.get('completion_tokens', 0) > 0, 'No completion usage'
    finished = time.monotonic()
    return {'stream_done': done, 'model_matches': True, 'usage': usage,
            'finished_monotonic': finished,
            'elapsed_s': round(time.monotonic() - start, 3), 'finish_reason': finish}, text, list(calls.values())

def long_prompt():
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file('/opt/local-llm/models/HyperQwen/'
                                    'Qwen3.8-27B-AWQ-HyperQwen-fast/tokenizer.json')
    unit = 'Archive record: amber cedar granite river violet. This record contains no access codes.\n'
    padding = unit * (args.long_tokens // len(tokenizer.encode(unit).ids))
    blocks = [padding[i*len(padding)//3:(i+1)*len(padding)//3] for i in range(3)]
    text = ('Return only the values of ACCESS_A, ACCESS_B, and ACCESS_C from the archive.\n'
            'ACCESS_A=RIVER-731\n' + blocks[0] + '\nACCESS_B=CEDAR-942\n' + blocks[1]
            + '\nACCESS_C=AMBER-583\n' + blocks[2] + '\nReturn all three access values now.')
    return text, len(tokenizer.encode(text).ids)

try:
    deadline = time.monotonic() + 900
    print('Waiting for launcher DFlash2 warmup.', flush=True)
    while time.monotonic() < deadline:
        try:
            if get(ROUTER, '/health').get('active_mode') == 'dflash2':
                break
        except OSError:
            pass
        time.sleep(2)
    else:
        raise RuntimeError('Initial DFlash2 load did not become ready in 900 seconds')
    initial = owned_pids()
    result['initial_gpu_mib'] = gpu()
    if args.queue_only:
        print('Starting DFlash2 output; queue MTP after its first token.', flush=True)
        first_event = threading.Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(chat, 'dflash2', 'Write a detailed Python tutorial about merging sorted lists.',
                                  first_event=first_event, max_tokens=1024, ignore_eos=True)
            assert first_event.wait(60), 'No first DFlash2 token'
            assert not pending.done(), 'DFlash2 already finished; cannot test queued switch'
            mtp, mtp_text, _ = chat('mtp', 'Reply with exactly QUEUED_SWITCH_OK.', max_tokens=64)
            old, old_text, _ = pending.result(timeout=30)
            assert 'QUEUED_SWITCH_OK' in mtp_text and old_text.strip()
            assert old['usage']['completion_tokens'] == 1024, 'Active reply was truncated'
            assert old['finished_monotonic'] < mtp['finished_monotonic']
            assert not any(Path('/proc', str(pid)).exists() for pid in initial)
            result['queued_switch'] = {'active_reply_completed': True, 'mtp_after_reply': True,
                                       'dflash2_reply': old, 'mtp_reply': mtp, 'old_group_exited': True}
        restored, text, _ = chat('dflash2', 'Reply with exactly RESTORED_DFLASH2_OK.', max_tokens=64)
        assert 'RESTORED_DFLASH2_OK' in text
        result['restored_dflash2'] = restored
        result['passed'] = True
        save()
        print('PASS: active DFlash2 reply completed before queued MTP switch; DFlash2 restored.', flush=True)
        raise SystemExit(0)
    prompt, tokens = long_prompt() if not args.quick else ('', 0)
    previous = initial
    for index, mode in enumerate(('dflash2', 'mtp', 'dflash2', 'mtp', 'dflash2')):
        stage = {'index': index, 'mode': mode, 'gpu_peak_mib': [0, 0]}
        result['stages'].append(stage)
        stop = threading.Event()
        def monitor():
            while not stop.is_set():
                try:
                    for n, used, _ in gpu():
                        stage['gpu_peak_mib'][n] = max(stage['gpu_peak_mib'][n], used)
                except (OSError, subprocess.CalledProcessError):
                    pass
                stop.wait(1)
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        print(f'Stage {index}: {mode}, streaming generation (reload if switching).', flush=True)
        try:
            check, text, _ = chat(mode, 'Write a Python function to merge two sorted lists and explain its complexity.')
            assert text.strip(), 'Empty generation'
            stage['chat'] = check
            health = get(ROUTER, '/health')
            assert health['active_mode'] == mode and health['active_model'] == IDS[mode]
            info = get('http://127.0.0.1:18021', '/v1/models')['data']
            assert any(m['id'] == IDS[mode] and m['max_model_len'] == 65536 for m in info)
            stage['worker_context_verified'] = 65536
            current = owned_pids()
            assert current, 'No worker process group detected'
            stage['speculative_config_verified'] = verify_spec(mode, current)
            if index:
                stage['old_group_exited'] = not any(Path('/proc', str(pid)).exists() for pid in previous)
                assert stage['old_group_exited'], 'Old worker processes remain after switch'
            previous = current
            stage['owned_worker_pids'] = current
            if not args.quick and index < 3:
                check, _, calls = chat(mode, 'Call get_test_value with key alpha.', tools=TOOLS,
                                       tool_choice='required', max_tokens=96)
                assert len(calls) == 1 and calls[0]['id']
                assert calls[0]['function']['name'] == 'get_test_value'
                assert json.loads(calls[0]['function']['arguments']) == {'key': 'alpha'}
                stage['tool_call'] = check
                check, text, _ = chat(mode, messages=[{'role': 'user', 'content': 'Call get_test_value with key alpha, then return its value.'},
                    {'role': 'assistant', 'content': None, 'tool_calls': calls},
                    {'role': 'tool', 'tool_call_id': calls[0]['id'], 'content': '{"value":"SWITCH_TOOL_OK_731"}'}],
                    tools=TOOLS, tool_choice='none', max_tokens=96)
                assert 'SWITCH_TOOL_OK_731' in text
                stage['tool_result'] = check
                print(f'Stage {index}: tools passed, long retrieval (~{tokens} raw tokens).', flush=True)
                check, text, _ = chat(mode, prompt, max_tokens=192)
                assert all(marker in text for marker in ('RIVER-731', 'CEDAR-942', 'AMBER-583'))
                assert 59000 <= check['usage']['prompt_tokens'] < 65536
                stage['long_retrieval'] = {**check, 'all_markers_found': True}
            stage['passed'] = True
        finally:
            stop.set()
            thread.join(timeout=5)
            stage['gpu_after_mib'] = gpu()
            save()
        print(f'Stage {index} passed: {mode}.', flush=True)
    # Exercise the same external authenticated API clients use, on both network paths.
    private = json.loads((ROOT / 'dsh/data/network-access.json').read_text())
    key = Path(private['key_file']).read_text().strip()
    result['network_streams'] = {}
    for address in private['listen']:
        if address == '127.0.0.1':
            continue
        label = 'tailscale' if address.startswith('100.') else 'lan'
        check, text, _ = chat('dflash2', 'Reply with exactly HYPERQWEN_NETWORK_OK.',
            base=f'http://{address}:{private["port"]}', key=key, max_tokens=64)
        assert 'HYPERQWEN_NETWORK_OK' in text
        result['network_streams'][label] = check
    result['passed'] = True
    save()
    print('PASS: two complete DFlash2/MTP/DFlash2 cycles, tools, long context and network streaming.', flush=True)
except Exception as error:
    result['error'] = str(error)
    save()
    raise
