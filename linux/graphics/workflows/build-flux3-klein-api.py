#!/usr/bin/env python3
"""Build API graphs for FLUX 3 Image Klein from the official BF16 UI workflows.

The official workflows use subgraphs, which the /prompt API does not accept. This keeps
their no-bounding-box path: prompt upsampler (TextGenerate) -> Qwen3-VL-4B encoder ->
16-step Euler with ModelSamplingFlux shift log(16) -> FLUX.2 VAE. System prompts, sampler
settings and the edit template are read from the official files, not retyped.
Denoiser on cuda:0; upsampler, encoder and VAE on cuda:1 (the local device loaders).
"""
import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OFFICIAL = HERE / 'flux3-klein'
UNET = 'flux3-image-klein-bf16.safetensors'
ENCODER = 'qwen3vl_4b_bf16.safetensors'
UPSAMPLER = 'qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors'
VAE = 'flux2-vae.safetensors'


def subgraph_nodes(workflow, name_prefix):
    for sub in workflow['definitions']['subgraphs']:
        if sub['name'].startswith(name_prefix):
            return {node['id']: node for node in sub['nodes']}
    raise KeyError(name_prefix)


def official(kind):
    workflow = json.loads((OFFICIAL / f'flux3_klein_bf16_{kind}.json').read_text())
    upsampler = subgraph_nodes(workflow, 'Prompt Upsampler')
    diffusion = subgraph_nodes(workflow, 'Diffusion' if kind == 't2i' else 'Image to image')
    top = {node['id']: node for node in workflow['nodes']}
    # TextGenerate widgets: prompt, max_length, mode, temperature, top_k, top_p, min_p,
    # repetition_penalty, seed, presence_penalty, thinking, use_default_template, mtp.
    gen = upsampler[111]['widgets_values']
    sampler = top[128]['widgets_values']  # prompt, w, h, batch, steps, alpha, seed, sampler, scheduler, ...
    return {
        'system_prompt': upsampler[114]['widgets_values'][0],
        'edit_template': upsampler[134]['widgets_values'][0] if 134 in upsampler else None,
        'textgen': dict(zip(['max_length', 'sampling_mode', 'temperature', 'top_k', 'top_p', 'min_p',
                             'repetition_penalty', 'seed', 'presence_penalty', 'thinking',
                             'use_default_template', 'mtp'], gen[1:])),
        'steps': sampler[4], 'alpha': sampler[5], 'sampler_name': sampler[7], 'scheduler': sampler[8],
        'cfg': diffusion[107]['widgets_values'][3],
    }


def build(kind, prompt, seed, megapixels, width, height, image, prefix):
    spec = official(kind)
    gen = spec['textgen']
    shift = math.log(spec['alpha'])
    graph = {
        'up_clip': {'class_type': 'GraphicsCLIPLoader',
                    'inputs': {'clip_name': UPSAMPLER, 'type': 'flux3', 'device': 'cuda:1'}},
        'upsample': {'class_type': 'TextGenerate', 'inputs': {
            'clip': ['up_clip', 0], 'system_prompt': spec['system_prompt'],
            'prompt': prompt if kind == 't2i' else spec['edit_template'].replace('{a}', prompt),
            'max_length': gen['max_length'], 'sampling_mode': gen['sampling_mode'],
            **{f'sampling_mode.{k}': gen[k] for k in ('temperature', 'top_k', 'top_p', 'min_p',
                                                      'repetition_penalty', 'presence_penalty')},
            'sampling_mode.seed': seed, 'thinking': gen['thinking'],
            'use_default_template': gen['use_default_template'], 'mtp': gen['mtp']}},
        'caption': {'class_type': 'PreviewAny', 'inputs': {'source': ['upsample', 0]}},
        'unet': {'class_type': 'UNETLoader', 'inputs': {'unet_name': UNET, 'weight_dtype': 'default'}},
        'shift': {'class_type': 'ModelSamplingFlux', 'inputs': {
            'model': ['unet', 0], 'max_shift': shift, 'base_shift': shift, 'width': 1024, 'height': 1024}},
        'clip': {'class_type': 'GraphicsCLIPLoader',
                 'inputs': {'clip_name': ENCODER, 'type': 'flux3', 'device': 'cuda:1'}},
        'vae': {'class_type': 'GraphicsVAELoader', 'inputs': {'vae_name': VAE, 'device': 'cuda:1'}},
        'pos': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['clip', 0], 'text': ['upsample', 0]}},
        'neg': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['clip', 0], 'text': ''}},
        'sample': {'class_type': 'KSampler', 'inputs': {
            'model': ['shift', 0], 'seed': seed, 'steps': spec['steps'], 'cfg': spec['cfg'],
            'sampler_name': spec['sampler_name'], 'scheduler': spec['scheduler'], 'denoise': 1.0}},
        'decode': {'class_type': 'VAEDecode', 'inputs': {'samples': ['sample', 0], 'vae': ['vae', 0]}},
        'save': {'class_type': 'SaveImage', 'inputs': {'images': ['decode', 0], 'filename_prefix': prefix}},
    }
    if kind == 't2i':
        graph['latent'] = {'class_type': 'EmptyFlux2LatentImage',
                           'inputs': {'width': width, 'height': height, 'batch_size': 1}}
        graph['sample']['inputs'].update(positive=['pos', 0], negative=['neg', 0], latent_image=['latent', 0])
    else:
        graph['load'] = {'class_type': 'LoadImage', 'inputs': {'image': image}}
        graph['upsample']['inputs']['image'] = ['load', 0]
        # Official "match input image" output size: the reference scaled to the target megapixels.
        graph['scaled'] = {'class_type': 'ImageScaleToTotalPixels', 'inputs': {
            'image': ['load', 0], 'upscale_method': 'lanczos', 'megapixels': megapixels, 'resolution_steps': 16}}
        graph['size'] = {'class_type': 'GetImageSize', 'inputs': {'image': ['scaled', 0]}}
        graph['latent'] = {'class_type': 'EmptyFlux2LatentImage',
                           'inputs': {'width': ['size', 0], 'height': ['size', 1], 'batch_size': 1}}
        graph['refs'] = {'class_type': 'ReferenceMultiLatent', 'inputs': {
            'positive': ['pos', 0], 'negative': ['neg', 0], 'vae': ['vae', 0],
            'resolution': 'resize', 'resolution.megapixels': 1.0, 'images.image0': ['scaled', 0]}}
        graph['sample']['inputs'].update(positive=['refs', 0], negative=['refs', 1], latent_image=['latent', 0])
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['t2i', 'i2i'])
    parser.add_argument('--prompt', required=True)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--megapixels', type=float, default=1.0)
    parser.add_argument('--width', type=int, default=1024)
    parser.add_argument('--height', type=int, default=1024)
    parser.add_argument('--image', help='input image name in ComfyUI/input (i2i)')
    parser.add_argument('--prefix', default='flux3_klein')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.kind == 'i2i' and not args.image:
        parser.error('i2i needs --image')
    graph = build(args.kind, args.prompt, args.seed, args.megapixels, args.width, args.height,
                  args.image, args.prefix)
    args.output.write_text(json.dumps(graph, indent=2) + '\n')


if __name__ == '__main__':
    main()
