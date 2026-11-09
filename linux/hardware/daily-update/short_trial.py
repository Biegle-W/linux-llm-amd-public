"""One owned, guarded DSH read-tool round trip; no benchmark or retry."""
from pathlib import Path
import ast
import datetime
import hashlib
import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import yaml

W = Path(sys.argv[1]).resolve()
R = Path(__file__).resolve().parents[2]

sys.path[:0] = [str(W), str(R / 'dsh')]

from prevention_guard import durable
from inference_swap import WorkerSwapGuard
from streaming_memory import scope_properties, scope_limits
from short_cases import check_case as check_config
from moe_memory import host_memory

LABEL = 'short-check'
D = W / 'result'
D.mkdir(exist_ok=False)
cfg = json.loads((W / 'profile.private.json').read_text())
check_config(cfg, W)
guard = WorkerSwapGuard()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
proc = harness = proxy = None
result = {'status': 'starting', 'scope': 'one short DSH tool round trip only',
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'requests': [], 'production_changed': False}

from short_test_timing import StageBudget
_budget_spec=json.loads((W/(LABEL+'.stage.private.json')).read_text())
budget=StageBudget(time.monotonic(),_budget_spec['timeout'],_budget_spec['watchdog_limits']['cleanup_seconds'])

def phase(name, **extra):
    now = time.monotonic()
    with (D/'phase-events.private.jsonl').open('a') as f:f.write(json.dumps({'phase':name,'monotonic':now,**extra})+'\n')
    durable(Path(os.environ.get('LOCAL_LLM_PROGRESS_PATH',str(W / (LABEL + '.progress.private.json')))),
            {'phase': name, 'phase_started': now, 'last_output': now, **extra})

def save():
    durable(D / 'result.private.json', result)

def halt(*unused):
    raise SystemExit(143)

for sig in [signal.SIGTERM, signal.SIGINT]:
    signal.signal(sig, halt)

class ProgressProxy(http.server.BaseHTTPRequestHandler):
    def log_message(self, *unused):
        pass

    def do_POST(self):
        if self.path != '/v1/chat/completions' or len(result['requests']) >= 2:
            self.send_error(409, 'Exactly two model steps are allowed')
            return
        row = {'index': len(result['requests']) + 1, 'status': 'starting'}
        result['requests'].append(row)
        started = time.monotonic()
        phase('prefill', request_started=started)
        try:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert body.get('stream') is True
            body['max_tokens'] = min(body.get('max_tokens', 256), 256)
            body['chat_template_kwargs'] = {'enable_thinking': False}
            if cfg['backend'] in ('maya','strata'):body['strata_checkpoint'] = False
            else:body.pop('strata_checkpoint',None)
            row['max_tokens'] = body['max_tokens']
            row['input_bytes'] = len(json.dumps(body).encode())
            row['message_count'] = len(body.get('messages', []))
            row['tool_count'] = len(body.get('tools', []))
            durable(D / ('request-' + str(row['index']) + '.private.json'), body)
            save()
            row['input_sha256'] = hashlib.sha256(json.dumps(body).encode()).hexdigest()
            req = urllib.request.Request('http://127.0.0.1:18032/v1/chat/completions',
                json.dumps(body).encode(), {'Content-Type': 'application/json'})
            with guard.inference(proc), opener.open(req, timeout=budget.timeout_seconds()) as response:
                self.send_response(response.status)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Connection', 'close')
                self.end_headers()
                first = None
                chunks = 0
                for raw in response:
                    guard.check()
                    if raw.startswith(b'data:') and raw[5:].strip() != b'[DONE]':
                        event = json.loads(raw[5:])
                        if event.get('usage'):
                            row['usage'] = event['usage']
                        for choice in event.get('choices', []):
                            delta = choice.get('delta', {})
                            if any(delta.get(k) for k in ['content', 'reasoning_content', 'tool_calls']):
                                now = time.monotonic()
                                if first is None:
                                    first = now
                                    row['TTFT_seconds'] = now - started
                                    save()
                                chunks += 1
                                row['output_chunks'] = chunks
                                durable(Path(os.environ.get('LOCAL_LLM_PROGRESS_PATH',str(W / (LABEL + '.progress.private.json')))),
                                    {'phase': 'decode', 'phase_started': first,
                                     'request_started': started, 'decode_started': first, 'last_output': now,
                                     'output_chunks': chunks})
                    self.wfile.write(raw)
                    self.wfile.flush()
            row.update(status='completed', output_chunks=chunks,
                       TTFT_seconds=first - started if first else None,
                       elapsed_seconds=time.monotonic() - started)
            phase('idle')
        except Exception as exc:
            row.update(status='failed', error=type(exc).__name__ + ': ' + str(exc), elapsed_seconds=time.monotonic()-started)
        finally:
            save()

try:
    phase('loading')
    save()
    started = time.monotonic()
    with (D / 'service.private.log').open('w') as log:
        proc = guard.spawn(['systemd-run', '--user', '--scope', '--quiet',
            *scope_properties(cfg), '--property=RuntimeMaxSec='+str(_budget_spec['timeout'])+'s',
            str(R/'strata/.venv/bin/python'), '-B', str(R/'hardware/daily-update/case_server.py'), str(W)], stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, expected_memory_limits=scope_limits(cfg))
    while True:
        guard.check()
        if proc.poll() is not None:
            raise RuntimeError('Candidate exited before ready; no retry')
        try:
            with opener.open('http://127.0.0.1:18032/health', timeout=1) as f:
                health = json.load(f)
            from server_ready import server_ready
            ready_path=W/'backend-ready.private.json'
            attestation=json.loads(ready_path.read_text()) if ready_path.exists() else None
            if server_ready(health,cfg['model_name'],attestation):
                break
        except (OSError, ValueError):
            pass
        if time.monotonic() - started > _budget_spec['watchdog_limits']['load_seconds']:
            raise TimeoutError(str(_budget_spec['watchdog_limits']['load_seconds'])+'-second loading deadline')
        time.sleep(.25)
    result.update(load_seconds=time.monotonic() - started, owned_unit=guard.watch.owner.unit)

    from strata_memory import vram_snapshot
    result['normal_startup_VRAM']=vram_snapshot()
    if cfg.get('normal_native_startup'):
        import resource_policy  # owner headroom policy; the pre-November 3 6 GiB floor was dropped on November 9
        assert len(result['normal_startup_VRAM'])==2 and min(x['free'] for x in result['normal_startup_VRAM'])>=resource_policy.VRAM_RESERVE_BYTES,'Per-card startup VRAM headroom below the owner policy'
    guard.ready(proc, phase='idle')
    phase('idle')
    save()
    print('READY', result['load_seconds'], flush=True)
    proxy = http.server.ThreadingHTTPServer(('127.0.0.1', 18033), ProgressProxy)
    threading.Thread(target=proxy.serve_forever, daemon=True).start()
    home = D / 'harness-home'
    profile = home / 'profiles/headless'
    profile.mkdir(parents=True)
    for name in ['cordis.yml', 'package.json', 'pnpm-workspace.yaml']:
        shutil.copy2(R / 'dsh/data/profiles/headless' / name, profile / name)
    (profile / 'node_modules').symlink_to(R / 'dsh/node_modules', target_is_directory=True)
    patch = [{'id': 'llm-pi-ai', 'config': {'providers': {'amd-server': {
        'displayName': 'AMD isolated USERPTR trial', 'api': 'openai-completions',
        'baseURL': 'http://127.0.0.1:18033/v1', 'apiKeyEnv': 'LOCAL_LLAMA_API_KEY',
        'timeoutMs': budget.timeout_ms(), 'streamIdleTimeoutMs': budget.timeout_ms(),
        'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'},
        'models': [{'id': cfg['model_name'], 'name': cfg['model_name'], 'contextWindow': cfg.get('context',32768),
                    'maxTokens': 256, 'input': ['text'], 'reasoningEfforts': False}]}}}},
        {'id': 'agent-default-model', 'config': {'provider': 'amd-server', 'model': cfg['model_name']}},
        {'id': 'session-title-llm', 'disabled': True}]
    (profile / 'cordis.patch.yml').write_text(yaml.safe_dump(patch, sort_keys=False))
    fixture = D / 'fixture'
    fixture.mkdir()
    marker = 'DSH_TOOL_' + os.urandom(8).hex()
    target = fixture / 'marker.txt'
    target.write_text(marker + '\n')
    task = f'Use the read tool exactly once to read this exact file: {target}. Then reply with only the exact marker from the file. Do not use glob or any other tool. Do not perform any other task.'
    env = dict(os.environ, DSH_HOME=str(home), LOCAL_LLAMA_API_KEY='local-llama-server')
    env['PATH'] = str(R / 'dsh/node-v24.21.0-linux-x64/bin') + ':' + env['PATH']
    events_path = D / 'tool-events.private.jsonl'
    with events_path.open('w') as out, (D / 'tool-stderr.private.log').open('w') as err:
        harness = subprocess.Popen([str(R / 'dsh/node-v24.21.0-linux-x64/bin/node'),
            str(R / 'dsh/node_modules/@deepseek-ai/dsh/lib/bin.js'), 'headless', '--json', task],
            cwd=fixture, env=env, stdout=out, stderr=err, start_new_session=True)
    started = time.monotonic()
    while harness.poll() is None:
        guard.check()
        events = []
        for line in events_path.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        assert sum(e.get('type') == 'tool_call' for e in events) <= 1, 'Extra tool call'
        assert not any(e.get('type') == 'status' and e.get('phase') == 'step_start' and e.get('step', 0) > 2 for e in events), 'Extra model step'
        budget.check()
        time.sleep(.15)
    from tool_result import parse_result
    tool = {'exit_code': harness.returncode}
    passed = parse_result(tool, events_path, marker)
    result['tool'] = tool
    assert passed, 'Strict DSH tool gate failed; no retry'
    from await_requests import await_completed
    await_completed(result['requests'], 2, guard.check)
    result['status'] = 'passed-one-short-DSH-check'
except BaseException as exc:
    result.update(status='failed', error=type(exc).__name__ + ': ' + str(exc))
    raise
finally:
    save()
    phase('cleanup')
    if harness is not None and harness.poll() is None:
        os.killpg(harness.pid, signal.SIGTERM)
        try:
            harness.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(harness.pid, signal.SIGKILL)
            harness.wait(timeout=2)
    if proxy is not None:
        proxy.shutdown()
        proxy.server_close()
    try:
        if proc is not None:
            guard.stop(proc)
            result['owned_unload_requested'] = True
    finally:
        result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()
        print(json.dumps(result), flush=True)
