# Current AMD runtime handoff — November 8, 2026

This is the current operational summary for Linux, Windows and phone API clients. Read the root [rules](../../README.md) first. Dated history is in the [changelog](../hardware/CHANGELOG.md); it is not startup reading.

## State in one paragraph

Twelve qualified routes are enabled and all passed the guarded short tool-call check on November 7 in the [working layout](../hardware/AMD-WORKING-SETUP-2026-11-07.md). The GPU fault hold was released by the owner on November 7 at 03:56; `hardware/generated/GPU-LOCK` is absent. On November 8 GLM and both DeepSeek routes got larger RAM tiers, expert profiles and 2 GiB VRAM reserves, which made them about 2× (DeepSeek) to 7× (GLM) faster ([report](../hardware/GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md)). Three routes were removed after the [quant comparison](../hardware/QUANT-QUALITY-COMPARISON-2026-11-08.md), and their weights were deleted. A resident ComfyUI TP2 worker currently holds the GPUs, so the nightly updater skips until it exits.

## First five minutes

```bash
cd /opt/local-llm && git status --short
ls hardware/generated/GPU-LOCK 2>/dev/null || echo "no lock or hold"
systemctl --user list-timers 'llm-*' --no-pager
systemctl --user is-active local-llm-hub.service local-llm-api.service
pgrep -af 'router|strata|maya|vllm|sglang|llama-server|comfy' | cut -c1-160
df -h   # keep every drive below 90% used
uname -r   # expect 7.0.14-42-vmpt1
```

## Enabled routes

| API model ID | Engine | Weights | Mode | Context | Key settings |
|---|---|---|---|---:|---|
| `empero-qwen3.8-35b-a3b` | llama.cpp | Empero Qwen3.8-35B-A3B IQ4_XS | VRAM | 262,144 | layer split, MTP |
| `flint-40b-a2.5b` | llama.cpp | Flint-40B-A2.5B Unsloth UD-Q4_K_XL | VRAM | 32,768 | layer split, bounded reasoning |
| `ornith-1.5-122b` | llama.cpp | Ornith-1.5-122B Q4_K_M + mmproj | CPU-RAM offload | 32,768 | CPU experts + VRAM cache, vision |
| `qwen3.8-27b-vllm` | vLLM TP2 | Qwen3.8-27B AutoRound W4A16 | VRAM | 163,840 | compiled MTP3, BF16 KV |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | same Qwen3.8-27B weights + DFlash2 drafter | VRAM | 163,840 | BF16 KV, prefix cache |
| `nemotron-3.5-bolt-vllm` | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 | VRAM | 262,144 | runtime globaldev229 |
| `sage-a1.5` | vLLM | Sage-A1.5 AutoRound W4A16 | VRAM | 65,536 | MTP3, text only |
| `ripple-65b-vllm` | vLLM TP2 | Ripple-65B-Preview GPTQ W4A16 | VRAM | 65,536 | P2P, out-of-tree `vllm/ripple-plugin` |
| `qwen3.8-flash-next-iq3_xxs` | Strata | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | SSD streaming | 262,144 | RAM/VRAM expert caches, reserve 1024 MiB |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S | SSD streaming | 32,768 | expert profile, 36 GB RAM store, reserve 2048 MiB, 14 threads |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | same DeepSeek UD-IQ1_S backing | SSD streaming | 32,768 | expert profile, `64gb-q1-v1` tier, reserve 2048 MiB, 20 threads |
| `glm-5.3-flash-maya` | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS | SSD streaming | 32,768 | `MAYA_GLM_RAM_GB=40`, expert profile, reserves 2048/2048 MiB |

- The registries are `dsh/models.json` and `dsh/models-hip.ini` (llama), `dsh/llama-runtime.json` (active and paused llama models), `dsh/vllm-profiles.json`, `dsh/sglang-profiles.json`, `dsh/strata-profiles.json`, `dsh/maya-profiles.json`, and the sealed `dsh/qualified-native-profiles.json` / `dsh/qualified-strata-qwen-profiles.json` (currently empty). `dsh/model_catalog.py` combines them; authenticated `/v1/models` is the live list.
- Context is allocation capacity. Short checks prove neither full-window quality nor sustained throughput.
- Disabled rows kept for reference (weights removed): `nemotron-3.5-super-iq3`, `deepseek-v4.1-flash-1017-strata-xs`, `deepseek-v4.1-flash-1017-maya`. Removed November 8: Flash-Next UD-IQ1_M and both DeepSeek Coder IQ2_XXS routes. Final failed candidates (no retry without new evidence): PLE host-file-gather, Super INT4 EP2, the Maya DeepSeek 36 GB store, RDNA3 full-stack fork `2314df4`.

## Hardware and kernel

- Intel i5-13600KF, ASUS TX GAMING B760M WIFI, 61.5 GiB visible RAM (64 GB DDR5).
- Two RX 7900 XTX 24 GB behind a PEX880xx switch: Gen4 x16 uplink, x8 per card. PowerColor `0b:00.0` is ROCm 0 and Sapphire `13:00.0` is ROCm 1 (`ROCR_VISIBLE_DEVICES=0,1`, `HIP_VISIBLE_DEVICES=0,1`, set in `hardware/rocm-env.sh`).
- Kernel `7.0.14-42-vmpt1` is the owner-selected default; stock is installed as fallback. 
- Past Sapphire bus-loss faults happened only with Sapphire behind the switch. The [working setup](../hardware/AMD-WORKING-SETUP-2026-11-07.md) has the crash-recovery runbook.

## Guards (do not weaken)

- 100°C stop for CPU, GPU edge/junction/memory and SSD; SMART health checks.
- Host floor 1 GiB available RAM; 128 MiB free per card while live; dedicated-VRAM spill check; supervisor heartbeat (6 s); phase budgets of 1800 s for loading, prefill and generation; owned cleanup within 15 s.
- Native VRAM reserve: at least 2048 MiB requested per card (`MIN_RESERVE_MIB` in `dsh/qualified_native_runtime.py`). At startup the Maya router (all routes) and the Strata router (DeepSeek routes only) require free VRAM of the reserve minus 1 GiB, between 1 and 6 GiB.
- Resource policy `loading-swap-v5`: worker hard limits come from installed RAM; device-speed swap is allowed with storage and temperature protection. Never disable global swap or touch unrelated applications.
- The hub unloads an owned idle backend after 600 s. It never stops active, queued, starting or unknown work.

## Timers

| Timer | When | Notes |
|---|---|---|
| `llm-daily-update.timer` | 03:00, `Persistent=false` | Skips while any inference or KFD owner exists. November 8 skipped because of the resident ComfyUI worker. |

## Runtime and source identities

<!-- daily-update:begin -->
**Engine versions after the 2026-11-07 daily update** (`llm-daily-update.timer`, 03:00; details in `hardware/DAILY-UPDATES.md`):

| Engine | Production |
|---|---|
| llama.cpp | `818ac6b078e3` |
| vLLM | `0.33.0rc1.dev229+g3966924d5.rocm72` |
| SGLang | `f84475ccf593` |
| Strata | `146df3c46873` |
| Maya | `7bf15ac68f9b` |
| Strata DeepSeek | `ffa80d73133e` |
| Graphics | See `graphics/runtime-versions.json` for the selected ComfyUI/Torch/HIP identities |

Last run: llama.cpp promoted; Strata promoted; Maya promoted; Strata DeepSeek rejected.
<!-- daily-update:end -->

Enabled native source/binary/profile/backing identities are sealed per profile in `dsh/qualified-native-profiles.json`. Retired legacy pins remain separate; they are not the selected native sources.

Public native exports use `/opt/local-llm/qualified-sources` and **`requires-local-validation`** status. Admission rejects them before launch until independently qualified and sealed locally. Machine-specific inode/device/mtime seals are omitted; content hashes remain source-host evidence. Never manufacture a seal or mark passed merely to bypass admission.

ROCm SDK 7.2.3 and isolated runtime libraries are retained (`llm-tools/rocm-sdk`, `llm-tools/rccl-nohostcall`). `hardware/rocm-env.sh` selects qualified RCCL peer transport; llama's peer flag is enabled only for the qualified IDs in its registry. Native layer-group handoffs and default graphics placement make no direct peer-copy claim.

## Client access and managed lifecycle

LAN `http://<server-lan-ip>:10000/v1`; Tailscale `http://<server-vpn-ip>:10000/v1`; MagicDNS `http://<server-vpn-name>:10000/v1`.

Use the existing private bearer key and access policy. Retrieve credentials through the established local setup; keep credentials and their locations out of handoffs and exports. No new public exposure or tailnet-policy grant is authorized.

- OpenAI-compatible Chat Completions and native Responses `POST /v1/responses` are supported. Stream with a 600-second client timeout for cold loading, and start with 2,048 output tokens. OpenCat mixed tools and self-hosted SearXNG/RSS search are available; see [network details](README.md).
- The gateway on TCP 10000 forwards to `local-llm-hub.service` on `127.0.0.1:30100`. An inference request starts or switches a backend through the managed launchers; catalog and health GETs do not load models or reset idle time.
- Use the `bin/` and installed `llm-*` entry points and the Desktop launchers. DSH and Turnstone are optional frontends. Switching may interrupt owned replies but must preserve DSH, the gateway, unrelated Python, training or graphics applications and unknown port owners. Never blanket-kill Python or GPU processes.
- Production ComfyUI (`graphics/start-comfyui`) runs projected-8B H3 as two-card TP over RCCL P2P; FLUX, Qwen-Image and native-32B H3 use staged placement; `COMFY_MODE=staged` rolls back ([report](../graphics/H3-TP2-PRODUCTION-2026-11-07.md)). Do not load a second model worker while it holds the GPUs.

## Open items

1. **Updater starved.** The daily updater skips while a resident ComfyUI worker owns the KFD. Ask the owner before stopping that worker.
2. **One DeepSeek NaN event** on Sapphire (CUDA1) at the new settings, in about 141 requests. If it recurs, raise the Strata DeepSeek reserve to 4 GiB first.
3. **No sustained benchmark.** All route numbers are short checks. A longer owned soak at the November 8 settings is the main open check.
4. **Strata Qwen reserve is 1024 MiB** (`dsh/strata-iq3-profile.json`), below the 2 GiB floor for sealed native profiles. That floor does not apply to it: the route has no sealed record (`dsh/qualified-strata-qwen-profiles.json` (currently empty) is empty since the UD-IQ1_M route was removed). Leave it unless the owner asks.
5. **Stale metadata inside sealed profiles** (for example "8GiB requested reserve" in their `settings` text). Editing them would change the seals; leave them.
6. **Stale unit tests.** `python3 -m unittest discover -s hardware -p "test_*.py"` gives 40 failures and 8 errors out of 655 tests (November 8). The failing tests assert older guard values (8 GiB or 5 GiB reserves, swap policy v4, old RAM tiers) that the owner has since changed. Update the tests to the current policy before relying on them; do not relax a guard to make one pass.
## Keep this handoff small

After authorized work, replace the state above, add one changelog line, sanitize and publish both repos, and keep the private operational copy byte-identical on the shared drive (`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md`). `hardware/daily-update/publish.py` rewrites the block between the `daily-update` markers and depends on the `## Runtime and source identities` heading, the `Public native exports` paragraph after it, and this file's name; keep all three.

History only: [November 5 handoff](../hardware/history/documentation-2026-11-05/LINUX-LLM-RUNTIME-HANDOFF.reference.md), Git history for the November 8 pre-cleanup version, [benchmark history](../hardware/BENCHMARK-HISTORY.md). Do not restore superseded settings or resume old plans without a new owner request.
