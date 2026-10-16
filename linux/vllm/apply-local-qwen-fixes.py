#!/usr/bin/env python3
"""Retain opt-in PP1/V2 MTP vocab sharing on the validated vLLM 0.32.0rc1.dev182+g429a3da66 wheel."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
PYTHON=ROOT/'vllm/.venv/bin/python'
version=subprocess.check_output([str(PYTHON),'-c','import importlib.metadata as m;print(m.version("vllm"))'],text=True).strip()
assert version=='0.32.0rc1.dev182+g429a3da66',f'Review local MTP sharing for vLLM {version}'
file=ROOT/'vllm/.venv/lib/python3.12/site-packages/vllm/model_executor/models/qwen3_5_mtp.py'
old=file.read_text()
if 'def _local_share_target_weights(' in old:
    print('Local vLLM 0.32.0rc1.dev182+g429a3da66 MTP sharing already installed.')
    raise SystemExit(0)

def one(s,needle,replacement):
    assert s.count(needle)==1,f'Unexpected source: {needle[:80]}'
    return s.replace(needle,replacement,1)

new=one(old,'import torch\n','import os\n\nimport torch\n')
helper='''
def _local_share_target_weights(config):
    """V2 load_eagle_model attaches target vocabulary modules after draft loading."""
    spec = config.speculative_config
    return (
        os.environ.get("VLLM_LOCAL_SHARE_QWEN_MTP") == "1"
        and config.use_v2_model_runner
        and get_pp_group().world_size == 1
        and spec is not None and spec.method == "mtp"
        and spec.draft_model_config.model == config.model_config.model
    )

'''
new=one(new,'logger = init_logger(__name__)\n', 'logger = init_logger(__name__)\n'+helper)
new=one(new,'''        self.embed_tokens = VocabParallelEmbedding(
            self.vocab_size,
            config.hidden_size,
        )''','''        self.embed_tokens = (
            PPMissingLayer() if _local_share_target_weights(vllm_config)
            else VocabParallelEmbedding(self.vocab_size, config.hidden_size)
        )''')
new=one(new,'        if get_pp_group().is_last_rank:\n            self.lm_head = ParallelLMHead(',
        '        if get_pp_group().is_last_rank and not _local_share_target_weights(vllm_config):\n            self.lm_head = ParallelLMHead(')
new=one(new,'            for name, weight in weights:\n                if self.is_unused_checkpoint_weight(name):',
'''            for name, weight in weights:
                if _local_share_target_weights(self.vllm_config) and any(
                    key in name for key in ("embed_tokens", "lm_head")
                ):
                    continue
                if self.is_unused_checkpoint_weight(name):''')
compile(new,str(file),'exec')
relative='model_executor/models/qwen3_5_mtp.py'
patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
(ROOT/'vllm/qwen-mtp-share-0.32.0rc1.dev182+g429a3da66.patch').write_text(patch)
file.write_text(new)
report={'version':version,'file':relative,'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest(),'opt_in':'VLLM_LOCAL_SHARE_QWEN_MTP=1','requires':'V2, PP1, same target/draft model path'}
(ROOT/'dsh/research/upgrade-2026-10-14/vllm-patch.json').write_text(json.dumps(report,indent=2)+'\n')
print('vLLM 0.32.0rc1.dev182+g429a3da66 local MTP sharing applied; source syntax checked.')
