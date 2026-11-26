#!/usr/bin/env python3
"""Quick quality test, block G: gBench's Golden Set as a serving check for a new route.

  run_golden.py <out_dir> <route> --tokenizer <HF id or local tokenizer folder>
                [--url http://127.0.0.1:30100] [--class fast|slow] [--minutes M] [--abort-file PATH] [--engine-check]

--engine-check runs only the six chat-template and tool-call cases (FIRST below). That is the gBench part of
the engine-update check both servers share (benchmarks/shared/README.md); NVIDIA runs the same six cases with
scripts/gbench_template_check.py.

Owner rule (November 22, 2026): run only for a new model or new weights; existing routes are not rerun.

Block G runs first in the quick test. Its 16 fixed cases (about 11 on a text-only route) check that the
route's chat template, tool-call parser and plain answers work through the hub; the four chat-template
cases come in pairs whose plain-turn twin tells a broken template from a weak model. gBench 0.5.0.post1 is
pinned in ../gbench/.venv (not committed; see README.md for the install line).

What this wrapper adds, and why:
- Time limit. Block G gets 2 minutes on a fast route and 5 on a slow one, out of the quick test's 15 and 60.
  The clock starts after the warm-up. A case starts only if the slowest case so far still fits in the time
  left; one that does not is "not run", never wrong (a local relay answers it with an error this script
  recognises). Chat-template and tool cases run first. Time the block does not use goes to the next blocks.
- Thinking off. gBench sends no thinking switch and caps answers at 512 tokens, so a model that thinks by
  default could spend them all thinking. The relay adds the same switch the other quick-test blocks send.
- Request timeout. gBench waits 30 s per request, too short for 512 tokens on a slow route, so the launcher
  raises it to 60 s (fast) or 150 s (slow). A warm-up request first loads the route, outside the clock.
Stdlib only; gBench runs in its own venv.
"""
import argparse, http.client, http.server, json, os, subprocess, sys, threading, time
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
GB_PY = HERE.parent / 'gbench/.venv/bin/python'
GB_VERSION = '0.5.0.post1'
PORT = 18034
BLOCK_MINUTES = {'fast': 2, 'slow': 5}
REQUEST_TIMEOUT = {'fast': 60, 'slow': 150}
WARMUP_TIMEOUT = 1800                 # a cold load of the largest route; outside the block's clock
THINKING_OFF = {'enable_thinking': False, 'thinking': False}   # as ../pub/run_pub.py sends
LIMIT_REASON = 'golden block time limit reached'
HOLD_REASON = 'golden block stopped: GPU hold file present'
FIRST = ['template_tool_response', 'template_tool_response_twin', 'template_multi_turn',
         'template_multi_turn_twin', 'function_call_single', 'tool_call_minimal']
PAIRS = [('template_tool_response', 'template_tool_response_twin'), ('template_multi_turn', 'template_multi_turn_twin')]
KNOWN_BUGS = {'safety_boundary': ('’', 'gBench 0.5.0 misreads refusals written with a curly apostrophe '
                                  '(open fix: github.com/google-deepmind/gbench/pull/13); read the answer by hand')}

LAUNCH = r'''
import sys
from gbench.runners import golden
golden.GoldenBenchmarkRunner._request_json.__defaults__ = (int(sys.argv[1]),)
sys.argv = ['gbench'] + sys.argv[2:]
from gbench.cli import main
sys.exit(main())
'''


class Relay(http.server.ThreadingHTTPServer):
    """127.0.0.1:PORT -> the hub. Adds the thinking-off switch, records each request, refuses after the deadline."""
    daemon_threads = True

    def __init__(self, upstream, deadline, abort_file, timeout):
        super().__init__(('127.0.0.1', PORT), RelayHandler)
        u = urlparse(upstream); self.host, self.port = u.hostname, u.port or 80
        self.deadline, self.abort_file, self.timeout_s = deadline, abort_file, timeout
        self.log, self.lock = [], threading.Lock()


class RelayHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass

    def send(self, code, body, ctype='application/json', reason=None):
        self.send_response(code, reason); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def forward(self, method, body=None):
        s = self.server; c = http.client.HTTPConnection(s.host, s.port, timeout=s.timeout_s + 30)
        try:
            c.request(method, self.path, body=body, headers={'Content-Type': 'application/json'} if body else {})
            r = c.getresponse(); data = r.read(); return r.status, data, r.getheader('Content-Type') or 'application/json'
        finally: c.close()

    def do_GET(self):
        try: self.send(*self.forward('GET')[:2])
        except OSError as e: self.send(502, json.dumps({'error': str(e)}).encode())

    def do_POST(self):
        s = self.server; req = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        with s.lock: longest = max((r.get('seconds', 0) for r in s.log), default=0)
        # Start a case only if the slowest case so far still fits, so the block ends inside its limit.
        stop = HOLD_REASON if s.abort_file and os.path.exists(s.abort_file) else LIMIT_REASON if time.monotonic() + longest > s.deadline else None
        if stop:
            with s.lock: s.log.append({'refused': stop})
            return self.send(400, json.dumps({'error': {'message': stop}}).encode(), reason=stop)
        req.setdefault('chat_template_kwargs', dict(THINKING_OFF))
        t = time.monotonic(); rec = {'max_tokens': req.get('max_tokens'), 'tools': bool(req.get('tools'))}
        try:
            code, data, ctype = self.forward('POST', json.dumps(req).encode())
        except OSError as e:
            rec.update(seconds=round(time.monotonic() - t, 2), error=str(e))
            with s.lock: s.log.append(rec)
            return self.send(504, json.dumps({'error': {'message': str(e)}}).encode())
        rec.update(seconds=round(time.monotonic() - t, 2), status=code)
        try:
            d = json.loads(data); m = (d.get('choices') or [{}])[0]; msg = m.get('message') or {}
            rec.update(completion_tokens=(d.get('usage') or {}).get('completion_tokens'), finish=m.get('finish_reason'),
                       thinking_left_on=not (msg.get('content') or msg.get('tool_calls')) and bool(msg.get('reasoning_content') or msg.get('reasoning')))
        except (ValueError, AttributeError, IndexError): pass
        with s.lock: s.log.append(rec)
        self.send(code, data, ctype)


def warm_up(url, route):
    u = urlparse(url); c = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=WARMUP_TIMEOUT); t = time.monotonic()
    body = {'model': route, 'messages': [{'role': 'user', 'content': 'Reply OK.'}], 'max_tokens': 32, 'temperature': 0,
            'stream': False, 'chat_template_kwargs': dict(THINKING_OFF)}
    try:
        c.request('POST', '/v1/chat/completions', body=json.dumps(body), headers={'Content-Type': 'application/json'})
        r = c.getresponse(); r.read(); ok = r.status == 200
    except OSError: ok = False
    finally: c.close()
    return ok, round(time.monotonic() - t, 1)


def task_ids():
    out = subprocess.run([str(GB_PY), '-c', 'import gbench,os,json;d=os.path.join(os.path.dirname(gbench.__file__),"golden_dataset");'
                          'print(json.dumps(sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))))'], capture_output=True, text=True, check=True)
    ids = json.loads(out.stdout)
    return [t for t in FIRST if t in ids], [t for t in ids if t not in FIRST]


def run_group(out, name, route, tokenizer, tasks, timeout, hard_seconds, extra):
    res = out / 'gbench' / name; before = set(res.glob('*/summary.json')) if res.exists() else set()
    cmd = [str(GB_PY), '-c', LAUNCH, str(timeout), '--golden-only', '--remote-endpoint', f'http://127.0.0.1:{PORT}/v1',
           '--models', route, '--served-model-id', route, '--tokenizer', tokenizer, '--results-dir', str(res),
           '--golden-tasks', *tasks, *extra]
    with open(out / 'gbench.log', 'a') as log:
        try: rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=max(hard_seconds, 30)).returncode
        except subprocess.TimeoutExpired: rc = 'killed'
    new = sorted(set(res.glob('*/summary.json')) - before)
    rows = []
    for f in new:
        for m in json.loads(f.read_text()).get('models', []):
            rows += m.get('task_results', []); meta = {k: m.get(k) for k in ('scoring_version', 'chat_template_leak_check', 'harness_errors')}
    return rc, rows, (meta if new else {})


def summarise(rows, first, rest):
    by = {r['task_id']: r for r in rows}; out = {}
    for t in first + rest:
        r = by.get(t)
        if r is None: out[t] = {'status': 'not_run'}; continue
        st, det = r.get('status'), r.get('details') or ''
        if st == 'error' and (LIMIT_REASON in det or HOLD_REASON in det): st = 'not_run'
        row = {'status': st, 'category': r.get('category')}
        if st in ('failed', 'error'): row['details'] = det[:300]
        bug = KNOWN_BUGS.get(t)
        if st == 'failed' and bug and bug[0] in (r.get('response_text') or ''): row['known_gbench_bug'] = bug[1]
        out[t] = row
    pairs = {}
    for a, b in PAIRS:
        sa, sb = out[a]['status'], out[b]['status']
        pairs[a] = ('healthy' if sa == sb == 'passed' else 'template or parser broken' if sa == 'failed' and sb == 'passed'
                    else 'model cannot answer; template not implicated' if sa == sb == 'failed' else 'incomplete')
    return out, pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out'); ap.add_argument('route'); ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--url', default='http://127.0.0.1:30100'); ap.add_argument('--class', dest='cls', choices=['fast', 'slow'], default='slow')
    ap.add_argument('--minutes', type=float); ap.add_argument('--abort-file'); ap.add_argument('--trust-remote-code', action='store_true')
    ap.add_argument('--engine-check', action='store_true', help='only the six shared template and tool cases')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if not GB_PY.exists(): sys.exit(f'gBench venv missing: {GB_PY} (see README.md)')
    if a.abort_file and os.path.exists(a.abort_file): print('GPU hold present; not started'); return 3
    minutes, timeout = a.minutes or BLOCK_MINUTES[a.cls], REQUEST_TIMEOUT[a.cls]
    first, rest = task_ids()
    if a.engine_check: rest = []

    ok, warm = warm_up(a.url, a.route)
    if not ok:
        (out / 'summary.json').write_text(json.dumps({'route': a.route, 'status': 'warm-up failed', 'warmup_seconds': warm}, indent=1) + '\n')
        print('warm-up failed'); return 2

    t0 = time.monotonic(); deadline = t0 + minutes * 60
    relay = Relay(a.url, deadline, a.abort_file, timeout); threading.Thread(target=relay.serve_forever, daemon=True).start()
    extra = ['--tokenizer-trust-remote-code'] if a.trust_remote_code else []
    rows, meta, rcs = [], {}, []
    try:
        for name, group in (('first', first), ('rest', rest)):
            left = deadline - time.monotonic()
            if left <= 0: break
            rc, r, m = run_group(out, name, a.route, a.tokenizer, group, timeout, left + timeout + 30, extra)
            rows += r; meta = meta or m; rcs.append(rc)
    finally:
        relay.shutdown(); relay.server_close()
    used = round((time.monotonic() - t0) / 60, 2)

    cases, pairs = summarise(rows, first, rest)
    count = lambda s: sum(1 for c in cases.values() if c['status'] == s)
    reqs = [r for r in relay.log if 'refused' not in r]
    summary = {
        'route': a.route, 'class': a.cls, 'engine_check': a.engine_check, 'gbench': GB_VERSION, 'scoring_version': meta.get('scoring_version'),
        'tokenizer': a.tokenizer, 'block_minutes': minutes, 'minutes_used': used, 'within_block': used <= minutes,
        'warmup_seconds': warm, 'request_timeout_seconds': timeout,
        'passed': count('passed'), 'applicable': sum(1 for c in cases.values() if c['status'] not in ('not_applicable', 'not_run')),
        'failed': count('failed'), 'harness_errors': count('error'), 'not_run': count('not_run'), 'not_applicable': count('not_applicable'),
        'template_pairs': pairs, 'cases': cases,
        'requests': {'count': len(reqs), 'refused_after_limit': len(relay.log) - len(reqs),
                     'completion_tokens': sum(r.get('completion_tokens') or 0 for r in reqs),
                     'longest_seconds': max((r.get('seconds', 0) for r in reqs), default=0),
                     'hit_512_cap': sum(1 for r in reqs if r.get('finish') == 'length'),
                     'thinking_left_on': sum(1 for r in reqs if r.get('thinking_left_on'))},
        'chat_template_leak_check_tokenizer': (meta.get('chat_template_leak_check') or {}).get('tokenizer_class'),
        'gbench_exit_codes': rcs,
    }
    (out / 'requests.json').write_text(json.dumps(relay.log, indent=1) + '\n')
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    for t, c in cases.items():
        print(f"{c['status'].upper():15} {t}" + (f"  [{c['known_gbench_bug'][:60]}]" if 'known_gbench_bug' in c else ''))
    print(f"golden: {summary['passed']}/{summary['applicable']} passed, {summary['not_run']} not run, "
          f"{summary['harness_errors']} harness errors; {used} of {minutes} min; warm-up {warm}s; pairs {pairs}")
    return 0 if summary['failed'] == summary['harness_errors'] == summary['not_run'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
