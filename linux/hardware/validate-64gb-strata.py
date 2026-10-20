#!/usr/bin/env python3
"""Compare two isolated Strata CPU pools, with guards and numeric evidence.

Never changes production. Each pool gets the same three-trial benchmark,
functional checks and near-window retrieval/follow-up test. Stops only its own
candidate harness. Optional --after-result waits for a specific Q4 test to finish; it never promotes that result.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'hardware/generated/cpu-ram-validation-2026-10-19/strata'
MODEL = 'qwen3.8-flash-next-iq3_xxs'
RESULT_PATH = None


def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    global RESULT_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--after-result', type=Path)
    parser.add_argument('--name', default='pool-comparison')
    parser.add_argument('--tag-suffix', default='')
    parser.add_argument('--base-tags', nargs=2, default=['64gb-6-all', '64gb-7-pcores'],
                        help='Baseline and candidate config stems; order defines the retention baseline')
    parser.add_argument('--minimum-decode-gain', type=float, default=.05,
                        help='Retain baseline unless eligible candidate improves decode by this fraction')
    parser.add_argument('--resume-tests', action='store_true', help='Reuse passed benchmark/functional records only with an identical config and binary; preserve every old artifact')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.name) and re.fullmatch(r'[A-Za-z0-9_-]*',args.tag_suffix)
    assert len(set(args.base_tags)) == 2 and all(re.fullmatch(r'[A-Za-z0-9_-]+',tag) for tag in args.base_tags)
    assert 0 <= args.minimum_decode_gain <= 1
    summary_path = OUT/(args.name+'.json')
    assert not summary_path.exists(), 'Do not overwrite a recorded comparison'
    RESULT_PATH = summary_path
    summary = {'status':'waiting' if args.after_result else 'running', 'trials':[],
        'base_tags':args.base_tags, 'minimum_decode_gain':args.minimum_decode_gain,
        'selection_method':'Each pool must pass functional, near-window and memory checks. Eligible prefill must be within 5 percent of the faster pool. Retain baseline unless the eligible candidate improves geometric-mean median code/prose decode by the declared minimum gain; no statistical significance claim from three trials.'}
    def save():
        summary_path.write_text(json.dumps(summary, indent=2)+'\n')
    save()
    if args.after_result:
        start = time.monotonic()
        while time.monotonic()-start < 10800:
            q4 = read(args.after_result)
            if q4.get('status') in ('passed','failed'):
                assert q4['model'] == 'nemotron-3.5-super-q4'
                summary['previous_q4_status'] = q4['status']
                break
            time.sleep(10)
        else:
            raise TimeoutError('Q4 result did not finish within three hours')
    summary['status'] = 'running'
    save()
    def interrupt(*_):
        raise KeyboardInterrupt
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, interrupt)
    for base_tag in args.base_tags:
        tag = base_tag + args.tag_suffix
        config = OUT/(tag+'.json')
        prior_server_path = OUT/(tag+'.server.json')
        reuse = args.resume_tests and prior_server_path.exists()
        if reuse:
            prior = read(prior_server_path)
            assert prior['status']=='stopped_after_testing' and prior['config']==read(config)
            assert prior['binary_sha256']==hashlib.sha256(Path(prior['config']['exe']).read_bytes()).hexdigest()
        server_tag = tag+'-resumed' if reuse else tag
        server_path = OUT/(server_tag+'.server.json')
        assert not server_path.exists(), 'Do not overwrite a measured candidate'
        harness = None
        try:
            harness = subprocess.Popen([sys.executable, '-B', str(ROOT/'hardware/serve-strata-candidate.py'),
                '--config',str(config),'--port','18184','--tag',server_tag])
            start = time.monotonic()
            while time.monotonic()-start < 960:
                assert harness.poll() is None, 'Candidate harness exited before ready'
                state = read(server_path)
                if state.get('status') == 'ready':
                    break
                time.sleep(1)
            else:
                raise TimeoutError('Strata candidate did not become ready')
            def run(command, suffix, timeout):
                log_path = OUT/(tag+'.'+suffix+'.console.log')
                with log_path.open('w') as output:
                    subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                                   timeout=timeout, check=True, cwd=ROOT)
            benchmark_path = OUT/(tag+'.benchmark.json')
            code = "import importlib.util,sys; s=importlib.util.spec_from_file_location('bench',sys.argv[1]); b=importlib.util.module_from_spec(s); s.loader.exec_module(b); b.PORTS['strata']=(18184,18184); sys.argv=sys.argv[1:]; b.main()"
            reuse_benchmark = reuse and benchmark_path.exists()
            if reuse_benchmark:
                assert read(benchmark_path)['profiles'][0]['status']=='passed'
            else:
                run([str(ROOT/'vllm/.venv-rocm/bin/python'),'-B','-c',code,
                    str(ROOT/'hardware/benchmark-current-amd.py'),'--kind','strata',
                    '--model',MODEL,'--runs','3','--date','2026-10-20','--output',str(benchmark_path)],
                    'benchmark',1800)
            functional_path = OUT/(tag+'.functional.json')
            reuse_functional = reuse and functional_path.exists()
            if reuse_functional:
                assert read(functional_path)['status']=='passed'
            else:
                run([str(ROOT/'strata/.venv/bin/python'),'-B',str(ROOT/'hardware/validate-strata.py'),
                    '--config',str(config),'--port','18184','--long','--output',str(functional_path)],
                    'functional',900)
            long_path = OUT/(tag+'.long.json')
            assert not long_path.exists(), 'Preserve an earlier long-probe result'
            run([str(ROOT/'strata/.venv/bin/python'),'-B',str(ROOT/'hardware/probe-strata-context.py'),
                '--config',str(config),'--port','18184','--tokens','258000','--decode',
                '--checkpoints','--follow-up','--output',str(long_path)],'long',1800)
            b, f, long = read(benchmark_path)['profiles'][0], read(functional_path), read(long_path)
            assert b['status'] == f['status'] == long['status'] == 'passed'
            assert all(long['markers_found']) and all(long['follow_up']['markers_found'])
            assert long['follow_up']['usage']['prompt_tokens_details']['cached_tokens'] > .9*long['usage']['prompt_tokens']
            record = {'tag':tag,'server_tag':server_tag,'status':'passed',
                'reused_passed_benchmark':reuse_benchmark,'reused_passed_functional':reuse_functional,
                'decode_score':math.sqrt(b['short']['code']['median_decode_tps']*b['short']['prose']['median_decode_tps']),
                'median_prefill_tps':sorted(t['prefill_native_tps'] for t in b['prefill'])[1]}
            summary['trials'].append(record)
            save()
            print('POOL PASS',tag,record,flush=True)
        finally:
            if harness is not None and harness.poll() is None:
                harness.send_signal(signal.SIGINT)
                try:
                    harness.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    # A second interrupt still targets only our own harness;
                    # its owned worker cleanup remains in its finally block.
                    harness.send_signal(signal.SIGINT)
                    harness.wait(timeout=45)
            state = read(server_path)
            assert state.get('status') == 'stopped_after_testing', state.get('status')
        time.sleep(5)  # Allow the driver's rolling utilization sample to settle.
    fastest_prefill = max(r['median_prefill_tps'] for r in summary['trials'])
    eligible = [r for r in summary['trials'] if r['median_prefill_tps'] >= .95*fastest_prefill]
    winner = max(eligible,key=lambda r:r['decode_score'])
    baseline = summary['trials'][0]
    if baseline in eligible and winner['decode_score'] < baseline['decode_score']*(1+args.minimum_decode_gain):
        winner = baseline
    summary.update(status='passed', selected=winner['tag'])
    save()
    print('SELECTED',winner['tag'],flush=True)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        if RESULT_PATH is not None:
            state = read(RESULT_PATH)
            if state.get('status') not in ('passed','blocked'):
                state.update(status='failed',error_type=type(error).__name__)
                RESULT_PATH.write_text(json.dumps(state,indent=2)+'\n')
        raise
