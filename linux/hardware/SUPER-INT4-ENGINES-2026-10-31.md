# Super INT4: vLLM and SGLang admission retry — October 31, 2026

The owner requested trying Nemotron 3.5 Super VL 120B INT4 with both engines. A fresh unchanged capacity check rejects full-model startup on the current 30.56 GiB host. Neither engine launched a candidate worker; the working llama.cpp IQ3 profile remains selected.

## Current results

| Engine | Result |
|---|---|
| vLLM `0.33.0rc1.dev229+g3966924d5.rocm72` | Optimistic admission requires **27.625 GiB available RAM**; **22.181 GiB** available. No full-model load or inference. |
| SGLang `f84475ccf593` | Same physical capacity obstacle, plus the exact Super architecture is unregistered and the RDNA3 compressed-tensors path rejects channelwise weights used by this checkpoint's INT8 Mamba projections. No full-model load or inference. |

The retained, previously verified [mixed INT4/INT8 checkpoint](https://huggingface.co/halt95/Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin) is revision `835d4cc7c9cc95f6dff9b1e4db2d5c520e847148`, about 67.88 GiB of weight files. Its routed experts are INT4 group128; Mamba projections are channelwise INT8, with remaining components in BF16. It is not a uniformly four-bit model.

The fresh lower bound removes optional MTP/vision tensors and assumes the remaining weights occupy all available VRAM except the unchanged 3 GiB reserve per card. CPU backing plus the existing 4 GiB startup reserve determines admission. It excludes KV/recurrent caches, activations, workspaces, replication and repacking, so a pass would still need full guarded qualification. Swap is not counted as physical expert capacity.

SGLang does have an RDNA3 W4A16/GPTQ fallback; describing every layer as simply Marlin-only would be inaccurate. Its explicit `group_size == -1` rejection and missing `NemotronH_Omni_Reasoning_V3` registration are the relevant current source blockers. Renaming the checkpoint architecture alone is not a validated port.

The earlier [small vLLM INT4/INT8 and UVA offload checks](SUPER-INT4-VLLM-PREFLIGHT-2026-10-29.md) remain valid within their limited scope and were not repeated. No new checkpoint download, source/runtime modification, service pause, guard change, GPU reservation or model promotion occurred. The hub health snapshot remains OK and idle. No task job or lock remains.

Next: after sufficient RAM is installed, repeat capacity admission and qualify vLLM first. SGLang additionally needs an isolated architecture/quantization compatibility implementation and correctness qualification. No speedup or full-model engine success is established. [Fresh measurements](results/super-int4-engines-2026-10-31.json).
