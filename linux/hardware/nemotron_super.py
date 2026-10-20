"""Inspect downloaded Nemotron shards and prepare bounded, inactive profiles."""
import json
import os
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = Path('/mnt/llm-models/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF')
# Verified runtime copy on the shared NVMe (load 42 s vs 112 s from SATA, identical inference;
# hardware/SUPER-NVME-LOAD-2026-10-20.md). The SATA tree keeps the manifest and backup.
RUNTIME_MODELS = Path('/mnt/shared-nvme/LLM-Models/Nemotron-Super/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF')
GIB = 1024**3
IQ3_LAYERS = [3, 12, 17, 21, 26, 30, 34, 39, 43, 48, 52, 59, 65, 74, 81, 85]


def tensor_headers(path):
    """Read headers only; never materialize a weight or import a GPU runtime."""
    with Path(path).open('rb') as stream:
        def number(fmt):
            return struct.unpack('<' + fmt, stream.read(struct.calcsize('<' + fmt)))[0]

        def string(keep=True):
            size = number('Q')
            if keep:
                return stream.read(size).decode()
            stream.seek(size, 1)

        def value(kind, keep=True):
            formats = {0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i', 6:'f', 7:'?', 10:'Q', 11:'q', 12:'d'}
            if kind == 8:
                return string(keep)
            if kind == 9:
                subtype, count = number('I'), number('Q')
                if subtype in formats and not keep:
                    stream.seek(count * struct.calcsize(formats[subtype]), 1)
                    return
                result = [value(subtype, keep) for _ in range(count)]
                return result if keep else None
            return number(formats[kind])

        if stream.read(4) != b'GGUF' or number('I') != 3:
            raise ValueError('Expected a GGUF v3 shard')
        count, fields = number('Q'), number('Q')
        metadata = {}
        for _ in range(fields):
            key, kind = string(), number('I')
            item = value(kind, not key.startswith('tokenizer.'))
            if not key.startswith('tokenizer.'):
                metadata[key] = item
        tensors = []
        for _ in range(count):
            name, dimensions = string(), number('I')
            shape = [number('Q') for _ in range(dimensions)]
            kind, offset = number('I'), number('Q')
            tensors.append({'name':name, 'shape':shape, 'type':kind, 'offset':offset})
        alignment = metadata.get('general.alignment', 32)
        start = (stream.tell() + alignment - 1) // alignment * alignment
        tensors.sort(key=lambda item:item['offset'])
        for index, tensor in enumerate(tensors):
            end = tensors[index+1]['offset'] if index+1 < len(tensors) else Path(path).stat().st_size-start
            tensor['bytes'] = end-tensor['offset']
        return metadata, tensors


def prepare():
    manifest = json.loads((MODELS/'download-manifest.json').read_text())
    profiles = {}
    for quant, ident in [('UD-IQ3_XXS','nemotron-3.5-super-iq3'), ('UD-Q4_K_XL','nemotron-3.5-super-q4')]:
        tensors = []
        files = [entry for entry in manifest['files'] if entry['path'].startswith(quant + '/')]
        if len(files) != 3:
            raise ValueError('Expected three verified shards for ' + quant)
        metadata = {}
        for entry in sorted(files, key=lambda item:item['path']):
            path = MODELS/entry['path']
            if entry['status'] != 'verified' or path.stat().st_size != entry['size_bytes']:
                raise ValueError('Previously verified shard missing or resized: ' + str(path))
            shard_metadata, header = tensor_headers(path)
            metadata.update(shard_metadata)
            tensors.extend(header)
        layers = defaultdict(int)
        for tensor in tensors:
            if '_exps.' in tensor['name']:
                layers[int(tensor['name'].split('.')[1])] += tensor['bytes']
        if ident.endswith('iq3'):
            selected = IQ3_LAYERS
        else:
            # Spread host storage across the trunk; skip every third MoE layer.
            selected = [layer for index, layer in enumerate(sorted(layers)) if layer != 88 and index % 3 != 2]
            if not 46*GIB <= sum(layers[layer] for layer in selected) <= 49*GIB:
                raise ValueError('Q4 candidate CPU storage no longer matches the reviewed budget')
        profile = {
            'id':ident, 'enabled':False, 'backend':'hip-amd',
            'name':f'Nemotron 3.5 Super VL 120B {quant} (32K, dual AMD HIP, CPU experts + GPU cache, text/tools)',
            'quantization':quant, 'path':str(RUNTIME_MODELS/sorted(files,key=lambda item:item['path'])[0]['path']),
            'context':32768, 'minimum_host_ram_gib':28 if ident.endswith('iq3') else 60,
            'expert_count':int(metadata['nemotron_h_moe.expert_count']),
            'cpu_expert_layers':selected, 'host_expert_bytes':sum(layers[layer] for layer in selected),
            'gpu_expert_cache_mib':2048 if ident.endswith('iq3') else 4096,
            'all_weight_bytes':sum(tensor['bytes'] for tensor in tensors),
            'expert_layer_bytes':dict(layers), 'min_free_vram_gib':3, 'min_start_vram_gib':21,
            'kv_cache':'q8_0', 'load_mode':'none', 'tensor_split':'1,1',
            'mtp':False, 'vision_enabled':False, 'model_revision':manifest['revision'],
            'validation':'Prepared only; not activated or runtime-validated',
        }
        profiles[ident] = profile
    return profiles


def overrides(profile):
    layers = '|'.join(map(str, profile['cpu_expert_layers']))
    return 'token_embd.*=ROCm0,^blk\\.(?:' + layers + ')\\.ffn_.*_exps\\.weight$=CPU'


def server_args(profile, context=32768, split='1,1', mtp=False, port=18183, model_path=None, load_mode='none'):
    # LLAMA_CPP_DIR selects an isolated candidate build, matching dsh/llama_runtime.py.
    source = Path(os.environ.get('LLAMA_CPP_DIR') or ROOT/'llama.cpp')
    return [str(source/'build-hip/bin/llama-server'),
            '--model',str(model_path or profile['path']), '--alias',profile['id'], '--host','127.0.0.1', '--port',str(port), '--verbosity','4',
            '--ctx-size',str(context), '--parallel','1', '--device','ROCm0,ROCm1',
            '--split-mode','layer', '--tensor-split',split, '--n-gpu-layers','99', '--fit','off',
            '--override-tensor',overrides(profile), '--n-cpu-moe','0',
            '--moe-cache-mib',str(profile['gpu_expert_cache_mib']), '--load-mode',load_mode,
            '--batch-size','512', '--ubatch-size','128', '--threads','6', '--threads-batch','6',
            '--flash-attn','on', '--cache-type-k','q8_0', '--cache-type-v','q8_0',
            '--cache-ram','0', '--ctx-checkpoints','0', '--jinja', '--reasoning','off',
            '--chat-template-kwargs','{"enable_thinking":false}', '--temp','1.0', '--top-p','0.95',
            '--top-k','0', '--min-p','0', '--spec-type','draft-mtp' if mtp else 'none',
            *(['--spec-draft-n-max','3', '--spec-draft-type-k','q8_0', '--spec-draft-type-v','q8_0'] if mtp else [])]


if __name__ == '__main__':
    destination = ROOT/'dsh/candidates/nemotron-super.json'
    destination.parent.mkdir(exist_ok=True)
    profiles = prepare()
    destination.write_text(json.dumps(profiles, indent=2) + '\n')
    for profile in profiles.values():
        print(profile['id'], 'CPU expert GiB',profile['host_expert_bytes']/GIB,
              'minimum available GiB',profile['host_expert_bytes']/GIB+4)
