"""CPU-only zero-block boundary parity, not real-model/SP correctness qualification."""
from pathlib import Path
import json, sys, types

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--comfy-root',type=Path,required=True)
parser.add_argument('--plugin-root',type=Path,required=True)
args=parser.parse_args()
C=args.comfy_root.resolve()
sys.path[:0]=[str(C),str(args.plugin_root.resolve())]
sys.argv=[sys.argv[0],'--cpu','--use-pytorch-cross-attention','--disable-dynamic-vram','--disable-pinned-memory']
import comfy.options
comfy.options.enable_args_parsing()
import torch
from comfy.ldm.minimax.model import MiniMaxH3Model
from minimax_h3_amd_sp.h3_forward import prepare_rank_zero,finish_rank_zero

torch.set_num_threads(1)
torch.manual_seed(42)
d=MiniMaxH3Model(hidden_size=16,num_layers=0,token_refiner_num_layers=0,
 num_attention_heads=2,attention_head_dim=8,ffn_hidden_size=32,latents_dim=4,
 audio_latents_dim=8,text_dim=16,timestep_input_dim=8,time_embed_hidden_size=16,
 time_embed_dim=8,rope_inv_freq_len=1,dtype=torch.float32,device='cpu',operations=torch.nn)
with torch.no_grad():
 for parameter in d.parameters():parameter.normal_(mean=0,std=.05)
 d.rope.inv_freq.fill_(.1)

video=torch.randn(1,4,2,4,4)
audio=torch.randn(1,8,2,3)
context=torch.randn(1,3,16)
original=d._forward
results=[]
for scale in [1.0,4.0]:
 for sigma in [.1,.5,.9]:
  t=torch.tensor([sigma*1000])
  payload={'audio_scale':scale}
  opts={'sample_sigmas':torch.linspace(1,0,21)}
  with torch.inference_mode():expected=d.forward([video,audio],t,context,transformer_options=opts.copy(),minimax_payload=payload)
  def adapter(self,x,timestep,context,transformer_options={},minimax_payload=None,**kwargs):
   hidden,embedding,rope,segments,state=prepare_rank_zero(self,x,timestep,context,transformer_options,minimax_payload)
   return finish_rank_zero(self,hidden,embedding,state,x[0].dtype,x[1].dtype)
  d._forward=types.MethodType(adapter,d)
  try:
   with torch.inference_mode():actual=d.forward([video,audio],t,context,transformer_options=opts.copy(),minimax_payload=payload)
  finally:d._forward=original
  for a,b in zip(actual,expected):torch.testing.assert_close(a,b,rtol=1e-5,atol=1e-6)
  results.append({'audio_scale':scale,'sigma':sigma,'max_abs_video':(actual[0]-expected[0]).abs().max().item(),'max_abs_audio':(actual[1]-expected[1]).abs().max().item()})
record={'passed':True,'cases':results,'scope':'CPU zero-block float32 synthetic packing/final-layer and carried-audio boundary parity only; no quantized weights, attention, distributed execution or generation quality tested'}
print(json.dumps(record,indent=2))
