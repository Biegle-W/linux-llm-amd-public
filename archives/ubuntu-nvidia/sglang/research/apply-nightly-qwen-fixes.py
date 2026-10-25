"""Apply the validated local mixed-GPU/MTP fixes to SGLang 0.5.22.dev20261015+ga12814c158 only."""
import difflib, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'sglang/.venv/lib/python3.12/site-packages/sglang'
version=subprocess.check_output([str(ROOT/'sglang/.venv/bin/python'),'-c','import importlib.metadata; print(importlib.metadata.version("sglang"))']).decode().strip()
assert version=='0.5.22.dev20261015+ga12814c158',f'Review this patch for SGLang {version} before applying'
changes={}

def edit(relative,transform):
 p=base/relative;old=p.read_text();new=transform(old)
 changes[relative]=(old,new)

def one(s,old,new):
 assert s.count(old)==1,f'Unexpected source for {old[:80]}'
 return s.replace(old,new,1)

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
 return one(s,'''                    param = params_dict[param_name]
                    weight_loader = getattr(''', '''                    param = params_dict[param_name]
                    if get_bool_env_var("SGLANG_LOCAL_SHARE_QWEN_MTP") and param.numel() == 0:
                        continue
                    weight_loader = getattr(''')

def runner(s):
 return one(s,'                torch.get_device_module(self.device).set_device(get_device().gpu_id)', '''                torch.get_device_module(self.device).set_device(get_device().gpu_id)
                if self.device == "cuda":
                    from sglang.kernels.jit.utils.arch import _init_jit_cuda_arch_once
                    _init_jit_cuda_arch_once()
                    _init_jit_cuda_arch_once.__wrapped__()''')

edit('srt/models/qwen3_5.py',qwen)
edit('srt/models/qwen3_5_mtp.py',mtp)
edit('srt/model_executor/model_runner.py',runner)
# All source expectations are checked before any file is modified.
for relative,(old,new) in changes.items():compile(new,relative,'exec')
patch=''.join(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative)) for relative,(old,new) in changes.items())
(Path(__file__).parent/'qwen-local-0.5.22.dev20261015+ga12814c158.patch').write_text(patch)
report={}
for relative,(old,new) in changes.items():
 (base/relative).write_text(new)
 report[relative]={'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest()}
(ROOT/'dsh/research/upgrade-2026-10-14/sglang-patch.json').write_text(json.dumps({'version':version,'files':report},indent=2)+'\n')
print('SGLang 0.5.22.dev20261015+ga12814c158 local fixes applied and syntax-checked.')
