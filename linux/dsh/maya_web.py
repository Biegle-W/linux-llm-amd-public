"""Persistent, same-origin Maya UI; inference remains in the guarded worker."""
import hmac
import http.client
import json
import mimetypes
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlsplit
from inference_idle import inference_request

ROOT = Path(__file__).resolve().parent
POSTS = {'/v1/chat/completions', '/v1/messages', '/v1/completions', '/v1/responses',
         '/v1/strata/cancel', '/api/tokens', '/settings', '/mcp'}


def make_web_handler(controller, web_root, worker_port):
    class WebHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def log_message(self, *_):
            pass

        def reply(self, code, body, kind='application/json'):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def local_request(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            if (host not in hosts or (origin and origin != 'http://' + host)
                    or self.headers.get('Sec-Fetch-Site') == 'cross-site'
                    or urlsplit(self.path).netloc):
                self.reply(403, {'error': 'Use Maya’s own local page.'})
                return False
            return True

        def authorized(self):
            keys = controller.web_api_keys()
            auth = self.headers.get('Authorization', '')
            given = auth[7:].strip() if auth.lower().startswith('bearer ') else self.headers.get('x-api-key', '')
            if keys and not any(hmac.compare_digest(given.encode(), key.encode()) for key in keys):
                self.reply(401, {'error': 'Missing or wrong Maya API key.'})
                return False
            return True

        def body(self, limit):
            if self.headers.get('Transfer-Encoding'):
                raise ValueError('Send a Content-Length JSON request.')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= limit:
                raise ValueError('Invalid or oversized request body.')
            self.connection.settimeout(10)
            data = self.rfile.read(size)
            if len(data) != size:
                raise ValueError('Incomplete request body.')
            return data

        def do_GET(self):
            if not self.local_request():
                return
            path = urlsplit(self.path).path.rstrip('/')
            if path == '/managed/models':
                if self.authorized():
                    self.reply(200, controller.web_status())
                return
            if path == '/managed/model-switch.js':
                return self.reply(200, (ROOT / 'maya-model-switch.js').read_bytes(), 'text/javascript; charset=utf-8')
            if path in ('', '/index.html'):
                body = (web_root / 'index.html').read_bytes().replace(
                    b'</body>', b'<script src="/managed/model-switch.js" defer></script></body>')
                return self.reply(200, body, 'text/html; charset=utf-8')
            # Serve the pinned frontend assets even before a worker is ready.
            # Resolve both traversal and symlinks within this public asset root.
            asset = (web_root / unquote(path.removeprefix('/web/'))).resolve()
            if path.startswith('/web/') and asset.is_relative_to(web_root.resolve()) and asset.is_file():
                return self.reply(200, asset.read_bytes(),
                                  mimetypes.guess_type(asset.name)[0] or 'application/octet-stream')
            self.proxy('GET')

        @inference_request
        def do_POST(self):
            if not self.local_request():
                return
            path = urlsplit(self.path).path.rstrip('/')
            if path == '/managed/models/load':
                if not self.authorized():
                    return
                if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                    return self.reply(415, {'error': 'Send application/json.'})
                try:
                    data = json.loads(self.body(4096))
                    if not isinstance(data, dict) or set(data) != {'model'} or not isinstance(data['model'], str):
                        raise ValueError('Choose a model ID only; runtime/config overrides are not accepted.')
                    state = controller.queue_model_switch(data['model'])
                except (ValueError, TypeError) as error:
                    return self.reply(400, {'error': str(error)})
                except BlockingIOError as error:
                    return self.reply(409, {'error': str(error)})
                except RuntimeError as error:
                    return self.reply(503, {'error': str(error)})
                return self.reply(202, state)
            if path not in POSTS:
                return self.reply(409, {'error': 'Managed profiles keep context, GPU settings and runtime updates fixed.'})
            try:
                data = self.body(32 * 1024**2)
            except (ValueError, OSError) as error:
                return self.reply(400, {'error': str(error)})
            # Cancellation must still reach an active streaming request.
            if path == '/v1/strata/cancel':
                return self.proxy('POST', data)
            if not controller.requests.acquire(blocking=False):
                return self.reply(409, {'error': 'Maya is busy loading or serving another request.'})
            try:
                self.proxy('POST', data)
            finally:
                controller.requests.release()

        def proxy(self, method, data=None):
            connection = None
            started = False
            try:
                if not controller.worker_ready():
                    return self.reply(503, {'error': 'Maya is loading or unloaded. Use the model selector to load a validated profile.'})
                connection = http.client.HTTPConnection('127.0.0.1', worker_port, timeout=86400)
                # Preserve the public Host/Origin pair for native authentication
                # and same-page protections. The target is always fixed loopback.
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in {'connection', 'transfer-encoding', 'content-length'}}
                connection.request(method, self.path, body=data, headers=headers)
                response = connection.getresponse()
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in {'connection', 'transfer-encoding', 'server', 'date'}:
                        self.send_header(key, value)
                self.send_header('Connection', 'close')
                self.end_headers()
                started = True
                while chunk := response.read1(65536):
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (OSError, http.client.HTTPException) as error:
                if not started:
                    self.reply(503, {'error': 'Maya worker unavailable: ' + str(error)})
            finally:
                if connection:
                    connection.close()
                self.close_connection = True
    return WebHandler
