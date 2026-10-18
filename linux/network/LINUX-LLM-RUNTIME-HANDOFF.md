# Local LLM consolidated handoff — Linux host and Windows clients

Updated **October 18, 2026 (America/Toronto)**. This is the **single current
handoff on Shared**, available as `D:\LINUX-LLM-RUNTIME-HANDOFF.md` in Windows and
`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md` in Linux. Its maintained
source is `network/LINUX-LLM-RUNTIME-HANDOFF.md` in the Linux repository.

The previous nine Shared Markdown documents are preserved byte-for-byte in
`D:\LLM-HANDOFF-ARCHIVE\2026-10-18\` (Linux:
`/mnt/shared/LLM-HANDOFF-ARCHIVE/2026-10-18/`). They are historical
references, not alternative current configurations. Their old CUDA commands,
addresses, defaults and single-GPU policies must not override the settings here.
No model files, runtime settings, credentials or inference processes were changed
by the original consolidation; the subsequent MoE offload update is documented below.

## Current status and hardware

- Intel i5-13600KF, **MSI MPG Z690 CARBON WIFI**, two **RX 7900 XTX 24 GB** cards.
  Both GPUs have CPU-connected PCIe 4.0 x8 links; the earlier chipset x4 layout
  is obsolete. RTX 4070 and RTX 3060 are retired from this Linux setup.
- **32 GB system RAM** is installed, about 30.6 GiB usable; another 32 GB is
  pending. Old B1/B2/A2 troubleshooting notes describe the previous motherboard,
  not a diagnosis of the current board. Dense models keep GPU-resident weights;
  all three active MoEs now use CPU expert backing and GPU hot-expert caches.
- Use **both AMD cards for every production model**. llama.cpp uses layer split 1:1;
  SGLang/vLLM use TP2. FreeToken and its former single-card exception are retired.
- ROCm peer access is unavailable; TP2 works through host transport. Retain the
  isolated no-hostcall RCCL 2.27.7, `NCCL_P2P_DISABLE=1`, `HSA_ENABLE_SDMA=0`
  and disabled custom all-reduce. A genuine active PCIe switch under one common
  root port is a proposed remedy, not installed or validated hardware.
- At the earlier October 18 Q4-replacement check, the authenticated gateway listed
  **eight enabled profiles** and `nemotron-3.5-bolt` Q4 was running through the
  normal llama.cpp HIP backend in a visible terminal. Authenticated generation
  passed. DSH remained running and its saved selection was preserved; consult
  `/health` for live availability. At the later FreeToken removal check, no
  FreeToken worker was running and port 1919 was closed. No inference backend
  was started during removal. FreeToken is completely removed.

Ubuntu kernel observed: `7.0.0-38-generic`; Shared is mounted as exFAT. Runtime
binaries, Python environments and build caches are Linux-specific. The machine
is dual-boot: booting this same PC into Windows stops the Linux inference server.

## Active model catalog

October 18 MoE update: the normal managed llama launcher passed authenticated
API generation for all three MoEs, a repeated cached-model request, switching
between MoEs and switching back to dense Qwen/Vulkan. All five llama models and
eight gateway profiles remained discoverable. DSH/Turnstone catalogs were
refreshed without changing the saved default. That initial update reused
existing weights; Bolt was subsequently replaced by the Q4 files documented below.

All contexts below include system instructions, tool definitions/results,
conversation history, user input **and output**. They are configured budgets,
not guarantees of full-window speed or general long-context accuracy.

| Backend / placement | Exact API model ID | Total context | Target quantization | Speculation |
|---|---|---:|---|---|
| llama.cpp / Vulkan | `qwen3.8-27b-q4` | 65,536 | Q4_K_M | MTP3 |
| llama.cpp / Vulkan | `muse-glimmer-30b` | 32,768 | UD-Q4_K_XL | Off |
| llama.cpp / HIP, CPU experts + cache | `qwen3.6-35b-a3b` | 262,144* | MXFP4_MOE | MTP3 |
| llama.cpp / HIP, CPU experts + cache | `nemotron-3.5-bolt` | 262,144* | Q4_K_M, two GGUF shards | Off |
| llama.cpp / HIP, CPU experts + cache | `empero-qwen3.8-35b-a3b` | 262,144* | IQ4_XS | MTP3 |
| SGLang / ROCm TP2 | `qwen3.8-27b-sglang` | 40,960 | GPTQ INT4/group64 | MTP3 |
| SGLang / ROCm TP2 | `qwen3.8-27b-sglang-dflash2` | 65,536 | GPTQ INT4/group64 | DFlash2, 8 draft tokens |
| vLLM / ROCm TP2 | `qwen3.8-27b-vllm` | 65,536 | GPTQ INT4/group64 | MTP3 |

All llama.cpp rows use both cards, Q8_0 K/V, flash attention, batch 512,
microbatch 128, one slot and embeddings on GPU0. Dense models use Vulkan with
GPU-resident weights. Qwen/Empero use HIP with layer split 1:1, 20 CPU expert
layers and a 12,288 MiB total cache ceiling. Bolt Q4 uses HIP with layer split
21:19, 12 CPU expert layers (12.73 GiB backing) and a 7,168 MiB total GPU
expert-cache ceiling. CPU backing and cached copies both consume memory. Actual
cache allocation is bounded by each GPU's host-expert set. Qwen/Empero MTP draft
experts remain on GPU. Effective settings come from `dsh/models-amd.ini`,
`dsh/models-hip.ini`, `dsh/moe-offload.json` and model-specific overrides.

*MoE 256K allocation passed with approximately 64K actual retrieval, tools/JSON
and arithmetic; full 256K filling, quality and sustained speed are untested.
The same launcher/router switches Vulkan/HIP automatically for the selected
model. CPU/cache profiles require their expert bytes plus 4 GiB available RAM;
loaded requests need 3 GiB. A scoped monitor stops only an unsafe owned worker
on sustained low memory, owned swap or dedicated VRAM spill. No unrelated
application/frontend is stopped. See [measurements and both forums' source trail](../hardware/MOE-OFFLOAD-2026-10-18.md).

Bolt vision remains disabled and unvalidated; this Q4 text profile uses no projector.

Bolt Q4 source: `darioooooo0o/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-GGUF`,
revision `b739f8c7c5484413ae3e55e6da8383f0f2570cee`. The two verified shards
are in `GGUF-Models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-Q4_K_M-GGUF/Q4_K_M/`
on Shared/D:. Pass `NVIDIA-Nemotron-3.5-Bolt-74B-A9B-Q4_K_M-00001-of-00002.gguf`
to the runtime; keep shard 2 beside it. The old 24GB IQ2 model was removed after
Q4 validation. API ID stays `nemotron-3.5-bolt`; clients need no model-ID change.
Q4 passed arithmetic/JSON/tools and 63,911-token retrieval. Short code decode:
**35.7 t/s**; long prefill: **424.0 t/s**. Single probes, not matched
IQ2/Q4 speed rankings or full 256K validation. See [replacement details](../hardware/NEMOTRON-Q4-2026-10-18.md).

SGLang uses BF16 activations/KV/Mamba, Triton attention, memory fraction 0.85,
one simultaneous request, graphs, GPU prefix caching and eight Mamba cache
slots. MTP uses chunk/max-prefill 512/1,024; DFlash2 uses 2,048/2,048 and draft
window 2,048. Both require 21 GiB free per GPU before loading. The selected
optimized verifier requires **both** `SGLANG_RDNA_VLLM_VERIFY=1` and
`SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX=1`; do not enable the unmodified verifier.
Host/disk HiCache and CPU weight offload are not enabled.

vLLM uses BF16 activations/KV/Mamba, compiled MTP3, full decode graphs at sizes
1/4, 2,048-token chunks, tuned RDNA3 prefill, RCCL Simple and a **fixed 3.5 GiB
KV allocation per GPU**. The October 18 startup fix uses utilization **0.82**
and requires **20 GiB free per GPU**. The previous 21 GiB guard rejected about
20.78 GiB free on the display card and closed the terminal before loading.
The corrected profile passed 64,033-token retrieval, tools/JSON, prefix caching
and authenticated API generation. It preserves 65,536 context and MTP3.
Startup host-page swapping was observed with 32 GB RAM; GPU weights stayed
resident. This is not a promise of swap-free startup or a new throughput claim.

The catalog refresh preserves the user's saved DSH provider/model, including a
non-local provider; it does not force a default. The original consolidation
recorded Local vLLM, but a user can change that selection in DSH at any time.
Existing conversations may retain another model. The SGLang launcher defaults
to DFlash2; the llama.cpp router initially starts its dense Vulkan parent.
Selecting a MoE in Local llama.cpp switches only its native worker to HIP.
Choose a model belonging
to the backend actually running. A DSH model selection does not launch another
backend, and the gateway requires an explicit model ID in each generation request.
Older Strata defaults in historical notes/private network metadata are not active
catalog entries and must not be copied into a client configuration.

## Start, stop and switch

Desktop icon update, October 18: all six LLM launchers now use official upstream
logo/favicon assets (llama.cpp, SGLang, vLLM, Strata Q3, dsh and Turnstone),
replacing the initial custom icons. See [logo sources and original licenses](../launchers/icons/README.md)
and `launchers/icons/SOURCES.json` for pinned URLs, SHA-256 values and extraction
notes. Artwork is unchanged; Turnstone's existing embedded favicon was decoded
from its official HTML. `Icon=` points to the corresponding SVG/PNG in the runtime
workspace; retain those files and update paths if moving the setup. Backend
commands, terminal visibility, models, contexts and Strata's deferred status remain. DSH
uses the official desktop PNG with its own opaque light tile/background; the
transparent web favicon was replaced for visibility against wallpaper.

October 18 menu preference: Turnstone was removed from the application menu.
Its Desktop launcher and `turnstone` PATH command remain available; this change
did not stop or uninstall Turnstone or affect any inference backend.

Backend Desktop launchers **llama.cpp**, **SGLang** and **vLLM** start only their
backend, with live terminal logs. Models load on the first matching request.
The **dsh** and **Turnstone** launchers are separate optional harnesses; external
OpenAI-compatible clients do not need either one.

| PATH command | Purpose |
|---|---|
| `llm-llama` | llama.cpp model router |
| `llm-sglang` | SGLang router; DFlash2 default, MTP selectable in client |
| `llm-vllm` | vLLM router, Qwen 27B |
| `llm-strata` | Retained but blocked until RAM expansion and dual-AMD validation |
| `dsh` | DSH frontend only |
| `turnstone --no-browser` | Turnstone frontend without opening a host browser |
| `llm-upgrade-check` | Hardware/readiness inspection; success is not an inference test |

Commands are installed in `~/.local/bin`, with sources in the
repository's `bin/`. Use these managed entry points. Starting a backend stops
only this user's configured llama.cpp, vLLM, SGLang, HyperQwen or Strata inference
servers and their owned workers/log monitors; active replies are interrupted.
DSH, Turnstone, the gateway, unrelated Python/training jobs and graphics apps
must remain running. Never use blanket Python/GPU process killing. A busy unknown
port or unrelated compute workload blocks startup rather than being terminated.
Clicking the same backend again restarts it. Keep its terminal/SSH session open;
Ctrl+C or disconnect stops a foreground backend. Raw research launchers bypass
managed handover and are not routine client entry points.

The vLLM Desktop entry now uses `dsh/start-backend-terminal vllm`: startup output
is saved in `dsh/logs/vllm-launcher.log`, and interactive failures wait for Enter
before the terminal closes. CLI/SSH failures still return normally. Worker logs:
`dsh/logs/vllm-qwen3.8-27b-vllm.log`, SGLang's model-specific files, and
`dsh/logs/llama.cpp.log`. Logs, sessions and credentials remain ignored by Git.

From Windows PowerShell or another SSH client, for example:

```powershell
ssh -t operator@<LINUX_LAN_IP> llm-vllm
# Through Tailscale instead:
ssh -t operator@<LINUX_TAILSCALE_IP> llm-vllm
```

Use another terminal for a frontend if wanted:

```powershell
ssh -L 3080:127.0.0.1:3080 -t operator@<LINUX_TAILSCALE_IP> dsh
# Or Turnstone:
ssh -L 3081:127.0.0.1:3081 -t operator@<LINUX_TAILSCALE_IP> turnstone --no-browser
```

Browse client localhost:3080 for DSH or localhost:3081 for Turnstone. Forward a
different client port if occupied. These harness ports remain Linux-loopback-only.
DSH is `@deepseek-ai/dsh@0.2.1-rc.2`, Node.js 24.21.0. It migrated legacy
`data/settings.yaml` into `data/profiles/web/cordis.patch.yml`, retaining the
imported backup; preserve settings, sessions and credentials. Turnstone 1.9.0a3
uses its own environment and private `turnstone/data/login.txt` for login details.
No password or API key is contained in this guide. Tool execution/web browsing is
a harness/client function, not an ability granted by the inference API alone.

## Connect any Windows, phone or other API client to Linux

| Setting | Current Linux value |
|---|---|
| Protocol | OpenAI-compatible **Chat Completions** |
| LAN base URL | `http://<LINUX_LAN_IP>:10000/v1` |
| Tailscale base URL | `http://<LINUX_TAILSCALE_IP>:10000/v1` |
| Linux MagicDNS alternative | `http://<LINUX_TAILSCALE_DNS>:10000/v1` |
| Authentication | Actual private bearer API key |
| Current vLLM model | `qwen3.8-27b-vllm` |
| Streaming / timeout | On / 600 seconds; allow for cold model loading |
| Initial client output limit | 2,048 tokens, within the total context budget |

The host must remain booted into Linux, awake and logged into its user session.
LAN clients need the permitted home network; Tailscale clients need authorized
tailnet access to TCP 10000. The real key is in Linux
`/opt/local-llm/dsh/data/network-api.key`; obtain/configure it
privately on the client. The old Windows Strata placeholder **`local-strata` is
not a valid key for this Linux gateway**. The same real key serves both addresses
and all enabled backend profiles. Use HTTP as shown; a `.ts.net` name does not
make this raw endpoint HTTPS. Tailscale carries remote transport encrypted.
No public Internet forwarding, Funnel or new tailnet-policy grant was added.

Read-only Windows PowerShell connection check:

```powershell
$env:LOCAL_LLM_BASE_URL = 'http://<LINUX_TAILSCALE_IP>:10000/v1'
$env:LOCAL_LLM_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'API key' -AsSecureString)).Password
curl.exe --noproxy '*' --connect-timeout 5 --max-time 30 `
  -H "Authorization: Bearer $env:LOCAL_LLM_API_KEY" `
  "$env:LOCAL_LLM_BASE_URL/models"
```

For Bash:

```bash
export LOCAL_LLM_BASE_URL='http://<LINUX_TAILSCALE_IP>:10000/v1'
read -r -s -p 'API key: ' LOCAL_LLM_API_KEY
printf '\n'
export LOCAL_LLM_API_KEY
curl --noproxy '*' --connect-timeout 5 --max-time 30 \
  -H "Authorization: Bearer $LOCAL_LLM_API_KEY" \
  "$LOCAL_LLM_BASE_URL/models"
```

After configuring the environment, this Python example sends a streamed request
when run by the client (requires its own `openai` package):

```python
import os
from openai import OpenAI
client = OpenAI(base_url=os.environ['LOCAL_LLM_BASE_URL'],
                api_key=os.environ['LOCAL_LLM_API_KEY'], timeout=600)
for chunk in client.chat.completions.create(
    model='qwen3.8-27b-vllm',
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=2048, stream=True,
):
    if chunk.choices:
        print(chunk.choices[0].delta.content or '', end='', flush=True)
print()
```

`GET /v1/models` lists all eight enabled profiles even when their backends are
stopped. `backend_available` means the corresponding router is available; it
need not have loaded weights yet. Authenticated `GET /health` reports available
profiles by backend. The gateway starts at user login and **does not start GPU
backends**. Internal routers/workers remain loopback-only:

| Backend | Router / worker ports |
|---|---|
| llama.cpp | 8080 / 8081 |
| SGLang | 30000 / 30001 |
| vLLM | 30010 / 30011 |
| Strata, inactive | 30020 / 30021 |

Do not use those internal ports for remote clients or confuse Linux's port 8081
with the historical Windows Strata API. The gateway exposes chat/completions,
model listing and authenticated health; it does not expose DSH, worker management
or the Responses API. Browser CORS is not enabled; use a native client or a
server-side connector. Tool-calling clients must execute tools and return results.

## Storage and runtime pins

Linux runtime/repository root: `/opt/local-llm` on ext4 NVMe.
Shared model root: `/mnt/shared/GGUF-Models` = `D:\GGUF-Models`.

- The five active GGUF models and retained Strata Q3 GGUF/pack/MTP files are
  actual files on Shared SATA, usable by a separately configured compatible
  Windows runtime. Shared exFAT does not support hardlink deduplication.
- Linux-only target checkpoint:
  `models/Qwen3.8-27B-W4A16-AutoRound-GPTQ/` on Linux NVMe, reused by both
  vLLM and SGLang. DFlash2 drafter:
  `models/drafts/Qwen3.8-27B-DFlash2-W4A16/`, also on Linux NVMe.
  Windows must not refer to these Linux-only absolute paths.
- Builds, SDKs, environments, compiler/JIT caches and harness data remain on
  Linux NVMe. Weights, binaries, caches, private settings, credentials and raw
  logs are excluded from both repositories. Public history is a separately
  sanitized distribution, never a copy of private Git history.
- SATA affects cold load time. SSD paging/PLE/expert reads can also affect a
  runtime that uses them; do not generalize resident-model decode measurements
  into a claim that disk speed can never affect Strata.

| Component | Selected source / version |
|---|---|
| llama.cpp Vulkan, retained HIP alternative | `f12aaa344c971556ec35be054d7aac1d901fd510` |
| SGLang Radeon fork (`gfx1100-support`) | `f84475ccf593087df3d1da13c9e675eadee12352`, locally repaired |
| vLLM | `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, locally patched |
| ROCm SDK / PyTorch / RCCL | 7.2.3 / `2.13.0+git733fca1` / no-hostcall 2.27.7 |
| Strata source, retained inactive | `296b59d2f73c8f04a805df29c2fa97655adace78`, 0.1.44.1 |

Source/configuration authorities: `dsh/models-amd.ini`, `dsh/llama-runtime.json`,
`dsh/sglang-profiles.json`, `dsh/vllm-profiles.json`, `dsh/strata-profiles.json`,
and private `dsh/data/network-access.json`. The installed SGLang wheel's generic
version string is not a substitute for its pinned fork revision. User preference
is latest capable upstream development/nightly candidates, with exact pins and
local validation before activation; this handoff is not permission to auto-upgrade.

## FreeToken removed — October 18

The user requested complete removal because performance was unsatisfactory.
The AMD source/runtime, extracted Desktop frontend, saved app state, menu/PATH
launchers, environment setting and FreeToken-specific caches are removed.
The former single-GPU exception is retired. Shared GGUF weights, production
ROCm and the other inference engines remain. No FreeToken API is served on
port 1919. No model backend was started during removal. Do not reinstall it
without a new request.

[Historical measurements and validation limits](../hardware/FREETOKEN-RETIRED-2026-10-18.md)
remain as reference. MoE API tests passed, but the final MoE GUI chat/Stop test
was cancelled before completion; it must not be reported as passed.

## Image/video generation planning — October 18

A [ComfyUI walkthrough](../hardware/IMAGE-VIDEO-SETUP-2026-10-18.md) now records
forum research and proposed ROCm/core multi-GPU component placement for Qwen-Image
2.1, Wan2.2 and later H3/LTX tests. **No installation, model download, launcher,
network listener or generation benchmark was performed.** Existing LLM profiles
and automatic shutdown scope are unchanged. Native H3 sequence parallelism remains
an unvalidated candidate for 24 GB cards; R9700/32 GB speeds are not local results.

## Retained Strata and retired setups

**Strata Q3 is disabled**, absent from the live API catalog and not AMD-validated.
The old disabled metadata names 262,144 context; that is not an active capacity
claim. Keep `GGUF-Models/Strata/models/IQ3_XXS`, `packs/iq3_xxs`, tokenizer and
`mtp/rt` data. Q2's model/pack is removed; do not follow archived Q2 install or
"leave Q2 running" instructions. HyperQwen, old CUDA environments/builds,
GPT-OSS-20B/120B, Qwen 27B Q5, Bonsai 2 and old Nemotron Lightning setups are
retired. Historical NVIDIA/Windows reference snapshots remain in the public repo.

### Workspace archive and completed cleanup — October 18

The retired NVIDIA recovery collection is now in
`/mnt/shared/LLM-ARCHIVE/NVIDIA/2026-10-18/nvidia-recovery.tar.zst` (example mount):
10.16 GiB compressed, with `MANIFEST.json`, `SHA256SUMS` and recovery instructions.
Full tar content/metadata comparison passed. It includes old pre-October-14
rollback environments and the later configuration snapshot; these have different
versions and must not be treated as one tested runtime. See the
[archive boundaries and recovery notes](../hardware/NVIDIA-ARCHIVE-2026-10-18.md).

**All five cleanup groups were explicitly approved and removed.** The
[completed scope and checks](../hardware/CLEANUP-REVIEW-2026-10-18.md) record 73
exact directory roots/installer files and **55.58 GiB observed NVMe recovery**.
Removed: unused NVIDIA rollback originals/Flash-MTP source, old CUDA kernels,
downloaded ROCm installers, unselected test build/cache files and UV package cache.
The archive SHA-256 was rechecked before removal; current model-file metadata
matched before/after and required runtime paths remain. Current AMD compiled
kernel caches and `llm-tools/cuda-build` remain; the latter is still required for
C++ builds/JIT. No runtime configuration or benchmark result changed. Historical
setup records, patches, source pins and benchmarks remain in both Git repositories,
including the public NVIDIA/Windows reference trees. Private binary archives and
cleanup logs are excluded from Git. Future package installations may redownload
packages; repeating removed experiments requires rebuilding their caches.

After stable 64 GB RAM is installed, `python3 hardware/check-strata-ready.py`
checks prerequisites; exit zero is not proof of successful inference. A future
Strata migration must validate **both AMD GPUs**, HIP kernel/library compatibility,
MTP on/off correctness, GPU/RAM residency, tools/streaming and progressively
larger real prompts before enabling a profile. The old single-AMD candidate and
4070/3060 CUDA layer splits are starting/history references, not current recipes.
Do not delete or regenerate shared Windows-compatible packs during a Linux-only
experiment without a specific reason and authorization.

The Windows handoffs were last validated on the **old NVIDIA hardware**. Their
Strata 0.1.44.1/CUDA 13.0, llama.cpp b11630, port 8081, Windows MagicDNS name and
36,919-token retrieval record describe that historical system. They do not prove
native Windows ROCm/HIP support or current dual-AMD readiness. The Windows agent
must inspect its actual hardware/runtime/profile before reuse. Keep Windows
binaries/environments/credentials separate from Linux; share compatible model
assets only. The original recipes, checksums, benchmark caveats and Windows
network administration instructions remain intact in the dated archive.

## Measurements and open work

The original consolidation did not rerun benchmarks. The later Q4 replacement
measurements are in the report above. The maintained README contains
all model results with dates/hardware/methods. Selected recent Qwen measurements:

| Profile | Code / prose decode t/s | Evidence |
|---|---:|---|
| vLLM MTP3, BF16 KV | 133.06 / 78.50 | October 17–18 Level1 candidate control |
| llama.cpp Vulkan Q8 KV/MTP3 | 79.38 / 45.53 | Same candidate comparison batch |
| SGLang DFlash2, repaired verifier | 205.59 / 71.84 | October 17 clean retry |
| SGLang MTP3, repaired verifier | 114.57 / 66.05 | October 17 clean retry |

Short code/prose numbers are medians of three timed 256-token-limit runs after
warm-up. They depend on speculative acceptance/text and are not sustained 64K
speeds or a perfectly controlled cross-engine ranking. The vLLM control's seeded
book estimates were 1,556.04 PP / 92.62 decode t/s at depth 0 and
1,457.42 / 67.54 at depth 16K plus prompt/template. A 22-token marker answer
validates retrieval but is too short for a sustained decode benchmark.

The restored rocWMMA candidate passed 84 CPU-reference cases but reduced matched
HIP 16K prefill from 1,001.78 to 465.65 t/s; Radiance and queue-cap-1 trials did
not justify replacing current defaults. Cooling fan A/B remains pending admin
access. No direct P2P collective was benchmarked because its prerequisite failed.
Do not activate kernel allowlist/ACS/IOMMU bypasses as a documented fix.

Repository evidence (also published in the sanitized public distribution):

- `hardware/VLLM-STARTUP-2026-10-18.md`: terminal/admission correction and 64K recovery.
- `hardware/LEVEL1-TESTS-2026-10-17.md`: candidate speeds, pins and resource limits.
- `hardware/VLLM-TUNING-2026-10-17.md`: selected vLLM kernels/cache/graphs.
- `hardware/CLEAN-TUNING-2026-10-17.md`: selected SGLang MTP3/DFlash2 verifier repair.
- `hardware/SGLANG-DUAL-CONTEXT-2026-10-17.md`: prior prefix/context probes; its
  earlier MTP2/verifier-off choice was superseded by the clean retry.
- `hardware/PCIE-P2P-2026-10-17.md`: platform routing diagnosis and switch requirements.
- `hardware/STRATA-AFTER-RAM.md`: inactive preparation, superseded single-card candidate caveat.
- `hardware/RETIRED-SETUPS-2026-10-16.md`: removal scope; no retired runtime should be selected.

Forum-derived claims must cite direct **both lcz.me and Level1Techs** sources in
both repositories, alongside primary implementation references and local tests.
Relevant source trail: `hardware/FORUM-OPTIMIZATION-SOURCES.md`, including
[lcz.me dual-XTX setup](https://lcz.me/topic/1252),
[lcz.me measured comparison](https://lcz.me/topic/1814),
[Level1Techs dual-R9700 report](https://forum.level1techs.com/t/dual-r9700-llama-cpp-rocm-tensor-split-working-p2p-on-proxmox-qwen3-8-27b/254183),
and [Linux P2PDMA routing documentation](https://docs.kernel.org/driver-api/pci/p2pdma.html).
Different platforms' headline speeds are not local measurements.

## Troubleshooting and maintenance

| Symptom | Action |
|---|---|
| Terminal closes immediately | vLLM now preserves startup errors; inspect its launcher log. Check per-GPU free VRAM and runtime probe. |
| HTTP 401 | Configure the actual private Linux API key, not `local-strata`. |
| HTTP 404 / unknown model | Copy an exact enabled ID from `/v1/models`; do not use Q2, HyperQwen or disabled Strata. |
| HTTP 503 | Start the required backend and inspect its terminal; gateway availability is separate from worker readiness. |
| Refused / timed out | Check Linux session, address, service, client LAN/Tailscale path and TCP 10000 access. |
| All Shared GGUF models fail after reboot | Confirm Shared is mounted; open it in Files if the mount helper lacks permission. Do not redownload first. |
| Context error | Input, history, tools and output together must fit the selected context. |
| Very slow first request | Inspect loading/JIT/host RAM/swap; prefix caching helps repeated prefixes, not every new prompt. |

Read-only host service check:

```bash
systemctl --user status local-llm-api.service
```

For an intentionally changed Linux network address, update private configuration
and this guide, then restart the gateway; preserve the key:

```bash
cd /opt/local-llm
python3 network/configure.py
systemctl --user restart local-llm-api.service
```

These are maintenance instructions for a future authorized change; they were not
run during consolidation. The legacy `network/check.py` still encodes a retired
12-model Strata snapshot; do not treat its historical assertions as a current
readiness test. Use authenticated `/v1/models` and `/health` instead.

The latest October 18 authenticated API/generation recovery was checked from
Linux loopback. Earlier host self-access checks covered LAN/Tailscale; a separate
remote device must still test its own network/ACL path. The October 18 MoE
update ran bounded local model validation and refreshed catalogs;
no driver, BIOS, firewall or credential changes were required. The original
consolidation check above remains a timestamped historical observation.

## Where the originals went

`LLM-HANDOFF-ARCHIVE/2026-10-18/` contains all nine pre-consolidation originals
plus `MANIFEST.json` (filenames, byte counts and SHA-256) and an archive README:

| Original file | Historical material retained |
|---|---|
| `LINUX-LLM-RUNTIME-HANDOFF.md` | Full chronological Linux changes and old runtime pins |
| `LINUX-LLM-CLIENT-HANDOFF.md` | Earlier client examples and catalog versions |
| `WINDOWS-LLM-LAN-CLIENT-HANDOFF.md` | Old Windows LAN forwarders/firewall and client checks |
| `WINDOWS-TAILSCALE-CLIENT-HANDOFF.md` | Old Windows Serve/MagicDNS/key handling and checks |
| `STRATA-WINDOWS-TO-LINUX-HANDOFF.md` | Original Strata recipes, asset hashes and Windows tuning |
| `LLM-GPU-UPGRADE-HANDOFF.md` | Superseded mixed AMD/NVIDIA upgrade plan |
| `AMD-ROCM-2026-10-16.md` | Earlier single-AMD runtime/quant experiments |
| `LLM-GPU-TESTS-2026-10-16.md` | Earlier single/mixed-GPU benchmarks, including retired models |
| `NEMOTRON-BOLT-2026-10-16.md` | Original replacement hashes and single-card measurements |

For future relevant changes, update this consolidated guide **in place**, the
matching Shared copy, README/evidence as needed and both private/public Git repos.
Do not prepend incompatible historical snapshots or recreate the old root guides.
Public exports use example addresses/paths and omit private archives, credentials,
raw logs and personal settings. Archive content documents history; it does not
provide authorization to start models, change security settings or message agents.
