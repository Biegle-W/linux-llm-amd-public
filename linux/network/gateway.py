#!/usr/bin/env python3
"""Authenticated LAN/Tailscale OpenAI API; inference workers remain on loopback."""
import argparse
import hmac
import http.client
import ipaddress
import json
import signal
import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BACKENDS = {
    'llama': ('models.json', 8080, 'llama.cpp'),
    'sglang': ('sglang-profiles.json', 30000, 'SGLang'),
    'vllm': ('vllm-profiles.json', 30010, 'vLLM'),
    'strata': ('strata-profiles.json', 30020, 'Strata Q3'),
    'maya': ('maya-profiles.json', 30030, 'Maya'),
}
MAX_BODY = 32 * 1024 * 1024
config = {}
token = b''
allowed = []


def catalog():
    models = {}
    for backend, (filename, port, label) in BACKENDS.items():
        path = ROOT / 'dsh' / filename
        if not path.exists():
            continue
        source = json.loads(path.read_text())
        rows = source if isinstance(source, list) else [dict(id=k, **v) for k, v in source.items()]
        for row in rows:
            if not row.get('enabled', backend != 'maya'):
                continue
            if row['id'] in models:
                raise ValueError('Duplicate API model ID')
            models[row['id']] = {'id': row['id'], 'object': 'model', 'created': 0,
                                 'owned_by': 'local-' + backend, 'name': row['name'],
                                 'context_length': row['context'], 'backend': backend}
    return models


def backend_models(backend):
    port = BACKENDS[backend][1]
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models', timeout=2) as response:
            data = json.load(response)
        return {m['id'] for m in data.get('data', [])}
    except (OSError, ValueError, KeyError, TypeError):
        return set()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Never log credentials, query strings or request/response bodies.
        print(self.client_address[0], self.command, urlsplit(self.path).path, flush=True)

    def send_json(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if status == 401:
            self.send_header('WWW-Authenticate', 'Bearer realm="local-llm"')
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, status, message, code):
        return self.send_json(status, {'error': {'message': message, 'type': 'invalid_request_error'
                                                if status < 500 else 'backend_error', 'code': code}})

    def authorized(self):
        try:
            address = ipaddress.ip_address(self.client_address[0])
            if not any(address in subnet for subnet in allowed):
                self.error_json(403, 'Client network is not allowed.', 'network_denied')
                return False
        except ValueError:
            self.error_json(403, 'Invalid client address.', 'network_denied')
            return False
        header = self.headers.get('Authorization', '')
        supplied = header[7:].encode() if header.startswith('Bearer ') else b''
        if not supplied or not hmac.compare_digest(supplied, token):
            self.error_json(401, 'A valid local LLM API key is required.', 'invalid_api_key')
            return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        path = urlsplit(self.path).path
        models = catalog()
        online = {backend: backend_models(backend) for backend in BACKENDS}
        if path == '/health':
            return self.send_json(200, {'status': 'ok', 'backends': {
                backend: {'available_models': sorted(ids & set(models))}
                for backend, ids in online.items()},
                'note': 'Start the chosen Desktop backend. This gateway does not start GPU processes.'})
        for model in models.values():
            model['backend_available'] = model['id'] in online[model['backend']]
        if path == '/v1/models':
            return self.send_json(200, {'object': 'list', 'data': list(models.values())})
        if path.startswith('/v1/models/'):
            model = models.get(unquote(path.removeprefix('/v1/models/')))
            if model:
                return self.send_json(200, model)
            return self.error_json(404, 'Unknown model.', 'model_not_found')
        self.error_json(404, 'Unknown endpoint.', 'not_found')

    def do_POST(self):
        if not self.authorized():
            return
        path = urlsplit(self.path).path
        if path not in ('/v1/chat/completions', '/v1/completions'):
            return self.error_json(404, 'Only OpenAI chat/completion endpoints are exposed.', 'not_found')
        try:
            if self.headers.get('Transfer-Encoding'):
                raise ValueError('Chunked request bodies are not supported')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.error_json(413, 'Request must be between 1 byte and 32 MiB.', 'body_size')
            self.connection.settimeout(60)
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('Incomplete request body')
            data = json.loads(body)
            if not isinstance(data, dict) or not isinstance(data.get('model'), str):
                raise ValueError('An object with a model ID is required')
        except (ValueError, OSError):
            return self.error_json(400, 'Invalid JSON request or framing.', 'bad_request')
        model = catalog().get(data['model'])
        if model is None:
            return self.error_json(404, 'Unknown or retired model. Use GET /v1/models.', 'model_not_found')
        backend = model['backend']
        if model['id'] not in backend_models(backend):
            return self.error_json(503, f'Start the {BACKENDS[backend][2]} Desktop backend and wait for readiness.', 'backend_unavailable')
        if backend in ('strata', 'maya') and path != '/v1/chat/completions':
            return self.error_json(400, f'{BACKENDS[backend][2]} supports chat completions.', 'unsupported_endpoint')
        connection = None
        started = False
        try:
            connection = http.client.HTTPConnection('127.0.0.1', BACKENDS[backend][1], timeout=86400)
            # External credentials stay at the gateway, never in worker logs/requests.
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            started = True
            while chunk := response.read1(65536):
                self.wfile.write(chunk)
                self.wfile.flush()
            self.close_connection = True
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except OSError:
            if not started:
                self.error_json(503, 'Backend connection failed; inspect its visible terminal.', 'backend_unavailable')
            self.close_connection = True
        finally:
            if connection is not None:
                connection.close()


def main():
    global config, token, allowed
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'dsh/data/network-access.json')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    token = Path(config['key_file']).read_bytes().strip()
    if len(token) < 32:
        raise ValueError('Refusing to run without a strong API key')
    allowed = [ipaddress.ip_network(n) for n in config['allowed_subnets']]
    # Binding is explicit: no wildcard sockets, public IPv4 or public IPv6.
    for address in config['listen']:
        ip = ipaddress.ip_address(address)
        if ip.version != 4 or not any(ip in n for n in allowed):
            raise ValueError('Listener must be within the configured private networks')
    ThreadingHTTPServer.daemon_threads = True
    servers = {}
    stopped = threading.Event()
    def stop(*_):
        stopped.set()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    try:
        while not stopped.is_set():
            for address in config['listen']:
                if address in servers:
                    continue
                try:
                    server = ThreadingHTTPServer((address, config['port']), Handler)
                except OSError as error:
                    print('Waiting for listener', address, 'errno', error.errno, flush=True)
                    continue
                servers[address] = server
                threading.Thread(target=server.serve_forever, daemon=True).start()
                print('Local LLM API listening on', address, config['port'], flush=True)
            stopped.wait(10)
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
