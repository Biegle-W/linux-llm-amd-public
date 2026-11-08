# Current AMD runtime handoff — November 5, 2026

[GLM and DeepSeek RAM/reserve tuning, November 8](../hardware/GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md): GLM RAM 40 GB + 2 GiB reserve: 17.8-22.1 tok/s (was 2.6), 396 tok/s prompt; DeepSeek expert profile + 2 GiB reserve: 7.5-10.1 tok/s (was 4.2-6.3), 120 tok/s prompt; Maya DeepSeek route 9.5-17.1 tok/s (was 5.0-9.3).

[Quant quality comparison, November 8](../hardware/QUANT-QUALITY-COMPARISON-2026-11-08.md): 54-item graded test. Flash-Next IQ3_XXS 53/54 vs UD-IQ1_M 52/54 (IQ1_M ~10% faster) -> IQ3_XXS kept, IQ1_M route removed. DeepSeek UD-IQ1_S 54/54 vs Coder IQ2_XXS 51/54, then 64/64 vs 59/64 on a harder rerun, plus an intermittent Coder NaN lock-up -> UD-IQ1_S kept (4-6 tok/s), both Coder IQ2_XXS routes (Strata, Maya) removed. Daily updater policy: always update unless broken; marginal parity misses and minor slowdowns are warnings.

[Ripple-65B on vLLM INT4, November 7](../hardware/RIPPLE-65B-VLLM-2026-11-07.md): `ripple-65b-vllm` route, TP2 over P2P, 28-29 tok/s decode vs 14-17 on llama.cpp; guarded tool check passed.

[AMD working setup, November 7](../hardware/AMD-WORKING-SETUP-2026-11-07.md): card positions, device order, tests that passed, crash-recovery runbook and model status.

[All-models short tool-call benchmark, November 7](../hardware/AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md): all 14 routes passed in the working layout; GPU fault hold released.

[Sapphire switch/P2P evidence audit](../hardware/SAPPHIRE-SWITCH-P2P-EVIDENCE-AUDIT-2026-11-06.md): completed direct HIP/IPC and RCCL P2P transfers passed before the headless failure. The model faulting operation and transport remain unlogged. An older driver-P2P-disabled Strata qualification also failed; its workload/software state differs and site-specific failure evidence remains private. Recent Sapphire/logical-GPU1 identity correction and all guard failures remain preserved. [Qwen backend comparison](../hardware/QWEN-VLLM-SGLANG-TRIGGER-COMPARISON-2026-11-05.md). Read-only audit; no retry or runtime change.

[Headless model campaign](../hardware/AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.md): Headless campaign stopped on SGLang Qwen DFlash2 startup: Sapphire `0b:00.0` lost PCI/SMU access. Four model tool checks completed first (three clean guard passes; one preserved Qwen vLLM harness-path failure after successful tools/cleanup). Nine routes, including Maya DeepSeek no-store, were not run. A connected physical monitor is not required for this failure. Latest fault hold retained; no retry or further GPU work.

[Monitor/display investigation](../hardware/MAYA-DISPLAY-MONITOR-INVESTIGATION-2026-11-05.md): owner reports earlier successful run was headless. Current monitor is on PowerColor, while Sapphire first lost PCI/SMU access. Display remains a plausible contributor, not a proved trigger; prior display errors followed the initial SMU failure. Read-only analysis only; fault hold retained.

[No-store DeepSeek failure and persistent inference kernel](../hardware/MAYA-DEEPSEEK-NO-STORE-2026-11-05.md): The single no-store DeepSeek baseline also failed loading: Sapphire `0b:00.0` was reported lost from the bus, followed by SMU errors, then heartbeat/owned-cleanup failure; no requests. Patched `7.0.14-42-vmpt1` is now the owner-selected persistent inference default, with stock installed as fallback. New fault hold retained; no automatic retry or further GPU work. The current post-crash boot has no fresh peer/model qualification.

Read the root [maintenance policy](../../README.md) first. This is the current operational summary for Linux and Windows/phone API clients. Historical narratives are linked at the end; they are not startup reading.

[IQ1_M qualification and cache status](../hardware/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md): new Unsloth UD-IQ1_M passed strict tools,5/6 local quality fixtures and57.140native tokens/s median across three short probes. All13 original routes remain;14routes/11 main weight sets are grouped below. GLM RAM24 completed strict tools and 5/6 local fixtures, with a 1.995 native tokens/s median across three short speed probes; it was not selected because follow-up performance regressed, so RAM8 remains selected. Maya DeepSeek36GB-store failed during loading on the six-second heartbeat guard and missed its 15-second owned cleanup deadline; the boot later suffered AMDGPU/CPU lockups. The persistent GPU fault hold remains: no automatic GPU work, retry, reboot or hold release. RAM40 is prepared but unrun and blocked. Current post-crash patched boot has no fresh peer/model qualification.

[DeepSeek cache comparison and cleanup](../hardware/MAYA-DEEPSEEK-CACHE-COMPARISON-2026-11-05.md): the36GBoption creates temporary RAM state, not a persistent disk store. One regenerable Maya Q1 tuning file was cleared as requested; weights/configuration/failure evidence and the GPU hold remain intact. No GPU test or repair claim.

[Full-day workload review](../hardware/AMD-DAY-REVIEW-2026-11-05.md): many model/graphics checks passed on the switch/custom-kernel setup, including Maya DeepSeek UD-IQ1_S at04:14-04:18. The later36GB-store candidate failed loading; the first SMU error preceded the watchdog stop. The16:50 power interruption has no identified journal cause and is separate from the18:45 GPU/kernel failure. Exact initial trigger remains unresolved; GPU hold retained.

[Read-only crash comparison](../hardware/AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md): the corrected placement records identify Sapphire in both stock/custom failures, across different switch branches but the same logical model GPU1 role. The earlier different-card claim is withdrawn. No root cause or repair is proved; keep the GPU hold and distinguish card identity from runtime role before another attempt. No GPU or boot change was made.

## State and next action

**12 qualified normal routes are enabled** (Flash-Next UD-IQ1_M and both DeepSeek Coder IQ2_XXS routes were removed November 8). The owner requested latest-engine qualification and realistic-budget retries. Maya Coder, Maya Q1, GLM and Strata Q1 passed their short tool round trips and guarded cleanup. Maya c167004 subsequently passed all three enabled profiles through the selective updater and is selected. Llama9c9074 passed Flint/Ornith through the updated updater, then passed the separate Empero strict check. It is selected for all three; the earlier3259 Empero rejection remains dated evidence.

Strata 0.2.11/engine+Control 0.1.57 with the already downloaded Unsloth V3.1 IQ3_XXS passed the strict tool test and completed6 quality fixtures (5/6) plus3 short timing prompts (median native 52.895 tokens/s). Owned cleanup passed with zero recorded swap/spill; production GSQ/source selections remain unchanged. [Details](../hardware/STRATA-0211-UNSLOTH-2026-11-05.md).

ComfyUI0.44/fb2b26f passed all six new-source normal workflows and is selected for the terminal launcher and existing Desktop installation. Torch/ROCm, prior source and input/user state were preserved. The correct RDNA3 branch perf/rdna3_full_stack at2314df4 is isolated; defaultmain2e3154 was never installed. Fresh owner-requested latest-guard attempts ended before inference: Flint AWQ requires unavailable FlashInfer; PLE stopped on the six-second heartbeat guard; Super stopped below the 1 GiB host reserve. PLE missed its 15-second KFD drain deadline, then drained later; that failed result remains recorded. None was promoted. The unused Strata DFlash2 source/packs were removed after pinned-hash and dependency verification; the separate SGLang drafter and all 13 selected routes remain unchanged. [Latest candidate outcomes](../hardware/CANDIDATE-RETESTS-2026-11-05.md). Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The RDNA3 fork at2314df4 built and passed native/CLI audits, but its Qwen startup warm-up failed on missing `CommonAttentionMetadata._seq_lens_cpu` before any request. The exact case is final; the fork remains isolated and unpromoted. The existing 03:00 daily updater timer is restored, enabled/active with Persistent=false and next run November6 03:00 EST; no catch-up service ran. Other timer states were unchanged. Llama9c9074 qualification is complete for all three enabled llama routes; the old Empero manual source was released only after its new-source strict pass. Check actual jobs and GPU-LOCK before acting; this summary does not release any owner or queue another GPU job. Other paused schedules, unrelated services/files, retired XS/Super IQ3 and the stock boot default remain protected.

[Current measurements, downloads and pending work](../hardware/REALISTIC-LARGE-MODELS-2026-11-05.md). Prior activation and its27cases are complete; do not repeat passed checks for publication. New-source qualifications are separately authorized.

[Native decode evidence](../hardware/AMD-DECODE-EVIDENCE-2026-11-05.md): all14 current routes now have short native per-request statistics; four routes completed owner-requested native timing probes. A sustained matched14-route benchmark remains missing. [Latest methods and removal disposition](../hardware/AMD-NATIVE-DECODE-TESTS-2026-11-05.md): failed FlintAWQ/FP8PLE/SuperINT4 downloads removed by explicit owner request; selected13routes unchanged.

## Hardware and protected policy

- Intel i5-13600KF; ASUS TX GAMING B760M WIFI; 61.55 GiB visible RAM; two RX 7900 XTX 24 GB behind PEX880xx. Gen4 x16 common uplink, x8 branch segments. Runtime logical order is PowerColor then Sapphire (`ROCR_VISIBLE_DEVICES=1,0`, `HIP_VISIBLE_DEVICES=0,1`).
- Current post-crash kernel remains `7.0.14-42-vmpt1`, the owner-selected persistent inference default with stock installed fallback. Fresh peers passed on the preceding headless trial boot, followed by four completed model tool checks and a SGLang startup lost-bus/SMU failure on Sapphire. No current-boot qualification is claimed. **Latest hardware fault hold remains; no automatic retry or GPU continuation.**
- Retain **100°C** CPU/GPU edge/junction/memory/SSD stop policy, SMART health, 1 GiB available host RAM and 128 MiB free per-card live floors, dedicated-VRAM spill, supervisor heartbeat, phase timing and owned cleanup guards. Native normal readiness retains its 6 GiB actual startup floor.
- Current resource policy has no `MemoryHigh`, computes worker hard limits from installed RAM, retains existing swap capacity and permits device-speed swap with storage/temperature protection. Old v4 swap-rate/zero-system-swap policies are historical. Never disable global swap or interfere with unrelated applications.
- GPU tests require the established owned `hardware/generated/GPU-LOCK` and fresh admission. Serialize GPU work and heavy I/O; unknown ownership blocks startup. Never delete another owner's lock or fault evidence. No new test is needed for documentation.

## Exact enabled catalog

| Execution mode | Engine | Exact weight variant | API model ID | Context |
|---|---|---|---|---:|
| VRAM only | llama.cpp | Empero Qwen3.8-35B-A3B IQ4_XS | `empero-qwen3.8-35b-a3b` | 262,144 |
| VRAM only | llama.cpp | Flint-40B-A2.5B Unsloth UD-Q4_K_XL | `flint-40b-a2.5b` | 32,768 |
| VRAM only | SGLang | Qwen3.8-27B AutoRound W4A16 GPTQ; DFlash2 auxiliary | `qwen3.8-27b-sglang-dflash2` | 163,840 |
| VRAM only | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 | `nemotron-3.5-bolt-vllm` | 262,144 |
| VRAM only | vLLM | Qwen3.8-27B AutoRound W4A16 GPTQ; shared main weights | `qwen3.8-27b-vllm` | 163,840 |
| VRAM only | vLLM | Sage-A1.5 AutoRound W4A16 | `sage-a1.5` | 65,536 |
| CPU RAM offload | llama.cpp | Ornith-1.5-122B Q4_K_M; CPU experts + VRAM cache | `ornith-1.5-122b` | 32,768 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 32,768 |
| SSD streaming | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS; RAM/VRAM tiers | `glm-5.3-flash-maya` | 32,768 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing +36GB store | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 32,768 |
| SSD streaming | Strata | Qwen3.8-Flash-Next GSQ IQ3_XXS; RAM/VRAM expert caches | `qwen3.8-flash-next-iq3_xxs` | 262,144 |

Configured context is allocation capacity. The latest short checks add no full-window-quality or sustained-throughput proof. `dsh/model_catalog.py` combines the enabled backend registries; authenticated `/v1/models` is the live client source. DSH remains one AMD-server catalog; preserve its saved default/provider and private conversations/settings.

## Held and retired routes

| Candidate | Current disposition |
|---|---|
| PLE host-file-gather | Final dev229 loading stop on the unchanged six-second heartbeat guard; no inference/promotion, clean owned cleanup. Reviewed hold archived intact; no exact retry. |
| Super INT4 EP2 | Final dev229 loading stop on the unchanged six-second heartbeat guard; no inference/promotion, clean owned cleanup. Reviewed hold archived intact; no exact retry. |
| Maya DeepSeek UD-IQ1_S 36GB store | Final loading failure: six-second heartbeat and original 15-second cleanup failure, followed by AMDGPU/CPU lockups. No inference or promotion. Worker drained only after reboot; that fault hold was released by the owner on November 7 at 03:56. The same model without the store is the enabled `deepseek-v4.1-flash-1017-maya-unsloth-q1` route. |
| RDNA3 full-stack fork2314 | Isolated wheel/native/CLI audits passed; Qwen startup warm-up failed on missing `_seq_lens_cpu` before requests. Exact case final; no promotion. Reviewed own hold archived intact after fresh health/ownership checks. |

Four former timing-limited native candidates now passed and are enabled under their exact new source/profile seals. Deleted XS and Super IQ3 stay retired and are not fallbacks. No weights were deleted in the current update task.

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
- vLLM/SGLang routes have measured TP2/RCCL P2P/IPC evidence. Current llama presets use layer splitting; native engines use layer groups. Since November 7, production ComfyUI (`graphics/start-comfyui`) runs projected-8B H3 as fcys tp2-comfy TP2 over RCCL P2P/IPC; FLUX, Qwen-Image and native-32B H3 keep staged component placement on the same server; `COMFY_MODE=staged` rolls back ([report](../graphics/H3-TP2-PRODUCTION-2026-11-07.md)).

[Current results/downloads](../hardware/REALISTIC-LARGE-MODELS-2026-11-05.md) · [Numeric current results](../hardware/results/REALISTIC-LARGE-MODELS-2026-11-05.json) · [RDNA3/Radiance research](../hardware/RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md) · [Prior methods](../hardware/ALL-MODEL-P2P-2026-11-05.md) · [Media gallery](../graphics/results/p2p-2026-11-05/README.md)

## Keep this handoff small

After relevant authorized work, replace current state here, update applicable dated evidence/current index, sanitize and normally publish both AMD repositories, and verify the operational copy exactly matches `/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md` (Windows `D:\LINUX-LLM-RUNTIME-HANDOFF.md`). Keep credentials and machine-specific secret locations out of handoffs and public exports. Check actual Git status, job/lock ownership and remote refs; preserve unrelated untracked work.

For a historical question only: [previous full handoff](../hardware/history/documentation-2026-11-05/LINUX-LLM-RUNTIME-HANDOFF.reference.md), [benchmark history](../hardware/BENCHMARK-HISTORY.md), [root maintenance policy](../../README.md). Do not restore superseded historical settings or resume old plans without a new owner request.
