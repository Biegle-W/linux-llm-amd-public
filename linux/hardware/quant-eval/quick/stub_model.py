#!/usr/bin/env python3
"""A scripted stand-in for a model endpoint, used only to test the quick-test runner without running any route.
It answers the no-tool arithmetic task directly and drives one bash tool call for the failed-command task."""
import http.server, json, re, sys

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        body = json.dumps({'object': 'list', 'data': [{'id': 'stub', 'object': 'model'}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        msgs = req['messages']; text = lambda m: m['content'] if isinstance(m['content'], str) else ' '.join(p.get('text', '') for p in m['content'] or [])
        user = '\n'.join(text(m) for m in msgs if m['role'] == 'user'); tool = [text(m) for m in msgs if m['role'] == 'tool']
        delta, finish = {'role': 'assistant'}, 'stop'
        m = re.search(r'What is (\d+) \* (\d+) \+ (\d+)', user)
        if m: delta['content'] = str(int(m[1]) * int(m[2]) + int(m[3]))
        elif 'tools/build.py' in user and not tool:
            bash = next(t['function'] for t in req.get('tools', []) if t['function']['name'] == 'bash')
            props = bash['parameters']['properties']; key = 'command' if 'command' in props else list(props)[0]
            cmd = 'python3 tools/build.py --profile release; (python3 -c "import socket;socket.create_connection((\'1.1.1.1\',53),2)" 2>/dev/null && echo NET-OPEN || echo NET-CLOSED); echo HOSTHOME=$(ls -A /home/*/ 2>&1 | xargs); echo HOME=$HOME'
            delta['tool_calls'] = [{'index': 0, 'id': 'call_stub1', 'type': 'function', 'function': {'name': 'bash', 'arguments': json.dumps({**{k: 'run the build' for k in bash['parameters'].get('required', []) if props[k].get('type') == 'string'}, key: cmd})}}]; finish = 'tool_calls'
        elif tool:
            b = re.search(r'build-\d{6}', tool[-1]); delta['content'] = b[0] if b else 'no build id'
        else: delta['content'] = 'stub has no script for this task'
        chunks = [{'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]}, {'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}]},
                  {'choices': [], 'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}]
        if not req.get('stream'):
            body = json.dumps({'id': 'stub', 'object': 'chat.completion', 'model': req.get('model'), 'choices': [{'index': 0, 'message': delta, 'finish_reason': finish}], 'usage': chunks[2]['usage']}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Connection', 'close'); self.end_headers()
        for c in chunks:
            c.update(id='stub', object='chat.completion.chunk', created=0, model=req.get('model'))
            self.wfile.write(b'data: ' + json.dumps(c).encode() + b'\n\n')
        self.wfile.write(b'data: [DONE]\n\n'); self.wfile.flush()

if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
