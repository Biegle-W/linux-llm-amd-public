#!/usr/bin/env python3
"""Daily engine update (03:00, llm-daily-update.timer).

For every engine whose upstream moved since the last run:
1. build the newer version in isolation (no GPU, production untouched);
2. under hardware/generated/GPU-LOCK, benchmark production with the shared method;
3. install the new build at the production paths, keeping a rollback copy;
4. benchmark again through the normal launcher and keep it only if every standard
   promotion gate passes (hardware/compare-runtime-candidate.py); otherwise roll back.
A rejected revision is not retried until upstream moves again. A run interrupted while a
build is provisionally installed rolls it back first. See hardware/daily-update/README.md.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'dsh'))
sys.path.insert(0, str(ROOT/'hardware'))
from inference_memory import MemoryMonitor, memory_failures, lifecycle_failures
GEN = ROOT/'hardware/generated'
LOCK = GEN/'GPU-LOCK'
COORD = GEN/'AGENT-COORDINATION.md'
WORK = GEN/'daily-update'
STATE = WORK/'state.json'
HARNESS = ROOT/'hardware/daily-update/.venv/bin/python'   # tokenizers for the shared benchmark
PORT = {'llama': 8080, 'sglang': 30000, 'vllm': 30010, 'strata': 30020, 'maya': 30030}
OWNER = 'daily-update'
TODAY = datetime.date.today().isoformat()
BUILD_JOBS = os.environ.get('BUILD_JOBS', '8')


class Step(Exception):
    """A step failed; production is left as it was (or rolled back)."""


def now():
    return datetime.datetime.now().strftime('%H:%M:%S')


def log(message, file=None):
    line = f'[{now()}] {message}'
    print(line, flush=True)
    if file:
        with open(file, 'a') as f:
            f.write(line + '\n')


def sh(cmd, logfile, env=None, cwd=ROOT, timeout=None, check=True):
    shell = isinstance(cmd, str)
    with open(logfile, 'a') as f:
        f.write(f'\n[{now()}] $ {cmd if shell else shlex.join(map(str, cmd))}\n')
        f.flush()
        p = subprocess.run(cmd, shell=shell, executable='/bin/bash' if shell else None, cwd=cwd,
                           env=env, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
    if check and p.returncode:
        raise Step(f'command failed ({p.returncode}): {cmd if shell else shlex.join(map(str, cmd))[:160]}')
    return p.returncode


def out(cmd, cwd=ROOT, timeout=120):
    return subprocess.check_output(cmd, cwd=cwd, text=True, timeout=timeout).strip()


def remote_head(url, ref='HEAD'):
    line = out(['git', 'ls-remote', url, ref], timeout=60).split('\n')[0]
    if not line:
        raise Step(f'no {ref} at {url}')
    return line.split()[0]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {'engines': {}}


def save_state(state):
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(STATE)


def git_clone_at(source_repo, url, rev, dest, logfile):
    """Clone a local repo (shares nothing afterwards), fetch rev from upstream, check it out."""
    if dest.exists():
        shutil.rmtree(dest)
    if source_repo and (Path(source_repo)/'.git').exists() and \
            subprocess.run(['git', '-C', str(source_repo), 'rev-parse', 'HEAD'], capture_output=True).returncode == 0:
        sh(['git', 'clone', '--no-checkout', '--no-hardlinks', str(source_repo), str(dest)], logfile)
        sh(['git', '-C', str(dest), 'remote', 'set-url', 'origin', url], logfile)
    else:
        sh(['git', 'clone', '--no-checkout', url, str(dest)], logfile)
    sh(['git', '-C', str(dest), 'fetch', '--quiet', 'origin', rev], logfile)
    sh(['git', '-C', str(dest), 'checkout', '--quiet', '--detach', rev], logfile)


# ---------------------------------------------------------------- host state

def busy():
    """Reason not to start now, or None."""
    if LOCK.exists():
        try:
            holder = json.loads(LOCK.read_text()).get('owner', '?')
        except ValueError:
            holder = '?'
        return f'GPU-LOCK held by {holder}'
    journal = subprocess.run(['journalctl', '--user', '-u', 'local-llm-hub', '-u', 'local-llm-api',
                              '--since', '-20 min', '-o', 'cat', '--no-pager'],
                             capture_output=True, text=True).stdout
    if re.search(r'\bPOST /v1/', journal):
        return 'a client used a model in the last 20 minutes'
    ports = ' or '.join(f'sport = :{p}' for p in PORT.values())
    active = subprocess.run(['ss', '-Htn', 'state', 'established', f'( {ports} )'],
                            capture_output=True, text=True).stdout.strip()
    if active:
        return 'a request is in progress'
    return None


def take_lock(purpose):
    fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    os.write(fd, (json.dumps({'owner': OWNER, 'purpose': purpose,
                              'started': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                              'expected_end': 'about 3 hours', 'unit': 'llm-daily-update.service',
                              'pid': os.getpid()}) + '\n').encode())
    os.close(fd)


def release_lock():
    try:
        if json.loads(LOCK.read_text()).get('owner') == OWNER:
            LOCK.unlink()
    except (OSError, ValueError):
        pass


def coordinate(message):
    with open(COORD, 'a') as f:
        f.write(f'\n- {datetime.datetime.now().strftime("%H:%M %b%d")} — daily-update → Codex: {message}\n')


def stop_backends():
    from backend_switch import stop_other_backends
    stop_other_backends()


def vram_used():
    return max(int((d/'mem_info_vram_used').read_text()) for d in Path('/sys/bus/pci/devices').iterdir()
               if (d/'vendor').exists() and (d/'vendor').read_text().strip() == '0x1002'
               and (d/'mem_info_vram_used').exists())


def wait_idle(timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if vram_used() < 3 * 1024**3:
            return
        time.sleep(2)
    raise Step(f'GPUs not idle after stopping the backend ({vram_used() / 1024**3:.1f} GiB used)')


# ---------------------------------------------------------------- benchmark

def post(port, body, timeout):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions', json.dumps(body).encode(),
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.status


def wait_port(port, launcher, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models', timeout=5):
                return
        except OSError:
            pass
        if launcher.poll() is not None:
            raise Step(f'launcher exited ({launcher.returncode}) before port {port} answered')
        time.sleep(2)
    raise Step(f'port {port} not ready after {timeout} s')


def launcher_bench(kind, models, stage, label, logfile):
    """Normal launcher + unchanged shared benchmark for each model. Returns the merged record."""
    profiles = []
    groups = [[m] for m in models] if kind in ('maya','strata') else [models]
    monitor = MemoryMonitor().start()
    try:
        for group in groups:
            monitor.set_phase('loading')
            args = ['--no-browser'] if kind in ('strata', 'maya') else []
            if kind in ('maya','strata'):
                args += ['--model', group[0]]
            with open(stage/f'{label}-launcher.log', 'a') as launch_log:
                launcher = subprocess.Popen(['/usr/bin/python3', str(ROOT/'dsh/launch-backend.py'), kind, *args],
                                            cwd=ROOT, stdout=launch_log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                wait_port(PORT[kind], launcher, 1800)
                for model in group:
                    monitor.set_phase('loading')
                    started = time.monotonic()
                    try:
                        status = post(PORT[kind], {'model': model, 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 4,
                                                   'chat_template_kwargs': {'enable_thinking': False}}, 3600)
                        if status != 200:
                            raise Step(f'{label} {model}: prewarm returned HTTP {status}')
                    except OSError as error:
                        log(f'{label} {model}: prewarm failed ({error})', logfile)
                        raise Step(f'{label} {model}: prewarm failed') from error
                    else:
                        monitor.set_phase('inference')
                    log(f'{label} {model}: loaded in {time.monotonic() - started:.0f} s', logfile)
                    result = stage/f'{label}-{model}.json'
                    sh([str(HARNESS), str(ROOT/'hardware/benchmark-current-amd.py'), '--kind', kind, '--date', TODAY,
                        '--model', model, '--output', str(result)], stage/f'{label}-bench.log', check=False)
                    try:
                        profile = json.loads(result.read_text())['profiles'][0]
                    except (OSError, ValueError, IndexError):
                        profile = {'model': model, 'status': 'failed', 'error_type': 'no result'}
                    profiles.append(profile)
                    log(f'{label} {model}: {profile["status"]}', logfile)
            finally:
                monitor.set_phase('shutdown')
                if launcher.poll() is None:
                    os.killpg(launcher.pid, signal.SIGTERM)
                    try:
                        launcher.wait(180)
                    except subprocess.TimeoutExpired:
                        stop_backends()
                stop_backends()
                wait_idle()
    finally:
        monitor.set_phase('shutdown')
        record = {'date': TODAY, 'backend': kind, 'label': label, 'profiles': profiles,
                  'lifecycle_memory': monitor.stop()}
        (stage/f'{label}.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def gates(stage, logfile):
    p = subprocess.run([sys.executable, str(ROOT/'hardware/compare-runtime-candidate.py'), '--baseline',
                        str(stage/'baseline.json'), str(stage/'candidate.json'), '--require-lifecycle-memory'], capture_output=True, text=True)
    (stage/'gates.md').write_text(p.stdout + p.stderr)
    log('gates:\n' + p.stdout, logfile)
    return p.returncode == 0, p.stdout


def smoke(kind, model, stage, label, logfile):
    """Short normal-launcher check after a rollback: the restored build answers."""
    args = ['--no-browser'] if kind in ('strata', 'maya') else []
    if kind in ('maya','strata'):
        args += ['--model', model]
    with open(stage/f'{label}-launcher.log', 'a') as launch_log:
        launcher = subprocess.Popen(['/usr/bin/python3', str(ROOT/'dsh/launch-backend.py'), kind, *args],
                                    cwd=ROOT, stdout=launch_log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wait_port(PORT[kind], launcher, 1800)
        return post(PORT[kind], {'model': model, 'messages': [{'role': 'user', 'content': 'What is 17 times 19? Reply with only the integer.'}],
                                 'max_tokens': 64, 'temperature': 0, 'chat_template_kwargs': {'enable_thinking': False}}, 3600) == 200
    except (Step, OSError) as error:
        log(f'{label}: {error}', logfile)
        return False
    finally:
        if launcher.poll() is None:
            os.killpg(launcher.pid, signal.SIGTERM)
            try:
                launcher.wait(180)
            except subprocess.TimeoutExpired:
                pass
        stop_backends()
        wait_idle()


# ---------------------------------------------------------------- engines

class Engine:
    """prepare() never touches production; install() saves what rollback() needs first."""
    name = kind = ''

    def models(self):
        raise NotImplementedError

    def current(self):
        raise NotImplementedError

    def latest(self):
        raise NotImplementedError

    def prepare(self, stage, rev, logfile):
        raise NotImplementedError

    def check(self, stage, logfile):
        """Optional GPU correctness tests on the isolated build (lock held, before install)."""

    def install(self, stage, rev, logfile):
        raise NotImplementedError

    def rollback(self, stage, logfile):
        raise NotImplementedError

    def finalize(self, stage, rev, gate_table):
        """Record the promoted version in the engine's pin files."""


class Llama(Engine):
    name, kind = 'llama.cpp', 'llama'
    url = 'https://github.com/ggml-org/llama.cpp.git'
    src = ROOT/'llama.cpp'
    pin = ROOT/'dsh/llama-runtime.json'

    def models(self):
        return json.loads(self.pin.read_text())['models']

    def current(self):
        return json.loads(self.pin.read_text())['source_commit']

    def latest(self):
        return remote_head(self.url, 'refs/heads/master')

    def prepare(self, stage, rev, logfile):
        # Compile check in an isolated clone; the production rebuild happens in install().
        sh(['git', '-C', str(self.src), 'fetch', '--quiet', 'origin', rev], logfile)
        git_clone_at(self.src, self.url, rev, stage/'llama.cpp', logfile)
        sh(['bash', str(ROOT/'hardware/build-llama-hip.sh')], logfile,
           env={**os.environ, 'LLAMA_SRC': str(stage/'llama.cpp'), 'BUILD_JOBS': BUILD_JOBS})

    def install(self, stage, rev, logfile):
        rollback = stage/'rollback'
        rollback.mkdir()
        (rollback/'source_commit').write_text(out(['git', '-C', str(self.src), 'rev-parse', 'HEAD']))
        shutil.copy2(self.pin, rollback/'llama-runtime.json')
        sh(['cp', '-a', str(self.src/'build-hip'), str(rollback/'build-hip')], logfile)
        sh(['git', '-C', str(self.src), 'checkout', '--quiet', '--detach', rev], logfile)
        sh(['bash', str(ROOT/'hardware/build-llama-hip.sh')], logfile, env={**os.environ, 'BUILD_JOBS': BUILD_JOBS})
        pin = json.loads(self.pin.read_text())
        pin['source_commit'] = rev
        self.pin.write_text(json.dumps(pin, indent=2) + '\n')

    def rollback(self, stage, logfile):
        rollback = stage/'rollback'
        if not (rollback/'source_commit').exists():
            return
        sh(['git', '-C', str(self.src), 'checkout', '--quiet', '--detach', (rollback/'source_commit').read_text().strip()], logfile)
        if (rollback/'build-hip').exists():
            shutil.rmtree(self.src/'build-hip', ignore_errors=True)
            sh(['cp', '-a', str(rollback/'build-hip'), str(self.src/'build-hip')], logfile)
        shutil.copy2(rollback/'llama-runtime.json', self.pin)


class Vllm(Engine):
    name, kind = 'vLLM', 'vllm'
    env = ROOT/'vllm/.venv-rocm'
    index = 'https://wheels.vllm.ai/rocm/nightly/{variant}/vllm/'

    def models(self):
        return [k for k, v in json.loads((ROOT/'dsh/vllm-profiles.json').read_text()).items() if v.get('enabled', True)]

    def current(self):
        return out([str(self.env/'bin/python'), '-c', 'import importlib.metadata as m;print(m.version("vllm"))'])

    def latest(self):
        variant = self.current().rsplit('.', 1)[-1]          # e.g. rocm72: keep the same ROCm wheel line
        page = urllib.request.urlopen(self.index.format(variant=variant), timeout=60).read().decode()
        wheels = set(re.findall(r'vllm-([0-9][^"<>/]*?)-cp312-cp312-manylinux[^"<>/]*\.whl', page.replace('%2B', '+')))
        def key(version):
            nums = re.findall(r'\d+', version.split('+')[0])
            return [int(n) for n in nums]
        wheels = [w for w in wheels if w.endswith('.' + variant)]
        if not wheels:
            raise Step(f'no {variant} wheels listed')
        return max(wheels, key=key)

    def prepare(self, stage, version, logfile):
        variant = version.rsplit('.', 1)[-1]
        page = urllib.request.urlopen(self.index.format(variant=variant), timeout=60).read().decode()
        names = [n for n in re.findall(r'href="([^"]+\.whl)', page) if version.replace('+', '%2B') in n or version in n]
        if not names:
            raise Step(f'wheel {version} not found')
        wheel_url = urllib.request.urljoin(self.index.format(variant=variant), names[0])
        wheel = stage/f'vllm-{version}-cp312-cp312-manylinux_2_39_x86_64.whl'
        sh(['curl', '-fsSL', '-o', str(wheel), wheel_url], logfile, timeout=3600)
        sh(['cp', '-a', str(self.env), str(stage/'venv')], logfile)
        # Keep the private ROCm Torch stack; anything else may move with the new wheel. Its ROCm
        # kernel dependencies (amd-aiter) come from the same nightly index.
        python = str(stage/'venv/bin/python')
        frozen = out(['uv', 'pip', 'freeze', '--python', python])
        keep = [line for line in frozen.splitlines() if re.match(r'(torch|torchvision|torchaudio|triton|pytorch-triton-rocm|amdsmi)==', line)]
        (stage/'constraints.txt').write_text('\n'.join(keep) + '\n')
        sh(['uv', 'pip', 'install', '--python', python, '--constraint', str(stage/'constraints.txt'),
            '--extra-index-url', self.index.format(variant=variant).removesuffix('vllm/'), str(wheel)],
           logfile, timeout=3600)
        sh(['uv', 'pip', 'check', '--python', python], logfile)
        env = {**os.environ, 'VLLM_ENV_PATH': str(stage/'venv')}
        sh([sys.executable, str(ROOT/'vllm/apply-rocm-fixes.py')], logfile, env=env)
        sh([sys.executable, str(ROOT/'vllm/apply-rdna-prefill.py')], logfile, env=env)
        sh([python, '-c', 'import vllm, torch; print(vllm.__version__, torch.__version__)'], logfile)

    def install(self, stage, version, logfile):
        os.rename(self.env, stage/'rollback-venv')
        os.rename(stage/'venv', self.env)

    def rollback(self, stage, logfile):
        if (stage/'rollback-venv').exists():
            if self.env.exists():
                os.rename(self.env, stage/'rejected-venv')
            os.rename(stage/'rollback-venv', self.env)


class Sglang(Engine):
    """The gfx1100 fork plus the local fixes in sglang/apply-rocm-fixes.py (which refuse changed code)."""
    name, kind = 'SGLang', 'sglang'
    url = 'https://github.com/StevenChenSE/sglang.git'
    branch = 'refs/heads/gfx1100-support'
    src = ROOT/'sglang/rocm-src'
    env = ROOT/'sglang/.venv-rocm'
    pin = ROOT/'sglang/fork-pin.json'

    def models(self):
        return [k for k, v in json.loads((ROOT/'dsh/sglang-profiles.json').read_text()).items() if v.get('enabled', True)]

    def current(self):
        if self.pin.exists():
            return json.loads(self.pin.read_text())['source_commit']
        return out(['git', '-C', str(self.src), 'rev-parse', 'HEAD'])

    def latest(self):
        return remote_head(self.url, self.branch)

    def prepare(self, stage, rev, logfile):
        git_clone_at(self.src, self.url, rev, stage/'rocm-src', logfile)
        sh(['cp', '-a', str(self.env), str(stage/'venv')], logfile)

    def install(self, stage, rev, logfile):
        # Paths inside the environment and kernel build are absolute, so the fixes, kernels and
        # editable install are applied after the swap, at the production paths.
        if self.pin.exists():
            shutil.copy2(self.pin, stage/'pin-before.json')
        os.rename(self.src, stage/'rollback-rocm-src')
        os.rename(self.env, stage/'rollback-venv')
        os.rename(stage/'rocm-src', self.src)
        os.rename(stage/'venv', self.env)
        env = {**os.environ, 'SGLANG_FORK_COMMIT': rev}
        sh([sys.executable, str(ROOT/'sglang/apply-rocm-fixes.py')], logfile, env=env)
        sh(['uv', 'pip', 'install', '--python', str(self.env/'bin/python'), '--no-deps', '-e', str(self.src/'python')], logfile)
        sh(['bash', str(ROOT/'hardware/build-sglang-rocm.sh')], logfile, timeout=4 * 3600)
        self.pin.write_text(json.dumps({'repository': self.url, 'branch': self.branch.split('/')[-1],
                                        'source_commit': rev}, indent=2) + '\n')

    def rollback(self, stage, logfile):
        for prod, saved in ((self.src, 'rollback-rocm-src'), (self.env, 'rollback-venv')):
            if (stage/saved).exists():
                if prod.exists():
                    os.rename(prod, stage/('rejected-' + saved.split('-', 1)[1]))
                os.rename(stage/saved, prod)
        if (stage/'pin-before.json').exists():
            shutil.copy2(stage/'pin-before.json', self.pin)
        else:
            self.pin.unlink(missing_ok=True)


class Strata(Engine):
    name, kind = 'Strata', 'strata'
    url = 'https://github.com/Niko1221/Strata.git'
    src = ROOT/'strata'
    build = ROOT/'strata/build-hip'

    def models(self):
        return [k for k, v in json.loads((ROOT/'dsh/strata-profiles.json').read_text()).items()
                if v.get('enabled', True) and v.get('family')!='deepseek41']

    def current(self):
        return json.loads((self.build/'local-build.json').read_text())['source_commit']

    def latest(self):
        return remote_head(self.url)

    def ggml_dir(self, source, stage, logfile):
        declared = (source/'third_party/ggml/VERSION.txt').read_text().split()[0]
        prod = json.loads((self.build/'local-build.json').read_text())['ggml']
        if declared == prod.get('declared_archive_commit', prod.get('source_commit')):
            return Path(prod['source_directory'])
        dest = stage/'ggml-llama.cpp'
        git_clone_at(ROOT/'llama.cpp', 'https://github.com/ggml-org/llama.cpp.git', declared, dest, logfile)
        return dest

    def prepare(self, stage, rev, logfile):
        git_clone_at(None, self.url, rev, stage/'src', logfile)
        ggml = self.ggml_dir(stage/'src', stage, logfile)
        sh(['bash', str(ROOT/'hardware/build-strata-hip.sh')], logfile,
           env={**os.environ, 'STRATA_SOURCE_DIR': str(stage/'src'), 'STRATA_BUILD_DIR': str(stage/'src/build-hip'),
                'STRATA_GGML_DIR': str(ggml), 'BUILD_JOBS': BUILD_JOBS})

    def tracked(self, repo, rev):
        return set(out(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', rev]).splitlines())

    def install(self, stage, rev, logfile):
        # The managed runtime runs this tree's Python server beside the engine, so both move together.
        rollback = stage/'rollback'
        rollback.mkdir()
        old = self.current()
        new_files, old_files = self.tracked(stage/'src', rev), self.tracked(stage/'src', old)
        (rollback/'files.json').write_text(json.dumps({'old_commit': old, 'old': sorted(old_files),
                                                       'new_only': sorted(new_files - old_files)}) + '\n')
        existing = [f for f in sorted(old_files | new_files) if (self.src/f).is_file()]
        (rollback/'list.txt').write_text('\n'.join(existing) + '\n')
        sh(['tar', '-C', str(self.src), '-cf', str(rollback/'tracked.tar'), '-T', str(rollback/'list.txt')], logfile)
        for name in ('strata', 'strata-device', 'local-build.json'):
            shutil.copy2(self.build/name, rollback/name)
        if (self.src/'.git').exists():
            os.rename(self.src/'.git', rollback/'git')
        sh(['cp', '-a', str(stage/'src/.git'), str(self.src/'.git')], logfile)
        sh(['git', '-C', str(self.src), 'checkout', '--quiet', '--force', '--detach', rev], logfile)
        for name in ('strata', 'strata-device', 'local-build.json'):
            tmp = self.build/(name + '.new')
            shutil.copy2(stage/'src/build-hip'/name, tmp)
            os.replace(tmp, self.build/name)

    def rollback(self, stage, logfile):
        rollback = stage/'rollback'
        if not (rollback/'files.json').exists():
            return
        info = json.loads((rollback/'files.json').read_text())
        for f in info['new_only']:
            (self.src/f).unlink(missing_ok=True)
        if (rollback/'tracked.tar').exists():
            sh(['tar', '-C', str(self.src), '-xf', str(rollback/'tracked.tar')], logfile)
        for name in ('strata', 'strata-device', 'local-build.json'):
            if (rollback/name).exists():
                shutil.copy2(rollback/name, self.build/name)
        if (rollback/'git').exists():
            shutil.rmtree(self.src/'.git', ignore_errors=True)
            os.rename(rollback/'git', self.src/'.git')


class Maya(Engine):
    name, kind = 'Maya', 'maya'
    url = 'https://github.com/mw00/project-maya.git'
    src = ROOT/'maya/upstream'
    pin = ROOT/'maya/runtime.json'
    binaries = ('maya', 'maya-ds4')
    # Kernel parity tests run on each GPU before install (as for 1.1.24). hip_prefill_fused_parity
    # is recorded but not blocking: that path failed parity on gfx1100 and production disables it
    # (MAYA_GLM_PREFILL_FUSED=0 in the GLM profile).
    parity = ['glm_model_test', 'hip_expert_cache_staging', 'hip_intrinsics', 'hip_handoff', 'hip_glm_handoff',
              'hip_glm_prefill_attention', 'iq1_s_parity', 'glm_hc_parity', 'glm_kda_parity', 'glm_ffn_parity',
              'glm_dsa_parity', 'glm_layer_parity', 'hip_device_selftest', 'hip_prefill_mmq_parity',
              'hip_prefill_fused_parity', 'hip_expert_kernel_parity', 'glm_mv_parity', 'hip_prefill_native_batch']
    not_blocking = {'hip_prefill_fused_parity'}

    def models(self):
        return [k for k, v in json.loads((ROOT/'dsh/maya-profiles.json').read_text()).items() if v.get('enabled', False)]

    def current(self):
        return json.loads(self.pin.read_text())['source_commit']

    def latest(self):
        return remote_head(self.url)

    def prepare(self, stage, rev, logfile):
        source = stage/'source'
        git_clone_at(self.src, self.url, rev, source, logfile)
        declared = (source/'third_party/ggml/VERSION.txt').read_text().split()[0]
        ggml = self.src/'third_party/llama.cpp'
        if declared != json.loads(self.pin.read_text())['llama_dependency']:
            ggml = stage/'llama.cpp'
            git_clone_at(ROOT/'llama.cpp', 'https://github.com/ggml-org/llama.cpp.git', declared, ggml, logfile)
        (stage/'ggml-dir').write_text(str(ggml))
        os.symlink(self.src/'.venv', source/'.venv')
        cmake = str(self.src/'.venv/bin/cmake')
        sh(f'source maya/build-env.sh && "{cmake}" -S "{source}" -B "{source}/build-hip" -G Ninja '
           f'-DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_HIP=ON -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_PREFILL_MMQ=ON '
           f'-DSTRATA_BUILD_TESTS=ON -DSTRATA_NATIVE_EXPERTS=ON -DSTRATA_GGML_DIR="{ggml}" '
           f'-DCMAKE_HIP_ARCHITECTURES=gfx1100 -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" && '
           f'"{cmake}" --build "{source}/build-hip" -j {BUILD_JOBS}', logfile)
        for name in self.binaries:
            if not (source/'build-hip'/name).is_file():
                raise Step(f'build produced no {name}')

    def check(self, stage, logfile):
        source = stage/'source'
        results = []
        for gpu in (0, 1):
            for name in self.parity:
                cmd = (f'source maya/build-env.sh && export HIP_VISIBLE_DEVICES={gpu} ROCR_VISIBLE_DEVICES=0,1 && '
                       f'unset CUDA_VISIBLE_DEVICES && exec "{source}/.venv/bin/ctest" --test-dir "{source}/build-hip" '
                       f'--no-tests=error --output-on-failure -R "^{name}$"')
                rc = sh(cmd, stage/f'parity-gpu{gpu}.log', timeout=600, check=False)
                results.append({'gpu': gpu, 'test': name, 'returncode': rc})
        (stage/'parity.json').write_text(json.dumps(results, indent=2) + '\n')
        failed = sorted({f'{r["test"]} (GPU{r["gpu"]})' for r in results
                         if r['returncode'] and r['test'] not in self.not_blocking})
        if failed:
            raise Step('kernel parity failed: ' + ', '.join(failed))

    def profile_files(self):
        return sorted((ROOT/'dsh').glob('maya-*-profile.json'))

    def install(self, stage, rev, logfile):
        from maya_runtime import config_fingerprint
        rollback = stage/'rollback'
        rollback.mkdir()
        (rollback/'source_commit').write_text(out(['git', '-C', str(self.src), 'rev-parse', 'HEAD']))
        for path in [self.pin, *self.profile_files()] + [self.src/'build-hip'/b for b in self.binaries]:
            shutil.copy2(path, rollback/path.name)
        ggml = Path((stage/'ggml-dir').read_text())
        if ggml != self.src/'third_party/llama.cpp':
            os.rename(self.src/'third_party/llama.cpp', rollback/'llama.cpp')
            sh(['cp', '-a', str(ggml), str(self.src/'third_party/llama.cpp')], logfile)
        sh(['git', '-C', str(self.src), 'fetch', '--quiet', str(stage/'source'), rev], logfile)
        sh(['git', '-C', str(self.src), 'checkout', '--quiet', '--detach', rev], logfile)
        for name in self.binaries:
            tmp = self.src/'build-hip'/(name + '.new')
            shutil.copy2(stage/'source/build-hip'/name, tmp)
            os.replace(tmp, self.src/'build-hip'/name)
        version = (stage/'source/VERSION').read_text().strip() if (stage/'source/VERSION').exists() else rev[:7]
        runtime = json.loads(self.pin.read_text())
        runtime.update(source_commit=rev, version=version,
                       status=f'daily-update {TODAY}: provisional, normal-launcher gates running')
        if ggml != self.src/'third_party/llama.cpp':
            runtime['llama_dependency'] = (stage/'source/third_party/ggml/VERSION.txt').read_text().split()[0]
        self.pin.write_text(json.dumps(runtime, indent=2) + '\n')
        for path in self.profile_files():
            cfg = json.loads(path.read_text())
            validation = cfg.setdefault('local_validation', {})
            validation.update(status='passed', source_commit=rev, binary_sha256=sha256(cfg['exe']),
                              config_sha256=config_fingerprint(cfg), candidate_tag=f'daily-update-{TODAY}',
                              validated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                              normal_integration_status='pending')
            path.write_text(json.dumps(cfg, indent=2) + '\n')

    def rollback(self, stage, logfile):
        rollback = stage/'rollback'
        if not (rollback/'source_commit').exists():
            return
        sh(['git', '-C', str(self.src), 'checkout', '--quiet', '--detach', (rollback/'source_commit').read_text().strip()], logfile)
        if (rollback/'llama.cpp').exists():
            shutil.rmtree(self.src/'third_party/llama.cpp', ignore_errors=True)
            os.rename(rollback/'llama.cpp', self.src/'third_party/llama.cpp')
        for name in self.binaries:
            shutil.copy2(rollback/name, self.src/'build-hip'/name)
        for path in [self.pin, *self.profile_files()]:
            if (rollback/path.name).exists():
                shutil.copy2(rollback/path.name, path)

    def finalize(self, stage, rev, gate_table):
        runtime = json.loads(self.pin.read_text())
        runtime['status'] = f'daily-update {TODAY}: promoted after normal-launcher gates and per-GPU kernel parity'
        self.pin.write_text(json.dumps(runtime, indent=2) + '\n')
        for path in self.profile_files():
            cfg = json.loads(path.read_text())
            cfg['local_validation'].update(
                normal_integration_status='passed', evidence=f'hardware/generated/daily-update/{TODAY}/maya',
                normal_validated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                scope=f'Daily update {TODAY}: source {rev[:7]} passed the shared-method gates against same-night '
                      'production through the normal launcher and per-GPU kernel parity; profile settings unchanged.')
            path.write_text(json.dumps(cfg, indent=2) + '\n')


class StrataDeepSeek(Engine):
    """Separate upstream component: never substitute its binary for the Qwen engine."""
    name,kind,routing_kind='Strata DeepSeek','strata-dsv41','strata'
    url='https://github.com/Niko1221/Strata.git'
    src=ROOT/'strata-dsv41/upstream'
    pin=ROOT/'strata-dsv41/runtime.json'

    def models(self):
        return [k for k,v in json.loads((ROOT/'dsh/strata-profiles.json').read_text()).items()
                if v.get('enabled',True) and v.get('family')=='deepseek41']

    def profile_files(self):
        profiles=json.loads((ROOT/'dsh/strata-profiles.json').read_text())
        return [ROOT/'dsh'/profiles[m]['config'] for m in self.models()]

    def current(self):
        return json.loads(self.pin.read_text())['source_commit']

    def latest(self):
        return remote_head(self.url)

    def prepare(self,stage,rev,logfile):
        source=stage/'src'
        git_clone_at(self.src,self.url,rev,source,logfile)
        declared=(source/'third_party/ggml/VERSION.txt').read_text().split()[0]
        old=json.loads((self.src/'build-hip/local-build.json').read_text())['ggml']
        ggml=Path(old['source_directory'])
        if declared!=old.get('declared_archive_commit',old.get('source_commit')):
            ggml=stage/'ggml-llama.cpp'
            git_clone_at(ROOT/'llama.cpp','https://github.com/ggml-org/llama.cpp.git',declared,ggml,logfile)
        sh(['bash',str(ROOT/'hardware/build-strata-dsv41-hip.sh')],logfile,
           env={**os.environ,'STRATA_DSV41_SOURCE_DIR':str(source),
                'STRATA_GGML_DIR':str(ggml),'BUILD_JOBS':BUILD_JOBS})
        sh([str(ROOT/'strata/.venv/bin/python'),'-W','ignore','-m','unittest','serve.test_dsv41'],
           stage/'cpu-tests.log',cwd=source)

    def check(self,stage,logfile):
        from gpu_telemetry import ThermalRecorder
        telemetry=ThermalRecorder('daily-strata-deepseek-parity').start()
        try:
            sh(f'source hardware/rocm-env.sh && export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PWD/llm-tools/cuda-build/lib" && '
               f'"{stage}/src/build-hip/ds4_iq_test" --devices 0,1 --type 19,16,18,21,22',logfile)
            sh(f'source hardware/rocm-env.sh && export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PWD/llm-tools/cuda-build/lib" && '
               f'"{stage}/src/build-hip/ds4_iq_shape_test" --devices 0,1 --type 19,16,18,21,22',logfile)
            for gpu in (0,1):
                sh(f'source hardware/rocm-env.sh && export HIP_VISIBLE_DEVICES={gpu} ROCR_VISIBLE_DEVICES=0,1 && '
                   f'export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PWD/llm-tools/cuda-build/lib" && '
                   f'"{stage}/src/build-hip/ds4_core_selected_test" 5120 2304',stage/f'core-parity-gpu{gpu}.log')
            sh(f'source hardware/rocm-env.sh && export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PWD/llm-tools/cuda-build/lib" && '
               f'"{stage}/src/build-hip/ds4_slot_test"',logfile)
        finally:
            (stage/'parity-thermal.json').write_text(json.dumps(telemetry.stop(),indent=2)+'\n')

    def install(self,stage,rev,logfile):
        from strata_ds41_runtime import config_fingerprint
        version=re.search(r'project\(strata VERSION ([0-9.]+)',(stage/'src/CMakeLists.txt').read_text())
        if version is None:
            raise Step('Cannot read the candidate DeepSeek engine version; refusing installation')
        rollback=stage/'rollback';rollback.mkdir()
        for path in [self.pin,*self.profile_files()]:shutil.copy2(path,rollback/path.name)
        os.rename(self.src,rollback/'upstream')
        shutil.copytree(stage/'src',self.src,symlinks=True)
        pin=json.loads(self.pin.read_text());pin.update(source_commit=rev,status='provisional daily-update '+TODAY)
        pin['engine_version']=version.group(1)
        self.pin.write_text(json.dumps(pin,indent=2)+'\n')
        binary=sha256(self.src/'build-hip/strata-dsv41')
        for path in self.profile_files():
            cfg=json.loads(path.read_text())
            cfg['local_validation'].update(status='passed',source_commit=rev,binary_sha256=binary,
                config_sha256=config_fingerprint(cfg),normal_integration_status='pending')
            path.write_text(json.dumps(cfg,indent=2)+'\n')

    def rollback(self,stage,logfile):
        rollback=stage/'rollback'
        if (rollback/'upstream').exists():
            shutil.rmtree(self.src,ignore_errors=True);os.rename(rollback/'upstream',self.src)
        for path in [self.pin,*self.profile_files()]:
            if (rollback/path.name).exists():shutil.copy2(rollback/path.name,path)

    def finalize(self,stage,rev,gate_table):
        pin=json.loads(self.pin.read_text());pin['status']='promoted after dual-card parity and normal-launcher gates'
        self.pin.write_text(json.dumps(pin,indent=2)+'\n')
        for path in self.profile_files():
            cfg=json.loads(path.read_text());cfg['local_validation'].update(
                normal_integration_status='passed',evidence=f'hardware/generated/daily-update/{TODAY}/strata-dsv41')
            path.write_text(json.dumps(cfg,indent=2)+'\n')


ENGINES = {e.kind: e for e in (Llama(), Vllm(), Sglang(), Strata(), Maya(), StrataDeepSeek())}


# ---------------------------------------------------------------- run

BULKY = ('rollback', 'rollback-venv', 'rollback-rocm-src', 'rejected-venv', 'rejected-rocm-src', 'venv', 'source',
         'src', 'llama.cpp', 'rocm-src', 'ggml-llama.cpp')


def cleanup(state, days=14):
    """Drop build trees and rollback copies older than two weeks; reports and records stay."""
    if not WORK.is_dir():
        return
    keep = Path(state['provisional']['stage']).parent if state.get('provisional') else None
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    for run in WORK.iterdir():
        try:
            if not run.is_dir() or run == keep or datetime.date.fromisoformat(run.name) >= cutoff:
                continue
        except ValueError:
            continue
        for stage in run.iterdir():
            if stage.is_dir():
                for item in stage.iterdir():
                    if item.name in BULKY and item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    elif item.suffix in ('.whl', '.tar'):
                        item.unlink(missing_ok=True)


def recover(state, logfile):
    pending = state.get('provisional')
    if not pending:
        return
    engine = ENGINES[pending['engine']]
    log(f'{engine.name}: a previous run stopped while {pending["revision"]} was provisionally installed; rolling back', logfile)
    stop_backends()
    engine.rollback(Path(pending['stage']), logfile)
    state['engines'].setdefault(engine.kind, {}).update(rejected=pending['revision'], reason='interrupted run', date=TODAY)
    state.pop('provisional')
    save_state(state)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='Only show current and upstream versions (no build, no GPU)')
    ap.add_argument('--engines', default=','.join(ENGINES), help='Comma-separated subset: ' + ','.join(ENGINES))
    ap.add_argument('--retry-rejected', action='store_true', help='Test a previously rejected revision again')
    ap.add_argument('--wait-until', default='06:30', help='Keep waiting for an idle machine until this local time')
    ap.add_argument('--no-publish', action='store_true', help='Do not update docs or push the repositories')
    ap.add_argument('--recover-only', action='store_true', help='Only roll back a build left provisionally installed by an interrupted run')
    args = ap.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))   # run the finally blocks: roll back, release the lock
    selected = [ENGINES[k] for k in args.engines.split(',')]
    state = load_state()
    run = WORK/TODAY
    if state.get('provisional') and not args.check:
        run.mkdir(parents=True, exist_ok=True)
        recover(state, run/'run.log')
    if args.recover_only:
        return
    if not args.check:
        cleanup(state)

    found = []
    for engine in selected:
        try:
            current, latest = engine.current(), engine.latest()
        except (Step, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
            print(f'{engine.name}: version check failed: {error}')
            continue
        info = state['engines'].get(engine.kind, {})
        status = 'current' if current == latest else \
            'rejected before' if info.get('rejected') == latest and not args.retry_rejected else 'update available'
        print(f'{engine.name:9} production {current[:24]:24} upstream {latest[:24]:24} {status}')
        if status == 'update available':
            found.append((engine, current, latest))
    if args.check or not found:
        return
    run.mkdir(parents=True, exist_ok=True)
    logfile = run/'run.log'
    results = []

    prepared = []
    for engine, current, latest in found:
        stage = run/engine.kind
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        log(f'{engine.name}: building {latest} in isolation', logfile)
        try:
            engine.prepare(stage, latest, stage/'build.log')
            prepared.append((engine, current, latest, stage))
        except (Step, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
            log(f'{engine.name}: build failed: {error}', logfile)
            results.append({'engine': engine.name, 'from': current, 'to': latest, 'result': 'build failed', 'detail': str(error)})
            state['engines'].setdefault(engine.kind, {}).update(rejected=latest, reason='build failed', date=TODAY)
            save_state(state)

    deadline = datetime.datetime.combine(datetime.date.today(), datetime.time.fromisoformat(args.wait_until))
    while prepared and (reason := busy()):
        if datetime.datetime.now() >= deadline:
            log(f'not started: {reason}; retrying tomorrow', logfile)
            for engine, current, latest, _ in prepared:
                results.append({'engine': engine.name, 'from': current, 'to': latest, 'result': 'skipped (machine busy)', 'detail': reason})
            prepared = []
            break
        log(f'waiting: {reason}', logfile)
        time.sleep(600)

    if prepared:
        take_lock('daily engine update: ' + ', '.join(f'{e.name} {r[:12]}' for e, _, r, _ in prepared))
        coordinate('daily update started; GPU-LOCK held (unit llm-daily-update.service). Testing '
                   + ', '.join(f'{e.name} {c[:12]}→{r[:12]}' for e, c, r, _ in prepared)
                   + '. Production keeps a rollback copy; please no GPU work until release.')
        try:
            stop_backends()
            wait_idle()
            for engine, current, latest, stage in prepared:
                results.append(test_engine(engine, current, latest, stage, state, logfile))
        finally:
            if state.get('provisional'):          # stopped mid-test: never leave an untested build in place
                recover(state, logfile)
            release_lock()
            coordinate('daily update finished; GPU-LOCK released. '
                       + '; '.join(f'{r["engine"]}: {r["result"]}' for r in results))

    report(run, results)
    if not args.no_publish and any(r['result'] in ('promoted', 'rejected') for r in results):
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from publish import publish
            publish(run, results, logfile)
        except Exception as error:  # publication never undoes a tested runtime change
            log(f'publication failed: {error}', logfile)
    notify(results)


def test_engine(engine, current, latest, stage, state, logfile):
    row = {'engine': engine.name, 'kind': engine.kind, 'from': current, 'to': latest}
    log(f'{engine.name}: baseline benchmark of production {current[:12]}', logfile)
    try:
        baseline = launcher_bench(getattr(engine,'routing_kind',engine.kind), engine.models(), stage, 'baseline', logfile)
    except Step as error:
        return {**row, 'result': 'skipped (production baseline failed)', 'detail': str(error)}
    failed = [p['model'] for p in baseline['profiles']
              if p.get('status') != 'passed' or memory_failures(p.get('memory'))]
    lifecycle = lifecycle_failures(baseline)
    expected = engine.models()
    actual = [p['model'] for p in baseline['profiles']]
    if not expected or sorted(actual) != sorted(expected) or len(actual) != len(set(actual)):
        lifecycle.append('incomplete_production_model_coverage')
    if failed or lifecycle:
        detail = ', '.join(failed + lifecycle)
        return {**row, 'result': 'skipped (production baseline failed)', 'detail': detail}
    try:
        engine.check(stage, stage/'check.log')
    except (Step, OSError, subprocess.SubprocessError) as error:
        state['engines'].setdefault(engine.kind, {}).update(rejected=latest, reason=str(error), date=TODAY)
        save_state(state)
        return {**row, 'result': 'rejected', 'detail': str(error)}

    state['provisional'] = {'engine': engine.kind, 'revision': latest, 'stage': str(stage)}
    save_state(state)
    passed, table, detail = False, '', ''
    try:
        log(f'{engine.name}: installing {latest[:12]} provisionally', logfile)
        engine.install(stage, latest, stage/'install.log')
        log(f'{engine.name}: candidate benchmark through the normal launcher', logfile)
        launcher_bench(getattr(engine,'routing_kind',engine.kind), engine.models(), stage, 'candidate', logfile)
        passed, table = gates(stage, logfile)
        detail = 'all gates passed' if passed else 'missed a promotion gate'
    except (Step, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        detail = f'{type(error).__name__}: {error}'
        log(f'{engine.name}: candidate failed: {detail}', logfile)
    if passed:
        engine.finalize(stage, latest, table)
        state['engines'][engine.kind] = {'production': latest, 'promoted': TODAY}
        result = 'promoted'
    else:
        log(f'{engine.name}: rolling back to {current[:12]}', logfile)
        try:
            stop_backends()
            engine.rollback(stage, stage/'rollback.log')
            restored = engine.current() == current
            answered = smoke(getattr(engine,'routing_kind',engine.kind), engine.models()[0], stage, 'rollback-smoke', logfile)
            detail += f'; rollback {"verified" if restored and answered else "NEEDS ATTENTION"}'
        except Exception as error:
            detail += f'; ROLLBACK FAILED: {error}'
        state['engines'].setdefault(engine.kind, {}).update(rejected=latest, reason=detail, date=TODAY)
        result = 'rejected'
    state.pop('provisional', None)
    save_state(state)
    log(f'{engine.name}: {result} ({detail})', logfile)
    return {**row, 'result': result, 'detail': detail, 'gates': table}


def report(run, results):
    """Merge with an earlier run the same day (a newer result for an engine replaces the older)."""
    try:
        earlier = json.loads((run/'report.json').read_text())
    except (OSError, ValueError):
        earlier = []
    engines = {r['engine'] for r in results}
    results = [r for r in earlier if r['engine'] not in engines] + list(results)
    lines = [f'# Daily engine update — {TODAY}', '']
    if not results:
        lines.append('Nothing to do.')
    for r in results:
        lines += [f'## {r["engine"]}: {r["result"]}', '', f'- From `{r["from"]}` to `{r["to"]}`', f'- {r.get("detail", "")}', '']
        if r.get('gates'):
            lines += [r['gates'], '']
    (run/'report.md').write_text('\n'.join(lines) + '\n')
    (run/'report.json').write_text(json.dumps(results, indent=2) + '\n')


def notify(results):
    if not results:
        return
    summary = '; '.join(f'{r["engine"]}: {r["result"]}' for r in results)
    subprocess.run(['notify-send', '--app-name=Local LLM', 'Daily engine update', summary], check=False,
                   capture_output=True)


if __name__ == '__main__':
    main()
