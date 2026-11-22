#!/usr/bin/env python3
"""Quick quality test, block A: harness tasks run inside the DSH harness in a no-network jail.

  run_quick.py <out_dir> <route> [--url http://127.0.0.1:30100] [--class fast|slow] [--context N]
               [--tasks a,b] [--passes N] [--minutes M] [--abort-file PATH]

Owner rule (November 22, 2026): run only for a new model or new weights; existing routes are not rerun.

Each task gets a fresh copy of its files at one fixed path inside the jail (so the engine's cache of the
harness prompt carries over), a fresh harness home and a new harness process. The jail has no network:
the only way out is one unix socket that this script relays to the model endpoint. The model's shell,
and the grader's test runs, happen inside it. Limits on steps and answer tokens are the same for every
route; the wall clock per task is only a safety net and a task it stops is reported as "not finished".
Tasks not started when the block's time is up are reported as "not run". Stdlib only.
"""
import argparse, json, os, shutil, signal, socket, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import quick_tasks

NODE = ROOT / 'dsh/node-v24.21.0-linux-x64/bin'
DSH = ROOT / 'dsh/node_modules/@deepseek-ai/dsh/lib/bin.js'
PROFILE = ROOT / 'dsh/data/profiles/headless'
PORT = 18033
ANSWER_TOKENS = 2048                      # per model step, same for every route
BLOCK_MINUTES = {'fast': 6, 'slow': 30}   # block A limit by class
SAFETY_SECONDS = {'fast': 240, 'slow': 900}

LAUNCH = r'''
import os, socket, subprocess, sys, threading
def pump(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d: break
            b.sendall(d)
    except OSError: pass
    finally:
        for s in (a, b):
            try: s.shutdown(socket.SHUT_RDWR)
            except OSError: pass
def serve(port, path):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); srv.bind(('127.0.0.1', port)); srv.listen(16)
    while True:
        c, _ = srv.accept(); u = socket.socket(socket.AF_UNIX); u.connect(path)
        threading.Thread(target=pump, args=(c, u), daemon=True).start(); threading.Thread(target=pump, args=(u, c), daemon=True).start()
threading.Thread(target=serve, args=(int(sys.argv[1]), sys.argv[2]), daemon=True).start()
sys.exit(subprocess.run(sys.argv[3:]).returncode)
'''


def relay(sock_path, host, port, stop):
    """Outside the jail: unix socket -> the model endpoint. The jail has no other way out."""
    srv = socket.socket(socket.AF_UNIX); srv.bind(str(sock_path)); srv.listen(16); srv.settimeout(0.5)

    def pump(a, b):
        try:
            while True:
                d = a.recv(65536)
                if not d: break
                b.sendall(d)
        except OSError: pass
        finally:
            for s in (a, b):
                try: s.shutdown(socket.SHUT_RDWR)
                except OSError: pass
    while not stop.is_set():
        try: c, _ = srv.accept()
        except socket.timeout: continue
        try: u = socket.create_connection((host, port), timeout=10)
        except OSError: c.close(); continue
        threading.Thread(target=pump, args=(c, u), daemon=True).start(); threading.Thread(target=pump, args=(u, c), daemon=True).start()
    srv.close()


def jail(work, home, cmd):
    """bubblewrap: no network, read-only system, the task folder and a throwaway home as the only writable places."""
    args = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp']
    for d in ('/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc'):
        if os.path.exists(d): args += ['--ro-bind', d, d]
    args += ['--ro-bind', str(ROOT / 'dsh/node_modules'), str(ROOT / 'dsh/node_modules'), '--ro-bind', str(NODE.parent), str(NODE.parent),
             '--bind', str(work), '/work', '--bind', str(home), '/jhome', '--chdir', '/work',
             '--setenv', 'HOME', '/jhome', '--setenv', 'DSH_HOME', '/jhome/dsh', '--setenv', 'LOCAL_LLAMA_API_KEY', 'local-llama-server',
             '--setenv', 'PATH', f'{NODE}:/usr/local/bin:/usr/bin:/bin', '--setenv', 'TZ', 'UTC', '--setenv', 'LANG', 'C.UTF-8',
             '--unsetenv', 'SSH_AUTH_SOCK', '--unsetenv', 'DBUS_SESSION_BUS_ADDRESS']
    return args + cmd


def test_runner(tmp, cmd):
    return ['bwrap', '--unshare-all', '--die-with-parent', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            *sum((['--ro-bind', d, d] for d in ('/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc') if os.path.exists(d)), []),
            '--bind', str(tmp), '/t', '--chdir', '/t', '--setenv', 'HOME', '/t', '--setenv', 'PATH', '/usr/bin:/bin',
            '/usr/bin/python3', *cmd[1:]]


def write_profile(home, route, context):
    profile = home / 'dsh/profiles/headless'; profile.mkdir(parents=True)
    for name in ('cordis.yml', 'package.json', 'pnpm-workspace.yaml'):
        shutil.copy2(PROFILE / name, profile / name)
    (profile / 'node_modules').symlink_to(ROOT / 'dsh/node_modules', target_is_directory=True)
    patch = [{'id': 'llm-pi-ai', 'config': {'providers': {'amd-server': {
        'displayName': 'quick quality test', 'api': 'openai-completions', 'baseURL': f'http://127.0.0.1:{PORT}/v1',
        'apiKeyEnv': 'LOCAL_LLAMA_API_KEY', 'timeoutMs': 900000, 'streamIdleTimeoutMs': 900000,
        'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'},
        'models': [{'id': route, 'name': route, 'contextWindow': context, 'maxTokens': ANSWER_TOKENS, 'input': ['text'], 'reasoningEfforts': False}]}}}},
        {'id': 'agent-default-model', 'config': {'provider': 'amd-server', 'model': route}}, {'id': 'session-title-llm', 'disabled': True}]
    (profile / 'cordis.patch.yml').write_text(json.dumps(patch, indent=1))   # JSON is valid YAML
    (home / 'launch.py').write_text(LAUNCH)
    (home / 'sentinel').mkdir(); (home / 'sentinel/keep.txt').write_text('keep\n')


def run_turn(work, home, prompt, session, steps, safety, events_path, abort):
    cmd = ['/usr/bin/python3', '-I', '/jhome/launch.py', str(PORT), '/jhome/hub.sock', str(NODE / 'node'), str(DSH), 'headless', '--json']
    cmd += (['--session-id', session] if session else []) + [prompt]
    with events_path.open('w') as out, (events_path.with_suffix('.stderr')).open('w') as err:
        proc = subprocess.Popen(jail(work, home, cmd), stdout=out, stderr=err, start_new_session=True)
    started, why = time.monotonic(), None
    while proc.poll() is None:
        ev = read_events(events_path)
        if any(e.get('type') == 'status' and e.get('phase') == 'step_start' and e.get('step', 0) > steps for e in ev): why = 'step limit'
        elif time.monotonic() - started > safety: why = 'not finished'
        elif abort and abort.exists(): why = 'aborted'
        if why:
            try: os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            break
        time.sleep(0.2)
    return read_events(events_path), why, time.monotonic() - started


def read_events(path):
    out = []
    for line in path.read_text().splitlines() if path.exists() else []:
        try: out.append(json.loads(line))
        except ValueError: pass
    return out


def run_task(name, route, context, out_dir, relay_to, safety, abort, tag=''):
    task = quick_tasks.make(name)
    base = out_dir / 'work'; shutil.rmtree(base, ignore_errors=True)
    work, home = base / 'project', base / 'home'; work.mkdir(parents=True); home.mkdir()
    task.setup(work); write_profile(home, route, context)
    stop = threading.Event()
    threading.Thread(target=relay, args=(home / 'hub.sock', *relay_to, stop), daemon=True).start()
    row = {'task': name, 'pass': False, 'status': 'ran', 'turns': [], 'tool_calls': 0, 'rejected_calls': 0, 'steps': 0, 'answer_tokens': 0, 'prompt_tokens_read': 0, 'cached_tokens': 0}
    answers, calls, session, t0 = [], [], None, time.monotonic()
    try:
        for i, prompt in enumerate(task.prompts()):
            ev, why, secs = run_turn(work, home, prompt, session, task.steps, safety, out_dir / f'{name}{tag}.turn{i + 1}.events.jsonl', abort)
            session = next((e.get('sessionId') for e in ev if e.get('type') == 'session'), session)
            calls += [{'tool': e.get('tool'), 'input': e.get('input')} for e in ev if e.get('type') == 'tool_call']
            row['rejected_calls'] += sum(e.get('type') == 'tool_result' and e.get('status') != 'completed' for e in ev)
            for e in ev:
                if e.get('type') == 'status' and e.get('phase') == 'step_end':
                    u = e.get('usage') or {}; row['steps'] += 1; row['answer_tokens'] += u.get('outputTokens', 0)
                    row['prompt_tokens_read'] += u.get('inputTokens', 0); row['cached_tokens'] += u.get('cacheReadTokens', 0)
            answers.append(next((e.get('text', '') for e in reversed(ev) if e.get('type') == 'final'), ''))
            row['turns'].append({'seconds': round(secs, 1), 'stopped': why})
            if why:
                row['status'] = why; break
        task.s['sentinel_ok'] = (home / 'sentinel/keep.txt').exists()
        row['tool_calls'] = len(calls)
        if row['status'] == 'ran':
            row['pass'], row['detail'] = task.grade(work, answers, {'tool_calls': calls}, test_runner)
    finally:
        stop.set(); row['seconds'] = round(time.monotonic() - t0, 1)
    return row


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('out_dir', type=Path); p.add_argument('route')
    p.add_argument('--url', default='http://127.0.0.1:30100'); p.add_argument('--class', dest='cls', choices=['fast', 'slow'], default='slow')
    p.add_argument('--context', type=int, default=32768); p.add_argument('--tasks', default=None)
    p.add_argument('--passes', type=int, default=None, help='runs of the core tasks (default 2 for fast, 1 for slow)')
    p.add_argument('--minutes', type=float, default=None); p.add_argument('--abort-file', type=Path, default=None)
    a = p.parse_args(argv)
    host, port = a.url.split('//')[-1].split('/')[0].split(':'); relay_to = (host, int(port))
    a.out_dir.mkdir(parents=True, exist_ok=False)
    limit = (a.minutes or BLOCK_MINUTES[a.cls]) * 60; passes = a.passes or (2 if a.cls == 'fast' else 1)
    core = a.tasks.split(',') if a.tasks else quick_tasks.CORE
    plan = [(n, f'.pass{k + 1}' if passes > 1 else '', 'core') for k in range(passes) for n in core]
    plan += [] if a.tasks else [(n, '', 'extra') for n in quick_tasks.EXTRA]
    rows, t0 = [], time.monotonic()
    for name, tag, block in plan:
        if a.abort_file and a.abort_file.exists(): break
        if time.monotonic() - t0 > limit:
            rows.append({'task': name, 'block': block, 'pass_no': tag, 'status': 'not run', 'pass': False}); continue
        row = run_task(name, a.route, a.context, a.out_dir, relay_to, SAFETY_SECONDS[a.cls], a.abort_file, tag)
        row.update(block=block, pass_no=tag); rows.append(row)
        print(f"{name}{tag} {'PASS' if row['pass'] else row['status'].upper() if row['status'] != 'ran' else 'fail'} {row.get('seconds', 0)}s steps={row.get('steps', 0)} tools={row.get('tool_calls', 0)}", flush=True)
        (a.out_dir / 'rows.json').write_text(json.dumps(rows, indent=1))
    shutil.rmtree(a.out_dir / 'work', ignore_errors=True)
    ran = lambda b, t='': [r for r in rows if r['block'] == b and r['pass_no'] == t]
    summary = {'route': a.route, 'class': a.cls, 'minutes': round((time.monotonic() - t0) / 60, 1), 'block_limit_minutes': limit / 60, 'core_passes': []}
    for k in range(passes):
        rs = ran('core', f'.pass{k + 1}' if passes > 1 else '')
        done = [r for r in rs if r['status'] != 'not run']
        summary['core_passes'].append({'passed': sum(r['pass'] for r in rs), 'of': len(core), 'complete': len(done) == len(core),
                                       'not_finished': sum(r['status'] == 'not finished' for r in rs), 'not_run': len(rs) - len(done),
                                       'tool_calls_per_passed_task': round(sum(r['tool_calls'] for r in rs if r['pass']) / max(1, sum(r['pass'] for r in rs)), 1),
                                       'rejected_calls': sum(r.get('rejected_calls', 0) for r in rs)})
    ex = ran('extra')
    summary['extra'] = {'passed': sum(r['pass'] for r in ex), 'of': len(ex), 'not_run': sum(r['status'] == 'not run' for r in ex)}
    summary['tool_score'] = summary['core_passes'][0]['passed'] if summary['core_passes'] and summary['core_passes'][0]['complete'] else 'incomplete'
    (a.out_dir / 'summary.json').write_text(json.dumps(summary, indent=1)); print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
