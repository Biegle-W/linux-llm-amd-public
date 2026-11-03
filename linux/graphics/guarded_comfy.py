"""Run ComfyUI within the shared owned resource and SSD-health guard."""
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from inference_swap import WorkerSwapGuard


def main():
    if (ROOT / 'hardware/generated/GPU-LOCK').exists():
        raise SystemExit('GPUs are reserved by an existing task/fault hold; ComfyUI was not started.')
    if len(sys.argv) < 2:
        raise SystemExit('An explicit ComfyUI command is required.')
    guard = WorkerSwapGuard()
    proc = None
    def stop(*unused):
        raise KeyboardInterrupt
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
        signal.signal(sig, stop)
    try:
        proc = guard.spawn(sys.argv[1:], start_new_session=True)
        guard.ready(proc, phase='idle')
        while proc.poll() is None:
            guard.check()
            time.sleep(.2)
        return proc.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        if proc is not None:
            guard.stop(proc)


if __name__ == '__main__':
    raise SystemExit(main())
