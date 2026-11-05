# Current AMD runtime handoff — November 5, 2026

Read the root [maintenance policy](../README.md) first. This is the current operational summary for Linux and Windows/phone API clients. Historical narratives are linked at the end; they are not startup reading.

## State and next action

**13 qualified normal routes are enabled.** The owner requested latest-engine qualification and realistic-budget retries. Maya Coder, Maya Q1, GLM and Strata Q1 passed their short tool round trips and guarded cleanup. Maya c167004 subsequently passed all three enabled profiles through the selective updater and is selected. Llama9c9074 passed Flint/Ornith through the updated updater, then passed the separate Empero strict check. It is selected for all three; the earlier3259 Empero rejection remains dated evidence.

Strata 0.2.11/engine+Control 0.1.57 with the already downloaded Unsloth V3.1 IQ3_XXS passed the strict tool test and completed6 quality fixtures (5/6) plus3 short timing prompts (median native 52.895 tokens/s). Owned cleanup passed with zero recorded swap/spill; production GSQ/source selections remain unchanged. [Details](../hardware/STRATA-0211-UNSLOTH-2026-11-05.md).

ComfyUI0.44/fb2b26f passed all six new-source normal workflows and is selected for the terminal launcher and existing Desktop installation. Torch/ROCm, prior source and input/user state were preserved. The correct RDNA3 branch perf/rdna3_full_stack at2314df4 is isolated; defaultmain2e3154 was never installed. Fresh owner-requested latest-guard attempts ended before inference: Flint AWQ requires unavailable FlashInfer; PLE stopped on the six-second heartbeat guard; Super stopped below the 1 GiB host reserve. PLE missed its 15-second KFD drain deadline, then drained later; that failed result remains recorded. None was promoted. The unused Strata DFlash2 source/packs were removed after pinned-hash and dependency verification; the separate SGLang drafter and all 13 selected routes remain unchanged. [Latest candidate outcomes](../hardware/CANDIDATE-RETESTS-2026-11-05.md). Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The RDNA3 fork at2314df4 built and passed native/CLI audits, but its Qwen startup warm-up failed on missing `CommonAttentionMetadata._seq_lens_cpu` before any request. The exact case is final; the fork remains isolated and unpromoted. The existing 03:00 daily updater timer is restored, enabled/active with Persistent=false and next run November6 03:00 EST; no catch-up service ran. Other timer states were unchanged. Llama9c9074 qualification is complete for all three enabled llama routes; the old Empero manual source was released only after its new-source strict pass. Check actual jobs and GPU-LOCK before acting; this summary does not release any owner or queue another GPU job. Other paused schedules, unrelated services/files, retired XS/Super IQ3 and the stock boot default remain protected.

[Current measurements, downloads and pending work](../hardware/REALISTIC-LARGE-MODELS-2026-11-05.md). Prior activation and its27cases are complete; do not repeat passed checks for publication. New-source qualifications are separately authorized.

[Native decode evidence](../hardware/AMD-DECODE-EVIDENCE-2026-11-05.md): all13 current routes now have short native per-request statistics; four routes completed owner-requested native timing probes. A sustained matched13-route benchmark remains missing. [Latest methods and removal disposition](../hardware/AMD-NATIVE-DECODE-TESTS-2026-11-05.md): failed FlintAWQ/FP8PLE/SuperINT4 downloads removed by explicit owner request; selected13routes unchanged.

## Hardware and protected policy

- Intel i5-13600KF; ASUS TX GAMING B760M WIFI; 61.55 GiB visible RAM; two RX 7900 XTX 24 GB behind PEX880xx. Gen4 x16 common uplink, x8 branch segments. Runtime logical order is PowerColor then Sapphire (`ROCR_VISIBLE_DEVICES=1,0`, `HIP_VISIBLE_DEVICES=0,1`).
- Current boot `7.0.14-42-vmpt1`, identity GPU IOMMU domains and six-bridge ACS `0x11` passed bounded peer/IPC/RCCL correctness checks. **Stock persistent boot default is unchanged.** Earlier crashes remain evidence; this is no sustained-stability or causal hardware verdict.
- Retain **100°C** CPU/GPU edge/junction/memory/SSD stop policy, SMART health, 1 GiB available host RAM and 128 MiB free per-card live floors, dedicated-VRAM spill, supervisor heartbeat, phase timing and owned cleanup guards. Native normal readiness retains its 6 GiB actual startup floor and the qualified Coder profile requests 8 GiB reserve.
- Current resource policy has no `MemoryHigh`, computes worker hard limits from installed RAM, retains existing swap capacity and permits device-speed swap with storage/temperature protection. Old v4 swap-rate/zero-system-swap policies are historical. Never disable global swap or interfere with unrelated applications.
- GPU tests require the established owned `hardware/generated/GPU-LOCK` and fresh admission. Serialize GPU work and heavy I/O; unknown ownership blocks startup. Never delete another owner's lock or fault evidence. No new test is needed for documentation.

## Exact enabled catalog

| Exact API model ID | Backend | Context |
|---|---|---:|
| `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | maya | 32,768 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | maya | 32,768 |
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | strata | 32,768 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | strata | 32,768 |
| `empero-qwen3.8-35b-a3b` | llama | 262,144 |
| `flint-40b-a2.5b` | llama | 32,768 |
| `glm-5.3-flash-maya` | maya | 32,768 |
| `nemotron-3.5-bolt-vllm` | vllm | 262,144 |
| `ornith-1.5-122b` | llama | 32,768 |
| `qwen3.8-27b-sglang-dflash2` | sglang | 163,840 |
| `qwen3.8-27b-vllm` | vllm | 163,840 |
| `qwen3.8-flash-next-iq3_xxs` | strata | 262,144 |
| `sage-a1.5` | vllm | 65,536 |

Configured context is allocation capacity. The latest short checks add no full-window-quality or sustained-throughput proof. `dsh/model_catalog.py` combines the enabled backend registries; authenticated `/v1/models` is the live client source. DSH remains one AMD-server catalog; preserve its saved default/provider and private conversations/settings.

## Held and retired routes

| Candidate | Current disposition |
|---|---|
| PLE host-file-gather | Final dev229 loading stop on the unchanged six-second heartbeat guard; no inference/promotion, clean owned cleanup. Reviewed hold archived intact; no exact retry. |
| Super INT4 EP2 | Final dev229 loading stop on the unchanged six-second heartbeat guard; no inference/promotion, clean owned cleanup. Reviewed hold archived intact; no exact retry. |
| RDNA3 full-stack fork2314 | Isolated wheel/native/CLI audits passed; Qwen startup warm-up failed on missing `_seq_lens_cpu` before requests. Exact case final; no promotion. Reviewed own hold archived intact after fresh health/ownership checks. |

Four former timing-limited native candidates now passed and are enabled under their exact new source/profile seals. Deleted XS and Super IQ3 stay retired and are not fallbacks. No weights were deleted in the current update task.

## Runtime and source identities

<!-- daily-update:begin -->
**Engine versions after the 2026-11-05 daily update** (`llm-daily-update.timer`, 03:00; details in `hardware/DAILY-UPDATES.md`):

| Engine | Production |
|---|---|
| llama.cpp | `9c9074e14e02` |
| vLLM | `0.33.0rc1.dev229+g3966924d5.rocm72` |
| SGLang | `f84475ccf593` |
| Strata | `ffa80d73133e` |
| Maya | `c1670044bbc0` |
| Strata DeepSeek | `ffa80d73133e` |
| Graphics | See `graphics/runtime-versions.json` for the selected ComfyUI/Torch/HIP identities |

Last run: Maya promoted c167 after three strict tool checks; llama.cpp promoted9c9074 for all three enabled profiles.
<!-- daily-update:end -->

Enabled native source/binary/profile/backing identities are sealed per profile in `dsh/qualified-native-profiles.json`. Selected Maya uses `c1670044bbc09310f35f9d00f7596c50ae8a38f1`; its GLM fused prefill remains disabled. Native profiles retain32K context, requested8GiB reserves and the normal6GiB startup guard. Strata Q1 retains its36GiB cache and60/52GiB physical/available RAM admission. Retired legacy pins remain separate.

Public native exports use `/opt/local-llm/qualified-sources` and **`requires-local-validation`** status. Admission rejects them before launch until independently qualified and sealed locally. Machine-specific inode/device/mtime seals are omitted; content hashes remain source-host evidence. Never manufacture a seal or mark passed merely to bypass admission.

Retain ROCm SDK 7.2.3 and isolated runtime libraries. `hardware/rocm-env.sh` selects qualified RCCL peer transport; llama's presence-based peer flag is enabled only for the explicitly qualified IDs in its registry. Native layer-group handoffs and default graphics component placement have no direct peer-copy claim. Environment flags alone do not prove transport.

## Client access and managed lifecycle

LAN `http://<server-lan-ip>:10000/v1`; Tailscale `http://<server-vpn-ip>:10000/v1`; MagicDNS `http://<server-vpn-name>:10000/v1`.

Use the existing private bearer key and access policy. Retrieve credentials through the established local setup; keep credentials and their machine-specific locations out of handoffs and exports. No new public exposure or tailnet-policy grant is authorized.

OpenAI-compatible Chat Completions and native Responses `POST /v1/responses` are supported; stream with a 600-second client timeout for cold loading. Start with 2,048 output tokens within the configured context budget. Existing OpenCat mixed tools and free self-hosted SearXNG/RSS search remain; [network compatibility details](README.md).

The authenticated gateway on TCP 10000 forwards to `local-llm-hub.service` on loopback `127.0.0.1:30100`. Matching inference starts/switches a backend through managed launchers; catalog/health GETs do not load models or reset inference idle time. Retained 600-second inference-aware idle release unloads only owned managed backends, never active/queued/startup/unknown work.

Use existing `bin/` / installed `llm-*` entry points and Desktop launchers. DSH/Turnstone are optional frontends. Switching may interrupt owned managed replies; it must preserve DSH, gateway, unrelated Python/training/graphics applications and unknown port owners. Never blanket-kill Python/GPU processes. Desktop UI shortcuts open browser interfaces; menu entries open native apps. Preserve the shared Comfy server lock and native/browser launcher separation. Standalone native apps do not inherit the managed profile/guards; do not load concurrent workers.

The existing03:00 daily engine updater timer is enabled and active with `Persistent=false`; next scheduled run is Fri 2026-11-06 03:00:00 EST. Its service remains inactive: restoration started no catch-up GPU work. Maya c167 and llama9c9074 qualifications are complete; all scoped qualification jobs have ended; inspect actual jobs and locks before future GPU work. Every other timer state was verified unchanged, and other paused schedules stay paused. Saved DSH defaults and unrelated services remain unchanged.

## Completed verification and evidence

- Completed normal-route qualification: four native realistic-budget passes; latest llama9c9074 Flint/Ornith/Empero strict passes (the older3259 Empero rejection remains dated evidence), with complete owned unload and no new kernel fault or dedicated-VRAM spill. Loading swap is permitted and was observed in the llama stage.111 targeted CPU checks pass. The new supervisor's corrected CPU smoke and new-source GPU path completed.
- The three-second decode-progress stop is removed. Native loading/prefill/generation each have1800-second phase budgets; PLE loading gets3600seconds. Two model steps,256output tokens per step, six-second supervisor heartbeat and 15-second owned cleanup retain finite bounds. All100°C/storage/RAM/VRAM/spill/swap protections remain.
- Prior campaign:27cases,21functional/guard passes and6failed/inconclusive; all27owned cleanups verified. Seven router, seven graphics and three extended copy-coverage cases passed.160activation and35public-exportCPU checks are historical evidence, not new test counts.
- vLLM/SGLang routes have measured TP2/RCCL P2P/IPC evidence. Current llama presets use layer splitting; native engines use layer groups. Normal graphics component placement is distinct from the isolated H3 TP2 result, whose cached conditioning excludes encoder cost.

[Current results/downloads](../hardware/REALISTIC-LARGE-MODELS-2026-11-05.md) · [Numeric current results](../hardware/results/REALISTIC-LARGE-MODELS-2026-11-05.json) · [RDNA3/Radiance research](../hardware/RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md) · [Prior methods](../hardware/ALL-MODEL-P2P-2026-11-05.md) · [Media gallery](../graphics/results/p2p-2026-11-05/README.md)

## Keep this handoff small

After relevant authorized work, replace current state here, update applicable dated evidence/current index, sanitize and normally publish both AMD repositories, and verify the operational copy exactly matches `/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md` (Windows `D:\LINUX-LLM-RUNTIME-HANDOFF.md`). Keep credentials and machine-specific secret locations out of handoffs and public exports. Check actual Git status, job/lock ownership and remote refs; preserve unrelated untracked work.

For a historical question only: [previous full handoff](../hardware/history/documentation-2026-11-05/LINUX-LLM-RUNTIME-HANDOFF.full.md), [benchmark history](../hardware/BENCHMARK-HISTORY.md), [root maintenance policy](../README.md). Do not restore superseded historical settings or resume old plans without a new owner request.
