#!/usr/bin/env python3
"""Read-only thermal observer. Can follow an existing PID without controlling it."""
import argparse
import json
import math
from pathlib import Path
import signal
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dsh'))
from gpu_telemetry import ThermalRecorder


def process_identity(pid):
    try:
        text = (Path('/proc')/str(pid)/'stat').read_text()
        fields = text[text.rfind(')')+2:].split()
        return None if fields[0] == 'Z' else fields[19]
    except (OSError, IndexError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--directory', type=Path)
    bound = parser.add_mutually_exclusive_group(required=True)
    bound.add_argument('--pid', type=int, help='Stop when this exact process exits; PID reuse is rejected')
    bound.add_argument('--seconds', type=float, help='Finite read-only recording duration')
    args = parser.parse_args()
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error('--seconds must be finite and positive')
    if args.pid is not None and args.pid <= 0:
        parser.error('--pid must be positive')
    identity = process_identity(args.pid) if args.pid else None
    if args.pid and identity is None:
        parser.error('The followed PID is not running')
    done = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, lambda *_: done.set())
    started = time.monotonic()
    thermal = ThermalRecorder(args.label, directory=args.directory)
    thermal.state['coverage'] = 'Observation begins now; no retrospective coverage'
    if args.pid:
        thermal.state['followed_pid'] = args.pid
        thermal.state['followed_start_ticks'] = identity
    try:
        thermal.start()
        print(json.dumps({'raw_log': str(thermal.raw_path), 'summary': str(thermal.summary_path)}), flush=True)
        while not done.wait(.5):
            if args.pid and process_identity(args.pid) != identity:
                break
            if args.seconds is not None and time.monotonic()-started >= args.seconds:
                break
    finally:
        print(json.dumps(thermal.stop()), flush=True)


if __name__ == '__main__':
    main()
