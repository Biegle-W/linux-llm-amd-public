"""Publish a daily update: ledger entry, handoff version block, Shared copy, both repositories.

Only an explicit list of files is committed, after a privacy check; unrelated working-tree
changes are never staged. A failed push keeps the local commit and is reported.
"""
import datetime
import getpass
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT.parent/'local-llm-public'
LEDGER = 'hardware/DAILY-UPDATES.md'
HANDOFF = ROOT/'network/LINUX-LLM-RUNTIME-HANDOFF.md'
SHARED = Path('/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md')
PINS = ['dsh/llama-runtime.json', 'maya/runtime.json', 'dsh/maya-glm-profile.json', 'dsh/maya-deepseek-profile.json',
        'dsh/maya-deepseek-s-profile.json', 'sglang/fork-pin.json', 'sglang/apply-rocm-fixes.py',
        'strata-dsv41/runtime.json','dsh/strata-deepseek-s-profile.json','dsh/strata-deepseek-xs-profile.json']
BEGIN, END = '<!-- daily-update:begin -->', '<!-- daily-update:end -->'
def _identity():
    """Local account and Git e-mail names, read at run time so they never appear in the source."""
    names = {getpass.getuser()}
    email = subprocess.run(['git', '-C', str(ROOT), 'config', 'user.email'], capture_output=True, text=True).stdout.strip()
    names.update(part for part in re.split(r'[@.]', email)[:1] if len(part) > 2)
    return '|'.join(map(re.escape, sorted(names)))


PRIVATE = re.compile(r'/home/|/run/media|\b(?:100|192\.168)\.\d+\.\d+|\.ts\.net|' + _identity(), re.I)
HEADER = '''# Daily engine updates

Every night at 03:00 `llm-daily-update.timer` checks llama.cpp, vLLM, SGLang, Strata and
Maya for newer upstream versions. Each one is built in isolation, benchmarked against the
current production build with the shared method, and kept only when every standard
promotion gate passes (prefill and code/prose decode ≥95% of production, short time to
first token within max(1.25×, +0.05 s), no fewer retrieval markers, at most 64 MiB aggregate observed
worker swap and zero VRAM spill with valid launch-through-shutdown memory telemetry).
Anything else is rolled back. Newest entries first. Method: [daily-update/README.md](daily-update/README.md).

'''


def short(value):
    return value[:12] if re.fullmatch(r'[0-9a-f]{40}', value) else value


def clean(text):
    """Error details quote commands; keep repository-relative paths only."""
    text = text.replace(str(ROOT) + '/', '')
    return re.sub(r'/run/media/[^/\s]+/[^/\s]+/', '<model drive>/', re.sub(r'/home/[^\s:;,)]+', '<local path>', text))


def entry(results):
    lines = [f'## {datetime.date.today().isoformat()}', '']
    for r in results:
        lines.append(f'- **{r["engine"]}** `{short(r["from"])}` → `{short(r["to"])}`: **{r["result"]}**. {clean(r.get("detail", ""))}')
    for r in results:
        if r.get('gates'):
            lines += ['', f'{r["engine"]} gates (baseline = production the same night):', '', r['gates'].strip()]
    return '\n'.join(lines) + '\n\n'


def versions():
    from daily_update import ENGINES
    rows = []
    for engine in ENGINES.values():
        try:
            rows.append(f'| {engine.name} | `{short(engine.current())}` |')
        except Exception as error:
            rows.append(f'| {engine.name} | unknown ({type(error).__name__}) |')
    return rows


def handoff_block(results):
    today = datetime.date.today().isoformat()
    return '\n'.join([BEGIN, f'**Engine versions after the {today} daily update** (`llm-daily-update.timer`, 03:00; '
                      f'details in `hardware/DAILY-UPDATES.md`):', '', '| Engine | Production |', '|---|---|',
                      *versions(), '',
                      'Last run: ' + '; '.join(f'{r["engine"]} {r["result"]}' for r in results) + '.', END])


def update_ledger(path, text):
    old = path.read_text() if path.exists() else HEADER
    head, _, rest = old.partition('\n## ')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head.rstrip('\n') + '\n\n' + text + ('## ' + rest if rest else ''))


def update_handoff(results):
    text = HANDOFF.read_text()
    block = handoff_block(results)
    if BEGIN in text:
        text = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        anchor = 'in the Linux repository.\n'
        index = text.index(anchor) + len(anchor)
        text = text[:index] + '\n' + block + '\n' + text[index:]
    HANDOFF.write_text(text)
    if SHARED.parent.is_dir():
        shutil.copyfile(HANDOFF, SHARED)
        if SHARED.read_bytes() != HANDOFF.read_bytes():
            raise RuntimeError('Shared handoff copy differs after writing')
    else:
        raise RuntimeError('Shared drive not mounted; handoff copy not updated')


def commit(repo, paths, message, logfile):
    paths = [p for p in paths if (repo/p).exists()]
    changed = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain', '--', *paths],
                             capture_output=True, text=True, check=True).stdout.strip()
    if not changed:
        return 'nothing to commit'
    with open(logfile, 'a') as f:
        subprocess.run(['git', '-C', str(repo), 'add', '--', *paths], check=True, stdout=f, stderr=subprocess.STDOUT)
        subprocess.run(['git', '-C', str(repo), 'commit', '-m', message, '--', *paths], check=True, stdout=f,
                       stderr=subprocess.STDOUT)
        push = subprocess.run(['git', '-C', str(repo), 'push', 'origin', 'HEAD:main'], stdout=f, stderr=subprocess.STDOUT)
        if push.returncode:   # another agent pushed first: replay this commit on top once, never force
            subprocess.run(['git', '-C', str(repo), 'pull', '--rebase', '--autostash', 'origin', 'main'], stdout=f,
                           stderr=subprocess.STDOUT)
            push = subprocess.run(['git', '-C', str(repo), 'push', 'origin', 'HEAD:main'], stdout=f, stderr=subprocess.STDOUT)
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--short', 'HEAD'], text=True).strip()
    return f'{head} pushed' if push.returncode == 0 else f'{head} committed locally; push failed'


def public_deepseek_pins():
    """Publish example paths and require a new local proof after sanitizing a profile."""
    from shared_storage import STREAM_SHARED
    exported=[]
    for name in ('strata-dsv41/runtime.json','dsh/strata-deepseek-s-profile.json','dsh/strata-deepseek-xs-profile.json'):
        path=ROOT/name
        if not path.exists():continue
        text=path.read_text().replace(str(ROOT),'/opt/local-llm').replace(str(STREAM_SHARED),'/mnt/shared-nvme')
        cfg=json.loads(text)
        if 'local_validation' in cfg:
            v=cfg['local_validation'];v['status']='requires-local-validation'
            if 'config_sha256' in v:v['reference_config_sha256']=v.pop('config_sha256')
            v['note']='Sanitized example paths; validate the local binary, pack and profile before loading.'
        text=json.dumps(cfg,indent=2)+'\n'
        if PRIVATE.search(text):raise RuntimeError('Strata DeepSeek reference contains private workstation information')
        dest=PUBLIC/'linux'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        exported.append('linux/'+name)
    return exported


def publish(run, results, logfile):
    from daily_update import log
    text = entry(results)
    if PRIVATE.search(text):
        raise RuntimeError('ledger entry contains a private path or address; not published')
    update_ledger(ROOT/LEDGER, text)
    update_handoff(results)
    summary = ', '.join(f'{r["engine"]} {r["result"]}' for r in results)
    message = f'Daily engine update {datetime.date.today().isoformat()}: {summary}'
    log('private repository: ' + commit(ROOT, [LEDGER, 'network/LINUX-LLM-RUNTIME-HANDOFF.md', *PINS], message, logfile), logfile)
    if PUBLIC.is_dir():
        update_ledger(PUBLIC/'linux'/LEDGER, text)
        public_handoff = PUBLIC/'linux/network/LINUX-LLM-RUNTIME-HANDOFF.md'
        if public_handoff.exists() and BEGIN in public_handoff.read_text():   # the block holds no private paths
            public_handoff.write_text(re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda _: handoff_block(results),
                                             public_handoff.read_text(), flags=re.S))
        references=public_deepseek_pins()
        log('public repository: ' + commit(PUBLIC, ['linux/' + LEDGER, 'linux/network/LINUX-LLM-RUNTIME-HANDOFF.md',*references],
                                           message, logfile), logfile)
    (run/'published.json').write_text(json.dumps({'message': message}, indent=2) + '\n')
