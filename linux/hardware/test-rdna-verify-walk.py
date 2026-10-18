#!/usr/bin/env python3
"""Check repaired scattered prefix+draft attention against a dense FP32 oracle."""
import argparse
import json
import amdsmi
import torch
from sglang.kernels.ops.attention.rdna_verify_adapter import (
    RdnaVerifyBuffers, rdna_fill_extend, rdna_verify_fwd)


def check(device, prefix, draft, broken=False):
    print('CHECK',device,prefix,draft,flush=True)
    torch.manual_seed(42)
    torch.cuda.set_device(device)
    hq,hkv,dim = 12,2,256  # Qwen target's TP2 attention shape.
    total = prefix+draft
    pool_size = 2*total+32
    key = torch.randn(pool_size,hkv,dim,device='cuda',dtype=torch.bfloat16)
    value = torch.randn_like(key)
    query = torch.randn(draft,hq,dim,device='cuda',dtype=torch.bfloat16)
    output = torch.empty_like(query)
    ids = torch.randperm(pool_size,device='cuda')[:total].to(torch.int64)
    prefix_ids = ids[:prefix].clone()
    out_locs = ids[prefix:].clone()
    prefix_indptr = torch.tensor([0,prefix],device='cuda',dtype=torch.int32)
    full_lens = torch.tensor([total],device='cuda',dtype=torch.int32)
    full_indptr = torch.tensor([0,total],device='cuda',dtype=torch.int32)
    bufs = RdnaVerifyBuffers('cuda',1,total+32,draft,hq,dim,16//(hq//hkv),segments=32)
    def forward():
        if broken:
            rdna_verify_fwd(query,output,key,value,prefix_indptr,prefix_ids,prefix_indptr[1:],
                            dim**-.5,bufs,1,draft,skip_fill=False)
            return
        rdna_fill_extend(bufs,prefix_ids,prefix_indptr,out_locs,full_lens,1,draft,full_indptr)
        rdna_verify_fwd(query,output,key,value,prefix_indptr,prefix_ids,full_lens,
                        dim**-.5,bufs,1,draft,skip_fill=True)
    def reference():
        joined = torch.cat([prefix_ids,out_locs])
        k = key[joined].float().repeat_interleave(hq//hkv,dim=1)
        v = value[joined].float().repeat_interleave(hq//hkv,dim=1)
        scores = torch.einsum('qhd,khd->hqk',query.float(),k)*(dim**-.5)
        mask = torch.arange(total,device='cuda')[None,:] <= prefix+torch.arange(draft,device='cuda')[:,None]
        scores.masked_fill_(~mask[None],float('-inf'))
        return torch.einsum('hqk,khd->qhd',scores.softmax(-1),v)
    warm_stream = torch.cuda.Stream(device=device)
    warm_stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(warm_stream):
        for _ in range(3):
            forward()
    warm_stream.synchronize()
    error = (output.float()-reference()).abs().max().item()
    if broken:
        assert error > .03, ('Old prefix-only metadata did not reproduce a large discrepancy',error)
        return dict(gpu=device,prefix=prefix,draft=draft,expected_mismatch=True,max_abs_error=error)
    assert error < .03, (device,prefix,draft,error)
    graph = torch.cuda.CUDAGraph()
    warm_stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.graph(graph,stream=warm_stream):
        forward()
    # Change scatter addresses after capture; stale metadata must not survive.
    new_ids = torch.randperm(pool_size,device='cuda')[:total]
    prefix_ids.copy_(new_ids[:prefix]);out_locs.copy_(new_ids[prefix:])
    graph.replay()
    torch.cuda.synchronize()
    graph_error = (output.float()-reference()).abs().max().item()
    assert graph_error < .03, (device,prefix,draft,graph_error)
    return dict(gpu=device,prefix=prefix,draft=draft,max_abs_error=error,graph_max_abs_error=graph_error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--broken-prefix-walk',action='store_true',help='Reproduce the old adapter metadata error')
    args = parser.parse_args()
    assert torch.cuda.device_count()==2
    shapes = ((7,3),) if args.broken_prefix_walk else ((7,3),(257,4),(2049,8))
    rows=[check(device,prefix,draft,args.broken_prefix_walk) for device in range(2)
          for prefix,draft in shapes]
    print(json.dumps(dict(status='reproduced_old_error' if args.broken_prefix_walk else 'passed',cases=rows)),flush=True)
