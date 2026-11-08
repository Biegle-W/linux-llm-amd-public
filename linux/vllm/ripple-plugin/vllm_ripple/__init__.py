"""Out-of-tree vLLM plugin: Ricursive Ripple-65B (RicursiveForCausalLM).

Model and config code are vllm-project/vllm commit 03bd3c6848 (PR #65745, merged 2026-11-05),
unchanged except for absolute imports. Loaded only when this directory is on PYTHONPATH (the
ripple-65b vLLM route); the production vLLM environment is not modified.
"""


def register():
    from vllm import ModelRegistry
    import vllm.transformers_utils.config as cfg
    from vllm_ripple.ricursive_config import RicursiveConfig

    if "RicursiveForCausalLM" not in ModelRegistry.get_supported_archs():
        ModelRegistry.register_model("RicursiveForCausalLM", "vllm_ripple.ricursive:RicursiveForCausalLM")
    if "ricursive" not in cfg._CONFIG_REGISTRY:
        cfg._CONFIG_REGISTRY["ricursive"] = RicursiveConfig
    try:
        from transformers import AutoConfig
        AutoConfig.register("ricursive", RicursiveConfig, exist_ok=True)
    except Exception:
        pass
