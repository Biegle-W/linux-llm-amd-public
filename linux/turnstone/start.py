#!/usr/bin/env python3
"""Run the independent Turnstone UI in the foreground; never load GPU workers."""
import argparse
import fcntl
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:3081'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true', help='For SSH: serve without opening a browser')
    args = parser.parse_args()
    os.umask(0o077)
    if not (ROOT / 'data/config.toml').exists():
        raise SystemExit('First run: turnstone/.venv/bin/python turnstone/configure.py')
    lock = (ROOT / 'data/launcher.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f'Turnstone is already running at {URL}')
        if not args.no_browser:
            subprocess.run(['xdg-open', URL], check=False)
        return
    env = dict(os.environ)
    env.update({
        'TURNSTONE_CONFIG': str(ROOT / 'data/config.toml'),
        'TURNSTONE_NODE_ID': 'localuser-local',
        'TURNSTONE_WORKSPACE': str(ROOT / 'workspace'),
        'LOCAL_LLM_API_KEY': (ROOT.parent / 'dsh/data/network-api.key').read_text().strip(),
    })
    print(f'Turnstone UI: {URL}\nLogin details: {ROOT / "data/login.txt"}', flush=True)
    print('Start an inference backend separately and select its model in Turnstone.\n'
          'Ctrl+C stops only Turnstone; DSH and inference remain running.', flush=True)
    child = subprocess.Popen([
        str(ROOT / '.venv/bin/turnstone-server'), '--config', env['TURNSTONE_CONFIG'],
        '--host', '127.0.0.1', '--port', '3081',
    ], cwd=ROOT / 'workspace', env=env, start_new_session=True)

    def open_when_ready():
        for _ in range(120):
            if child.poll() is not None:
                return
            try:
                with urllib.request.urlopen(URL + '/health', timeout=1) as response:
                    if response.status == 200:
                        subprocess.run(['xdg-open', URL], check=False,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
            except OSError:
                pass
            time.sleep(0.5)

    if not args.no_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()

    def stop(*_):
        raise KeyboardInterrupt

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, stop)
    try:
        code = child.wait()
    except KeyboardInterrupt:
        code = 0
    finally:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    raise SystemExit(code)


if __name__ == '__main__':
    main()
