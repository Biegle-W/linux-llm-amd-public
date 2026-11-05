# Current AMD runtime handoff — November 5, 2026

Read the root [maintenance policy](../../README.md) first. This is the current operational summary for Linux and Windows/phone API clients. Historical narratives are linked at the end; they are not startup reading.

## State and next action

The owner-approved archive of the reviewed global STOP/GPU hold is complete. **Nine qualified routes are enabled.** Six failed/inconclusive candidates remain held; deleted XS and Super IQ3 remain retired. Activation is already applied: do not repeat it. No GPU test, implementation campaign, failed-profile retry or schedule change is pending.

All 27 bounded cases and 10 reviewed graphics outputs are complete. Latest verification found no owned GPU job or KFD client and free campaign locks. Recheck actual jobs/locks before any new work; a client can start a backend after this snapshot. Preserve unrelated user files/services and paused schedules. Proceed only with the next owner-requested task.

## Hardware and protected policy

- Intel i5-13600KF; ASUS TX GAMING B760M WIFI; 61.55 GiB visible RAM; two RX 7900 XTX 24 GB behind PEX880xx. Gen4 x16 common uplink, x8 branch segments. Runtime logical order is PowerColor then Sapphire (`ROCR_VISIBLE_DEVICES=1,0`, `HIP_VISIBLE_DEVICES=0,1`).
- Current boot `7.0.14-42-vmpt1`, identity GPU IOMMU domains and six-bridge ACS `0x11` passed bounded peer/IPC/RCCL correctness checks. **Stock persistent boot default is unchanged.** Earlier crashes remain evidence; this is no sustained-stability or causal hardware verdict.
- Retain **100°C** CPU/GPU edge/junction/memory/SSD stop policy, SMART health, 1 GiB available host RAM and 128 MiB free per-card live floors, dedicated-VRAM spill, heartbeat/decode, phase timing and owned cleanup guards. Native normal readiness retains its 6 GiB actual startup floor and the qualified Coder profile requests 8 GiB reserve.
- Current resource policy has no `MemoryHigh`, computes worker hard limits from installed RAM, retains existing swap capacity and permits device-speed swap with storage/temperature protection. Old v4 swap-rate/zero-system-swap policies are historical. Never disable global swap or interfere with unrelated applications.
- GPU tests require the established owned `hardware/generated/GPU-LOCK` and fresh admission. Serialize GPU work and heavy I/O; unknown ownership blocks startup. Never delete another owner's lock or fault evidence. No new test is needed for documentation.

## Exact enabled catalog

| Exact API model ID | Backend | Context |
|---|---|---:|
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | strata | 32,768 |
| `empero-qwen3.8-35b-a3b` | llama | 262,144 |
| `flint-40b-a2.5b` | llama | 32,768 |
| `nemotron-3.5-bolt-vllm` | vllm | 262,144 |
| `ornith-1.5-122b` | llama | 32,768 |
| `qwen3.8-27b-sglang-dflash2` | sglang | 163,840 |
| `qwen3.8-27b-vllm` | vllm | 163,840 |
| `qwen3.8-flash-next-iq3_xxs` | strata | 262,144 |
| `sage-a1.5` | vllm | 65,536 |

Configured context is allocation capacity. The latest short checks add no full-window-quality or sustained-throughput proof. `dsh/model_catalog.py` combines the enabled backend registries; authenticated `/v1/models` is the live client source. DSH remains one AMD-server catalog; preserve its saved default/provider and private conversations/settings.

## Held and retired routes

| Held candidate | Final reason |
|---|---|
| Maya Coder, normal 8 GiB-reserve profile | Three-second decode-progress guard |
| Maya Q1 | Decode-progress guard |
| Strata Q1 | Decode-progress guard |
| GLM | Enclosing stage budget exhausted before complete tool round trip |
| PLE | 900-second loading deadline |
| Super INT4 EP2 | 1 GiB available host-RAM guard |

Small-reserve Maya Coder passing earlier does not qualify the failed normal 8 GiB-reserve profile. Keep all six held; do not retry or auto-resume them. Old Maya/Strata XS backing and Super IQ3 were deleted/retired and must not be restored as fallbacks. Their historical metadata/pins remain intact.

## Runtime and source identities

| Runtime | Retained selection / source of truth |
|---|---|
| llama.cpp global / Flint | `0ef27309b78d054832e44a95a6fb9314d4b7363c`; [llama runtime registry](../dsh/llama-runtime.json) |
| Empero independent override | `eb4e244be77a906a183cd4a00fd51d9ad3200955` |
| Ornith independent override | `2280f0fd163b03d4331d49e08460f66502e35854` |
| vLLM Qwen/Sage | `0.33.0rc1.dev229+g3966924d5.rocm72`; retained launchers/profiles |
| vLLM Bolt manual pin | `0.32.1rc1.dev435+gc50aca144.rocm72`; no automatic unpin |
| SGLang ROCm | Source `f84475ccf593087df3d1da13c9e675eadee12352` with retained local ROCm/attention fixes; preserve source patches and [profile](../dsh/sglang-profiles.json) |
| Strata Qwen MTP | `0.2.10`, source `ffa80d73133ea5c548aefe57889a16e8085a938f`; [profile](../dsh/strata-iq3-profile.json) |
| Strata Coder separate native source | Same source revision `ffa80d73133ea5c548aefe57889a16e8085a938f`; registry below seals its separate binary/config/backing |
| Graphics | ComfyUI `0.42.0` / `8f04fd6ecf4a548937971e840af2a985529fab76`; Torch `2.15.0.dev20260827+rocm7.2`, HIP `7.2.53211`, Comfy Kitchen `0.2.39`; [runtime record](../graphics/runtime-versions.json) |

Native Strata Coder source location: `/opt/local-llm/qualified-sources/strata-dsv41-ffa80d7`. Binary SHA-256 `581959940cff920e638a2b27241c5f8276ce92d849fc0905bf7ca58c17171acf`; 32K context, two layer groups, one request. [Native registry](../dsh/qualified-native-profiles.json) and [sealed profile](../dsh/deepseek-v4.1-flash-1017-strata-coder-iq2-xxs-profile.json) retain metadata/backing/source/binary/config checks independently from legacy XS pins. Preserve all exact weight/tokenizer/manifests and manual runtime pins.

Public native exports use `/opt/local-llm/qualified-sources` and **`requires-local-validation`** status. Admission rejects them before launch until independently qualified and sealed locally. Machine-specific inode/device/mtime seals are omitted; content hashes remain source-host evidence. Never manufacture a seal or mark passed merely to bypass admission.

Retain ROCm SDK 7.2.3 and isolated runtime libraries. `hardware/rocm-env.sh` selects qualified RCCL peer transport; llama's presence-based peer flag is enabled only for the explicitly qualified IDs in its registry. Native layer-group handoffs and default graphics component placement have no direct peer-copy claim. Environment flags alone do not prove transport.

## Client access and managed lifecycle

LAN `http://<LINUX_LAN_IP>:10000/v1`; Tailscale `http://<LINUX_TAILSCALE_IP>:10000/v1`; MagicDNS `http://<LINUX_TAILSCALE_DNS>:10000/v1`.

Configure bearer authentication privately using the established gateway setup. Obtain permitted access details from the owner; never place credentials, credential locations or private client configuration in a public handoff. No new public exposure or tailnet-policy grant is authorized.

OpenAI-compatible Chat Completions and native Responses `POST /v1/responses` are supported; stream with a 600-second client timeout for cold loading. Start with 2,048 output tokens within the configured context budget. Existing OpenCat mixed tools and free self-hosted SearXNG/RSS search remain; [network compatibility details](README.md).

The authenticated gateway on TCP 10000 forwards to `local-llm-hub.service` on loopback `127.0.0.1:30100`. Matching inference starts/switches a backend through managed launchers; catalog/health GETs do not load models or reset inference idle time. Retained 600-second inference-aware idle release unloads only owned managed backends, never active/queued/startup/unknown work.

Use existing `bin/` / installed `llm-*` entry points and Desktop launchers. DSH/Turnstone are optional frontends. Switching may interrupt owned managed replies; it must preserve DSH, gateway, unrelated Python/training/graphics applications and unknown port owners. Never blanket-kill Python/GPU processes. Desktop UI shortcuts open browser interfaces; menu entries open native apps. Preserve the shared Comfy server lock and native/browser launcher separation. Standalone native apps do not inherit the managed profile/guards; do not load concurrent workers.

Daily engine updates and other paused schedules remain paused until explicitly resumed. Documentation cleanup changes no service, runtime selection, boot option, schedule or saved DSH default.

## Completed verification and evidence

- 27 cases complete, 21 functional/guard passes and 6 failed/inconclusive; all 27 owned cleanups verified. All 7 router, 7 graphics and 3 extended copy-coverage cases passed. Ten reviewed generated media outputs are published.
- 160 activation CPU checks and 35 additional public-export CPU checks passed. Live read-only checks verified exact 9-route catalog, healthy authenticated health, 401 for missing/wrong keys, exact 17 activated files, retained source pins and native seals. No inference request was sent for publication.
- Empero/Flint/Ornith show successful inference peer-copy APIs. Qwen/vLLM, Bolt, Sage and Qwen/SGLang show both-direction RCCL P2P/IPC with successful TP2 requests. Normal Flux/Qwen/H3 component placement has no observed cross-device copy. Separate H3 fcys TP2 remains isolated; cached conditioning excludes encoder cost and does not qualify a normal TP2 promotion or speed claim.
- No passed GPU check or failed profile was rerun for publication/cleanup. Final kernel/storage/temperature checks were clean. Results are short functional/transport evidence, not a long benchmark or hardware-cause conclusion.

[Result index](../hardware/CURRENT-AMD-BENCHMARKS.md) · [full methods/failures](../hardware/ALL-MODEL-P2P-2026-11-05.md) · [numeric cases](../hardware/results/ALL-MODEL-P2P-2026-11-05.json) · [research](../hardware/ALL-MODEL-P2P-RESEARCH-2026-11-05.md) · [image/video gallery](../graphics/results/p2p-2026-11-05/README.md)

## Keep this handoff small

After relevant authorized work, replace current state here, update applicable dated evidence/current index, sanitize and normally publish both AMD repositories, and verify the operational copy exactly matches `<SHARED_DRIVE>/LINUX-LLM-RUNTIME-HANDOFF.md` (Windows `D:\LINUX-LLM-RUNTIME-HANDOFF.md`). Keep private agent workflows/checkpoints out of this file and Shared/public exports. Check actual Git status, job/lock ownership and remote refs; preserve unrelated untracked work.

For a historical question only: [earlier handoff guide](../hardware/history/documentation-2026-11-05/LINUX-LLM-RUNTIME-HANDOFF.reference.md), [benchmark history](../hardware/BENCHMARK-HISTORY.md), [root maintenance policy](../../README.md). Do not restore superseded historical settings or resume old plans without a new owner request.
