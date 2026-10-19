#!/usr/bin/env python3
"""Queue a local ComfyUI API graph and save its result and resource samples."""
import argparse
import json
import time
import urllib.request
from pathlib import Path


def request(base, path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(base + path, payload, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def resources():
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        if key in ('MemAvailable', 'SwapFree'):
            memory[key] = int(value.split()[0]) * 1024
    gpus = []
    for path in sorted(Path('/sys/class/drm').glob('card[0-9]*/device/mem_info_vram_used')):
        busy = path.with_name('gpu_busy_percent')
        gpus.append({"card": path.parents[1].name,
                     "vram_used": int(path.read_text()),
                     "busy_percent": int(busy.read_text()) if busy.exists() else None})
    return {"memory": memory, "gpus": gpus}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workflow', type=Path)
    parser.add_argument('--url', default='http://127.0.0.1:8188')
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=3600)
    args = parser.parse_args()
    args.result.parent.mkdir(parents=True, exist_ok=True)
    graph = json.loads(args.workflow.read_text())
    start = time.monotonic()
    reply = request(args.url, '/prompt', {"prompt": graph, "client_id": "local-model-validation"})
    prompt_id = reply['prompt_id']
    print(json.dumps({"prompt_id": prompt_id, "queued": True}), flush=True)
    samples = []
    while time.monotonic() - start < args.timeout:
        sample = resources()
        sample['elapsed_seconds'] = round(time.monotonic() - start, 2)
        samples.append(sample)
        if len(samples) == 1 or len(samples) % 15 == 0:
            args.result.write_text(json.dumps({"prompt_id": prompt_id, "running": True,
                                              "resource_samples": samples}, indent=2) + '\n')
        history = request(args.url, '/history/' + prompt_id).get(prompt_id)
        if history:
            result = {"elapsed_seconds": round(time.monotonic() - start, 2),
                      "history": history, "resource_samples": samples}
            args.result.write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps({"elapsed_seconds": result['elapsed_seconds'],
                              "status": history.get('status'),
                              "outputs": history.get('outputs')}, indent=2), flush=True)
            return 0 if history.get('status', {}).get('status_str') == 'success' else 1
        if len(samples) % 15 == 0:
            print(json.dumps(sample), flush=True)
        time.sleep(2)
    args.result.write_text(json.dumps({"prompt_id": prompt_id, "timeout": True,
                                      "resource_samples": samples}, indent=2) + '\n')
    raise TimeoutError('Validation timeout; the server task has not been cancelled automatically')


if __name__ == '__main__':
    raise SystemExit(main())
