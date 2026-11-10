"""Run ComfyUI within the shared owned resource and SSD-health guard.

Idle stop (November 9): like the hub's 600 s rule for LLM engines, ComfyUI is
stopped after COMFY_IDLE_TIMEOUT_S seconds (default 600; 0 disables) with an
empty queue and no connected client (an open browser tab counts as use).
Anything unknown (server not answering yet, unreadable state) counts as busy.
Start it again with graphics/start-comfyui or the ComfyUI desktop icon.
"""
import json
import os
from pathlib import Path
import signal
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from inference_swap import WorkerSwapGuard

IDLE_POLL_S = 5


def port_of(args):
    return int(args[args.index('--port') + 1]) if '--port' in args else 8188


def clients(port):
    """Established TCP connections to the ComfyUI port (browser websockets)."""
    count = 0
    for table in ('/proc/net/tcp', '/proc/net/tcp6'):
        for line in Path(table).read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] == '01' and int(fields[1].rsplit(':', 1)[1], 16) == port:
                count += 1
    return count


def busy(port):
    """True unless ComfyUI positively reports an empty queue and nobody is connected."""
    try:
        if clients(port):
            return True
        with urllib.request.urlopen('http://127.0.0.1:%d/queue' % port, timeout=5) as response:
            queue = json.load(response)
        return bool(queue['queue_running'] or queue['queue_pending'])
    except Exception:
        return True


def main():
    if (ROOT / 'hardware/generated/GPU-LOCK').exists():
        raise SystemExit('GPUs are reserved by an existing task/fault hold; ComfyUI was not started.')
    if len(sys.argv) < 2:
        raise SystemExit('An explicit ComfyUI command is required.')
    timeout = float(os.environ.get('COMFY_IDLE_TIMEOUT_S', '600'))
    port = port_of(sys.argv[1:])
    guard = WorkerSwapGuard()
    proc = None
    def stop(*unused):
        raise KeyboardInterrupt
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
        signal.signal(sig, stop)
    try:
        proc = guard.spawn(sys.argv[1:], start_new_session=True)
        guard.ready(proc, phase='idle')
        last_busy = last_poll = time.monotonic()
        while proc.poll() is None:
            guard.check()
            now = time.monotonic()
            if timeout > 0 and now - last_poll >= IDLE_POLL_S:
                last_poll = now
                if busy(port):
                    last_busy = now
                elif now - last_busy >= timeout:
                    print('[guard] ComfyUI idle for %d s (empty queue, no clients); stopping it. '
                          'Start it again with graphics/start-comfyui.' % timeout, flush=True)
                    return 0
            time.sleep(.2)
        return proc.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        if proc is not None:
            guard.stop(proc)


if __name__ == '__main__':
    raise SystemExit(main())
