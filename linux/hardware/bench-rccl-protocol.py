#!/usr/bin/env python3
"""Compare host-transport RCCL protocols with checked dual-GPU collectives."""
import datetime
import json
import os
import statistics
import time
import amdsmi  # Initialize AMD SMI before torch in this runtime.
import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def worker(rank):
    torch.cuda.set_device(rank)
    dist.init_process_group('nccl', init_method='tcp://127.0.0.1:29583', rank=rank,
                            world_size=2, timeout=datetime.timedelta(seconds=45))
    results = []
    for size in (1, 5120, 131072, 1048576):
        x = torch.full((size,), rank+1, device=f'cuda:{rank}', dtype=torch.bfloat16)
        outputs = [torch.empty_like(x), torch.empty_like(x)]
        for operation in ('all_reduce', 'all_gather'):
            samples = []
            for repeat in range(4):
                dist.barrier()
                torch.cuda.synchronize()
                start = time.perf_counter()
                for _ in range(30):
                    if operation == 'all_reduce':
                        x.fill_(rank+1)
                        dist.all_reduce(x)
                    else:
                        x.fill_(rank+1)
                        dist.all_gather(outputs, x)
                torch.cuda.synchronize()
                elapsed = (time.perf_counter()-start)/30
                if operation == 'all_reduce':
                    assert torch.all(x == 3).item()
                else:
                    assert all(torch.all(y == i+1).item() for i,y in enumerate(outputs))
                if repeat:
                    samples.append(elapsed*1e6)
            results.append(dict(operation=operation, bytes=size*2,
                                median_us=statistics.median(samples), samples_us=samples))
    if rank == 0:
        print('RESULT_JSON '+json.dumps(dict(protocol=os.environ.get('NCCL_PROTO', 'auto'),
                                            correctness=True, results=results)), flush=True)
    dist.destroy_process_group()


if __name__ == '__main__':
    assert torch.cuda.device_count() == 2
    mp.spawn(worker, nprocs=2, join=True)
