"""Avoid temporary BF16 vocab tables for this headless DFlash2 checkpoint."""
import difflib
import sys
from pathlib import Path

root = Path(__file__).parent
file = root / 'upstream/venv/lib/python3.12/site-packages/vllm/model_executor/models/qwen3_dflash.py'
old = file.read_text()
if "def _local_shared_dflash_module(" in old:
    print("Local opt-in DFlash meta sharing is already installed")
    sys.exit(0)
marker = '\nclass DFlashQwen3Attention(nn.Module):'
helper = '''
def _local_shared_dflash_module(factory, *args, **kwargs):
    # Opt-in only for a drafter whose checkpoint has no embedding/head weights.
    # load_dflash_model() replaces these placeholders with the target modules.
    import os
    if os.environ.get("VLLM_LOCAL_DFLASH_META_SHARE") == "1":
        if get_current_vllm_config().parallel_config.pipeline_parallel_size != 1:
            raise ValueError("Local DFlash meta sharing requires PP1")
        with torch.device("meta"):
            return factory(*args, **kwargs)
    return factory(*args, **kwargs)

'''
assert old.count(marker) == 1
assert old.count('self.embed_tokens = VocabParallelEmbedding(') == 1
assert old.count('self.lm_head = ParallelLMHead(') == 1
new = old.replace(marker, '\n' + helper + marker)
new = new.replace('self.embed_tokens = VocabParallelEmbedding(', 'self.embed_tokens = _local_shared_dflash_module(VocabParallelEmbedding,')
new = new.replace('self.lm_head = ParallelLMHead(', 'self.lm_head = _local_shared_dflash_module(ParallelLMHead,')
compile(new, str(file), 'exec')
patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='a/model_executor/models/qwen3_dflash.py', tofile='b/model_executor/models/qwen3_dflash.py'))
(root / 'dflash-meta-share.patch').write_text(patch)
file.write_text(new)
print('Applied local opt-in DFlash meta sharing')
