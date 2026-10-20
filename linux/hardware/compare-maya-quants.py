#!/usr/bin/env python3
"""Bounded S24/S ABBA comparison; never changes production configuration.

Requires the operator's GPU coordination lock. Each run starts from the same
expert-profile seed and executes the same functional, long-context and benchmark
sequence. Only owned candidate processes are stopped. Raw results stay private.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from backend_switch import is_inference, processes


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--seed-profile', type=Path, default=ROOT / 'dsh/data/maya/glm-expert-profile.bin')
    ap.add_argument('--port', type=int, default=18195)
    args = ap.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / 'comparison.json'
    assert not result_path.exists(), 'Preserve an earlier comparison'
    lock = read(ROOT / 'hardware/generated/GPU-LOCK')
    assert lock['owner'] == 'Codex', 'GPU coordination lock is not owned by this task'
    baseline, candidate = read(args.baseline), read(args.candidate)
    assert baseline['model_name'] == candidate['model_name'] == 'glm-5.3-flash-maya'
    for cfg in (baseline, candidate):
        assert cfg['gpu'] == [0, 1] and not cfg['split_skip_if_fits']
        assert cfg['args'][cfg['args'].index('--max-context') + 1] == '32768'
    # File/pack paths may differ. All effective inference settings must match.
    def settings(cfg):
        c = json.loads(json.dumps(cfg))
        for key in ('log', 'tokenizer', 'installer', 'local_validation',
                    'expert_profile_seed_sha256', 'upstream_expert_profile_seed_sha256'):
            c.pop(key, None)
        for flag in ('--glm-pack', '--expert-profile'):
            c['args'][c['args'].index(flag) + 1] = '<matched asset>'
        return c
    assert settings(baseline) == settings(candidate), 'Unmatched inference settings'
    protected = [ROOT / 'dsh/maya-glm-profile.json', ROOT / 'dsh/maya-deepseek-profile.json',
                 ROOT / 'dsh/maya-profiles.json', ROOT / 'maya/runtime.json']
    protected_hashes = {str(p): sha(p) for p in protected}
    seed = args.seed_profile.read_bytes()
    spec = importlib.util.spec_from_file_location('matched_bench', ROOT / 'hardware/benchmark-current-amd.py')
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    prompts = [bench.prefill_prompt(i) for i in range(3)]
    write(out / 'prefill-prompts.private.json', prompts)
    result = {'status': 'running', 'order': ['s24-a1', 's-b1', 's-b2', 's24-a2'],
              'rule': 'Promote Maya-S only if EACH six-trial median(code SSE decode, prose SSE decode, fresh native PP) / S24 median is strictly >0.90, with all functional/near30K/memory checks passing.',
              'context': 32768, 'runs_per_task_per_start': 3, 'starts_per_quant': 2,
              'seed_sha256': hashlib.sha256(seed).hexdigest(),
              'prefill_prompt_sha256': [hashlib.sha256(p.encode()).hexdigest() for p in prompts],
              'protected_config_hashes_before': protected_hashes, 'cases': []}
    write(result_path, result)
    harness = None

    def interrupted(*_):
        raise KeyboardInterrupt

    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, interrupted)
    try:
        for tag in result['order']:
            assert not any(is_inference(p) for p in processes().values()), 'Other inference is running'
            quant = 's24' if tag.startswith('s24') else 's'
            cfg = json.loads(json.dumps(baseline if quant == 's24' else candidate))
            profile = out / (tag + '-expert-profile.bin')
            profile.write_bytes(seed)
            cfg['args'][cfg['args'].index('--expert-profile') + 1] = str(profile)
            cfg['expert_profile_seed_sha256'] = hashlib.sha256(seed).hexdigest()
            cfg['log'] = str(out / (tag + '.native.log'))
            cfg['port'] = args.port
            cfg.pop('local_validation', None)
            config = out / (tag + '.json')
            write(config, cfg)
            case = {'tag': tag, 'quant': quant, 'status': 'starting', 'config_sha256': sha(config)}
            result['cases'].append(case)
            write(result_path, result)
            with (out / (tag + '.console.log')).open('w') as log:
                harness = subprocess.Popen([sys.executable, '-u', '-B', str(ROOT / 'hardware/serve-maya-candidate.py'),
                    '--config', str(config), '--port', str(args.port), '--tag', tag,
                    '--output-dir', str(out), '--startup-free-gib', '6'], stdout=log, stderr=subprocess.STDOUT)
                server = out / (tag + '.server.json')
                for _ in range(1000):
                    assert harness.poll() is None, 'Candidate guard/harness exited before ready'
                    if server.exists() and read(server)['status'] == 'ready':
                        break
                    time.sleep(1)
                else:
                    raise TimeoutError('Candidate did not reach readiness')
                case['status'] = 'testing'
                write(result_path, result)
                subprocess.run([sys.executable, '-B', str(ROOT / 'hardware/validate-maya.py'),
                    '--port', str(args.port), '--model', cfg['model_name'], '--context', '32768',
                    '--long-tokens', '30000', '--prompt-seed', 'maya-s-s24-matched-context-20261020',
                    '--output', str(out / (tag + '.functional.json'))], stdout=log, stderr=subprocess.STDOUT,
                    check=True, timeout=1500)
                bench.PORTS['maya'] = (args.port, args.port)
                bench.profiles = lambda _: [(cfg['model_name'], 32768)]
                bench.prefill_prompt = lambda index: prompts[index]
                old_argv = sys.argv
                try:
                    sys.argv = ['benchmark', '--kind', 'maya', '--date', '2026-10-20', '--runs', '3',
                                '--output', str(out / (tag + '.benchmark.json'))]
                    bench.main()
                finally:
                    sys.argv = old_argv
            harness.send_signal(signal.SIGINT)
            assert harness.wait(timeout=90) == 0
            harness = None
            assert read(server)['status'] == 'stopped_after_testing'
            case['status'] = 'passed'
            case['seed_sha256_after'] = sha(profile)
            write(result_path, result)
            print('COMPLETED', tag, flush=True)
            # Wait for owned ROCm allocations to disappear; never stop other apps.
            for _ in range(20):
                if not any(is_inference(p) for p in processes().values()):
                    break
                time.sleep(1)
        scores = {}
        for quant in ('s24', 's'):
            cases = [read(out / (x['tag'] + '.benchmark.json'))['profiles'][0]
                     for x in result['cases'] if x['quant'] == quant]
            scores[quant] = {
                **{task: statistics.median(t['decode_tps_sse'] for c in cases
                    for t in c['short'][task]['trials']) for task in ('code', 'prose')},
                'prefill': statistics.median(t['prefill_native_tps'] for c in cases for t in c['prefill'])}
        result['scores'] = scores
        result['ratios'] = {task: scores['s'][task] / scores['s24'][task] for task in scores['s']}
        result['candidate_passed_speed'] = all(r > .90 for r in result['ratios'].values())
        result['selected_quant'] = 's' if result['candidate_passed_speed'] else 's24'
        result['status'] = 'passed'
    except BaseException as error:
        result.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, signal.SIG_IGN)
        if harness is not None and harness.poll() is None:
            harness.send_signal(signal.SIGINT)
            try:
                harness.wait(timeout=90)
            except subprocess.TimeoutExpired:
                # The harness owns a bounded process group. Do not broaden cleanup
                # to other inference or arbitrary Python/GPU processes.
                result['cleanup_attention_required'] = True
        result['protected_config_hashes_after'] = {str(p): sha(p) for p in protected}
        result['production_configs_unchanged'] = result['protected_config_hashes_after'] == protected_hashes
        write(result_path, result)


if __name__ == '__main__':
    main()
