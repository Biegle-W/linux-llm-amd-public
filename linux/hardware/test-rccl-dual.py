"""Exercise collectives on both AMD GPUs before loading model weights."""
import datetime
import os
import amdsmi
import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def worker(rank):
    torch.cuda.set_device(rank)
    dist.init_process_group('nccl', init_method='tcp://127.0.0.1:29583',
                            rank=rank, world_size=2, timeout=datetime.timedelta(seconds=45))
    for dtype in (torch.float32, torch.bfloat16):
        for size in (1, 4096, 1048576):
            x = torch.full((size,), rank + 1, device=f'cuda:{rank}', dtype=dtype)
            dist.all_reduce(x)
            assert torch.all(x == 3).item()
            outputs = [torch.empty_like(x), torch.empty_like(x)]
            dist.all_gather(outputs, x)
            assert all(torch.all(y == 3).item() for y in outputs)
    torch.cuda.synchronize()
    print(f'rank {rank}: all-reduce/all-gather passed', flush=True)
    dist.destroy_process_group()


if __name__ == '__main__':
    assert torch.cuda.device_count() == 2
    mp.spawn(worker, nprocs=2, join=True)
