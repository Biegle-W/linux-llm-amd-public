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
        'sglang/fork-pin.json', 'sglang/apply-rocm-fixes.py',
        'strata-dsv41/runtime.json','dsh/strata-deepseek-xs-profile.json']
BEGIN, END = '<!-- daily-update:begin -->', '<!-- daily-update:end -->'
def _identity():
    """Local account and Git e-mail names, read at run time so they never appear in the source."""
    names = {getpass.getuser()}
    email = subprocess.run(['git', '-C', str(ROOT), 'config', 'user.email'], capture_output=True, text=True).stdout.strip()
    names.update(part for part in re.split(r'[@.]', email)[:1] if len(part) > 2)
    return '|'.join(map(re.escape, sorted(names)))


PRIVATE = re.compile(r'/home/|/run/media|\b(?:100|192\.168)\.\d+\.\d+|\.ts\.net|' + _identity(), re.I)
HEADER = '''# Daily engine updates

The existing 03:00 updater uses isolated builds, required per-card parity and one strict two-step DSH read-tool round trip per enabled qualified profile, then owned unload. It retains source/profile/weight identities, manual holds, rollback, 100°C thermal/storage, RAM/VRAM/spill/swap, heartbeat and cleanup guards. No routine full-window or throughput comparison is claimed. Rejected revisions wait for a changed upstream. The runtime handoff records schedule state. [Method](daily-update/README.md).

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
    import daily_update
    ENGINES=getattr(daily_update,'active_engines',lambda:daily_update.ENGINES)()
    rows = []
    for engine in ENGINES.values():
        try:
            rows.append(f'| {engine.name} | `{short(engine.current())}` |')
        except Exception as error:
            rows.append(f'| {engine.name} | unknown ({type(error).__name__}) |')
    # Global source promotion leaves explicitly held llama models on independent builds.
    llama = ENGINES.get('llama')
    if llama is not None:
        for model, cfg in llama.held_sources().items():
            rows.append(f'| llama.cpp {model} (manual source pin) | `{short(cfg["source_commit"])}` |')
    # A global wheel does not replace a separately held model runtime.
    for model, cfg in json.loads((ROOT/'dsh/vllm-profiles.json').read_text()).items():
        if cfg.get('enabled', True) and cfg.get('manual_runtime_pin'):
            rows.append(f'| vLLM {model} (manual runtime pin) | `{cfg["manual_runtime_pin"]}` |')
    graphics=ROOT/'graphics/runtime-versions.json'
    if graphics.exists():
        data=json.loads(graphics.read_text())
        rows.append('| Graphics | See `graphics/runtime-versions.json` for the selected ComfyUI/Torch/HIP identities |')
    return rows


def handoff_block(results):
    today = datetime.date.today().isoformat()
    return '\n'.join([BEGIN, f'**Engine versions after the {today} daily update** (`llm-daily-update.timer`, 03:00; '
                      f'details in `hardware/DAILY-UPDATES.md`):', '', '| Engine | Production |', '|---|---|',
                      *versions(), '',
                      'Last run: ' + '; '.join(f'{r["engine"]} {r["result"]}' for r in results) + '.', END])


def update_ledger(path, text):
    old = path.read_text() if path.exists() else HEADER
    if text.strip() in old:return
    head, _, rest = old.partition('\n## ')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER + text + ('## ' + rest if rest else ''))


def update_handoff(results):
    text = HANDOFF.read_text()
    block = handoff_block(results)
    heading='## Runtime and source identities'
    public_anchor='Public native exports'
    if heading in text and public_anchor in text:
        start=text.index(heading);end=text.index(public_anchor,start)
        text=text[:start]+heading+'\n\n'+block+'\n\nEnabled native source/binary/profile/backing identities are sealed per profile in `dsh/qualified-native-profiles.json`. Retired legacy pins remain separate; they are not the selected native sources.\n\n'+text[end:]
    elif BEGIN in text:
        text=re.sub(re.escape(BEGIN)+'.*?'+re.escape(END),lambda _:block,text,flags=re.S)
    else:
        anchor='\n## Client access and managed lifecycle';index=text.find(anchor)
        if index<0:index=len(text)
        text=text[:index]+'\n'+block+'\n'+text[index:]
    HANDOFF.write_text(text)
    if SHARED.parent.is_dir():
        shutil.copyfile(HANDOFF, SHARED)
        if SHARED.read_bytes() != HANDOFF.read_bytes():
            raise RuntimeError('Shared handoff copy differs after writing')
    else:
        raise RuntimeError('Shared drive not mounted; handoff copy not updated')


def commit(repo,paths,message,logfile):
    paths=[p for p in paths if (repo/p).exists()]
    progress=Path(logfile).parent/('publication-'+repo.name+'.private.json')
    prior=json.loads(progress.read_text()) if progress.exists() else {}
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','-C',str(repo),'ls-remote','origin','refs/heads/main'],text=True).split()[0]
    if remote!=head and prior.get('head')!=head:raise RuntimeError('Local HEAD differs from remote and is not this queued publication; review before pushing')
    changed=subprocess.run(['git','-C',str(repo),'status','--porcelain','--',*paths],capture_output=True,text=True,check=True).stdout.strip() if paths else ''
    if changed:
        with open(logfile,'a') as log:
            subprocess.run(['git','-C',str(repo),'add','--',*paths],check=True,stdout=log,stderr=subprocess.STDOUT)
            subprocess.run(['git','-C',str(repo),'commit','-m',message,'--',*paths],check=True,stdout=log,stderr=subprocess.STDOUT)
        head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        progress.write_text(json.dumps({'head':head,'status':'push pending'})+'\n')
    if remote==head:return 'nothing to commit; remote synchronized'
    with open(logfile,'a') as log:
        subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True,stdout=log,stderr=subprocess.STDOUT)
    remote=subprocess.check_output(['git','-C',str(repo),'ls-remote','origin','refs/heads/main'],text=True).split()[0]
    if remote!=head:raise RuntimeError('Remote main differs after normal push')
    progress.write_text(json.dumps({'head':head,'status':'pushed and verified'})+'\n')
    return head+' pushed and verified'


def public_llama_pin():
    """Compatibility export; unknown external paths still fail closed."""
    name='dsh/llama-runtime.json';source=ROOT/name
    if not source.exists():return []
    text=source.read_text().replace(str(ROOT),'/opt/local-llm')
    if PRIVATE.search(text):raise RuntimeError('llama reference contains unrecognized private paths')
    cfg=json.loads(text);cfg['reference_note']='Sanitized example paths; verify each selected source/build locally before loading.'
    target=PUBLIC/'linux'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(cfg,indent=2)+'\n')
    return ['linux/'+name]

def runtime_paths(results=None):
    paths=['dsh/llama-runtime.json','sglang/fork-pin.json','dsh/vllm-profiles.json','vllm/start-bolt-rocm','graphics/runtime-versions.json','dsh/qualified-native-profiles.json']
    registry=json.loads((ROOT/'dsh/qualified-native-profiles.json').read_text())
    for family in ['maya','strata']:
        name='dsh/'+family+'-profiles.json';paths.append(name);catalog=json.loads((ROOT/name).read_text())
        for model,record in registry['profiles'].items():
            if record['family']==family and record['status']=='passed' and catalog.get(model,{}).get('enabled',family!='maya'):
                paths.append('dsh/'+catalog[model]['config'])
    packaged=ROOT/'dsh/qualified-strata-qwen-profiles.json'
    if packaged.exists():
        data=json.loads(packaged.read_text())
        catalog=json.loads((ROOT/'dsh/strata-profiles.json').read_text())
        if data.get('schema_version')!=1:raise RuntimeError('Unknown packaged Qwen registry schema')
        paths.append('dsh/qualified-strata-qwen-profiles.json')
        for model,record in data['profiles'].items():
            profile=catalog.get(model,{})
            name=profile.get('config','')
            if (record.get('status')!='passed' or record.get('family')!='strata-qwen'
                    or not profile.get('qualified_qwen_package') or not name
                    or Path(name).name!=name):
                raise RuntimeError('Unreviewed packaged Qwen reference')
            paths.append('dsh/'+name)
    allowed=list(dict.fromkeys(paths))
    if results is None:return allowed
    changed=list(dict.fromkeys(p for row in results for p in row.get('runtime_files',[])))
    if any(p not in allowed for p in changed):raise RuntimeError('Unrecognized runtime publication path')
    return changed

def public_runtime_references(results=None):
    registry=json.loads((ROOT/'dsh/qualified-native-profiles.json').read_text())
    mapping={str(ROOT):'/opt/local-llm','/run/media/'+getpass.getuser()+'/sharedSATA1':'/mnt/shared','/run/media/'+getpass.getuser()+'/sharedNVME1':'/mnt/shared-nvme'}
    for record in registry['profiles'].values():
        mapping[record['source']]='/opt/local-llm/qualified-sources/'+record['family']+'-'+record['source_commit'][:12]
    packaged=ROOT/'dsh/qualified-strata-qwen-profiles.json'
    packaged_profiles=json.loads(packaged.read_text())['profiles'] if packaged.exists() else {}
    for record in packaged_profiles.values():
        base='/opt/local-llm/qualified-packages/strata-qwen-'+record['binary_sha256'][:12]
        mapping[str(Path(record['binary']).parent)]=base+'/engine'
        mapping[record['control']]=base+'/control'
    pin=json.loads((ROOT/'dsh/llama-runtime.json').read_text())
    for value in [pin,*pin.get('source_overrides',{}).values()]:
        path=value.get('source_path',value.get('path'))
        if path and not Path(path).is_relative_to(ROOT):
            source=Path(path)
            actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
            if actual!=value['source_commit'] or not (source/'build-hip/bin/llama-server').is_file():
                raise RuntimeError('Unrecognized external llama source path; not exported')
            mapping[path]='/opt/local-llm/qualified-sources/llama-'+value['source_commit'][:12]
    graphics=ROOT/'graphics/runtime-versions.json'
    if graphics.exists():
        selected=json.loads(graphics.read_text()).get('runtime_selection')
        if selected:
            if selected.get('status')!='passed-six-normal-workflows':raise RuntimeError('Unqualified ComfyUI selection cannot be exported')
            source=Path(selected['source_path'])
            actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
            if actual!=selected['source_commit'] or not (source/'main.py').is_file():raise RuntimeError('Selected ComfyUI source changed; not exported')
            mapping[str(source)]='/opt/local-llm/qualified-sources/comfyui-'+actual[:12]
    exported=[];planned=[]
    for name in runtime_paths(results):
        source=ROOT/name
        if not source.exists():continue
        text=source.read_text()
        for old,new in sorted(mapping.items(),key=lambda item:len(item[0]),reverse=True):text=text.replace(old,new)
        if name.endswith('.json'):
            data=json.loads(text)
            def reject_credentials(value):
                if isinstance(value,dict):
                    for key,item in value.items():
                        if key.lower() in ['api_key','apikey','password','access_token','auth_token','client_secret','authorization'] and item:raise RuntimeError('Never export runtime credentials')
                        reject_credentials(item)
                elif isinstance(value,list):
                    for item in value:reject_credentials(item)
            reject_credentials(data)
            if 'local_validation' in data:
                data['local_validation']['status']='requires-local-validation'
                data['local_validation']['scope']='Sanitized source-host short-test reference; independently qualify and seal on the receiving host.'
            if name=='graphics/runtime-versions.json' and data.get('runtime_selection'):
                data['runtime_selection']['status']='requires-local-validation'
                data['runtime_selection']['reference_note']='Source-host workflow qualification only; independently qualify this source, dependencies and placement before selection.'
            if name in ('dsh/qualified-native-profiles.json','dsh/qualified-strata-qwen-profiles.json'):
                for record in data['profiles'].values():
                    if record.get('status')!='passed':raise RuntimeError('Never export an unreviewed provisional native record')
                    record['status']='requires-local-validation';record.pop('candidate_owner',None)
                    record['backing_identity']={p:{k:v for k,v in identity.items() if k in ['bytes','sha256']} for p,identity in record.get('backing_identity',{}).items()}
                    record['reference_note']='Source-host content references; local device/inode/mtime seals omitted. Independent local qualification required.'
            if data.get('model_name') in packaged_profiles:
                for key in ['local_validation','runtime_validation','tuning_validation','resource_guard_validation']:
                    if isinstance(data.get(key),dict):data[key]['status']='requires-local-validation'
                data['validation_status']='Sanitized source-host reference; independently qualify and seal before use.'
            text=json.dumps(data,indent=2)+'\n'
        if PRIVATE.search(text) or any(v in text for v in ['CODEX_THREAD_ID','context_meter','checkpoint.private','candidate_owner']):raise RuntimeError('Private runtime reference content: '+name)
        planned.append((name,text,source.stat().st_mode&0o777))
    for name,text,mode in planned:
        target=PUBLIC/'linux'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text);target.chmod(mode);exported.append('linux/'+name)
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
    references=public_runtime_references(results) if PUBLIC.is_dir() else []
    log('private repository: ' + commit(ROOT, [LEDGER, 'network/LINUX-LLM-RUNTIME-HANDOFF.md', *runtime_paths(results)], message, logfile), logfile)
    if PUBLIC.is_dir():
        update_ledger(PUBLIC/'linux'/LEDGER, text)
        public_handoff = PUBLIC/'linux/network/LINUX-LLM-RUNTIME-HANDOFF.md'
        if public_handoff.exists() and BEGIN in public_handoff.read_text():   # the block holds no private paths
            public_handoff.write_text(re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda _: handoff_block(results),
                                             public_handoff.read_text(), flags=re.S))
        log('public repository: ' + commit(PUBLIC, ['linux/' + LEDGER, 'linux/network/LINUX-LLM-RUNTIME-HANDOFF.md',*references],
                                           message, logfile), logfile)
    (run/'published.json').write_text(json.dumps({'message': message}, indent=2) + '\n')
