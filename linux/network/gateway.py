#!/usr/bin/env python3
"""Authenticated LAN/Tailscale OpenAI API; requests go to the loopback model hub, which starts backends on demand."""
import argparse
import hmac
import http.client
import ipaddress
import json
import signal
import select
import socket
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
import model_catalog  # noqa: E402
from model_catalog import BACKENDS  # noqa: E402
from hub_transport import clean_error_body, relay_sse, sse_error
import responses_web_search

HUB_PORT = 30100


def catalog():
    return model_catalog.catalog(ROOT)

MAX_BODY = 32 * 1024 * 1024
config = {}
token = b''
allowed = []


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
        if path == '/health':
            connection = http.client.HTTPConnection('127.0.0.1', HUB_PORT, timeout=5)
            try:
                connection.request('GET', '/health')
                response = connection.getresponse()
                state = json.loads(response.read())
                # Hub owns the snapshot. No independent backend probes or activity.
                return self.send_json(response.status, state)
            except (OSError, ValueError, http.client.HTTPException):
                return self.error_json(503, 'The local model hub is not reachable.', 'hub_unavailable')
            finally:
                connection.close()
        models = catalog()
        online = {backend: backend_models(backend) for backend in BACKENDS}
        for model in models.values():
            model['backend_available'] = model['id'] in online[model['backend']]
            model['auto_start'] = True
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
        if path not in ('/v1/chat/completions', '/v1/completions', '/v1/responses'):
            return self.error_json(404, 'Only OpenAI chat/completion/Responses endpoints are exposed.', 'not_found')
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
        if backend in ('strata', 'maya') and path not in ('/v1/chat/completions', '/v1/responses'):
            return self.error_json(400, f'{BACKENDS[backend][2]} supports chat completions and Responses.', 'unsupported_endpoint')
        if path == '/v1/responses':
            search_bridge = responses_web_search.handles(data)
            print('Responses local-search bridge:', 'selected' if search_bridge else 'unused', flush=True)
            if search_bridge:
                return responses_web_search.serve(self, data, HUB_PORT)
        connection = None
        started = False
        finished = threading.Event()
        disconnected = threading.Event()
        try:
            # The loopback model hub starts or switches the backend on demand.
            connection = http.client.HTTPConnection('127.0.0.1', HUB_PORT, timeout=86400)
            # External credentials stay at the gateway, never in worker logs/requests.
            connection.request('POST', path, body, {'Content-Type': 'application/json'})
            upstream = connection.sock
            def watch_client():
                # Propagate external disconnects even while waiting for hub headers.
                while not finished.wait(.25):
                    try:
                        readable, _, _ = select.select([self.connection], [], [], 0)
                        if not readable or self.connection.recv(1, socket.MSG_PEEK):
                            continue
                    except OSError:
                        pass
                    disconnected.set()
                    try:
                        upstream.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return
            threading.Thread(target=watch_client, daemon=True).start()
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            self.send_header('Cache-Control', 'no-store')
            if response.getheader('Retry-After'):
                self.send_header('Retry-After', response.getheader('Retry-After'))
            self.send_header('Connection', 'close')
            self.end_headers()
            started = True
            secrets = (token.decode(),)
            def output(chunk):
                self.wfile.write(chunk)
                self.wfile.flush()
            if response.status >= 400:
                output(clean_error_body(response.read(), secrets))
            elif 'text/event-stream' in response.getheader('Content-Type', ''):
                relay_sse(response, output, secrets, responses=path == "/v1/responses")
            else:
                while chunk := response.read1(65536):
                    output(chunk)
            self.close_connection = True
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except (OSError, http.client.HTTPException):
            if disconnected.is_set():
                return
            if started and data.get('stream'):
                try:
                    self.wfile.write(sse_error({'message': 'Hub stream interrupted.', 'status': 503, 'code': 'hub_unavailable'}, responses=path == '/v1/responses'))
                except OSError:
                    pass
            if not started:
                self.error_json(503, 'The local model hub is not reachable (local-llm-hub.service).', 'hub_unavailable')
            self.close_connection = True
        finally:
            finished.set()
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
