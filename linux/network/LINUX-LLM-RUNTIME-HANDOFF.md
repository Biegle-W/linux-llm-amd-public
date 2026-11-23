# Current AMD runtime handoff — November 11, 2026

This is the current operational summary for Linux, Windows and phone API clients. Read the root [rules](../../README.md) first. Dated history is in the [changelog](../hardware/CHANGELOG.md); it is not startup reading.

## State in one paragraph

Twelve qualified routes are enabled. On November 23 the owner had upstream Strata replace the RDNA3 fork under the main Flash-Next name `qwen3.8-flash-next-iq3_xxs` (the upstream setup had been the separate `qwen3.8-flash-next-iq3_xxs-upstream` entry since November 22; that name is gone). `inkling-2-mini-sq-20-strata` and `inkling-2-mini-sq-20-strata-2gpu` (November 23) were added at the owner's request as separate upstream Strata entries beside the existing routes (0.2.19, updated to 0.2.20 on November 23) ([report](../hardware/STRATA-0219-RESEARCH-2026-11-22.md)). `inkling-2-mini-q8` was added on November 21 at the owner's request (see the [report](../hardware/INKLING-2-MINI-2026-11-21.md)). Before that there were nine (`ornith-1.5-122b`, `sage-a1.5` and `flint-40b-a2.5b` were removed on November 11 at the owner's request). All nine passed the guarded short tool-call check on November 7 in the [working layout](../hardware/AMD-WORKING-SETUP-2026-11-07.md), and again on November 9 together with both graded quality suites ([report](../hardware/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.md)). Maya DeepSeek refuses to start while desktop GPU apps hold about 1 GiB of card 0; close them first. The GPU fault hold was released by the owner on November 7 at 03:56; `hardware/generated/GPU-LOCK` is absent. On November 8 GLM and both DeepSeek routes got larger RAM tiers, expert profiles and 2 GiB VRAM reserves, which made them about 2× (DeepSeek) to 7× (GLM) faster ([report](../hardware/GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md)). Three routes were removed after the [quant comparison](../hardware/QUANT-QUALITY-COMPARISON-2026-11-08.md), and their weights were deleted. Engine updates are no longer scripted: the owner retired the nightly updater on November 9, and the agent checks upstream and upgrades each engine by hand with the guarded short tool check.

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
| `inkling-2-mini-q8` | llama.cpp | Inkling 2 Mini UD-Q8_K_XL (upstream layout) | VRAM | 131,072 | all layer passes on the second card, expert blocks 20–23 and output on the display card; f16 KV; graph capture off (`no_graph_models`: ROCm 7.2.3 leaks VRAM on graph updates); since November 22 on the RDNA3 branch build `cb0e469607c1` through `source_overrides` (owner decision; upstream updates do not apply to this route); reasons briefly even at effort `none` |
| `qwen3.8-27b-vllm` | vLLM TP2 | Qwen3.8-27B AutoRound W4A16 | VRAM | 163,840 | compiled MTP3, BF16 KV |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | same Qwen3.8-27B weights + DFlash2 drafter | VRAM | 163,840 | BF16 KV, prefix cache |
| `nemotron-3.5-bolt-vllm` | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 | VRAM | 262,144 | runtime globaldev229 |
| `ripple-65b-vllm` | vLLM TP2 | Ripple-65B-Preview GPTQ W4A16 | VRAM | 65,536 | P2P, out-of-tree `vllm/ripple-plugin` |
| `qwen3.8-flash-next-iq3_xxs` | Strata 0.2.20 (upstream) | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | SSD streaming | 262,144 | sealed package in `hardware/generated/strata-0220-2026-11-23/`, layer split 26, upstream RDNA3 defaults, `STRATA_HC_Q8=0`; replaced the RDNA3 fork on November 23 (owner); the fork was deleted the same day at the owner's request |
| `inkling-2-mini-sq-20-strata` | Strata 0.2.20 `strata-inkling` | Inkling 2 Mini SQ-20 `.strata` + Vision | VRAM, second card only | 131,072 | sealed package, `--kv fp8`, DSpark, thinking always off (hidden reasoning still uses `max_tokens`) |
| `inkling-2-mini-sq-20-strata-2gpu` | Strata 0.2.20 `strata-inkling` | Inkling 2 Mini SQ-20 `.strata` + Vision | VRAM, both cards: second card leads, about 9.6 GB of experts on the display card | 262,144 | sealed package, expert parallel `--gpus 1,0 --ep-split 0.6`, `--kv fp16`, DSpark, thinking always off; use the one-card entry while gaming |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S | SSD streaming | 32,768 | expert profile, RAM store off (`--ssd-cache 0`), reserve 2048 MiB, 14 threads |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | same DeepSeek UD-IQ1_S backing | SSD streaming | 32,768 | expert profile, `64gb-q1-v1` tier, reserve 2048 MiB, 20 threads |
| `glm-5.3-flash-maya` | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS | SSD streaming | 32,768 | `MAYA_GLM_RAM_GB=40`, expert profile, reserves 2048/2048 MiB |

- The registries are `dsh/models.json` and `dsh/models-hip.ini` (llama), `dsh/llama-runtime.json` (active and paused llama models), `dsh/vllm-profiles.json`, `dsh/sglang-profiles.json`, `dsh/strata-profiles.json`, `dsh/maya-profiles.json`, and the sealed `dsh/qualified-native-profiles.json` / `dsh/qualified-strata-qwen-profiles.json` (currently empty). `dsh/model_catalog.py` combines them; authenticated `/v1/models` is the live list.
- Context is allocation capacity. Short checks prove neither full-window quality nor sustained throughput.
- Disabled rows kept for reference (weights removed): `nemotron-3.5-super-iq3`, `deepseek-v4.1-flash-1017-strata-xs`, `deepseek-v4.1-flash-1017-maya`. Removed November 11 (owner request): `ornith-1.5-122b`, `sage-a1.5`, `flint-40b-a2.5b` — routes, profiles and the Sage launcher gone, weights deleted (114 GB freed on sharedSATA1). Removed November 8: Flash-Next UD-IQ1_M and both DeepSeek Coder IQ2_XXS routes. Final failed candidates (no retry without new evidence): PLE host-file-gather, Super INT4 EP2, the Maya DeepSeek 36 GB store, RDNA3 full-stack fork `2314df4`.

## Hardware and kernel

- Intel i5-13600KF, ASUS TX GAMING B760M WIFI, 61.5 GiB visible RAM (64 GB DDR5).
- Two RX 7900 XTX 24 GB behind a PEX880xx switch: Gen4 x16 uplink, x8 per card. PowerColor `0b:00.0` is ROCm 0 and Sapphire `13:00.0` is ROCm 1 (`ROCR_VISIBLE_DEVICES=0,1`, `HIP_VISIBLE_DEVICES=0,1`, set in `hardware/rocm-env.sh`).
- Kernel `7.0.14-42-vmpt1` is the owner-selected default; stock is installed as fallback. 
- Past Sapphire bus-loss faults happened only with Sapphire behind the switch. The [working setup](../hardware/AMD-WORKING-SETUP-2026-11-07.md) has the crash-recovery runbook.

## Guards (do not weaken)

- 100°C stop for CPU, GPU edge/junction/memory and SSD; SMART health checks.
- Loading is admitted on the same 1 GiB of available RAM for every model since November 18 (owner): no per-model figure. Physical-RAM floors and VRAM checks are unchanged. After a backend switch, Maya and Strata DeepSeek wait up to 15 s for the cards to report 16 GiB free each before refusing (Flash-Next → Maya DeepSeek → Flash-Next verified November 18). DeepSeek Q1 on Maya leaves about 1 GiB free on the display card: with a game or another GPU app holding VRAM there it is refused with "whole-card startup headroom", which is the guard working.
- Host floor 1 GiB available RAM; 128 MiB free per card while live; dedicated-VRAM spill check; supervisor heartbeat (6 s); phase budgets of 1800 s for loading, prefill and generation; owned cleanup within 15 s.
- Native VRAM reserve: at least 2048 MiB requested per card (`MIN_RESERVE_MIB` in `dsh/qualified_native_runtime.py`). At startup the Maya router (all routes) and the Strata router (DeepSeek routes only) require free VRAM of the reserve minus 1 GiB, between 1 and 6 GiB.
- Resource policy `loading-swap-v5`: worker hard limits come from installed RAM; device-speed swap is allowed with storage and temperature protection. Never disable global swap or touch unrelated applications.
- The hub unloads an owned idle backend after 600 s. It never stops active, queued, starting or unknown work.

## Timers

| Timer | When | Notes |
|---|---|---|
| `llm-daily-update.timer` | **Removed November 9** (owner; the timer is no longer installed) | Retired after repeated skips and failures. The unit source stays in `hardware/daily-update/systemd/`. `llm-daily-update-recover.service` is still enabled; at login it only rolls back an interrupted install. Updates are checked and installed by hand ([update watch](../hardware/DAILY-UPDATES.md)). |

## Runtime and source identities

<!-- daily-update:begin -->
**Engine versions in production** (last update November 22, by hand: llama.cpp, Maya and the Flash-Next engine; the scripted updater is retired; details in `hardware/DAILY-UPDATES.md`):

| Engine | Production |
|---|---|
| llama.cpp | `1fb8a269603b` (265 commits past 1.0.0); the Inkling route alone runs `GodGMN/llama.cpp` `inkling-rdna3` at `cb0e469607c1` |
| vLLM | `0.33.0rc1.dev229+g3966924d5.rocm72` |
| SGLang | `f84475ccf593` |
| Strata (Flash-Next) | upstream `v0.2.20` (`a34979fc94f3`, engine 0.1.66), built from source in `hardware/generated/strata-0220-2026-11-23/` (owner, November 23: replaced the RDNA3 fork, which was then deleted at the owner's request; `strata/` keeps only `.venv`, the Python environment the Strata launchers use) |
| Maya | `f9a053dcb5a9` (1.1.73) |
| Strata DeepSeek | `13eedf552417` (frozen: upstream removed this engine) |
| Graphics | See `graphics/runtime-versions.json` for the selected ComfyUI/Torch/HIP identities |

November 22: llama.cpp `1fb8a269603b`, Maya 1.1.73 and the Flash-Next engine (fork branch `rows2-20261116`) promoted; two operator-caused holds were released by the owner; ComfyUI stays on 0.45.5 (0.46.0 was researched and not installed: it adds nothing for these cards). A trial of Hy4-Flash SQ-64 runs on a side install of Strata 0.2.18 (`hardware/generated/hy4-trial-2026-11-22/`, pack on the streaming NVMe drive, port 30031, stopped): it is not a hub route and holds almost all RAM while loaded ([report](../hardware/HY4-FLASH-SQ64-2026-11-22.md)). A second trial, Hy4-Flash Maya-M on a side copy of Maya 1.1.73 across both cards (`hardware/generated/hy4-maya-trial-2026-11-22/`, files on the streaming NVMe drive, port 30032, stopped), leaves 56–57 GB of RAM available but is no faster and reads prompts about four times slower; it is not a hub route either ([report](../hardware/HY4-FLASH-MAYA-M-2026-11-22.md)).

November 21: llama.cpp `9581154a2250` → `19bc41dbb41e` promoted for Inkling 2 Mini support; strict gate passed on `empero` and on the new `inkling-2-mini-q8` route. Other engines were not checked that day.

Last update (November 12, manual): llama.cpp, Strata, Strata DeepSeek and Maya promoted after strict short tool checks; all six engines were current that evening. November 13: llama.cpp 1.0.0 (`fe14cad51bbf`) failed the strict tool gate twice on `empero` (correct marker, wrapped in a sentence); a third stage at `9daa0aa22b8a` passed the strict gate and was promoted. That afternoon llama.cpp moved on to `ded522f83045` (strict gate passed first time), so all six engines are current. November 15: llama.cpp `9fba51d2c9a1`, Strata `baf16363b440` and Maya 1.1.65 promoted, each on the first stage; the 216-item suite on the new Strata build scored 164, unchanged. Strata upstream has removed its DeepSeek engine, so Strata DeepSeek stays in service on `13eedf552417` by the owner's decision and has no further updates; the upstream check reports it as behind, which is expected. Before any engine update, research the newer version's bug fixes and performance changes and record them in the ledger (owner, November 15). The `empero` tool check can fail on answer wording alone because the route samples at temperature 0.6 ([ledger](../hardware/DAILY-UPDATES.md)). On November 11 llama.cpp, Strata and Strata DeepSeek had been promoted. The Maya candidate `6fba6be98125` faulted the second GPU that day and was rolled back; a rerun on November 12 passed on both Maya routes and it was promoted, then Maya was updated to `c5842c5e5be0` (1.1.61) the same day after the same checks. If a Maya route page-faults again, record it and roll back to `00655481ce2b`.
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
- Production ComfyUI (`graphics/start-comfyui`) runs projected-8B H3 as two-card TP over RCCL P2P; FLUX, Qwen-Image, native-32B H3 and MiniMax H3 Image (added November 15 with ComfyUI 0.45.4; ComfyUI is 0.45.5 since November 16; [report](../graphics/MINIMAX-H3-IMAGE-2026-11-15.md)) use staged placement; `COMFY_MODE=staged` rolls back ([report](../graphics/H3-TP2-PRODUCTION-2026-11-07.md)). Do not load a second model worker while it holds the GPUs. Like the hub's LLM engines, it stops itself after 600 s idle (empty queue and no browser tab connected; `COMFY_IDLE_TIMEOUT_S` in the environment changes it, 0 disables); start it again with `graphics/start-comfyui` or the ComfyUI desktop icon.

## Open items

1. **Engine updates (checked and installed by hand).** November 9: llama.cpp, Strata, Maya and Strata DeepSeek updated and verified; all engines were current at that point except llama.cpp, whose upstream had moved on to `3d94ffe`. Check upstream each session; GPU work needs the owner's OK while ComfyUI is running. The old engine stage folders `hardware/generated/daily-update/2026-11-07T181342-*` (llama) and `2026-11-07T183647-*` (Maya) are no longer referenced by production; deleting them is the owner's call.
2. **DeepSeek NaN on Strata: gone with the RAM store off (November 12).** With `--ssd-cache 36` the route failed with NaN errors in every long run on November 8–11, and the server's kernel crashed during the last one (a general protection fault in the page-cache lookup on the model file). With `--ssd-cache 0` the 216-item suite ran to the end with no NaN and no kernel fault and scored 169, the same as Maya; a rerun on engine `13eedf552417` on November 13 was also clean and scored 166 ([report](../hardware/STRATA-DEEPSEEK-NO-RAM-STORE-2026-11-12.md)). Keep the store off; do not turn it back on without a long-run test. The cause is inferred from two clean runs, so treat a new NaN on this route as a reason to stop and record. Speed with the store off is the same or better (400-token answers 10.7–12.2 tok/s; cold first answer 82 s against 71).
3. **No sustained benchmark.** All route numbers are short checks. A longer owned soak at the November 8 settings is the main open check.
4. **Flash-Next runs upstream Strata 0.2.20 since November 23 (owner: "Replace the fork"); the RDNA3 fork was deleted (owner, November 23).** The main route `qwen3.8-flash-next-iq3_xxs` is a sealed package (`qualified_qwen_package`) built in `hardware/generated/strata-0220-2026-11-23/`, config `dsh/strata-iq3-upstream-profile.json`. Update it like the other upstream Strata entries: build each new release in a fresh stage folder, measure, reseal, strict tool check; never in `strata/`. There is no fork rollback: the fork tree, its configs and the 0.2.19 build were deleted at the owner's request. `strata/` now holds only `.venv`, which `run-strata-qwen-backend`, `run-strata-deepseek-backend`, `run-qualified-native-backend` and the retired updater use, so keep it. The retired updater's Strata engine read the fork build and no longer applies to Flash-Next; run the strict tool gate against the sealed route instead. History below. Until November 23 Flash-Next ran only the Strata RDNA3 fork (owner, November 17). The engine tree `strata/` holds `nicejunjie/Strata-rdna3` at `8b01b0c8512d` (engine 0.1.49.1), not upstream Strata. Do not install upstream Strata over it: the update check reports Strata as behind upstream, which is expected. Check the fork's repository for updates by hand and qualify them like any engine update. The route uses memory tier `64gb-qwen-v1` with no fixed expert budget (`expert_ram_mode: all-off-card`, owner choice late on November 17, the NVIDIA server's policy): the engine keeps 21.4 GiB of experts in RAM, pageable, and the file cache serves the rest of the prompt path, so RAM fills with reclaimable file cache and up to about 1 GiB of swap is used while it is loaded. About 37 GiB is in use and 28.4 GiB must be available before loading. A fixed cap is slower on prompts (24 GiB) or much slower (12 GiB). Before running the updater's strict tool gate by hand, wait for the hub to unload: started beside a loaded model, its guard latches `GPU-LOCK`. Its server thinks by default, so the profile sets `reasoning_effort: none`. The previous build (Strata 0.2.15, `c77572806996`) was deleted on November 23 at the owner's request. Its per-card reserve is 1536 MiB, below the 2 GiB floor for sealed native profiles, which does not apply because the route has no sealed record ([report](../hardware/STRATA-RDNA3-FORK-TEST-2026-11-17.md)). On November 22 upstream Strata 0.2.19 was built in `hardware/generated/strata-0219-2026-11-22/` and measured against the fork: faster and steadier prompt reading, about half the RAM, slower code decode; the route was not switched ([report](../hardware/STRATA-0219-RESEARCH-2026-11-22.md)). On November 22–23 the owner asked for separate entries: `qwen3.8-flash-next-iq3_xxs-upstream` (upstream 0.2.19) and `inkling-2-mini-sq-20-strata` are enabled beside the fork route, which stays the default Flash-Next. On November 23 both moved to 0.2.20, and the owner asked for the 0.2.20 two-card Inkling setup as its own entry: `inkling-2-mini-sq-20-strata-2gpu` (262K context, about 9.6 GB on the display card).
5. **Stale metadata inside sealed profiles** (for example "8GiB requested reserve" in their `settings` text). Editing them would change the seals; leave them.
6. **Untested spill stop.** Unit tests pass (`python3 -m unittest discover -s hardware -p "test_*.py"`: 669 tests, 2 skipped, November 22). The pre-November 3 guard replay was removed on November 9; the owner policy (1 GiB RAM, 128 MiB VRAM per card) is tested in `hardware/test_owner_resource_policy.py`. No test covers the Strata worker VRAM-spill stop in `dsh/inference_swap.py` (`WorkerSwapGuard`); add one before changing it.
## Keep this handoff small

After authorized work, replace the state above, add one changelog line, sanitize and publish both repos, and keep the private operational copy byte-identical on the shared drive (`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md`). The retired `hardware/daily-update/publish.py` rewrote the block between the `daily-update` markers and depends on the `## Runtime and source identities` heading, the `Public native exports` paragraph after it, and this file's name; keep all three in case it is reused.

History only: [November 5 handoff](../hardware/history/documentation-2026-11-05/LINUX-LLM-RUNTIME-HANDOFF.reference.md), Git history for the November 8 pre-cleanup version, [benchmark history](../hardware/BENCHMARK-HISTORY.md). Do not restore superseded settings or resume old plans without a new owner request.
