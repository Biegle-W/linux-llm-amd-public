#!/usr/bin/env python3
"""Serve an isolated Maya candidate with production-equivalent memory guards.

No production config is written. Refuse other inference workloads, bind only
loopback, enforce the existing dual-AMD admission and no-swap policy, and stop
only the owned process group on interruption or a latched guard failure.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dsh'))
from amd_device import amd_devices
from backend_switch import processes, is_inference
from backend_guard import require_worker_ports_free
from moe_memory import host_memory, worker_memory
from strata_memory import MemoryGuard, vram_snapshot
from maya_runtime import check_config


def stop(worker):
    if worker.poll() is None:
        try:
            os.killpg(worker.pid, signal.SIGTERM)
            worker.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait()
        except ProcessLookupError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--port', type=int, default=18195)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--output-dir', type=Path, default=ROOT/'hardware/generated/maya-setup-2026-10-20')
    ap.add_argument('--startup-free-gib', type=float, default=0, help='Final activation candidates must retain at least 6 GiB whole-card startup headroom')
    a = ap.parse_args()
    assert 1024 <= a.port <= 65535
    require_worker_ports_free([(a.port, 'isolated Maya candidate')])
    assert not any(is_inference(p) for p in processes().values()), 'Another inference workload is running'
    devices = amd_devices()
    for _ in range(10):
        if all(int((d/'gpu_busy_percent').read_text()) <= 10 for d in devices):
            break
        time.sleep(1)
    assert all(int((d/'gpu_busy_percent').read_text()) <= 10 for d in devices), 'A GPU is busy'
    cfg = json.loads(a.config.read_text())
    check_config(cfg, require_validated=False)
    assert Path(cfg['exe']).resolve() in {(ROOT/'maya/upstream/build-hip/maya').resolve(),(ROOT/'maya/upstream/build-hip/maya-ds4').resolve()}
    out = a.output_dir
    out.mkdir(exist_ok=True, parents=True)
    result_path = out/(a.tag+'.server.json')
    assert not result_path.exists(), 'Do not overwrite an experiment'
    result = {'source_commit':subprocess.check_output(['git','-C',str(ROOT/'maya/upstream'),'rev-parse','HEAD'],text=True).strip(),
        'cpu':next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),
        'os_visible_ram_bytes':host_memory()[0], 'kernel':os.uname().release,
        'gpu_usable_vram_bytes':[int((device/'mem_info_vram_total').read_text()) for device in devices],
        'binary_sha256':hashlib.sha256(Path(cfg['exe']).read_bytes()).hexdigest(),
        'measurement_started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'config':cfg,'port':a.port,'status':'starting','memory':{'minimum_available_bytes':host_memory()[1],
        'maximum_worker_swap_bytes':0,'maximum_vram_spill_bytes':0,'minimum_free_vram_bytes':[2**63,2**63]}}
    def save():result_path.write_text(json.dumps(result,indent=2)+'\n')
    save()
    def interrupt(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupt)
    command = ['systemd-run','--user','--scope','--quiet','--property=MemorySwapMax=0','--property=MemoryMax=52G',
        str(ROOT/'dsh/run-maya-backend'),'--config',str(a.config.resolve()),'--port',str(a.port)]
    guard = MemoryGuard()
    started = time.monotonic()
    worker = None
    try:
        with (out/(a.tag+'.server.log')).open('w') as log:
            worker = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            result['pid'] = worker.pid
            while worker.poll() is None:
                swap,spill = worker_memory(worker.pid)
                readings = vram_snapshot()
                available = host_memory()[1]
                memory = result['memory']
                memory['minimum_available_bytes'] = min(memory['minimum_available_bytes'],available)
                memory['maximum_worker_swap_bytes'] = max(memory['maximum_worker_swap_bytes'],swap)
                memory['maximum_vram_spill_bytes'] = max(memory['maximum_vram_spill_bytes'],spill)
                memory['minimum_free_vram_bytes'] = [min(old,row['free']) for old,row in zip(memory['minimum_free_vram_bytes'],readings)]
                reason = guard.check(available,swap,spill,readings)
                if reason:
                    result.update(status='guard_failed',guard_failure=reason)
                    save()
                    raise RuntimeError(reason)
                if result['status']=='starting':
                    if time.monotonic()-started > 900:raise TimeoutError('Candidate startup exceeded 15 minutes')
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{a.port}/health',timeout=1) as res:health=json.load(res)
                        if health.get('status')=='ok' and not health.get('unloaded',True):
                            assert health.get('model') == cfg['model_name']
                            assert health.get('max_context') == int(cfg['args'][cfg['args'].index('--max-context')+1])
                            assert all(row['free'] >= a.startup_free_gib*1024**3 for row in readings), 'Whole-card startup reserve not met'
                            result.update(status='ready',load_seconds=time.monotonic()-started,health=health,
                                          startup_whole_card_free_bytes=[row['free'] for row in readings],startup_free_required_gib=a.startup_free_gib)
                            print('READY',a.tag,round(result['load_seconds'],2),flush=True)
                    except (OSError,TimeoutError):pass
                save()
                time.sleep(.5)
            raise RuntimeError('Candidate worker exited')
    except KeyboardInterrupt:
        if result['status']=='ready':result['status']='stopped_after_testing'
    except Exception as error:
        result['error']=str(error)
        if result['status']!='guard_failed':result['status']='failed'
        raise
    finally:
        for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
        if worker is not None:stop(worker)
        save()
    assert result['status']=='stopped_after_testing'


if __name__ == '__main__':main()
