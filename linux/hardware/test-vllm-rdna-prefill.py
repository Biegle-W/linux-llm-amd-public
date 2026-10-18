#!/usr/bin/env python3
"""Compare gated prefill tiles with dense FP32 attention, scattered pages and graphs."""
import amdsmi  # Preload before torch.
import argparse
import json
import math
import os
import torch
import triton
from vllm.v1.attention.ops.triton_unified_attention import unified_attention
from vllm.v1.kv_cache_interface import KVQuantMode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',type=int,required=True,choices=[0,1])
    parser.add_argument('--kv',choices=['int8','bf16'],default='int8')
    args = parser.parse_args()
    torch.cuda.set_device(args.device)
    torch.manual_seed(42)
    records = []
    for length,prefix in [(17,0),(33,1024),(129,8192),(257,32768),(4,16384)]:
        total = prefix+length
        blocks = triton.cdiv(total,16)
        k = torch.randint(-127,128,(blocks,16,2,256),device='cuda',dtype=torch.int8)
        v = torch.randint(-127,128,k.shape,device='cuda',dtype=torch.int8)
        ks = torch.rand((blocks,16,2),device='cuda')*.01+.005
        vs = torch.rand_like(ks)*.01+.005
        if args.kv == 'bf16':
            k = torch.randn(k.shape,device='cuda',dtype=torch.bfloat16)
            v = torch.randn(v.shape,device='cuda',dtype=torch.bfloat16)
            ks = torch.ones_like(ks)
            vs = torch.ones_like(vs)
        table = torch.randperm(blocks,device='cuda',dtype=torch.int32)[None,:]
        q = torch.randn((length,12,256),device='cuda',dtype=torch.bfloat16)
        cu = torch.tensor([0,length],device='cuda',dtype=torch.int32)
        seq = torch.tensor([total],device='cuda',dtype=torch.int32)
        def call(enabled):
            os.environ['VLLM_LOCAL_RDNA_PREFILL'] = str(enabled)
            out = torch.empty_like(q)
            unified_attention(q,k,v,out,cu,length,seq,total,1/math.sqrt(256),True,(-1,-1),table,0,
                              1.,1.,1.,kv_quant_mode=KVQuantMode.INT8_PER_TOKEN_HEAD if args.kv == 'int8' else KVQuantMode.NONE,
                              k_scale_cache=ks,v_scale_cache=vs)
            return out
        kd = (k[table[0]].float()*ks[table[0]][...,None]).reshape(-1,2,256)[:total].repeat_interleave(6,1).transpose(0,1)
        vd = (v[table[0]].float()*vs[table[0]][...,None]).reshape(-1,2,256)[:total].repeat_interleave(6,1).transpose(0,1)
        def oracle():
            parts=[]
            for start in range(0,length,32):
                query=q[start:start+32].float().transpose(0,1)
                score=(query @ kd.transpose(1,2))/math.sqrt(256)
                positions=prefix+torch.arange(start,min(start+32,length),device='cuda')
                score.masked_fill_(torch.arange(total,device='cuda')[None,None,:]>positions[None,:,None],float('-inf'))
                parts.append((torch.softmax(score,dim=-1) @ vd).transpose(0,1))
            return torch.cat(parts)
        reference=oracle()
        original=call(0)
        candidate=call(1)
        torch.testing.assert_close(candidate.float(),reference,rtol=.03,atol=.012)
        torch.testing.assert_close(candidate,original,rtol=.03,atol=.012)
        timings={}
        for enabled in (0,1):
            timings[str(enabled)]=triton.testing.do_bench_cudagraph(lambda:call(enabled),rep=60)
        # Capture/replay after changing query values and scattered page addresses.
        side=torch.cuda.Stream()
        side.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(side):
            call(1)
        torch.cuda.current_stream().wait_stream(side)
        graph=torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph,stream=side):
            replay=call(1)
        for _ in range(2):
            q.copy_(torch.randn_like(q))
            table.copy_(table.flip(1))
            kd = (k[table[0]].float()*ks[table[0]][...,None]).reshape(-1,2,256)[:total].repeat_interleave(6,1).transpose(0,1)
            vd = (v[table[0]].float()*vs[table[0]][...,None]).reshape(-1,2,256)[:total].repeat_interleave(6,1).transpose(0,1)
            graph.replay()
            torch.cuda.synchronize()
            torch.testing.assert_close(replay.float(),oracle(),rtol=.03,atol=.012)
        records.append(dict(query=length,prefix=prefix,max_abs_error=(candidate.float()-reference).abs().max().item(),
                            graph_replays=2,milliseconds=timings))
        del graph
    print(json.dumps(dict(device=args.device,kv=args.kv,passed=True,cases=records),indent=2))


if __name__=='__main__':
    main()
