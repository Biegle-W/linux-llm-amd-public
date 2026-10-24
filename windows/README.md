# Windows local LLM — RTX 3060

Current Windows reference, validated 23 October 2026. This is a separate machine from the Linux dual-RX-7900-XTX build. Linux profiles, runtimes and benchmarks remain independent.

| Component | Validated Windows configuration |
|---|---|
| Hardware | i5-13600KF, 16 GB DDR5 at 6000 MT/s, RTX 3060 12 GB |
| Runtime | llama.cpp b11630 (`6868a52cb`), CUDA 13.4, NVIDIA 610.88 |
| Model | Ornith 1.5 35B-A3B IQ2_S MoE, text only |
| Profiles | Ornith default32K; LFM/Qwen27B/Empero8K; GPU + RAM, Q8 K/V, Flash Attention |
| Short decode samples | 48.24 / 44.29 tokens/s (two 128-token-limit samples) |

Chat, streaming, tool round trip and 8,080-token input retrieval passed. Allocation is not a full-32K quality or stress test. Measurements describe this complete profile and are not a controlled comparison with Linux or archived dual-NVIDIA results. See [curated evidence](reports/WINDOWS-MOE-MODELS-20261023.md) and [numeric record](reports/windows-moe-summary-20261023.json).

## Prepare and launch

This directory is a reference distribution: install the runtime and download weights separately. Binaries, models and private app data are excluded.

1. Put the matching CUDA runtime at `runtimes/llama.cpp-b11630-cuda-13.4/` under this directory. The launcher expects Python at `runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe`; install that runtime, a compatible NVIDIA driver and Windows Terminal.
2. Download [Ornith-1.5-35B-A3B-IQ2_S.gguf](https://huggingface.co/bartowski/Ornith-1.5-35B-A3B-GGUF/tree/64b0493d34a5ca4c1b4ad67bb99b41d74b4f07d6) into this directory's `models/` folder. The current registry needs all four files in the [verified inventory](reports/WINDOWS-CLEANUP-20261023.md); download the remaining models from the linked trial reports, or remove unwanted entries from `config/selected-profiles.json` before regenerating. The source profile uses `models/<filename>`, resolved against the project root. Preserve all options/admission fields; run `python scripts/build_configuration.py` to regenerate. Do not use `--full-gpu` for this mixed profile.

3. Open `Start Local LLM.cmd`. The owned backend opens in the visible Local-LLM terminal. The authenticated OpenAI-compatible API is `http://127.0.0.1:10000/v1`, model ID `Ornith-1.5-35B-A3B-IQ2_S`.

The router starts idle after validating registered weight paths. Loading a worker discovers the RTX 3060 UUID, exposes it as CUDA0 and refuses wrong hardware or insufficient resources. The default Ornith profile requires at least **4 GiB available RAM,16 GiB commit headroom and9,728 MiB actual free VRAM** before loading. Keep one model loaded; stop the owned backend with `scripts/Start.ps1 -Mode Stop` before benchmarking.

Selected options: fit on, GPU layers auto, **fit-target2816**, **no-host true**, split none, batch/microbatch512/128, Q8 KV, thinking off, no speculation. Measured normal model buffers:7,840.74 MiB GPU /2,643.67 MiB host; after streaming:1,571MiB actual free VRAM /1.19GiB available RAM. One short-generation sample reached1,336MiB free VRAM, so fitter target is not guaranteed headroom.

Both newer community MoEs passed functional tests: September's Empero Qwen3.8 distillation and August's Ornith1.5. Empero's IQ2_M remains downloaded outside the active catalog. The retired Qwen3.5 9B file was deleted at the user's request on October 23, freeing 5.56 GiB; historical results are retained. Empero is distilled into Qwen3.6 architecture; do not mistake its name for an official small Qwen3.8 release. Early faster trials used much less desktop VRAM headroom. Low-bit quantization and these functional checks do not establish answer-quality superiority. [All trials, hashes and limitations](reports/WINDOWS-MOE-MODELS-20261023.md).

## Clients and maintenance

The private key is generated/stored in `data/credentials/.local-api-key`. Do not commit it. DSH uses the `LLAMA_CPP_API_KEY` credential route; configure that variable or the app's credential service locally. The saved Windows DSH selector contains all four models and keeps Ornith default. The installed Desktop pi-ai SDK streamed through all four. Reopen DSH if its window caches the old selector; GUI selection was not tested. Thinking defaults are model-specific, including required LFM reasoning.

Tailscale forwarding selects only port 10000 while Windows Strata is disabled. Use `http://<TAILSCALE_HOST>:10000/v1` with the same real key. IPv4/MagicDNS host self-checks passed; a remote peer was not tested. No Funnel or Linux network policy was changed. LAN forwarding was not reconfigured/revalidated during this restoration.

`config/selected-profiles.json` and `config/stack.json` are the sources; `scripts/build_configuration.py` regenerates catalogs. The stale Windows dual-AMD draft is retired. Strata is disabled for this single-3060/16-GB reference; its source/settings are archived in `retired/20261023/`, outside maintained launch paths. Do not enable Linux AMD profiles here.

Keep Windows changes under `windows/`, preserve all Linux settings and historical measurement attribution, publish example paths and curated results only. Never commit runtime binaries, weights, keys, addresses, raw logs or private histories. This restoration reuses a validated runtime and does not claim a latest-version upgrade.

## LFM2.5 and official Qwen3.8 comparison — October 23

Separate8K IQ3_XXS test profiles passed chat, streaming, tools and~6K-input retrieval. LFM2.5 24B-A2B:78.24/85.04t/s total generation; Qwen3.8 27B:4.97/5.59t/s. LFM's128-token samples were reasoning only; Qwen's were visible prose with thinking off. First visible marker reply:1.828s LFM /0.922s Qwen. These are not matched completed-answer or quality results. Both used GPU + RAM; LFM required less host weight memory. Ornith remains the default. That earlier stopped-backend snapshot is historical; the later model router is running idle with all four models selectable and admission limits preserved.

[Methods, verified files, memory and limits](reports/WINDOWS-LFM-QWEN-TESTS-20261023.md), [numeric record](reports/windows-lfm-qwen-summary-20261023.json), [example separate test profiles](config/test-profiles-lfm-qwen-20261023.json). Weights must be downloaded separately into project `models/`; regenerate catalogs before testing. No Linux or network changes.

## Consolidated Windows layout — October 23

All four inference GGUFs belong in `models/`. Keep only selected CUDA/Python runtimes in `runtimes/`; configuration in `config/`; maintained helpers in `scripts/`; private state in `data/`; logs in `logs/`; dated evidence in `reports/`. Retired Strata source is in [retired/20261023](retired/20261023/README.md). Inactive binaries and backups are kept privately under ignored `archive/`. Regenerate catalogs after moving the project. All four model files were SHA256 verified after relocation; no benchmark rerun or default/guard change. [Cleanup record and inventory](reports/WINDOWS-CLEANUP-20261023.md).

## Select models through your harness — October 23

The authenticated endpoint remains `http://127.0.0.1:10000/v1`, with the existing
private API key. `GET /v1/models` lists Ornith32K, LFM8K, official Qwen27B8K and
Empero8K. Select one in the connected harness or set `model` in a chat/completions
request. A lightweight Python router starts without weights and owns one private
llama.cpp worker. It unloads before switching, applies each model's own admission
limits and keeps the switch lock through streaming. Busy/resource errors return
503 without a fallback. `/router/status` and `/router/unload` are authenticated.
Default Ornith's fitting and memory limits are unchanged. Stop/start after
changing registry settings. The installed DSH SDK streamed through all four; real
tools/JSON and unload checks plus seven protocol/concurrency tests pass. These are
functional smokes, not new throughput, full-window or GUI/remote-client tests.
The final router is running idle; desktop resource pressure can still refuse a
model load. [Usage and validation](reports/WINDOWS-MODEL-ROUTER-20261023.md).

## Optional MoE context in RAM — October 23

The router now has seven choices for four GGUF files. Original profiles and the
Ornith default remain unchanged. Extra `-128K-RAM` profiles for Ornith and LFM,
and `-64K-RAM` for Empero, keep Q8 K/V in CPU RAM. They reuse the same model files.
All passed chat/streaming/tools and retrieval beyond their previous allocations;
full64K/128K prompts were not tested. CPU attention trades speed for capacity.
LFM requires4.5GiB and Ornith/Empero5GiB available RAM before loading, with20GiB
commit headroom and the documented GPU limits. Reopen DSH to refresh its selector.
The router is running idle; desktop memory pressure can still refuse a load.
[Settings, measured cache placement and limits](reports/WINDOWS-MOE-RAM-CONTEXT-20261023.md).
