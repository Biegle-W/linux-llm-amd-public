#!/usr/bin/env python3
"""Use the isolated AMD CLI; refuse overlapping inference without stopping anything."""
import json
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]


def option(args,names):
    for index,arg in enumerate(args):
        for name in names:
            if arg==name:
                if index+1>=len(args):raise ValueError(f'{name} requires a value')
                value=args[index+1]
                if any(a==name or a.startswith(name+'=') for a in args[index+1:]):
                    raise ValueError(f'{name} must be supplied only once')
                return value
            if arg.startswith(name+'='):return arg.split('=',1)[1]
    return None


def serve_defaults(args):
    args=list(args)
    for names in (('--tensor-parallel-size','--tp-size'),('--gpu',)):
        if sum(any(a==n or a.startswith(n+'=') for n in names) for a in args)>1:
            raise ValueError('Supply each GPU/TP setting only once')
    tp=option(args,('--tensor-parallel-size','--tp-size'))
    if tp is not None and tp!='1':
        raise ValueError('This experimental FreeToken build is restricted to one AMD GPU; it cannot shard GGUF embeddings over TP2.')
    gpu=option(args,('--gpu',))
    if gpu is not None and gpu not in ('0','1'):
        raise ValueError('Select one installed AMD GPU with --gpu 0 or --gpu 1; dual-GPU GGUF serving is unavailable.')
    if gpu is None:args+=['--gpu','1']
    if tp is None:args+=['--tensor-parallel-size','1']
    if '--disable-pynccl' not in args:args+=['--disable-pynccl']
    if option(args,('--cuda-graph-max-bs','--graph')) is None:args+=['--cuda-graph-max-bs','0']
    chunk=option(args,('--max-prefill-length',))
    if chunk is not None and not 1<=int(chunk)<=128:
        raise ValueError('Use --max-prefill-length between 1 and 128: gfx1100 GGUF Q6_K dispatch failed at 256 tokens.')
    if chunk is None:args+=['--max-prefill-length','128']
    if option(args,('--attn',)) is None:args+=['--attn','triton']
    if option(args,('--max-running-requests',)) is None:args+=['--max-running-requests','1']
    return args


def vram_headroom_reason(total,used):
    free=total-used
    if free<20*1024**3:
        return f'FreeToken needs 20 GiB free on its selected GPU; only {free/1024**3:.2f} GiB is free. Close the running inference terminal first.'
    return None


def require_vram_headroom(args):
    sys.path.insert(0,str(ROOT/'dsh'))
    from amd_device import amd_devices
    try:
        device=amd_devices()[int(option(args,('--gpu',)))]
        reason=vram_headroom_reason(int((device/'mem_info_vram_total').read_text()),int((device/'mem_info_vram_used').read_text()))
    except (OSError,RuntimeError) as error:
        raise ValueError('Cannot verify AMD VRAM headroom; no FreeToken worker started: '+str(error)) from error
    if reason:raise ValueError(reason)


def main():
    args=sys.argv[1:]
    if args and args[0]=='qwen':
        if args[1:] not in ([],['--help'],['-h']):
            raise ValueError('The qwen command uses the fixed 8K test profile. Use serve for custom settings.')
        models=json.loads((ROOT/'dsh/models.json').read_text())
        model=next(m for m in models if m['id']=='qwen3.8-27b-q4')
        args=['serve','--model',model['path'],'--host','127.0.0.1','--port','1919',
            '--served-model-name','qwen3.8-27b-q4-freetoken','--text-model-only',
            '--max-seq-len-override','8192','--num-tokens','8192',
            '--memory-ratio','0.75','--cache-type','naive',*args[1:]]
    if args and args[0]=='serve' and not any(a in ('--help','-h') for a in args):
        args=serve_defaults(args)
        for port in (8080,8081,30000,30001,30010,30011,30020,30021,18030,1919):
            with socket.socket() as probe:
                probe.settimeout(.25)
                if probe.connect_ex(('127.0.0.1',port))==0:
                    raise ValueError(f'Inference port {port} is occupied. Close its inference terminal before starting raw FreeToken; no process was stopped.')
        require_vram_headroom(args)
    binary=ROOT/'freetoken/.venv-rocm/bin/ft'
    os.execv(str(binary),[str(binary),*args])


if __name__=='__main__':
    try:main()
    except ValueError as error:raise SystemExit(str(error))
