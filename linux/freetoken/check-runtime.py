#!/usr/bin/env python3
"""Check the isolated ROCm runtime on both cards without loading model weights."""
import argparse
from datetime import timedelta
import importlib.metadata
import json
from pathlib import Path
import socket

import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def rank_check(rank, address, output):
    torch.set_num_threads(2)
    torch.cuda.set_device(rank)
    dist.init_process_group('nccl', rank=rank, world_size=2,
                            init_method=address, timeout=timedelta(seconds=60))
    for dtype in (torch.float32, torch.bfloat16):
        for size in (1, 4096, 1048576):
            value = torch.full((size,), rank+1, device=f'cuda:{rank}', dtype=dtype)
            dist.all_reduce(value)
            torch.cuda.synchronize(rank)
            assert torch.all(value == 3).item(), (rank, dtype, size)
        value = torch.tensor([rank+1], device=f'cuda:{rank}', dtype=dtype)
        result = torch.empty(2, device=f'cuda:{rank}', dtype=dtype)
        dist.all_gather_into_tensor(result, value)
        assert result.cpu().tolist() == [1, 2]
    Path(output, f'collective-rank-{rank}.json').write_text(json.dumps({'rank':rank, 'passed':True})+'\n')
    dist.destroy_process_group()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collectives', action='store_true')
    args = parser.parse_args()
    output = Path(__file__).resolve().parent/'generated'
    output.mkdir(exist_ok=True)
    assert torch.version.hip and torch.version.cuda is None
    assert torch.cuda.device_count() == 2
    devices = []
    for index in range(2):
        properties = torch.cuda.get_device_properties(index)
        assert properties.name == 'AMD Radeon RX 7900 XTX'
        assert properties.gcnArchName.split(':')[0] == 'gfx1100'
        value = torch.arange(16, device=f'cuda:{index}', dtype=torch.float32)
        assert value.sum().item() == 120
        devices.append({'index':index, 'name':properties.name, 'architecture':properties.gcnArchName})
    result = {'torch':torch.__version__, 'hip':torch.version.hip, 'devices':devices,
              'gpu_calculations':True, 'collectives':'not tested',
              'model_serving':'not established by this check'}
    try:
        result['freetoken'] = importlib.metadata.version('freetoken')
        from freetoken.kernel import _pinned_tensor, _cpu_moe
        result['native_extensions'] = True
    except importlib.metadata.PackageNotFoundError:
        result['freetoken'] = 'not installed yet'
    if args.collectives:
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            address = f'tcp://127.0.0.1:{listener.getsockname()[1]}'
        mp.spawn(rank_check, args=(address,str(output)), nprocs=2, join=True)
        result['collectives'] = 'FP32/BF16 all-reduce and all-gather passed on both GPUs'
    (output/'runtime-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
