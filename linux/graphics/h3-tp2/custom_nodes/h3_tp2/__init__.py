"""Production glue for H3 two-card tensor parallel (fcys tp2-comfy over RCCL P2P).

Rank 0 (the production server on :8188) rewrites every H3 INT8 prompt to the qualified TP form:
  - the diffusion loader becomes H3TP2UNetLoader (wraps the INT8-Fast OTUNetLoaderW8A8 with the
    qualified settings), and every component `device` input becomes cuda:0 (the rank's own card);
  - when that loader executes on rank 0, it frees rank 0's models, then queues the follower graph
    (same encoder/conditioning/noise/sampler, ending in H3TP2FollowerSink) on rank 1.
Rank 1 runs the follower graph on the Sapphire; its sink frees rank 1's VRAM after sampling.
Non-H3 prompts are not touched.
"""
import copy
import json
import logging
import os
import sys
import threading
import time
import types
import urllib.request
from pathlib import Path

RANK = int(os.environ.get("TP_RANK", "-1"))
FOLLOWER = os.environ.get("H3_TP2_FOLLOWER", "")  # e.g. http://127.0.0.1:18189 (rank 0 only)
H3_FILES = {"minimax_h3_fl2va_pruned_int8_convrot.safetensors"}
DIFFUSION_LOADERS = {"UNETLoader", "OTUNetLoaderW8A8", "H3TP2UNetLoader", "H3StagedUNetLoader"}
TP_ENCODERS = {"GraphicsH3ProjectedCLIPLoader"}  # small encoders that each rank can run itself
SAMPLERS = {"SamplerCustomAdvanced", "SamplerCustom", "KSampler", "KSamplerAdvanced"}
CANONICAL = "ComfyUI-INT8-Fast-ROCM"
log = logging.getLogger("h3_tp2")


# --- make the plugin importable under its canonical name (fcys core/tp_linear import it so) ---
def _bridge():
    for _ in range(4800):
        found = []
        for name, module in list(sys.modules.items()):
            if not isinstance(module, types.ModuleType):
                continue
            src = module.__dict__.get("__file__")
            if src and Path(src).parent.name == CANONICAL and Path(src).name == "__init__.py" \
                    and module.__dict__.get("NODE_CLASS_MAPPINGS"):
                found.append((name, module))
        if found:
            break
        time.sleep(0.05)
    else:
        log.error("[h3_tp2] INT8 plugin did not load; H3 TP2 unavailable")
        return
    assert len(found) == 1, "duplicate INT8 plugin instances"
    prefix, _ = found[0]
    for name, module in list(sys.modules.items()):
        if name == prefix or name.startswith(prefix + "."):
            alias = CANONICAL + name[len(prefix):]
            assert alias not in sys.modules or sys.modules[alias] is module, alias
            sys.modules[alias] = module
    print("[h3_tp2] INT8 plugin bridged as " + CANONICAL, flush=True)


threading.Thread(target=_bridge, daemon=True).start()


# --- pre-sliced halves (make_halves.py): each rank loads only its ~10 GB half, no per-job CPU split ---
HALVES_DIR = os.environ.get("H3_TP2_HALVES", "")
_HALVES = {}


def _halves(source_name):
    """Return {0: rank0 file, 1: rank1 file} if the manifest still matches the source, else None."""
    if source_name in _HALVES:
        return _HALVES[source_name]
    result = None
    try:
        import folder_paths
        m = json.loads((Path(HALVES_DIR) / "manifest.json").read_text())
        src = Path(folder_paths.get_full_path("diffusion_models", source_name))
        st = src.stat()
        if m["source"] == source_name and m["source_bytes"] == st.st_size and m["source_mtime_ns"] == st.st_mtime_ns:
            names = {}
            for r in (0, 1):
                h = m["halves"][str(r)]
                if (Path(HALVES_DIR) / h["file"]).stat().st_size != h["bytes"]:
                    raise ValueError("half size changed")
                names[r] = h["file"]
            result = names
            H3_FILES.update(names.values())
    except Exception as e:
        print("[h3_tp2] pre-sliced halves unavailable (%r); splitting per job" % (e,), flush=True)
    _HALVES[source_name] = result
    return result


# --- graph helpers ---
def _h3_loader_ids(prompt):
    # The source name must be recognised before _halves() registers the half names.
    return [k for k, v in prompt.items()
            if v.get("class_type") in DIFFUSION_LOADERS and v.get("inputs", {}).get("unet_name") in H3_FILES]


def _ancestors(prompt, roots):
    seen, stack = set(), list(roots)
    while stack:
        k = stack.pop()
        if k in seen or k not in prompt:
            continue
        seen.add(k)
        for v in prompt[k].get("inputs", {}).values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                stack.append(v[0])
    return seen


def _own_card(prompt):
    for v in prompt.values():
        inp = v.get("inputs", {})
        if isinstance(inp.get("device"), str) and inp["device"].startswith("cuda:"):
            inp["device"] = "cuda:0"


def rewrite(prompt):
    """Return (rank0_prompt, follower_prompt) or None when the prompt is not H3."""
    loaders = _h3_loader_ids(prompt)
    if not loaders:
        return None
    p = copy.deepcopy(prompt)
    if not any(v.get("class_type") in TP_ENCODERS for v in p.values()):
        # Native 32B encoder: each rank would load its own 15 GB copy (measured 246 s vs 93 s
        # staged), so these prompts keep the staged single-process placement.
        for k in loaders:
            inp = p[k]["inputs"]
            p[k] = {"class_type": "H3StagedUNetLoader",
                    "inputs": {"unet_name": inp["unet_name"], "weight_dtype": inp.get("weight_dtype", "default")}}
        return p, None
    _own_card(p)
    for k in loaders:
        p[k] = {"class_type": "H3TP2UNetLoader",
                "inputs": {"unet_name": p[k]["inputs"]["unet_name"], "follower_graph": ""}}
    samplers = [k for k, v in p.items() if v.get("class_type") in SAMPLERS
                and set(loaders) & _ancestors(p, [k])]
    if not samplers:
        raise ValueError("H3 prompt has no sampler fed by the H3 model")
    f = {}
    for i, s in enumerate(samplers):
        f["h3tp2_sink_%d" % i] = {"class_type": "H3TP2FollowerSink", "inputs": {"samples": [s, 0]}}
    keep = _ancestors(p, samplers)
    for k in keep:
        f[k] = copy.deepcopy(p[k])
    for k in loaders:
        halves = _halves(p[k]["inputs"]["unet_name"]) if HALVES_DIR else None
        if halves:
            p[k]["inputs"]["unet_name"] = halves[0]
            f[k]["inputs"]["unet_name"] = halves[1]
    for k in loaders:
        p[k]["inputs"]["follower_graph"] = json.dumps(f, sort_keys=True)
    return p, f


def _post(path, payload=None, timeout=10):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(FOLLOWER + path, data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


# --- nodes ---
class H3TP2UNetLoader:
    @classmethod
    def INPUT_TYPES(cls):
        import folder_paths
        return {"required": {"unet_name": (folder_paths.get_filename_list("diffusion_models"),),
                             "follower_graph": ("STRING", {"default": "", "multiline": True})}}

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "load"
    CATEGORY = "advanced/loaders"

    def load(self, unet_name, follower_graph):
        import comfy.model_management as mm
        if follower_graph.startswith("queued:"):
            pass  # rank 1 was already started when the prompt arrived on an idle server
        elif follower_graph:  # rank 0: free both cards of our own models, then start rank 1
            if RANK != 0 or not FOLLOWER:
                raise RuntimeError("H3 TP2 follower graph on a non-leader rank")
            mm.unload_all_models()
            mm.soft_empty_cache()
            try:
                _post("/system_stats", timeout=5)
                res = _post("/prompt", {"prompt": json.loads(follower_graph), "client_id": "h3-tp2-follower"})
            except Exception as e:
                raise RuntimeError("H3 TP2 rank 1 is not reachable: %r" % (e,))
            if res.get("node_errors"):
                raise RuntimeError("H3 TP2 rank 1 rejected the follower graph: %s" % str(res)[:800])
            print("[h3_tp2] rank1 follower queued " + str(res.get("prompt_id")), flush=True)
        mod = sys.modules.get(CANONICAL + ".int8_unet_loader")
        if mod is None:
            raise RuntimeError("INT8 plugin not bridged; H3 TP2 unavailable")
        return mod.UNetLoaderINTW8A8().load_unet(
            unet_name, weight_dtype="bf16", model_type="minimax h3", on_the_fly_quantization=False,
            enable_convrot=True, lora_mode="None", disable_dynamic=True)


class H3StagedUNetLoader:
    """Plain UNETLoader that tells the TP hook to leave this H3 load unsplit (staged placement)."""
    @classmethod
    def INPUT_TYPES(cls):
        import nodes
        return nodes.UNETLoader.INPUT_TYPES()

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "load"
    CATEGORY = "advanced/loaders"

    def load(self, unet_name, weight_dtype):
        import nodes
        import comfy.model_management as mm
        mm._h3tp2_staged = True
        try:
            return nodes.UNETLoader().load_unet(unet_name, weight_dtype)
        finally:
            mm._h3tp2_staged = False


class H3TP2FollowerSink:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"samples": ("LATENT",)}}

    RETURN_TYPES = ()
    FUNCTION = "done"
    OUTPUT_NODE = True
    CATEGORY = "advanced/h3_tp2"

    def done(self, samples):
        import comfy.model_management as mm
        mm.unload_all_models()  # give the Sapphire back to rank 0's staged workflows
        mm.soft_empty_cache()
        return {}


NODE_CLASS_MAPPINGS = {"H3TP2UNetLoader": H3TP2UNetLoader, "H3TP2FollowerSink": H3TP2FollowerSink,
                       "H3StagedUNetLoader": H3StagedUNetLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"H3TP2UNetLoader": "H3 TP2 Loader (internal)",
                              "H3StagedUNetLoader": "H3 Staged Loader (internal)",
                              "H3TP2FollowerSink": "H3 TP2 Follower Sink (internal)"}


# --- rank 0 server hooks ---
if RANK == 0 and FOLLOWER:
    from server import PromptServer
    from aiohttp import web

    def _on_prompt(json_data):
        prompt = json_data.get("prompt")
        if not isinstance(prompt, dict):
            return json_data
        try:
            out = rewrite(prompt)
        except Exception as e:  # make validation fail loudly instead of running untested graphs
            json_data["prompt"] = {"h3tp2_error": {"class_type": "H3TP2RewriteFailed: " + str(e)[:200],
                                                   "inputs": {}}}
            return json_data
        if out is not None and out[1] is None:
            json_data["prompt"] = out[0]
            print("[h3_tp2] H3 prompt kept staged (native encoder)", flush=True)
        elif out is not None:
            json_data["prompt"] = out[0]
            print("[h3_tp2] H3 prompt rewritten for TP2", flush=True)
            _early_start(out[0])
        return json_data

    def _early_start(prompt):
        """If rank 0 is idle, free its models and start rank 1 now, so both ranks load in parallel.
        Otherwise the H3TP2UNetLoader starts rank 1 when this prompt actually runs."""
        try:
            running, pending = PromptServer.instance.prompt_queue.get_current_queue()
            if running or pending:
                return
            import comfy.model_management as mm
            mm.unload_all_models()
            mm.soft_empty_cache()
            for v in prompt.values():
                inp = v.get("inputs", {})
                if v.get("class_type") == "H3TP2UNetLoader" and inp.get("follower_graph"):
                    res = _post("/prompt", {"prompt": json.loads(inp["follower_graph"]),
                                            "client_id": "h3-tp2-follower"})
                    if res.get("node_errors"):
                        return
                    inp["follower_graph"] = "queued:" + str(res.get("prompt_id"))
                    print("[h3_tp2] rank1 follower started early " + str(res.get("prompt_id")), flush=True)
        except Exception as e:
            print("[h3_tp2] early start skipped: %r" % (e,), flush=True)

    PromptServer.instance.add_on_prompt_handler(_on_prompt)

    @web.middleware
    async def _forward_interrupt(request, handler):
        if request.method == "POST" and request.path in ("/interrupt", "/api/interrupt"):
            threading.Thread(target=lambda: _safe_post("/interrupt", {}), daemon=True).start()
        return await handler(request)

    def _safe_post(path, payload):
        try:
            _post(path, payload, timeout=5)
        except Exception:
            pass

    PromptServer.instance.app.middlewares.append(_forward_interrupt)
