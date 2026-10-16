#!/usr/bin/env python3
"""Launch only DSH; inference backends have independent terminals."""
import os, signal, subprocess, sys
from pathlib import Path
from backend_guard import require_worker_ports_free
from configure_local import configure
ROOT = Path(__file__).resolve().parent
app = None

def stop(*_):
    raise KeyboardInterrupt

for sig in (signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, stop)
try:
    require_worker_ports_free([(3080, 'DSH')])
    configure()
    print('DSH only. Start an inference backend separately, then select its provider/model in DSH.', flush=True)
    print('Closing this terminal stops DSH; the backend stays running in its own terminal.', flush=True)
    app = subprocess.Popen([str(ROOT / 'run'), 'web', '--host', '127.0.0.1', '--port', '3080', *sys.argv[1:]],
                           cwd=ROOT / 'workspace', start_new_session=True)
    raise SystemExit(app.wait())
except KeyboardInterrupt:
    pass
except Exception as error:
    print('DSH startup failed:', error, file=sys.stderr)
    raise SystemExit(1)
finally:
    if app is not None:
        try:
            os.killpg(app.pid, signal.SIGTERM)
            app.wait(timeout=20)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(app.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        app.wait()
