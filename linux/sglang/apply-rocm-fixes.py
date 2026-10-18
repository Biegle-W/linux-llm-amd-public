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

# The pinned backend now passes PREFIX-ONLY metadata to TARGET_VERIFY. The
# vendored unified adapter expects prefix+draft; keep this repair opt-in until
# its numerical/model tests pass on a deployment.
attention = base / 'srt/layers/attention/triton_backend.py'
source = attention.read_text()
if 'SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX' not in source:
    start = source.index('    def _rdna_unified_verify(')
    end = source.index('    def _rdna_unified_decode(', start)
    part = source[start:end]
    part = one(part, '        if extend_meta is not None:\n            from sglang.kernels.ops.attention.rdna_verify_adapter import (', '''        verify_seq_lens = forward_batch.seq_lens
        if (
            os.environ.get("SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX", "0") == "1"
            and extend_meta is None
            and forward_batch.forward_mode.is_target_verify()
        ):
            # This repair supports only a linear chain in an untranslated pool.
            if self.topk not in (0, 1) or self.dcp_size != 1 or self.kv_index_translator.is_translating:
                raise ValueError("KV-walk repair requires linear TP verification without pool translation")
            if q.shape[0] != bs * num_draft_tokens or meta.max_extend_len != num_draft_tokens:
                raise ValueError("KV-walk repair requires the configured fixed verify window")
            # TARGET_VERIFY's ordinary Triton path takes prefix KV separately
            # from this forward's K/V. Rebuild the causal chain expected by the
            # unified adapter, using the same scatter locations as the KV store.
            from sglang.kernels.ops.attention.rdna_verify_adapter import rdna_fill_extend

            verify_seq_lens = forward_batch.seq_lens + num_draft_tokens
            full_indptr = torch.zeros_like(kv_indptr)
            full_indptr[1:] = torch.cumsum(verify_seq_lens[:bs], dim=0)
            rdna_fill_extend(
                rdna_verify_bufs, kv_indices, kv_indptr,
                forward_batch.out_cache_loc, verify_seq_lens, bs,
                num_draft_tokens, full_indptr,
            )
            skip_fill = True

        if extend_meta is not None:
            from sglang.kernels.ops.attention.rdna_verify_adapter import (''')
    part = one(part, '            kv_indices,\n            forward_batch.seq_lens,\n            layer.scaling,', '            kv_indices,\n            verify_seq_lens,\n            layer.scaling,')
    source = source[:start] + part + source[end:]
    compile(source, str(attention), 'exec')
    attention.write_text(source)
print('Opt-in unified-verifier KV-walk repair is available.')

# Qwen TP2 uses 12 query / 2 KV heads (GQA=6). A 16-row tile holds two
# complete query groups and four partial lanes; those lanes must not race the
# next query block. Preserve the original kernel unless the repair is enabled.
unified = base / 'kernels/ops/attention/rdna_unified_verify.py'
source = unified.read_text()
if 'MASK_PARTIAL_Q_ROWS' not in source:
    source = one(source, 'import torch\n', 'import torch\nimport os\n')
    source = one(source, '    IS_3D: tl.constexpr,\n    q_block_offsets_ptr,',
                 '    IS_3D: tl.constexpr,\n    MASK_PARTIAL_Q_ROWS: tl.constexpr,\n    q_block_offsets_ptr,')
    source = one(source, '    query_mask_0 = tl.where(query_pos < cur_batch_query_len, 1, 0).to(tl.int1)', '''    query_mask_0 = tl.where(query_pos < cur_batch_query_len, 1, 0).to(tl.int1)
    if MASK_PARTIAL_Q_ROWS:
        query_mask_0 = query_mask_0 & ((offs_m // num_queries_per_kv) < BLOCK_Q)''')
    source = one(source, '        IS_3D=use_3d,', '''        IS_3D=use_3d,
        MASK_PARTIAL_Q_ROWS=(os.environ.get("SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX", "0") == "1"),''')
    compile(source, str(unified), 'exec')
    unified.write_text(source)
print('Opt-in partial-GQA query-row masking repair is available.')
