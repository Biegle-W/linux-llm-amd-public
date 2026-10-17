"""Apply MTP sharing and chipset-compatible KV bounds checks to the pinned fork."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'sglang/rocm-src/python/sglang'
assert subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip() == 'f84475ccf593087df3d1da13c9e675eadee12352'
def one(s, old, new):
    assert s.count(old) == 1, 'Review changed source: ' + old[:80]
    return s.replace(old, new, 1)
def qwen(s):
 s=one(s,'        self.embed_tokens = self._build_embed_tokens(config)', '''        if is_nextn and get_bool_env_var("SGLANG_LOCAL_SHARE_QWEN_MTP") and get_parallel().pp_size == 1:
            with torch.device("meta"):
                self.embed_tokens = self._build_embed_tokens(config)
            self.embed_tokens.weight = nn.Parameter(torch.empty(0, device="cuda"), requires_grad=False)
        else:
            self.embed_tokens = self._build_embed_tokens(config)''')
 old='head = self.lm_head.weight if self.pp_group.is_last_rank else None'
 assert s.count(old)==2
 return s.replace(old,'head = getattr(self.lm_head, "weight", None) if self.pp_group.is_last_rank else None')

def mtp(s):
 s=one(s, "    get_model,\n", "    get_model,\n    get_parallel,\n")
 s=one(s,'''                self.lm_head = ParallelLMHead(
                    config.vocab_size,
                    config.hidden_size,
                    quant_config=quant_config,
                    prefix=add_prefix("lm_head", prefix),
                )''', '''                if get_bool_env_var("SGLANG_LOCAL_SHARE_QWEN_MTP") and get_parallel().pp_size == 1:
                    with torch.device("meta"):
                        self.lm_head = ParallelLMHead(
                            config.vocab_size, config.hidden_size,
                            quant_config=None, prefix=add_prefix("lm_head", prefix),
                        )
                    self.lm_head.weight = nn.Parameter(torch.empty(0, device="cuda"), requires_grad=False)
                else:
                    self.lm_head = ParallelLMHead(
                        config.vocab_size,
                        config.hidden_size,
                        quant_config=quant_config,
                        prefix=add_prefix("lm_head", prefix),
                    )''')
 s=one(s,'''                    param = params_dict[param_name]
                    weight_loader = getattr(''', '''                    param = params_dict[param_name]
                    if get_bool_env_var("SGLANG_LOCAL_SHARE_QWEN_MTP") and param.numel() == 0:
                        continue
                    weight_loader = getattr(''')
 return one(s,'''                        param = params_dict[name]
                        weight_loader = getattr(''', '''                        param = params_dict[name]
                        if get_bool_env_var("SGLANG_LOCAL_SHARE_QWEN_MTP") and param.numel() == 0:
                            continue
                        weight_loader = getattr(''')

changes = {}
for name, transform in [('qwen3_5.py',qwen),('qwen3_5_mtp.py',mtp)]:
    p = base / 'srt/models' / name
    s = p.read_text()
    if 'SGLANG_LOCAL_SHARE_QWEN_MTP' in s:
        continue
    changes[p] = transform(s)
for p,s in changes.items(): compile(s,str(p),'exec')
for p,s in changes.items(): p.write_text(s)
kv = base / 'kernels/jit/csrc/elementwise/kvcache.cuh'
source = kv.read_text()
if 'Chipset-connected RDNA3' not in source:
    source = one(source, '  assert(index >= 0 && index < size_limit);', '''#if defined(__HIP_PLATFORM_AMD__)
  // A device assert introduces a hostcall requirement even for valid indices.
  // Chipset-connected RDNA3 can lack PCIe atomics; preserve bounds enforcement
  // with a device trap instead of disabling the check with NDEBUG.
  if (!(index >= 0 && index < size_limit)) __builtin_trap();
#else
  assert(index >= 0 && index < size_limit);
#endif''')
    kv.write_text(source)
print('ROCm MTP sharing and HIP KV bounds-trap patches applied.')
