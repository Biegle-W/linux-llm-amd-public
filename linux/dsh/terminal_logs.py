"""Mirror persistent backend logs into the launcher's terminal."""
import os
import shutil
import subprocess


def open_log_window(path, title, existing=None):
    """Reuse a desktop log viewer without making it the backend's supervisor."""
    if existing is not None and existing.poll() is None:
        return existing
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        return None
    terminal = shutil.which('ptyxis')
    if terminal is None:
        return None
    env = dict(os.environ, GSK_RENDERER='cairo')
    try:
        return subprocess.Popen(
            [terminal, '--standalone', '--new-window', f'--title={title}', '--',
             'tail', '--lines=30', '--follow=name', '--retry',
             '--sleep-interval=0.2', str(path)],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
    except OSError as error:
        print(f'Could not open {title} log window: {error}', flush=True)
        return None


def start_monitor(paths):
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    return subprocess.Popen(
        ['tail', '--lines=0', '--follow=name', '--retry', '--sleep-interval=0.2',
         *map(str, paths)],
        start_new_session=True,
    )


def stop_monitor(monitor):
    if monitor is not None and monitor.poll() is None:
        monitor.terminate()
        try:
            monitor.wait(timeout=3)
        except subprocess.TimeoutExpired:
            monitor.kill()
            monitor.wait()
