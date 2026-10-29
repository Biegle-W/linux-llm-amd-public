# Nemotron Super INT4 vLLM preflight — October 29, 2026

The downloaded Nemotron 3.5 Super VL mixed INT4/INT8 candidate passes small AMD kernel and CPU-offload correctness checks, but the unchanged host-RAM admission guard refuses a full-model load. **Keep `nemotron-3.5-super-iq3` on llama.cpp. No faster vLLM result or replacement is established.**

## Candidate and download

[halt95 W4A16 Merlin checkpoint](https://huggingface.co/halt95/Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin), revision `835d4cc7c9cc95f6dff9b1e4db2d5c520e847148`. The 64 safetensors files total 72,888,191,872 bytes (67.8824 GiB); all downloaded LFS files passed their published SHA-256 checks. The candidate is retained on the admitted static SATA model drive; working IQ3 weights are retained. No NVIDIA Merlin wheel was installed and no selected engine was modified.

The checkpoint stores routed experts as symmetric INT4 group128, Mamba input/output projections as per-channel INT8, and main attention/shared experts/vision as BF16. Its publisher targets a custom NVIDIA Merlin fork; format alone does not establish AMD compatibility.

## Completed checks

On kernel `7.0.0-42-generic`, vLLM `0.33.0rc1.dev229+g3966924d5`, two available RX 7900 XTX cards and 30.5578 GiB visible RAM:

| Small layer check | Selected AMD kernel | Relative L2 error vs BF16 reference | CPU-offload output difference |
|---|---|---:|---:|
| INT4 group128 | RDNA3W4A16LinearKernel | 0.003233 | exactly zero |
| INT8 per-channel | ConchLinearKernel | 0.005017 | exactly zero |

Each check used M=4, K=N=128 and BF16 activations on one GPU. Both offload checks used pinned CPU memory through UVA. They establish only those small layer paths; they do not validate full-model mapping, all shapes, TP2, tools, quality, context or speed. Microtest per-run thermal peaks were not captured; no model thermal/performance qualification is claimed.

## Full-model admission refused

The existing `dsh/moe_memory.py` admission function was applied without changing its reserve policy:

| Optimistic placement bound | GiB |
|---|---:|
| Checkpoint minus optional MTP and vision tensors | 64.841 |
| Maximum GPU weights after current usage and 3 GiB per-card reserve | 41.917 |
| Minimum CPU weight backing | 22.924 |
| Existing startup RAM reserve | 4.000 |
| Minimum available RAM required | 26.924 |
| Available RAM at admission check | 23.181 |

This is already an optimistic lower bound: it gives the GPU weight allocation no KV/recurrent cache, activation, workspace, TP replication or repacking overhead. The real requirement is higher. The guard reported **26.9 GiB required / 23.2 GiB available** and refused before a full-model worker launched. Swap is not counted as physical expert capacity. The earlier weight-only 44 GiB GPU estimate did not include the retained 3 GiB per-card safety reserves and cannot justify bypassing this check.

## Temporary service-pause retry — October 29

At the user's request, the Hermes gateway and Prometheus/Grafana monitoring containers were temporarily stopped after recording their running states and restart policies. No desktop, network, cooling, inference guard, API/hub or unrelated application was stopped.

Available RAM increased from **23.0458 GiB** to **23.5324 GiB**, a measured gain of **0.4866 GiB**. The same admission function still refused: **26.9243 GiB required**, before any cache/workspace overhead. Thus this retry also stopped before a full-model worker launched; there is no vLLM speed result.

All three stopped services were restored and verified running. The Hermes service enablement and both container restart policies match their pre-test states. No restoration obligation or test GPU lock remains. Guards and the selected llama.cpp profile are unchanged. More available physical RAM is still needed for a fresh guarded attempt.

## Outcome and next step

No full-model inference, matched post-update llama.cpp comparison, 32K context proof or normal API qualification was run. Existing benchmark speeds keep their original attribution. The conditional replacement criterion was not met; the working llama.cpp profile remains selected. All owned microtest processes exited and the GPU lock is released; the completed download job is inactive. Existing runtime pins, guards, paused routes and other schedules remain unchanged.

A future attempt needs sufficient available physical RAM beyond this lower bound, followed by a fresh guarded capacity check and the still-pending load, functional, context and matched speed tests. Do not repeat the completed download or small-kernel checks solely for documentation. [Numeric evidence](results/super-int4-vllm-preflight-2026-10-29.json).
