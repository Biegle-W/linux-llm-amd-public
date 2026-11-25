"""Sequential stdlib HTTP requests with a socket-enforced wall deadline."""

from contextlib import closing
import http.client
import json
import socket
import ssl
from threading import Lock, Thread
from time import monotonic
from urllib.parse import urlsplit


class RequestError(Exception):
    pass


class DeadlineExceeded(RequestError):
    pass


def request(url, deadline, body=None, *, require_ok=False):
    """POST a JSON body, or GET and return the HTTP status at response headers."""
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise DeadlineExceeded("Request deadline reached")
    target = urlsplit(url)
    path = target.path or "/"
    if target.query:
        path += "?" + target.query

    sock = None
    lock = Lock()
    cancelled = False
    result = {}

    class Connection(http.client.HTTPConnection):
        def connect(self):
            nonlocal sock
            transport = socket.create_connection((self.host, self.port), self.timeout)
            with lock:
                if cancelled:
                    transport.close()
                    raise DeadlineExceeded("Request deadline reached")
                sock = transport
                self.sock = transport
            if target.scheme == "https":
                context = ssl.create_default_context()
                with lock:
                    if cancelled:
                        raise DeadlineExceeded("Request deadline reached")
                    sock = context.wrap_socket(
                        transport, server_hostname=self.host, do_handshake_on_connect=False
                    )
                    self.sock = sock
                sock.do_handshake()

    def work():
        port = target.port or (443 if target.scheme == "https" else 80)
        with closing(Connection(target.hostname, port, timeout=remaining)) as conn:
            try:
                if body is None:
                    conn.request("GET", path)
                else:
                    conn.request("POST", path, json.dumps(body).encode(), {
                        "Content-Type": "application/json",
                    })
                with conn.getresponse() as response:
                    if body is None:
                        result["value"] = response.status
                    elif response.status == 200 or (not require_ok and 200 < response.status < 300):
                        result["value"] = json.loads(response.read())
                    else:
                        raise RequestError(f"HTTP {response.status}")
            except (OSError, http.client.HTTPException, ValueError, RequestError) as exc:
                result["error"] = exc
            finally:
                result["ended"] = monotonic()

    worker = Thread(target=work, daemon=True)
    worker.start()
    worker.join(max(0, deadline - monotonic()))
    if worker.is_alive() or result.get("ended", float("inf")) >= deadline:
        with lock:
            cancelled = True
            if sock is not None:
                try:
                    # HTTPConnection can drop its socket reference once it reads
                    # headers. The response's file still uses this same socket.
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        raise DeadlineExceeded("Request deadline reached")
    if "error" in result:
        error = result["error"]
        if isinstance(error, TimeoutError):
            raise DeadlineExceeded("Request deadline reached") from error
        raise RequestError(str(error)) from error
    return result["value"]
