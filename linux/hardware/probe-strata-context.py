#!/usr/bin/env python3
"""Probe an already-running dual-AMD Strata context; never launch or stop apps."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from backend_switch import processes
from moe_memory import host_memory, worker_memory
from strata_memory import vram_snapshot


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tokens', type=int, required=True, help='Target raw prompt tokens, before chat formatting')
    ap.add_argument('--decode', action='store_true', help='Generate 256 tokens of code instead of a short retrieval answer')
    ap.add_argument('--checkpoints', action='store_true', help='Use normal production checkpoint defaults')
    ap.add_argument('--follow-up', action='store_true', help='Check a subsequent turn with the full conversation')
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.follow_up or a.checkpoints, 'Follow-up testing requires production checkpoints'
    cfg = json.loads((ROOT / 'dsh/strata-iq3-profile.json').read_text())
    args = cfg['args']
    context = int(args[args.index('--max-context') + 1])
    assert 1000 <= a.tokens <= context - 1024
    assert cfg['gpu'] == [0, 1] and cfg['backend'] == 'hip'
    engines = [p for p in processes().values() if p.args and p.args[0] == cfg['exe']]
    assert len(engines) == 1, 'Expected exactly one managed Strata HIP engine'
    engine = engines[0]
    for flag in ('--max-context', '--kv-resident', '--vram-reserve-mib'):
        assert engine.args[engine.args.index(flag) + 1] == args[args.index(flag) + 1]
    sys.path.insert(0, str(ROOT / 'strata/tools'))
    from strata_tokenizer import Tokenizer
    directory = Path(cfg['tokenizer'])
    vocab = json.loads((directory / 'vocab.json').read_text())
    tokens_by_id = [None] * len(vocab)
    for token, index in vocab.items():
        tokens_by_id[index] = token
    tokenizer = Tokenizer(tokens_by_id, (directory / 'merges.txt').read_text().split('\n'),
                          json.loads((directory / 'token_type.json').read_text()))
    nonce = str(time.time_ns())
    unit = 'The ledger entry lists a routine inventory check.\n'
    markers = ('CEDAR-571', 'MAPLE-832', 'BIRCH-296')
    task = ('First list all three access codes in order. Then write a complete Python task queue with retries, '
            'logging, cancellation, tests and an example. '
            'Keep writing code until finished.' if a.decode else
            'Return only the alpha, beta and gamma access codes, in that order.')
    def make(n):
        return ('Ledger ID ' + nonce + '\nalpha access code: ' + markers[0] + '\n' + unit*n +
                '\nbeta access code: ' + markers[1] + '\n' + unit*n +
                '\ngamma access code: ' + markers[2] + '\n' + unit*n + '\n' + task)
    repeats = max(1, (a.tokens - 100) // (3 * len(tokenizer.encode(unit))))
    for _ in range(6):
        prompt = make(repeats)
        actual = len(tokenizer.encode(prompt))
        if a.tokens - 100 <= actual <= a.tokens:
            break
        repeats = max(1, int(repeats * (a.tokens - 50) / actual))
    assert a.tokens - 150 <= actual <= a.tokens
    result = {'context': context, 'target_raw_tokens': a.tokens, 'raw_tokens': actual,
              'kv': args[args.index('--kv') + 1],
              'kv_resident': int(args[args.index('--kv-resident') + 1]),
              'kind': 'retrieval_and_long_code' if a.decode else 'three_marker_retrieval',
              'production_checkpoints': a.checkpoints, 'status': 'running'}
    def save():
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, indent=2) + '\n')
    save()
    readings = []
    done = threading.Event()
    def monitor():
        while not done.is_set():
            swap, spill = worker_memory(engine.pid)
            readings.append({'available': host_memory()[1], 'swap': swap, 'spill': spill,
                             'vram': vram_snapshot()})
            done.wait(.5)
    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    start = time.monotonic()
    try:
        body = {'model': cfg['model_name'], 'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 256 if a.decode else 96, 'temperature': 0,
                'chat_template_kwargs': {'enable_thinking': False}}
        if not a.checkpoints:
            body['strata_checkpoint'] = False
        request = urllib.request.Request('http://127.0.0.1:30020/v1/chat/completions',
                                         json.dumps(body).encode(), {'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=2400) as response:
            data = json.load(response)
        content = data['choices'][0]['message'].get('content') or ''
        result.update(usage=data['usage'], timings=data.get('timings'),
                      finish_reason=data['choices'][0].get('finish_reason'),
                      content_sha256=hashlib.sha256(content.encode()).hexdigest())
        assert actual <= result['usage']['prompt_tokens'] < context
        result['markers_found'] = [m in content for m in markers]
        assert all(result['markers_found']), 'Retrieval did not return all three markers'
        if a.decode:
            assert result['usage']['completion_tokens'] >= 128 and ('def ' in content or 'class ' in content)
        if a.follow_up:
            body['messages'] += [data['choices'][0]['message'],
                                 {'role': 'user', 'content': 'Repeat the three access codes, in order. Nothing else.'}]
            body['max_tokens'] = 96
            request = urllib.request.Request('http://127.0.0.1:30020/v1/chat/completions',
                                             json.dumps(body).encode(), {'Content-Type': 'application/json'})
            next_start = time.monotonic()
            with urllib.request.urlopen(request, timeout=2400) as response:
                follow = json.load(response)
            text = follow['choices'][0]['message'].get('content') or ''
            result['follow_up'] = {'usage': follow['usage'], 'timings': follow.get('timings'),
                                   'wall_seconds': round(time.monotonic() - next_start, 3),
                                   'markers_found': [m in text for m in markers],
                                   'content_sha256': hashlib.sha256(text.encode()).hexdigest()}
            assert all(result['follow_up']['markers_found'])
        result['status'] = 'passed'
    except Exception as error:
        result.update(status='failed', error_type=type(error).__name__)
        raise
    finally:
        result['wall_seconds'] = round(time.monotonic() - start, 3)
        done.set()
        watcher.join(timeout=4)
        if readings:
            result['memory'] = {
                'minimum_available_gib': round(min(r['available'] for r in readings) / 1024**3, 3),
                'maximum_worker_swap_bytes': max(r['swap'] for r in readings),
                'maximum_nonresident_vram_bytes': max(r['spill'] for r in readings),
                'minimum_free_vram_gib': [round(min(r['vram'][i]['free'] for r in readings) / 1024**3, 3)
                                          for i in range(2)]}
        safe = bool(readings) and (
            result['memory']['maximum_worker_swap_bytes'] == 0 and
            result['memory']['maximum_nonresident_vram_bytes'] == 0 and
            min(result['memory']['minimum_free_vram_gib']) >= 3 and
            result['memory']['minimum_available_gib'] >= 3)
        if not safe and result['status'] == 'passed':
            result.update(status='failed', error_type='UnsafeMemoryReadings')
        save()
        print(json.dumps(result), flush=True)
    assert result['status'] == 'passed'


if __name__ == '__main__':
    main()
