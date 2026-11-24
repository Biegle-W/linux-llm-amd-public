#!/usr/bin/env python3
"""A scripted stand-in endpoint for testing run_golden.py without running any route or using the GPU.

  golden_stub.py <port> <golden_dataset_dir> [--tok-s N] [--pad-tokens N] [--model ID]

It answers each Golden Set case with that case's own reference answer, read at run time from the
installed gBench package (nothing from the case files is stored in this repository). --tok-s makes it
sleep as if it decoded the answer at that speed, and --pad-tokens adds that many tokens to every answer's
simulated length, so the slow-route and worst-case timings can be checked. It also records whether each
request carried the thinking-off switch (X-Stub-Thinking-Off), and --require-thinking-off refuses one without it.
"""
import argparse, http.server, json, sys, time
from pathlib import Path


def load_cases(folder):
    cases = []
    for f in sorted(Path(folder).glob('*.json')):
        d = json.loads(f.read_text())
        msgs = d.get('conversation', {}).get('messages', [])
        last_user = next((m for m in reversed(msgs) if m.get('role') == 'user'), {})
        cases.append((d, text_of(last_user.get('content'))))
    return cases


def text_of(content):
    if isinstance(content, str): return content.strip()
    return ' '.join(p.get('text', '') for p in content or [] if isinstance(p, dict) and p.get('type') == 'text').strip()


def answer(case):
    truth = case.get('golden_truth', {})
    calls = truth.get('expected_tool_calls')
    if calls:
        return {'role': 'assistant', 'content': None, 'tool_calls': [
            {'id': f'call_{i}', 'type': 'function', 'function': {'name': c['name'], 'arguments': json.dumps(c.get('arguments', {}))}}
            for i, c in enumerate(calls)]}, 'tool_calls'
    return {'role': 'assistant', 'content': str(truth.get('canonical_answer', ''))}, 'stop'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('port', type=int); ap.add_argument('dataset')
    ap.add_argument('--tok-s', type=float, default=0); ap.add_argument('--pad-tokens', type=int, default=0)
    ap.add_argument('--model', default='stub')
    ap.add_argument('--require-thinking-off', action='store_true')
    a = ap.parse_args()
    cases = load_cases(a.dataset)

    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'
        def log_message(self, *x): pass
        def reply(self, obj, extra=None, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body)))
            for k, v in (extra or {}).items(): self.send_header(k, v)
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            self.reply({'object': 'list', 'data': [{'id': a.model, 'object': 'model'}]})
        def do_POST(self):
            req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            msgs = req.get('messages', [])
            last_user = next((m for m in reversed(msgs) if m.get('role') == 'user'), {})
            key = text_of(last_user.get('content'))
            match = [c for c, k in cases if k == key]
            if len(match) > 1:   # twins can share a last user turn only if their histories differ
                match = [c for c in match if len(c['conversation']['messages']) == len(msgs)] or match
            if match: msg, finish = answer(match[0])
            else: msg, finish = {'role': 'assistant', 'content': 'OK'}, 'stop'
            n = len((msg.get('content') or json.dumps(msg.get('tool_calls'))).split()) + a.pad_tokens
            cap = int(req.get('max_tokens') or n)
            if n > cap: n, finish = cap, 'length'
            if a.tok_s: time.sleep(n / a.tok_s)
            off = (req.get('chat_template_kwargs') or {}).get('enable_thinking') is False
            if a.require_thinking_off and not off:
                return self.reply({'error': {'message': 'thinking switch missing'}}, code=422)
            self.reply({'id': 'stub', 'object': 'chat.completion', 'model': req.get('model'),
                        'choices': [{'index': 0, 'message': msg, 'finish_reason': finish}],
                        'usage': {'prompt_tokens': 10, 'completion_tokens': n, 'total_tokens': 10 + n}},
                       {'X-Stub-Thinking-Off': str(off)})

    http.server.ThreadingHTTPServer(('127.0.0.1', a.port), H).serve_forever()


if __name__ == '__main__':
    main()
