#!/usr/bin/env python3
"""Audit and stage narrowly scoped PEX/AMD peer routing before driver initialization."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import time

MARKER='# Managed local-llm AMD PEX peer routing; no live PCI writes.'
FLAGS='xxx00xx'  # Preserve every bit except Request Redirect (2), Completion Redirect (3).
GIB=1024**3
BDF=re.compile(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]')


def word(data,offset):
    if offset+2>len(data):raise RuntimeError('Truncated PCI configuration; administrator read required')
    return struct.unpack_from('<H',data,offset)[0]


def pcie_type(data):
    if len(data)<256:raise RuntimeError('Cannot read PCI capabilities; run audit with sudo')
    offset=data[0x34]&0xfc;seen=set()
    while offset:
        if offset<0x40 or offset>0xfc or offset in seen:raise RuntimeError('Malformed standard PCI capabilities')
        seen.add(offset)
        if data[offset]==0x10:return (word(data,offset+2)>>4)&15
        offset=data[offset+1]&0xfc
    return None


def acs(data):
    if len(data)<4096:raise RuntimeError('Cannot read extended PCI configuration; run audit with sudo')
    offset=0x100;seen=set()
    while offset:
        if offset<0x100 or offset>0xff8 or offset&3 or offset in seen:raise RuntimeError('Malformed extended PCI capabilities')
        seen.add(offset);header=struct.unpack_from('<I',data,offset)[0]
        if header in (0,0xffffffff):return None
        if header&0xffff==0x000d:return {'offset':offset,'capability':word(data,offset+4),'control':word(data,offset+6)}
        offset=(header>>20)&0xfff
    return None


def identity(path):
    return {'pci':path.name,'vendor':(path/'vendor').read_text().strip(),'device':(path/'device').read_text().strip(),'class':(path/'class').read_text().strip()}


def ancestry(device):
    return [p for p in device.resolve().parents if (p/'vendor').is_file()]


def path_selector(device):
    chain=list(reversed(ancestry(device)))+[device.resolve()]
    assert chain and all(BDF.fullmatch(x.name) for x in chain)
    return chain[0].name+''.join('/'+p.name.split(':')[-1] for p in chain[1:])


def audit(pci_root=Path('/sys/bus/pci/devices')):
    gpus=[]
    for p in sorted(pci_root.iterdir()):
        if (p/'vendor').read_text().strip()=='0x1002' and (p/'class').read_text().startswith(('0x0300','0x0302','0x0380')):
            if (p/'device').read_text().strip()!='0x744c' or (p/'driver').resolve().name!='amdgpu':raise RuntimeError('Unapproved AMD graphics device/driver')
            if int((p/'mem_info_vram_total').read_text())<23*GIB:raise RuntimeError('Expected two 24 GB Navi31 cards')
            gpus.append(p)
    if len(gpus)!=2:raise RuntimeError('Expected exactly two amdgpu Navi31 graphics functions')
    parents=[ancestry(p) for p in gpus];common=next((p for p in parents[0] if p in parents[1]),None)
    if common is None or identity(common)['vendor']!='0x1000' or identity(common)['device']!='0xc010':raise RuntimeError('No common approved Broadcom PEX880xx ancestor')
    relevant={common}
    for chain in parents:
        for p in chain:
            relevant.add(p)
            if p==common:break
    rows=[]
    for p in sorted(relevant):
        data=(p/'config').read_bytes();row={**identity(p),'pcie_type':pcie_type(data),'acs':acs(data),'selector':path_selector(p)};rows.append(row)
    selected=[r for r in rows if r['vendor']=='0x1000' and r['device']=='0xc010' and r['pcie_type']==6]
    if len(selected)!=4:raise RuntimeError('Expected exactly four Broadcom downstream bridges on the selected paths')
    internal_ids={p.resolve().parent.name for p in gpus}
    internal=[r for r in rows if r['pci'] in internal_ids and r['vendor']=='0x1002' and r['device']=='0x1479' and r['pcie_type']==6]
    if len(internal)!=2:raise RuntimeError('Expected one AMD 1479 downstream parent directly above each GPU')
    selected=selected+internal
    selected_ids={r['pci'] for r in selected}
    errors=[]
    for row in rows:
        a=row['acs']
        if row['pci'] in selected_ids:
            if not a or a['capability']&0x0c!=0x0c:errors.append(f"Selected bridge {row['pci']} lacks expected ACS capability");continue
            if a['control'] not in (0x1d,0x11):errors.append(f"Unexpected ACS control on {row['pci']}: {a['control']:#x}")
        elif a and a['control']&0x2c:errors.append(f"Additional redirecting bridge {row['pci']} vendor={row['vendor']} device={row['device']} type={row['pcie_type']} ACS={a['control']:#x}")
    groups=[]
    for p in gpus:
        group=(p/'iommu_group').resolve();t=group/'type';groups.append(t.read_text().strip() if t.exists() else None)
    return {'schema':1,'sampled_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'gpu_pci':[p.name for p in gpus],'common_switch':common.name,'bridges':rows,'selected_bridges':selected,'gpu_iommu_domains':groups,'request_completion_redirect_present':any(r['acs'] and r['acs']['control']&0x0c for r in selected),'admission_errors':errors,'live_pci_writes':False}


def parameter(report):
    selected=report['selected_bridges']
    if len(selected)!=6:raise RuntimeError('Refusing broad or incomplete six-bridge selection')
    selectors=[r['selector'] for r in selected]
    for s in selectors:
        if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7](?:/[0-9a-f]{2}\.[0-7])+',s):raise RuntimeError('Unsafe path selector')
    if len(set(selectors))!=6:raise RuntimeError('Duplicate bridge selectors')
    return 'pci=config_acs='+';'.join(FLAGS+'@'+s for s in selectors)


def dropin(param):
    if not re.fullmatch(r'pci=config_acs=[a-z0-9@:.\-/;]+',param):raise RuntimeError('Invalid kernel argument')
    # GRUB must receive one quoted token: semicolons must not become GRUB commands.
    return MARKER+'\n# Only ACS bits 2/3 change; path selectors tolerate bus renumbering.\nGRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} \''+param+'\'"\n'


def atomic(path,data,mode=0o644):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.amd-p2p-',dir=path.parent)
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def stage(report,config,state,grub,backup_root,run=subprocess.run,existing_args=''):
    if report.get('admission_errors'):raise RuntimeError('; '.join(report['admission_errors'])+'; run audit --output to save the read-only report')
    param=parameter(report);body=dropin(param).encode()
    if config.is_symlink() or state.is_symlink() or grub.is_symlink():raise RuntimeError('Refuse symlinked managed files')
    if config.exists():
        if config.read_bytes()==body and state.exists():return {'status':'already staged','reboot_required':True,'parameter':param}
        raise RuntimeError('Existing routing configuration differs; no overwrite')
    if state.exists():raise RuntimeError('Existing state requires explicit review')
    if re.search(r'(?:config_acs|disable_acs_redir|pcie_acs_override)=',existing_args):raise RuntimeError('Existing ACS boot policy requires review')
    if not report['request_completion_redirect_present']:raise RuntimeError('ACS redirect is already clear; this repair is not indicated')
    backup=Path(tempfile.mkdtemp(prefix='local-llm-amd-p2p-',dir=backup_root));backup.chmod(0o700)
    shutil.copy2(grub,backup/'grub.cfg');atomic(backup/'audit.json',(json.dumps(report,indent=2)+'\n').encode(),0o600)
    try:
        atomic(config,body)
        run(['update-grub'],check=True)
        run(['grub-script-check',str(grub)],check=True)
        # Require every Ubuntu kernel entry to carry one single, quoted policy argument.
        import shlex
        lines=[l.strip() for l in grub.read_text().splitlines() if re.match(r'^\s*linux(?:efi)?\s+.*vmlinuz',l)]
        if not lines or any(shlex.split(l).count(param)!=1 for l in lines):raise RuntimeError('Generated GRUB kernel entries did not preserve the exact policy token')
        record={'schema':1,'status':'staged for reboot; no live driver/routing change','parameter':param,'dropin_sha256':hashlib.sha256(body).hexdigest(),'backup':str(backup),'audit':report,'reboot_required':True,'IOMMU_policy_changed':False}
        atomic(state,(json.dumps(record,indent=2)+'\n').encode(),0o600)
        return record
    except BaseException:
        config.unlink(missing_ok=True);shutil.copy2(backup/'grub.cfg',grub);state.unlink(missing_ok=True);raise


def rollback(config,state,grub,run=subprocess.run):
    if not config.exists() or not state.exists():raise RuntimeError('No managed staged policy to remove')
    d=json.loads(state.read_text())
    if hashlib.sha256(config.read_bytes()).hexdigest()!=d['dropin_sha256']:raise RuntimeError('Managed file changed; refusing rollback')
    old=config.read_bytes();old_grub=grub.read_bytes()
    try:
        config.unlink();run(['update-grub'],check=True);run(['grub-script-check',str(grub)],check=True);state.unlink()
    except BaseException:atomic(config,old);atomic(grub,old_grub,0o600);raise
    return {'status':'next-boot policy removed; active boot unchanged','reboot_required':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['audit','install','verify','rollback']);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if os.geteuid()!=0:raise RuntimeError('Administrator PCI configuration access is required; run with sudo')
    installer_lock=open('/run/lock/local-llm-amd-p2p-support.lock','a')
    fcntl.flock(installer_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=Path('/etc/default/grub.d/zz-local-llm-amd-p2p.cfg');state=Path('/var/lib/local-llm-amd-p2p/state.json');grub=Path('/boot/grub/grub.cfg')
    if args.action=='rollback':result=rollback(config,state,grub)
    else:
        report=audit();result=report
        if args.action=='install':
            root=Path(__file__).resolve().parents[1];lock=root/'hardware/generated/GPU-LOCK'
            if lock.exists():raise RuntimeError('An existing GPU reservation is active; preserve it')
            defaults=Path('/etc/default/grub').read_text()+'\n'+'\n'.join(p.read_text() for p in Path('/etc/default/grub.d').glob('*.cfg') if p!=config)
            result=stage(report,config,state,grub,Path('/var/backups'),existing_args=defaults)
        elif args.action=='verify':
            record=json.loads(state.read_text());active=record['parameter'] in Path('/proc/cmdline').read_text().split();clear=not report['request_completion_redirect_present'] and not report.get('admission_errors');result={'active_parameter':active,'redirect_bits_clear':clear,'audit':report,'status':'routing policy verified; HIP/data correctness still required' if active and clear else 'not active or register verification failed'}
    output=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(output)
    print(output)


if __name__=='__main__':
    try:main()
    except Exception as error:raise SystemExit('No live PCI writes or reboot performed. '+str(error))
