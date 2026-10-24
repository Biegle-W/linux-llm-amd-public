# Windows local LLM — RTX 3060

Sanitized reference for the independent Windows RTX3060 12GB /i5-13600KF /16GB
build, llama.cpp b11630 CUDA13.4, NVIDIA610.88. Linux AMD remains separate.

## One setting per model — October 23, 2026

The OpenAI-compatible router exposes exactly four IDs, retaining the largest
currently configured context for each model. Ornith remains default at128K.

| API ID | Context | Q8 KV location | Available RAM before loading |
|---|---:|---|---:|
| `Ornith-1.5-35B-A3B-IQ2_S` | 128K | CPU RAM | 5 GiB |
| `LFM2.5-24B-A2B-UD-IQ3_XXS` | 128K | CPU RAM | 4.5 GiB |
| `Qwen3.8-27B-UD-IQ3_XXS` | 8K | GPU VRAM | 3.5 GiB |
| `Qwen3.8-35B-A3B-IQ2_M` (Empero) | 64K | CPU RAM | 5 GiB |

These are the same verified RAM-context settings; only duplicate profiles and
their suffixed API IDs were removed. All weights remain mixed GPU/RAM. The three
MoEs use Q8 KV in CPU RAM; dense Qwen27B retains its8K GPU-KV setting. Native
context allocation is not a full-window quality test: tested input lengths were
35,890/16,268/16,270 for Ornith/LFM/Empero and6,025 for Qwen27B. No new inference
benchmark was run for consolidation. [Measured placement and limits](reports/WINDOWS-MOE-RAM-CONTEXT-20261023.md),
[current catalog proof](reports/verification/windows-single-profile-20261023.json).

## Prepare and connect

Install the matching CUDA runtime under `runtimes/llama.cpp-b11630-cuda-13.4/`,
Python at `runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe`, and
Windows Terminal. Download all four GGUFs into `models/`; verified file names,
hashes and source links are in the [inventory](reports/WINDOWS-CLEANUP-20261023.md)
and linked trial reports. Binaries, models and private app data are not included.

Run `python scripts/build_configuration.py`, then `Start Local LLM.cmd`. The
authenticated endpoint is `http://127.0.0.1:10000/v1`; `GET /v1/models` lists the
four canonical IDs above. Send one in the chat request's `model` field. One
guarded private worker is loaded at a time. Active streams hold the switch lock;
busy/resource refusal returns503 without a fallback. Authenticated
`/router/status` and `/router/unload` remain available. Stop/start after changing
configuration. Regenerate absolute model paths after moving the project.

The private API key belongs in `data/credentials/.local-api-key`; DSH uses the
`LLAMA_CPP_API_KEY` credential route. Reopen DSH to refresh the selector. Keep
LFM's required reasoning template; do not globally disable thinking. The same
real key applies to `http://<TAILSCALE_HOST>:10000/v1`; remote-peer reachability
is not established by a host self-check. Network configuration was not changed.

RAM profiles need20GiB commit headroom and4.5–5GiB available physical RAM;
Qwen27B needs16GiB commit and3.5GiB available RAM. Fresh VRAM minimums remain
9216MiB for Ornith/Empero and8192MiB for LFM/Qwen27B, plus at least1024MiB after
loading. Preserve the0.75GiB/five-second RAM guard and CUDA0/split-none fitting.
CPU KV increases capacity at a speed cost. The router is left running idle.

Keep exactly one active configuration per model in `config/selected-profiles.json`.
Do not re-add smaller context alternatives. Archived trial profiles/source are
in `retired/20261023/`; dated reports preserve their original IDs and settings.
Historical settings may differ from the current registry. Keep weights/runtime/
state/backups ignored; publish no credentials, workstation paths or private app
data. Preserve Linux files and historical hardware/method attribution.
