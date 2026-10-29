#!/usr/bin/env python3
"""Run one inference backend with terminal logs, independently of DSH."""
import argparse, json, os, signal, subprocess, sys
from pathlib import Path
from backend_guard import require_worker_ports_free
from backend_switch import startup_handover, clear_owner
from shared_storage import ensure_llama_models, ensure_strata_models
from terminal_logs import start_monitor, stop_monitor
from hardware_guard import require_current_cuda_pair, require_strata
from llama_runtime import launch_spec, require_amd_headroom
from rocm_runtime import require_rocm, require_rocm_headroom
from maya_runtime import require_maya, profiles as maya_profiles
from native_frontend import start_frontend
from gpu_telemetry import ThermalRecorder
ROOT = Path(__file__).resolve().parent
kind = sys.argv[1]
names = {'llama': 'llama.cpp', 'sglang': 'SGLang', 'vllm': 'vLLM', 'strata': 'Strata', 'maya': 'Project Maya'}
if kind not in names:
    print('Choose llama, sglang, vllm, strata or maya. HyperQwen has been retired.', file=sys.stderr)
    raise SystemExit(1)
ports = [(8080, 'llama.cpp'), (8081, 'llama.cpp'),
         (30000, 'SGLang'), (30001, 'SGLang'), (30010, 'vLLM'), (30011, 'vLLM'),
         (30020, 'Strata'), (30021, 'Strata'), (30030, 'Maya'), (30031, 'Maya'), (30032, 'Maya')]
open_frontend = kind in ('strata', 'maya') and '--no-browser' not in sys.argv[2:]
if kind in ('strata', 'maya'):
    sys.argv = sys.argv[:2] + [arg for arg in sys.argv[2:] if arg != '--no-browser']
maya_model=None
if kind == 'maya':
    # Invalid selections and --help must not hand over a working backend.
    parser = argparse.ArgumentParser(description='Start guarded dual-AMD Maya with its native Chat/Monitor; DSH is optional.')
    parser.add_argument('--model', choices=list(maya_profiles()))
    parser.add_argument('--no-browser', action='store_true', help='Keep serving without opening the native web frontend.')
    maya_model=parser.parse_args(sys.argv[2:]).model or next(iter(maya_profiles()))
strata_model=None
if kind=='strata':
    available={k:v for k,v in json.loads((ROOT/'strata-profiles.json').read_text()).items() if v.get('enabled',True)}
    parser=argparse.ArgumentParser(description='Start a guarded Strata Qwen or DeepSeek profile.')
    parser.add_argument('--model',choices=list(available),default=next(iter(available)))
    strata_model=parser.parse_args(sys.argv[2:]).model
backend = monitor = log = frontend = thermal = None
worker_env = {**os.environ, 'CUDA_DEVICE_ORDER': 'PCI_BUS_ID', 'CUDA_VISIBLE_DEVICES': '0,1'}

def stop(*_):
    raise KeyboardInterrupt

for sig in (signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, stop)
try:
    # Must precede startup_handover: an obsolete profile must not kill a good server.
    llama_spec = launch_spec() if kind == 'llama' else None
    profiles = json.loads((ROOT / (kind + '-profiles.json')).read_text()) if kind in ('sglang', 'vllm') else {}
    rocm = bool(profiles) and all(profile.get('runtime') == 'rocm' for profile in profiles.values())
    if rocm:
        require_rocm(kind)
        worker_env.pop('CUDA_VISIBLE_DEVICES', None)
    elif kind == 'strata':
        selected_profile=available[strata_model]
        if selected_profile.get('family')!='deepseek41':
            profile_config = ROOT / (os.environ.get('STRATA_PROFILE_CONFIG') or selected_profile['config'])
            ensure_strata_models(profile_config)
        require_strata(before_handover=True,model=strata_model)
        worker_env.pop('CUDA_VISIBLE_DEVICES', None)
    elif kind == 'maya':
        require_maya(maya_model,before_handover=True)
        worker_env.pop('CUDA_VISIBLE_DEVICES', None)
    elif kind != 'llama':
        require_current_cuda_pair()
    if kind == 'llama':
        ensure_llama_models()
    if kind == 'llama':
        cmd = [sys.executable, str(ROOT / 'llama-router.py')]
        paths = [ROOT / 'logs/llama.cpp.log']
    elif kind in ('sglang', 'vllm'):
        cmd = [sys.executable, str(ROOT / (kind + '-router.py'))]
        profiles = json.loads((ROOT / (kind + '-profiles.json')).read_text())
        paths = [ROOT / 'logs' / (kind + '.log'),
                 *[ROOT / 'logs' / (kind + '-' + model + '.log') for model in profiles]]
    elif kind == 'maya':
        cmd = [sys.executable, str(ROOT / 'maya-router.py')]
        profiles = maya_profiles()
        paths = [ROOT / 'logs/maya-server.log']
        for model, profile in profiles.items():
            paths.append(ROOT / 'logs' / ('maya-' + model + '.log'))
            paths.append(Path(json.loads((ROOT / profile['config']).read_text())['log']))
    else:
        # Keep low-RAM native allocations out of expensive huge-page compaction.
        worker_env['STRATA_NO_ARENA_THP'] = '1'
        cmd = [sys.executable, str(ROOT / 'strata-router.py')]
        profiles = json.loads((ROOT / 'strata-profiles.json').read_text())
        paths = [ROOT / 'logs/strata-server.log']
        for model, profile in profiles.items():
            paths.append(ROOT / 'logs' / ('strata-' + model + '.log'))
            paths.append(Path(json.loads((ROOT / profile['config']).read_text())['log']))
    with startup_handover(kind) as startup:
        require_worker_ports_free(ports)
        if llama_spec and llama_spec[3] is not None:
            require_amd_headroom()
        if rocm:
            # The router enforces each profile's own requirement before it loads.
            require_rocm_headroom(min(profile.get('min_free_vram_gib', 21.0)
                                      for profile in profiles.values()))
        if kind == 'strata':
            require_strata(model=strata_model)
            require_rocm_headroom(16)
        if kind == 'maya':
            require_maya(maya_model)
        monitor = start_monitor(paths)
        print(f'{names[kind]} backend' + (' with native Chat/Monitor.' if kind in ('strata','maya') else ' only.') + ' Launch dsh separately if wanted. Ctrl+C stops this backend.', flush=True)
        print(f'Loading the selected {names[kind]} model from its configured model volume now. Cold loads may take a few minutes.' if kind in ('strata', 'maya')
              else 'Models load when requested by DSH or another API client.', flush=True)
        log = paths[0].open('a')
        thermal = ThermalRecorder(f'backend-{kind}').start()
        print(f'Thermal log: {thermal.raw_path}', flush=True)
        backend = subprocess.Popen(cmd + sys.argv[2:], stdout=log, stderr=subprocess.STDOUT,
                                   env=worker_env,
                                   start_new_session=True)
        startup.register()
        frontend = start_frontend(kind, backend, enabled=open_frontend)
    raise SystemExit(backend.wait())
except KeyboardInterrupt:
    pass
except Exception as error:
    print(f'{names[kind]} startup failed: {error}', file=sys.stderr)
    raise SystemExit(1)
finally:
    if frontend is not None:
        frontend.set()
    if backend is not None:
        try:
            os.killpg(backend.pid, signal.SIGTERM)
            backend.wait(timeout=60)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(backend.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        backend.wait()
    if thermal is not None:
        thermal.stop()
    stop_monitor(monitor)
    if log:
        log.close()
    clear_owner()
