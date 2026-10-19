#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""Opt-in RDNA3 prefill tiles for the reviewed vLLM attention source.

Tile sizes follow JartX/vllm perf/rdna3_full_stack (822d275), Apache-2.0.
This narrow port keeps the current wheel's quantized cache and split-K paths.
"""
import hashlib
import os
from pathlib import Path

environment = Path(os.environ.get('VLLM_ENV_PATH', Path(__file__).resolve().parent/'.venv-rocm'))
file = environment/'lib/python3.12/site-packages/vllm/v1/attention/ops/triton_unified_attention.py'
source = file.read_text()
digest = hashlib.sha256(source.encode()).hexdigest()
patched_hash = 'b2c2a9edeb0e2f9d4b339e1db5d976bdf420adbc0453cec69bc83d9e411be58e'
if digest == patched_hash:
    print('RDNA3 prefill patch already installed.')
    raise SystemExit(0)
if digest == 'a60704ae9b1e7a5403fa9220e9d21acff4b6949f6b75fffaef0b2ac849e7702c':
    old_gate = "        and kv_quant_mode == KVQuantMode.INT8_PER_TOKEN_HEAD\n"
    new_gate = "        and (max_seqlen_q >= 64 or max_seqlen_k <= 1024)\n        and kv_quant_mode in (KVQuantMode.NONE, KVQuantMode.INT8_PER_TOKEN_HEAD)\n"
    if old_gate in source:
        source = source.replace(old_gate,new_gate,1)
        compile(source,str(file),'exec')
        assert hashlib.sha256(source.encode()).hexdigest() == patched_hash
        file.write_text(source)
        print('Extended gated tiles to BF16 and kept small continuation queries upstream.')
    raise SystemExit(0)
if digest != 'c1cf2300c99f5dc1fb297d7e556620842ab53c64c5ecda4c6ba89fb8e16215da':
    raise SystemExit('Unexpected attention source; review before patching.')


def replace(old,new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old,new,1)


replace('    MM_PREFIX_CLAMP_SW: tl.constexpr = False,\n',
        '    MM_PREFIX_CLAMP_SW: tl.constexpr = False,\n    LOCAL_MASK_PARTIAL_Q: tl.constexpr = False,\n')
replace('    query_mask_0 = tl.where(query_pos < cur_batch_query_len, 1, 0).to(tl.int1)\n',
        '''    query_mask_0 = tl.where(query_pos < cur_batch_query_len, 1, 0).to(tl.int1)
    if LOCAL_MASK_PARTIAL_Q:
        query_mask_0 = query_mask_0 & (offs_m < BLOCK_Q * num_queries_per_kv)
''')
replace('    # Ideally we would launch with kernel with:\n',
        '''    # Narrow opt-in port of JartX's gfx1100 prefill tile sizing.
    # MTP verification (<=8 queries) and all other shapes retain upstream paths.
    _local_rdna_prefill = False
    if (
        __import__("os").environ.get("VLLM_LOCAL_RDNA_PREFILL") == "1"
        and current_platform.is_rocm() and not use_td
        and max_seqlen_q > MAX_3D_QUERY_LEN
        and head_size == 256 and num_queries_per_kv == 6
        and (max_seqlen_q >= 64 or max_seqlen_k <= 1024)
        and kv_quant_mode in (KVQuantMode.NONE, KVQuantMode.INT8_PER_TOKEN_HEAD)
    ):
        from vllm.platforms.rocm import on_gfx1100
        if on_gfx1100():
            _local_rdna_prefill = True
            if max_seqlen_k > 8192:
                BLOCK_M, launch_num_warps = 128, 8
            elif max_seqlen_k > 1024:
                BLOCK_M, launch_num_warps = 64, 4
            else:
                BLOCK_M, launch_num_warps = 32, 2
            BLOCK_Q = BLOCK_M // num_queries_per_kv
            launch_num_stages = 1

    # Ideally we would launch with kernel with:
''')
replace('        MM_PREFIX_CLAMP_SW=mm_prefix_clamp_sliding_window,\n',
        '        MM_PREFIX_CLAMP_SW=mm_prefix_clamp_sliding_window,\n        LOCAL_MASK_PARTIAL_Q=_local_rdna_prefill,\n')
compile(source,str(file),'exec')
assert hashlib.sha256(source.encode()).hexdigest() == patched_hash
file.write_text(source)
print('Installed opt-in RDNA3 prefill tiles; default remains off.')
