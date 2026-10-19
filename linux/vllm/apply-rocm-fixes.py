"""Apply the mixed-vendor detection fix only to the isolated ROCm wheel."""
from pathlib import Path
import os
root = Path(__file__).resolve().parent
environment = Path(os.environ.get('VLLM_ENV_PATH', root / '.venv-rocm'))
package = environment / 'lib/python3.12/site-packages/vllm'
p = package / 'platforms/__init__.py'
old = 'def cuda_platform_plugin() -> str | None:\n    is_cuda = False'
new = '''def cuda_platform_plugin() -> str | None:
    import torch
    if torch.version.hip is not None:
        return None  # ROCm build on a mixed AMD/NVIDIA workstation.
    is_cuda = False'''
s = p.read_text()
if new not in s:
    if old not in s:
        raise SystemExit('Upstream platform detection changed; review before patching.')
    p.write_text(s.replace(old, new, 1))
print('ROCm-only platform detection applied.')

# Avoid duplicate BF16 vocabulary allocation before V2 attaches target modules.
file = package / 'model_executor/models/qwen3_5_mtp.py'
old = file.read_text()
if 'def _local_share_target_weights(' in old:
    print('ROCm PP1/V2 MTP sharing already installed.')
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

file.write_text(new)
print("ROCm PP1/V2 MTP vocabulary sharing applied.")
