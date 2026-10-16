"""Mirror persistent backend logs into the launcher's terminal."""
import subprocess


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
