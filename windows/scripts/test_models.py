"""Sequential local model checks. Never writes to the model directory.

Uses a private loopback server on port 10001 and stops each owned process.
Usage: python test_models.py [profile-id ...] [--long-tokens N]
"""
import argparse
import configparser
import ctypes
import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
PORT = 10001
REQUEST_TIMEOUT = 600
SPEED_TEMPERATURE = 0.0

class MemoryStatus(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in
        ('physical_total', 'physical_available', 'commit_limit', 'commit_available',
         'virtual_total', 'virtual_available', 'extended_available')]

def memory():
    state = MemoryStatus()
    state.length = ctypes.sizeof(state)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        raise ctypes.WinError()
    return {k + '_gib': round(getattr(state, k) / 2**30, 2) for k in
            ('physical_total', 'physical_available', 'commit_limit', 'commit_available')}

def api(path, data=None, timeout=None):
    request = urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',
        data=None if data is None else json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT if timeout is None else timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'HTTP {error.code}: {error.read().decode()[:2000]}') from error

def gpu():
    result = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.free',
        '--format=csv,noheader'], capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW)
    return result.stdout.strip().splitlines()

def monitor_gpu(stop, samples):
    while not stop.is_set():
        snapshot = subprocess.run(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu,clocks.gr,clocks.mem,power.draw,pcie.link.gen.current,pcie.link.width.current',
            '--format=csv,noheader'], capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        samples.append({'time': datetime.datetime.now().astimezone().isoformat(),
                        'gpu': snapshot.stdout.strip().splitlines(), 'memory': memory()})
        stop.wait(1)

def chat(model, messages, **kwargs):
    return api('/v1/chat/completions', {'model': model, 'messages': messages,
        'temperature': 0, 'seed': 42, 'max_tokens': 1024,
        'chat_template_kwargs': {'enable_thinking': False}, **kwargs})

def checked_response(response, expected):
    content = response['choices'][0]['message'].get('content') or ''
    if expected not in content:
        raise AssertionError(f'Expected {expected!r}; received {content[:300]!r}')

def run(profile, common, runtime, output, long_tokens, speed_only=False, latency_tokens=None):
    model = profile['id']
    options = dict(common)
    options.pop('load-on-startup', None)
    options.update(profile.get('options', {}))
    options.update({'model': profile['path'], 'ctx-size': profile['context'],
        'fit-ctx': profile['context'], 'host': '127.0.0.1', 'port': PORT,
        'alias': model, 'log-verbosity': 4})
    command = [str(runtime)]
    for key, value in options.items():
        if str(value).lower() == 'true':
            command.append('--' + key)
        elif str(value).lower() != 'false':
            command.extend(['--' + key, str(value)])
    result = {'model': model, 'context_requested': profile['context'], 'command': command,
        'speed_only': speed_only, 'request_timeout': REQUEST_TIMEOUT,
        'speed_temperature': SPEED_TEMPERATURE,
        'started_at': datetime.datetime.now().astimezone().isoformat(),
        'memory_before': memory(), 'gpu_before': gpu(), 'checks': {}}
    log_path = output / (model + '.log')
    result['log'] = str(log_path)
    process = None
    print(f'{model}: loading {profile["context"]:,} context', flush=True)
    try:
        if result['memory_before']['commit_available_gib'] < 25:
            raise RuntimeError('Insufficient system commit headroom for a meaningful load test.')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', PORT))
        env = {k: v for k, v in os.environ.items()
               if not k.startswith('LLAMA_ARG_') and k not in ('CUDA_VISIBLE_DEVICES', 'LLAMA_API_KEY')}
        env['LLAMA_CACHE'] = str(ROOT / 'data' / 'cache' / 'router')
        with log_path.open('w', encoding='utf-8') as log:
            start = time.monotonic()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW)
            result['pid'] = process.pid
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'Server exited during loading: {process.returncode}')
                try:
                    if api('/health', timeout=3).get('status') == 'ok':
                        break
                except (OSError, RuntimeError):
                    pass
                if time.monotonic() - start > 240:
                    raise TimeoutError('Model load exceeded 240 seconds.')
                time.sleep(1)
            result['load_seconds'] = round(time.monotonic() - start, 2)
            result['properties'] = api('/props')
            actual_context = result['properties']['default_generation_settings']['n_ctx']
            if actual_context != profile['context']:
                raise AssertionError(f'Expected context {profile["context"]}, got {actual_context}')
            result['memory_loaded'] = memory()
            result['gpu_loaded'] = gpu()
            print(f'{model}: loaded in {result["load_seconds"]}s; checking chat', flush=True)

            def check(name, action):
                begin = time.monotonic()
                try:
                    evidence = action()
                    result['checks'][name] = {'passed': True, 'seconds': round(time.monotonic()-begin, 2), 'evidence': evidence}
                    print(f'{model}: {name} passed', flush=True)
                except Exception as error:
                    result['checks'][name] = {'passed': False, 'seconds': round(time.monotonic()-begin, 2), 'error': str(error)}
                    print(f'{model}: {name} FAILED: {error}', flush=True)
                (output / (model + '.json')).write_text(json.dumps(result, indent=2))
                if not result['checks'][name]['passed']:
                    raise RuntimeError(f'{name} failed; stopping this experiment')

            def initial():
                response = chat(model, [{'role': 'user', 'content': 'Reply with exactly LOCAL_BACKEND_OK.'}])
                checked_response(response, 'LOCAL_BACKEND_OK')
                return response
            check('chat', initial)

            def speed():
                samples = []
                result['generation_gpu_telemetry'] = []
                stop = threading.Event()
                monitor = threading.Thread(target=monitor_gpu, args=(stop, result['generation_gpu_telemetry']), daemon=True)
                monitor.start()
                try:
                    for _ in range(2):
                        response = chat(model, [{'role': 'user', 'content':
                            'Write a detailed practical maintenance checklist for a desktop computer. '
                            'Cover dust cleaning, backups, updates, cooling, disk health, and diagnostics. '
                            'Write at least 400 words.'}], max_tokens=128, cache_prompt=False,
                            temperature=SPEED_TEMPERATURE)
                        assert response['timings']['predicted_n'] >= 100, 'Too few generated tokens for comparison'
                        samples.append(response)
                finally:
                    stop.set()
                    monitor.join(timeout=5)
                rates = [format(r['timings']['predicted_per_second'], '.1f') + ' t/s' for r in samples]
                print(f'{model}: generation ' + ', '.join(rates), flush=True)
                return samples
            check('speed', speed)
            for latency_target in latency_tokens or []:
                def latency():
                    filler = 'This is filler text used to verify that the attention cache remains stable.\n'
                    per_line = len(api('/tokenize', {'content': filler * 100})['tokens']) / 100
                    target = min(latency_target, profile['context'] - 2048)
                    secret = 'LOCAL-LATENCY-OK-7429'
                    prompt = f'The verification passphrase is {secret}.\n' + filler * max(1, int((target - 150) / per_line)) + '\nReturn only the verification passphrase from the beginning of this message.'
                    body = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                            'temperature': 0, 'seed': 42, 'max_tokens': 256,
                            'stream': True, 'stream_options': {'include_usage': True}, 'cache_prompt': False}
                    request = urllib.request.Request(f'http://127.0.0.1:{PORT}/v1/chat/completions',
                        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
                    started = time.monotonic()
                    record = {'target_prompt_tokens': target, 'first_generated_seconds': None,
                              'first_visible_seconds': None, 'content': '', 'memory_before': memory()}
                    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                        for line in response:
                            if time.monotonic() - started > REQUEST_TIMEOUT:
                                raise TimeoutError('Streaming check exceeded its total time budget')
                            if not line.startswith(b'data: '):
                                continue
                            data = line[6:].strip()
                            if data == b'[DONE]':
                                break
                            event = json.loads(data)
                            if event.get('error'):
                                raise RuntimeError(str(event['error']))
                            for choice in event.get('choices', []):
                                delta = choice.get('delta', {})
                                if any(delta.get(k) for k in ('content', 'reasoning_content', 'reasoning')) and record['first_generated_seconds'] is None:
                                    record['first_generated_seconds'] = round(time.monotonic() - started, 3)
                                if delta.get('content'):
                                    if record['first_visible_seconds'] is None:
                                        record['first_visible_seconds'] = round(time.monotonic() - started, 3)
                                    record['content'] += delta['content']
                            for field in ('timings', 'usage'):
                                if event.get(field):
                                    record[field] = event[field]
                    record['total_seconds'] = round(time.monotonic() - started, 3)
                    record['memory_after'] = memory()
                    assert secret in record['content'], 'Streaming retrieval returned an incorrect passphrase'
                    print(f'{model}: first generated token {record["first_generated_seconds"]}s; first visible text {record["first_visible_seconds"]}s', flush=True)
                    return record
                check(f'latency_{latency_target}', latency)
            if speed_only:
                result['success'] = True
                return result

            def tools():
                tool = {'type': 'function', 'function': {'name': 'local_echo',
                    'description': 'Echo the supplied text.', 'parameters': {'type': 'object',
                    'properties': {'text': {'type': 'string'}}, 'required': ['text']}}}
                messages = [{'role': 'user', 'content': 'Call local_echo with text LOCAL_TOOL_OK. After the tool responds, reply with its returned text.'}]
                response = chat(model, messages, tools=[tool],
                    tool_choice={'type': 'function', 'function': {'name': 'local_echo'}})
                msg = response['choices'][0]['message']
                calls = msg.get('tool_calls', [])
                assert calls and calls[0]['function']['name'] == 'local_echo', 'Missing requested tool call'
                assert json.loads(calls[0]['function']['arguments'])['text'] == 'LOCAL_TOOL_OK'
                follow = chat(model, messages + [msg, {'role': 'tool', 'tool_call_id': calls[0]['id'],
                    'content': 'LOCAL_TOOL_OK'}], tools=[tool])
                checked_response(follow, 'LOCAL_TOOL_OK')
                return {'call': response, 'followup': follow}
            check('tool_round_trip', tools)

            def context():
                target = min(long_tokens, profile['context'] - 2048)
                filler = 'This is filler text used to verify that the attention cache remains stable.\n'
                per_line = len(api('/tokenize', {'content': filler * 100})['tokens']) / 100
                count = int((target - 150) / per_line)
                secret = 'LOCAL-CONTEXT-OK-7429'
                prompt = f'The verification passphrase is {secret}.\n' + filler * count + '\nReturn only the verification passphrase from the beginning of this message.'
                print(f'{model}: processing approximately {target:,} prompt tokens', flush=True)
                response = chat(model, [{'role': 'user', 'content': prompt}], cache_prompt=False)
                result['long_prompt_response'] = response
                checked_response(response, secret)
                assert response['usage']['prompt_tokens'] >= target - 512, 'Unexpectedly short prompt'
                return response
            check('long_prompt', context)
            result['memory_after_checks'] = memory()
            result['gpu_after_checks'] = gpu()
            result['success'] = all(c['passed'] for c in result['checks'].values())
    except Exception as error:
        result['success'] = False
        result['error'] = str(error)
        print(f'{model}: FAILED: {error}', flush=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        result['memory_after_unload'] = memory()
        (output / (model + '.json')).write_text(json.dumps(result, indent=2))
    return result

def main():
    global REQUEST_TIMEOUT
    global SPEED_TEMPERATURE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models', nargs='*')
    parser.add_argument('--long-tokens', type=int, default=21000)
    parser.add_argument('--context', type=int, help='Test an alternate context without changing saved presets')
    parser.add_argument('--speed-only', action='store_true', help='Only check basic chat and two generation samples')
    parser.add_argument('--request-timeout', type=int, default=600)
    parser.add_argument('--speed-temperature', type=float, default=0.0)
    parser.add_argument('--latency-tokens', type=int, nargs='+', default=[], help='Also measure streaming response latency at the specified prompt lengths')
    parser.add_argument('--option', action='append', default=[], metavar='NAME=VALUE',
                        help='Override a server option for this experiment; repeatable')
    args = parser.parse_args()
    REQUEST_TIMEOUT = args.request_timeout
    SPEED_TEMPERATURE = args.speed_temperature
    stack = json.loads((ROOT / 'config' / 'stack.json').read_text())
    profiles = json.loads((ROOT / 'config' / 'selected-profiles.json').read_text())
    by_id = {p['id']: p for p in profiles}
    order = args.models or list(by_id)
    config = configparser.ConfigParser(interpolation=None)
    config.read_string('[metadata]\n' + (ROOT / 'config' / 'models.ini').read_text())
    output = ROOT / 'reports' / 'benchmarks' / ('model-tests-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    output.mkdir(parents=True)
    print('Results: ' + str(output), flush=True)
    print('Memory: ' + json.dumps(memory()), flush=True)
    results = []
    for name in order:
        profile = dict(by_id[name])
        profile['options'] = dict(profile.get('options', {}))
        if args.context:
            profile['context'] = args.context
        for override in args.option:
            key, value = override.split('=', 1)
            profile['options'][key] = value
        results.append(run(profile, dict(config['*']), ROOT / stack['runtime'], output, args.long_tokens, args.speed_only, args.latency_tokens))
        (output / 'summary.json').write_text(json.dumps([{
            'model': r['model'], 'success': r['success'], 'checks': {
                k: v['passed'] for k, v in r['checks'].items()}, 'error': r.get('error')
            } for r in results], indent=2))
    print('Finished: ' + str(output), flush=True)
    if any(not result.get('success') for result in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
