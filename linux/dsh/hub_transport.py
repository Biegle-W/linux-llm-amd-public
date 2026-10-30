"""Error-preserving loopback transport. Successful completion/tool deltas stay intact."""
import http.client
import json
import re


def clean_text(value, secrets=()):
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(str(secret), '[redacted]')
    text = re.sub(r'(?i)\bBearer\s+[^\s"\'<>;,\\]+', 'Bearer [redacted]', text)
    text = re.sub(r'(?i)((?:api[_-]?key|access[_-]?token|authorization|password|secret)\s*[=:]\s*)[^\s"\'<>;,\\]+', r'\1[redacted]', text)
    text = re.sub(r'(?:/(?:home|root|opt|run/media|mnt|tmp|var/log)/)[^\s"\'<>;,]+', '[private path]', text)
    text = re.sub(r'[A-Za-z]:\\(?:Users|Local-LLM)\\[^\s"\'<>;,]+', '[private path]', text)
    return text


def clean_value(value, secrets=()):
    if isinstance(value, dict):
        return {clean_text(k, secrets): ('[redacted]' if re.sub(r'[_-]', '', k).lower() in
                {'apikey', 'accesstoken', 'authorization', 'password', 'secret', 'token'}
                else clean_value(v, secrets)) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_value(v, secrets) for v in value]
    return clean_text(value, secrets) if isinstance(value, str) else value


def clean_error_body(payload, secrets=()):
    try:
        value = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return clean_text(payload.decode(errors='replace'), secrets).encode()
    return json.dumps(clean_value(value, secrets)).encode()


def error_payload(payload, status, secrets=()):
    try:
        value = json.loads(payload)
        error = value.get('error', value) if isinstance(value, dict) else value
    except (ValueError, UnicodeDecodeError):
        error = payload.decode(errors='replace')
    if not isinstance(error, dict):
        error = {'message': str(error)}
    error = clean_value(error, secrets)
    error.setdefault('message', 'Backend rejected the request.')
    error.setdefault('code', 'backend_error')
    error['status'] = status
    return error


def sse_error(error, secrets=(), *, responses=False):
    error = clean_value(error, secrets)
    if responses:
        value = {**error, 'type': 'error', 'param': error.get('param')}
        return b'event: error\ndata: ' + json.dumps(value).encode() + b'\n\n'
    return b'data: ' + json.dumps({'error': error}).encode() + b'\n\ndata: [DONE]\n\n'


def relay_sse(response, write, secrets=(), *, responses=False):
    """Parse across arbitrary HTTP chunks; preserve successful events byte for byte.

    Normalize errors already inside a 200 stream, then terminate with one DONE.
    Responses streams finish on their typed terminal event instead of [DONE].
    A truncated HTTP/SSE response is a transport error, never a success.
    """
    pending = b''
    while chunk := response.read1(65536):
        pending += chunk
        while match := re.search(br'\r?\n\r?\n', pending):
            frame, pending = pending[:match.start()], pending[match.end():]
            raw = frame + match.group()
            lines = frame.splitlines()
            data = b'\n'.join(line[5:].lstrip(b' ') for line in lines if line.startswith(b'data:'))
            if data == b'[DONE]':
                if responses:
                    raise http.client.HTTPException('Responses stream lacks a terminal event')
                write(raw)
                return
            try:
                value = json.loads(data) if data else None
            except (ValueError, UnicodeDecodeError):
                value = None
            if responses and isinstance(value, dict) and value.get('type') in (
                    'response.completed', 'response.incomplete', 'response.failed'):
                if value['type'] == 'response.failed':
                    # Native failures may contain private diagnostics; retain
                    # their Responses envelope without a Chat Completions DONE.
                    write(b'event: response.failed\ndata: ' +
                          json.dumps(clean_value(value, secrets)).encode() + b'\n\n')
                else:
                    write(raw)
                return
            is_error = isinstance(value, dict) and ('error' in value or value.get('object') == 'error'
                                                       or value.get('type') == 'error')
            if is_error or any(line.strip() == b'event: error' for line in lines):
                error = value.get('error', value) if isinstance(value, dict) else None
                status = value.get('status', value.get('status_code', 502)) if isinstance(value, dict) else 502
                if isinstance(error, dict):
                    code = error.get('code')
                    fallback = code if type(code) is int and 400 <= code <= 599 else status
                    status = error.get('status', error.get('status_code', fallback))
                write(sse_error(error_payload(data, status, secrets), responses=responses))
                return
            write(raw)
        if len(pending) > 1024 * 1024:
            raise http.client.HTTPException('Oversized SSE event')
    raise http.client.HTTPException('Incomplete SSE response')
