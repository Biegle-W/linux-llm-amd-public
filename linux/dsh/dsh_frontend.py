"""Recognize/reopen only this installation's existing DSH web listener."""
import os
from pathlib import Path
import socket
import subprocess
from backend_switch import processes

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:3080'


def option(args, flag):
    for index, arg in enumerate(args):
        if arg.startswith(flag + '='):
            return arg.split('=', 1)[1]
        if arg == flag and index + 1 < len(args):
            return args[index + 1]
    return None


def is_dsh_web(proc, root=ROOT):
    args = proc.args
    return (len(args) >= 3 and Path(args[0]).name == 'node'
            and args[1] in {str(root / 'node_modules/.bin/dsh'),
                            str(root / 'node_modules/@deepseek-ai/dsh/lib/bin.js')}
            and args[2] == 'web' and option(args[3:], '--port') == '3080'
            and option(args[3:], '--host') == '127.0.0.1')


def owns_listener(proc, port=3080):
    inodes = set()
    for name in ('tcp', 'tcp6'):
        for line in (Path('/proc/net') / name).read_text().splitlines()[1:]:
            parts = line.split()
            if parts[3] == '0A' and int(parts[1].split(':')[1], 16) == port:
                inodes.add(parts[9])
    try:
        for fd in (Path('/proc') / str(proc.pid) / 'fd').iterdir():
            try:
                if os.readlink(fd) in {f'socket:[{inode}]' for inode in inodes}:
                    return True
            except OSError:
                continue
    except OSError:
        pass
    return False


def reuse_existing():
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', 3080)) != 0:
            return False
    if not any(is_dsh_web(proc) and owns_listener(proc) for proc in processes().values()):
        raise RuntimeError('Port 3080 is occupied by another application; DSH was not started and no process was stopped.')
    print('DSH is already running. Reopening its existing web interface; inference backends are unchanged.', flush=True)
    if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
        subprocess.Popen(['xdg-open', URL], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    return True
