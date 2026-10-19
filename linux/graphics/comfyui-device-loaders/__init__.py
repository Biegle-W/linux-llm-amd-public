"""Load the retained graphics components directly on their selected GPU.

Core SelectCLIPDevice reloads a second encoder through deepclone_multigpu.
Direct load_device options avoid that extra copy on a 32 GB host.
"""
import torch
import folder_paths
import comfy.sd
import comfy.utils


def gpu_device(name):
    device = torch.device(name)
    if device.type != 'cuda' or device.index not in range(torch.cuda.device_count()):
        raise ValueError(f'GPU is unavailable: {name}')
    return device


class GraphicsCLIPLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'clip_name': (folder_paths.get_filename_list('text_encoders'),),
            'type': (['qwen_image', 'minimax'],),
            'device': (['cuda:0', 'cuda:1'], {'default': 'cuda:1'}),
        }}

    RETURN_TYPES = ('CLIP',)
    FUNCTION = 'load_clip'
    CATEGORY = 'graphics/loaders'

    def load_clip(self, clip_name, type, device):
        path = folder_paths.get_full_path_or_raise('text_encoders', clip_name)
        clip = comfy.sd.load_clip(
            ckpt_paths=[path],
            embedding_directory=folder_paths.get_folder_paths('embeddings'),
            clip_type=getattr(comfy.sd.CLIPType, type.upper()),
            model_options={'load_device': gpu_device(device),
                           'offload_device': torch.device('cpu')},
        )
        return (clip,)


class GraphicsVAELoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'vae_name': (folder_paths.get_filename_list('vae'),),
            'device': (['cuda:0', 'cuda:1'], {'default': 'cuda:1'}),
        }}

    RETURN_TYPES = ('VAE',)
    FUNCTION = 'load_vae'
    CATEGORY = 'graphics/loaders'

    def load_vae(self, vae_name, device):
        path = folder_paths.get_full_path_or_raise('vae', vae_name)
        state, metadata = comfy.utils.load_torch_file(path, return_metadata=True)
        vae = comfy.sd.VAE(sd=state, metadata=metadata, device=gpu_device(device))
        vae.throw_exception_if_invalid()
        vae.patcher.cached_patcher_init = (comfy.sd.load_vae_patcher,
                                           (path, metadata, gpu_device(device)))
        return (vae,)


NODE_CLASS_MAPPINGS = {'GraphicsCLIPLoader': GraphicsCLIPLoader,
                       'GraphicsVAELoader': GraphicsVAELoader}
NODE_DISPLAY_NAME_MAPPINGS = {'GraphicsCLIPLoader': 'Load Graphics Encoder on GPU',
                              'GraphicsVAELoader': 'Load Graphics VAE on GPU'}
