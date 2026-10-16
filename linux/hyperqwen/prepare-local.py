"""Reuse the local AWQ body with HyperQwen's published fast heads, on Linux NVMe."""
import copy
import json
import shutil
from pathlib import Path
from safetensors import safe_open

ROOT = Path('/opt/local-llm/models')
BASE = ROOT / 'Qwen3.8-27B-INT4-MTP-LowLatency'
HEADS = ROOT / 'HyperQwen/fast-head-source'
DST = ROOT / 'HyperQwen/Qwen3.8-27B-AWQ-HyperQwen-fast'
DST.mkdir(parents=True, exist_ok=True)
c = json.loads((BASE / 'config.json').read_text())
h = json.loads((HEADS / 'config.json').read_text())
assert c['text_config']['hidden_size'] == h['text_config']['hidden_size']
assert c['quantization_config']['config_groups']['group_0'] == h['quantization_config']['config_groups']['group_0']
idx = json.loads((BASE / 'model.safetensors.index.json').read_text())
wm = {k: v for k, v in idx['weight_map'].items()
      if not k.startswith(('lm_head.', 'mtp.'))}
for name in sorted(set(wm.values())):
    target = DST / name
    if not target.exists():
        print('Copying retained body', name, flush=True)
        shutil.copyfile(BASE / name, target)
for name in ('tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja',
             'generation_config.json', 'processor_config.json', 'preprocessor_config.json',
             'merges.txt', 'vocab.json'):
    if (BASE / name).exists():
        shutil.copyfile(BASE / name, DST / name)
for name in ('model-00007-of-00007.safetensors', 'model_extra_tensors.safetensors',
             'mtp_draft_vocab_ids.pt'):
    shutil.copyfile(HEADS / name, DST / name)
    if name.endswith('.safetensors'):
        with safe_open(DST / name, framework='pt', device='cpu') as f:
            for key in f.keys():
                assert key.startswith(('lm_head.', 'mtp.')), key
                wm[key] = name
# Preserve the original AWQ body's unquantized GDN projections and ignore entries.
qc = c['quantization_config']
qc['ignore'] = [x for x in qc['ignore'] if 'mtp' not in x]
for name in ('group_1', 'group_2', 'group_3'):
    qc['config_groups'][name] = copy.deepcopy(h['quantization_config']['config_groups'][name])
(DST / 'config.json').write_text(json.dumps(c, indent=2) + '\n')
idx['weight_map'] = wm
idx['metadata']['total_size'] = sum(p.stat().st_size for p in DST.glob('*.safetensors'))
(DST / 'model.safetensors.index.json').write_text(json.dumps(idx, indent=2) + '\n')
(DST / 'preparation.json').write_text(json.dumps({
    'body': json.loads((BASE / 'download-verification.json').read_text()),
    'heads_repo': 'syvai/qwen3.8-27b-3090-fast-variant',
    'heads_revision': '124c14e7e8c7d2f5402933b9af368e772a9fcf0c',
    'note': 'Retained AWQ body; published int4 GPTQ head/MTP and truncated draft vocabulary. Embedding quantized separately with upstream quant_embed.py.'
}, indent=2) + '\n')
print('Prepared', DST, flush=True)
