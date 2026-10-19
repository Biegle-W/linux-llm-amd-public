# Local LLM consolidated handoff — Linux host and Windows clients

Updated **October 19, 2026 (America/Toronto)**. Most runtime checks remain dated October 18; October 19 adds measured Strata
overlap/prefill tuning, desktop headroom protection, validated native256K RAM-backed KV,
and the separately validated Nemotron Super IQ3 32K profile. Maintenance reconciles
all ten enabled profiles from saved evidence, validates launch paths and archives
unused working files; no timing rerun or runtime update is part of maintenance.
This is the **single current handoff on Shared**, available as `D:\LINUX-LLM-RUNTIME-HANDOFF.md` in Windows and
`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md` in Linux. Its maintained
source is `network/LINUX-LLM-RUNTIME-HANDOFF.md` in the Linux repository.

The previous nine Shared Markdown documents are preserved byte-for-byte in
`D:\LLM-ARCHIVE\LLM-HANDOFF-ARCHIVE\2026-10-18\` (Linux:
`/mnt/shared/LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/`). They are historical
references, not alternative current configurations. Their old CUDA commands,
addresses, defaults and single-GPU policies must not override the settings here.
No model files, runtime settings, credentials or inference processes were changed
by the original consolidation; the subsequent MoE offload update is documented below.

## Current status and hardware

- Intel i5-13600KF, **MSI MPG Z690 CARBON WIFI**, two **RX 7900 XTX 24 GB** cards.
  Both GPUs have CPU-connected PCIe 4.0 x8 links; the earlier chipset x4 layout
  is obsolete. RTX 4070 and RTX 3060 are retired from this Linux setup.
- **32 GB system RAM** is installed, about 30.6 GiB usable; a 64 GB
  configuration is planned. Benchmarks must state the memory capacity used.
  Dense models keep GPU-resident weights; all active MoEs use CPU expert
  backing and GPU hot-expert caches.
- Use **both AMD cards for every production model**. llama.cpp uses validated model-specific layer splits (1:1 or 21:19);
  SGLang/vLLM use TP2. FreeToken and its former single-card exception are retired.
- ROCm peer access is unavailable; TP2 works through host transport. Retain the
  isolated no-hostcall RCCL 2.27.7, `NCCL_P2P_DISABLE=1`, `HSA_ENABLE_SDMA=0`
  and disabled custom all-reduce. The owner purchased the PEX88096 four-slot GPU kit (listing title uses
  “plx8096”). It remains pending installation and local P2P/Gen4/RCCL validation.
  Keep current transport settings until validation passes; external forum results
  are not local measurements. [Source trail](../hardware/FORUM-OPTIMIZATION-SOURCES.md#pcie-switch-purchase-october-19).
- October 19 maintenance: authenticated gateway health and enabled-catalog checks
  cover **10 profiles**. No managed inference backend was available at the initial
  audit; catalog presence does not mean a model is loaded. This maintenance does
  not start models, repeat generation/timings or change the saved DSH default.
  FreeToken and HyperQwen remain retired from the current AMD setup.

Ubuntu kernel observed: `7.0.0-38-generic`; Shared is mounted as exFAT. Runtime
binaries, Python environments and build caches are Linux-specific. The machine
is dual-boot: booting this same PC into Windows stops the Linux inference server.

## Nemotron Super: 32 GB active profile / 64 GB candidate

`nemotron-3.5-super-iq3` is added to the existing llama.cpp launcher, DSH and
this authenticated gateway, with **32,768 total context**, both AMD cards,
HIP layer split **21:19**, Q8 K/V, Flash Attention, CPU expert backing
**20,533,739,520 bytes (19.124 GiB)** and a **2,048 MiB total GPU cache ceiling**.
Text and tools are validated; vision is disabled and no projector is installed.
The saved default model and connection settings are unchanged.
The normal launcher/gateway passed authenticated generation, tools/JSON/streaming,
zero-swap native scopes and IQ3/HIP -> Qwen/Vulkan -> IQ3/HIP switching. The
gateway lists 10 enabled profiles, with Q4 hidden. Validation workers were
stopped afterward; no inference backend was left running by this task.

All six Unsloth IQ3/Q4 shards are on Shared SATA beneath
`/mnt/llm-models/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF/`,
pinned to `75a5829055f69a0359085ae6bbd0a81b60bc05c6`, with size/SHA-256 verification
in `download-manifest.json`. llama.cpp remains at `31288c9c66e59377f7788d920678a565bb89dd37`.
There is no new model-weight copy or cache on the primary NVMe.

IQ3 passed arithmetic, JSON, streaming, a tool-call/result round trip and
three-marker retrieval at **28,546 uncached input tokens**. Three approximately
8K-input/256-output trials each measured code/prose medians of **95.75 / 97.13
native prefill t/s**, **84.699 / 83.521 s external TTFT**, and **14.16 / 16.32
external decode t/s**. These are not the earlier batch's short-prompt timings.
Peak whole-card VRAM was **20.00 / 20.94 GiB**, available host RAM stayed above
**5.84 GiB**, and worker swap/nonresident VRAM were zero. The 1:1 and 19:21 split
trials were stopped for insufficient per-card reserve, without swap or spill.

New loads need **23.124 GiB available RAM** and **21 GiB free VRAM per card**.
The owned-worker monitor retains **3 GiB available RAM / 3 GiB free per GPU**;
it does not terminate DSH or unrelated applications. MTP stays off: its expert
head alone adds 2.789 GiB, exceeding spare VRAM beyond the combined reserve.
No MTP speed comparison was run because that memory admission failed.

`nemotron-3.5-super-q4` is a prepared candidate only and is absent from active
API/DSH catalogs. It requires **60 GiB OS-visible total / 51.424 GiB available
RAM**, uses **47.424 GiB CPU expert backing**, a **4 GiB cache ceiling** and a
32K target. Installing RAM does not activate it. Its context and speed are not
locally validated. The inactive metadata and physical-memory gates are in
`dsh/candidates/nemotron-super.json`; validate after the upgrade before activation.

Start `llm-llama` or the existing llama.cpp Desktop launcher, then start DSH
separately and select the IQ3 model under Local llama.cpp. Remote clients use
the existing authenticated base URL and model ID `nemotron-3.5-super-iq3`.
Windows remains a client of the Linux HIP service; its historical NVIDIA
runtime configuration is not an AMD profile. [Settings and evidence](../hardware/NEMOTRON-SUPER-2026-10-19.md).

## Active model catalog

The current catalog has **10 enabled profiles**: six llama.cpp, two SGLang,
one vLLM and one Strata. The original nine-profile benchmark batch and later
Nemotron Super IQ3 measurements remain separate because input lengths and timing
methods differ. All were measured on the stated builds; no maintenance rerun was
performed. [Current results and limits](../hardware/CURRENT-AMD-BENCHMARKS.md).
Earlier runtime/placement checks remain in their dated reports and must not
replace the catalog and settings below.

All contexts below include system instructions, tool definitions/results,
conversation history, user input **and output**. They are configured budgets,
not guarantees of full-window speed or general long-context accuracy.

| Backend / placement | Exact API model ID | Total context | Target quantization | Speculation |
|---|---|---:|---|---|
| llama.cpp / Vulkan | `qwen3.8-27b-q4` | 65,536 | Q4_K_M | MTP3 |
| llama.cpp / Vulkan | `muse-glimmer-30b` | 32,768 | UD-Q4_K_XL | Off |
| llama.cpp / HIP, CPU experts + cache | `qwen3.6-35b-a3b` | 262,144* | MXFP4_MOE | MTP3 |
| llama.cpp / HIP, CPU experts + cache | `nemotron-3.5-bolt` | 262,144* | Q4_K_M, two GGUF shards | Off |
| llama.cpp / HIP, CPU experts + cache | `nemotron-3.5-super-iq3` | 32,768 | UD-IQ3_XXS, three shards | Off |
| llama.cpp / HIP, CPU experts + cache | `empero-qwen3.8-35b-a3b` | 262,144* | IQ4_XS | MTP3 |
| SGLang / ROCm TP2 | `qwen3.8-27b-sglang` | 40,960 | GPTQ INT4/group64 | MTP3 |
| SGLang / ROCm TP2 | `qwen3.8-27b-sglang-dflash2` | 65,536 | GPTQ INT4/group64 | DFlash2, 8 draft tokens |
| vLLM / ROCm TP2 | `qwen3.8-27b-vllm` | 65,536 | GPTQ INT4/group64 | MTP3 |
| Strata / HIP dual-card layer split | `qwen3.8-flash-next-iq3_xxs` | 262,144 | IQ3_XXS, bounded CPU expert backing + GPU cache | MTP (`--spec 3`) |

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

October 19 app-menu integration: **Strata App** opens the existing AMD RX7900
AppImage, with its official bundled 512×512 logo. The installed entry is
`~/.local/share/applications/Strata.desktop`; icon name is `strata-desktop`.
Tracked source and reinstall instructions: [launchers/STRATA-APP.md](../launchers/STRATA-APP.md).
**Strata Q3** and `llm-strata` still start the managed DSH backend. The app owns
its own settings/model worker; it does not inherit the managed profile or memory
watchdog. Avoid loading both workers concurrently. Registration was validated
without starting the app or interrupting the existing backend.

Desktop icon update, October 18: all six LLM launchers now use official upstream
logo/favicon assets (llama.cpp, SGLang, vLLM, Strata Q3, dsh and Turnstone),
replacing the initial custom icons. See [logo sources and original licenses](../launchers/icons/README.md)
and `launchers/icons/SOURCES.json` for pinned URLs, SHA-256 values and extraction
notes. Artwork is unchanged; Turnstone's existing embedded favicon was decoded
from its official HTML. `Icon=` points to the corresponding SVG/PNG in the runtime
workspace; retain those files and update paths if moving the setup. Backend
commands and terminal visibility remain; Strata now uses the tested dual-AMD profile below. DSH
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
| `llm-strata` | Retained but blocked until the planned RAM expansion and dual-AMD validation |
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

`GET /v1/models` lists all ten enabled profiles even when their backends are
stopped. `backend_available` means the corresponding router is available; it
need not have loaded weights yet. Authenticated `GET /health` reports available
profiles by backend. The gateway starts at user login and **does not start GPU
backends**. Internal routers/workers remain loopback-only:

| Backend | Router / worker ports |
|---|---|
| llama.cpp | 8080 / 8081 |
| SGLang | 30000 / 30001 |
| vLLM | 30010 / 30011 |
| Strata / HIP | 30020 / 30021 |

Do not use those internal ports for remote clients or confuse Linux's port 8081
with the historical Windows Strata API. The gateway exposes chat/completions,
model listing and authenticated health; it does not expose DSH, worker management
or the Responses API. Browser CORS is not enabled; use a native client or a
server-side connector. Tool-calling clients must execute tools and return results.

## Storage and runtime pins

The Shared SATA drive was found unmounted after the latest reboot and restored
with the existing UUID-checking storage helper. Model files were not moved or
re-downloaded, and no inference backend was started.

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
| llama.cpp Vulkan (dense), HIP (MoE) | `31288c9c66e59377f7788d920678a565bb89dd37` |
| SGLang Radeon fork (`gfx1100-support`) | `f84475ccf593087df3d1da13c9e675eadee12352`, locally repaired |
| vLLM | `0.32.0rc1.dev329+g39983a5e7.rocm723`, locally patched |
| ROCm SDK / PyTorch / RCCL | 7.2.3 / `2.13.0+git733fca1` / no-hostcall 2.27.7 |
| Strata HIP source | `477ac13cbe8e582c20484871ce459d20d82df09d`, 0.1.45 |

**October 18 authorized development update:** llama.cpp HIP/Vulkan, Strata HIP
and the official ROCm723 vLLM nightly were rebuilt/replaced at the pins above.
The existing SGLang gfx1100 branch has no newer commits. Official main was checked
at `fea48754de4b73276cad1062d6b5ae013288204d`, but cannot use the retained Radeon
GPTQ path unchanged; the tested fork and local verifier/MTP fixes remain.
[Exact upgrade and validation](../hardware/RUNTIME-UPGRADE-2026-10-18.md).
The promoted vLLM dev329 measured 130.61 / 72.69 t/s code/prose medians in
three warm short samples per task. These are not a controlled version A/B or
sustained full-context speed measurements.
The earlier [NVIDIA comparison/version audit](../hardware/NVIDIA-COMPARISON-RUNTIME-AUDIT-2026-10-18.md)
is a historical snapshot, not the current installed-version table.

AMD llama.cpp now uses a **worker-only systemd scope with `MemorySwapMax=0`**,
matching Strata's no-swap protection. The original MoE swap/low-RAM/VRAM-spill
guard remains enabled. This follows an observed guard stop during an unscoped
MoE load; global swap and unrelated processes are unchanged. An active systemd
user manager is required for Desktop/SSH launches; preflight rejects its absence
before stopping another backend. Do not remove the scope or disable the guard
to work around a model-loading failure. Obsolete rollback environments/builds are archived during October 19 maintenance
under `D:\LLM-ARCHIVE\MAINTENANCE\2026-10-19\obsolete-working-files.tar.zst`.
Restore the original relative paths from that private archive before following
older rollback instructions. The archive manifest and SHA-256 are kept beside it;
active runtime environments and selected compiled caches stay on Linux NVMe.

[Qwen 27B AMD speculative-decoding research](../hardware/QWEN27B-AMD-SPECULATION-2026-10-18.md)
traces the ~1,000 t/s headline to aggregate concurrency. Experimental ExLlamaV3
ROCm ports are research candidates, not installed profiles or exceptions to the
both-GPUs policy. FreeToken remains retired.

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

## Image/video generation models — October 18

The graphics collection now has **seven weight files / 70.40 GiB** in the
Shared SATA `Graphics-Models` directory: Qwen-Image 2.1 BF16 with BF16 encoder
and FP32 VAE; H3 fl2va pruned INT8 ConvRot with native NVFP4-AWQ encoder,
FP16 video VAE and FP32 audio VAE. Qwen's existing weights were losslessly
repacked; the H3 VAEs were moved intact. The H3 model/encoder replacements
were downloaded at pinned Comfy-Org revision
`e5eb578a89295337b8ff433a035929ce0279e0b6` and SHA-256 verified.

The old Qwen Q4/alternate encoders, H3 Q2/old GGUF encoders, embedding model
and original repacked shard copies were removed from the five Unsloth cache
repositories after verification. Net model-byte reduction: 22.78 GiB.
No model weights or partial downloads are included in Git; no shortcuts were
created. User media, app state, other LLM models and launchers are unchanged.

[Current inventory and limits](../hardware/UNSLOTH-MODEL-INVENTORY-2026-10-18.md),
[collection and Comfy path configuration](../graphics/README.md).
On Windows, use the corresponding `D:/Graphics-Models` path.

**ComfyUI is installed and both families passed generation.** Use the ComfyUI
Desktop/menu launcher or the `comfyui` PATH command; live logs stay in a visible
terminal. Web UI: `http://127.0.0.1:8188` (loopback; use SSH forwarding remotely).
Choose saved workflows **Qwen-Image 2.1 BF16** or **MiniMax H3 INT8**.
The runtime is `runtime/comfyui` in the Linux repository, isolated Python 3.12.14,
ComfyUI 0.42.0 at `8f04fd6ecf4a548937971e840af2a985529fab76`, Torch
`2.15.0.dev20260827+rocm7.2`, Kitchen 0.2.39, aimdo 0.5.6, frontend 1.55.18.

Denoiser runs on GPU 0; encoder/VAEs on GPU 1. Both-card activity was confirmed.
Direct component loaders use core APIs without the duplicate-encoder retarget
copy. This is staged placement, not TP. Qwen passed 512x512/40 base steps in
100.9 s total (~13 s denoising); H3 passed 608x352/39 frames/20 base steps in
232.4 s total (~29 s denoising), with coherent motion and finite 32 kHz stereo
audio. H3 used swap during loading on the 32 GB host. Models were unloaded after
the test and the server was left running. The existing LLM kill guard does not
terminate ComfyUI; run large graphics and LLM workloads separately.

[Validation details](../graphics/VALIDATION-2026-10-18.md),
[install/start guide](../graphics/INSTALL.md),
[exact versions](../graphics/runtime-versions.json).
No new weight quant or Turbo adapter was downloaded. Larger sizes, 124+ frame
video, I2V/editing, Turbo and Windows execution remain unvalidated. The earlier
Unsloth Q2 corrupt render is historical and not a controlled comparison with this
native INT8 pipeline. The seven real model files remain on Shared SATA.

## Strata and retired setups

Latest October 19 validation: **Strata Q3** `qwen3.8-flash-next-iq3_xxs`,
HIP 0.1.45/source `477ac13cbe8e`, both RX 7900 XTX, **262,144 native context**.
INT8 KV uses 32K GPU residency with full RAM backing; split 26, stage trimming,
overlap, MTP3/minimum probability 0.7,2048 prefill, six workers,13.5 GiB CPU expert
budget and 7/8 GiB reserve on GPU0/display GPU1. Same SATA assets; no RoPE scaling,
new quant or runtime update. Parking/adaptive swaps remain off.

Fresh **258,044 input / 256 output** retrieved all three markers and generated
code at native PP **775.1**, decode **39.9 t/s** (one sample). Short code/prose
medians: **72.2/48.0**, three warm runs/task. Tools/results and SSE passed;
worker swap/spill remained zero. [Results, methods and limits](../hardware/STRATA-CONTEXT-2026-10-19.md).
This restores the native window; it does not validate experimental contexts above 256K.

The worker retains its own `MemorySwapMax=0` scope. Every 0.5 seconds the router checks
both cards: below 3 GiB free twice or below 1.5 GiB once unloads only Strata.
It also checks host RAM, owned swap/spill and missing GPU telemetry. Guard
failures latch: chat requests return an error until explicit `/models/load` or
restart after freeing resources. The independent frontend/gateway and other
apps are preserved. This is sampled protection, not a guarantee against bursts.

The Desktop **Strata Q3** launcher and `llm-strata` start only the backend in a
visible terminal. DSH remains separate; **Local Strata** advertises native 256K.
Existing default and conversation model selections are preserved.
Router 30020 and private worker 30021 stay on loopback; the authenticated gateway
exports the enabled ID. No new weights were downloaded or copied to NVMe.

See [current upgrade checks](../hardware/RUNTIME-UPGRADE-2026-10-18.md),
[original 0.1.44.1 measurements and limits](../hardware/STRATA-DUAL-AMD-2026-10-18.md)
and [community sources](../hardware/STRATA-LOW-RAM-COMMUNITY-2026-10-18.md).
Admission now counts the complete streamed host KV copy:29 GiB physical,
22.852 GiB available before loading (13.5 GiB expert budget +3.352 GiB host KV +6 GiB
headroom). Swap does not count. Startup failure preserves unrelated applications.
The scoped watchdog and managed worker-only shutdown remain unchanged.

The additional 32 GB RAM candidate is inactive, retaining native 256K with 20 GiB
expert budget, both GPUs and the same KV/placement. Its 60 GiB physical /
29.352 GiB available gate and live validation still apply; adding RAM does not
activate it. `python3 hardware/check-strata-ready.py --ram 64` checks readiness.
[Procedure](../hardware/STRATA-AFTER-RAM.md).

Keep `GGUF-Models/Strata/models/IQ3_XXS`, `packs/iq3_xxs`, tokenizer and `mtp/rt`.
Q2's model/pack is removed; do not follow archived Q2 instructions. HyperQwen,
old CUDA environments/builds, GPT-OSS-20B/120B, Qwen 27B Q5, Bonsai 2 and old
Nemotron Lightning setups remain retired. Historical NVIDIA/Windows reference
snapshots remain in the public repo.

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

For the future 64 GB Strata candidate, validate both GPUs, residency, tools,
streaming and progressively larger actual prompts before enabling its larger
context. Preserve the Shared Windows-compatible packs. The old single-AMD
candidate and 4070/3060 CUDA layer splits are historical references.

The Windows handoffs were last validated on the **old NVIDIA hardware**. Their
Strata 0.1.44.1/CUDA 13.0, llama.cpp b11630, port 8081, Windows MagicDNS name and
36,919-token retrieval record describe that historical system. They do not prove
native Windows ROCm/HIP support or current dual-AMD readiness. The Windows agent
must inspect its actual hardware/runtime/profile before reuse. Keep Windows
binaries/environments/credentials separate from Linux; share compatible model
assets only. The original recipes, checksums, benchmark caveats and Windows
network administration instructions remain intact in the dated archive.

## Measurements and open work

October 19 original AMD benchmark refresh: the then-nine production profiles
were remeasured on llama.cpp `31288c9c`, repaired SGLang `f84475c`, vLLM dev329
and Strata HIP 0.1.45. Prefill and TTFT use three fresh ~8K marker requests;
code/prose decode and short TTFT use three warm timed requests/task. Production
contexts and placement are unchanged; these are not full-window tests. See
[the canonical current report](../hardware/CURRENT-AMD-BENCHMARKS.md) and
[results index](../hardware/results/README.md). Native/engine-phase prefill is
kept separate from API TTFT; previous speed tables are historical. The private
operational README was consolidated; its old dated notes remain in a private
archive. NVIDIA/Windows setup and benchmark history are preserved.
Muse returned all markers in 2/3 final probes within a 1,024-output-token
allowance; its failed trial remains in the medians. SGLang MTP/DFlash2 showed
about 5.29/8.32 GiB aggregate managed VmSwap; timed swap I/O was not recorded.
Do not claim universal retrieval success or zero paging. Actual corpus token
counts differ by tokenizer (Muse ~6.35K, Nemotron ~7.92K, others ~8.19K).
[Public benchmark report](https://github.com/Biegle-W/local-llm-public/blob/main/linux/hardware/CURRENT-AMD-BENCHMARKS.md).

The [benchmark/context history](../hardware/BENCHMARK-HISTORY.md) is the
current ten-profile index and dated update ledger. It records allocated context
separately from actual input tested, PP separately from TTFT, exact measured
builds and validation-only updates. The three llama.cpp 256K MoE allocations have
63,911-token retrieval evidence on the older build; full 256K is untested.
The current nine-profile batch measured vLLM dev329 code/prose at 131.05/73.31
t/s and Strata 0.1.45 at 71.50/48.46, using 256-token caps. Earlier tuning batches
on those builds recorded 130.61/72.69 and 72.2/48.0 respectively with their own
workloads; Strata used a 512-token cap. Do not merge those samples.
Nemotron Super IQ3's separate ~8K-input trials measured 14.16/16.32 t/s at 32K
context, with 95.75/97.13 native PP and 84.699/83.521 s TTFT. These are not
short-prompt TTFT/decode tests. All maintenance documentation uses saved results.
The [published history](https://github.com/Biegle-W/local-llm-public/blob/main/linux/hardware/BENCHMARK-HISTORY.md)
is also accessible to clients reading this handoff directly from Shared.

The original consolidation did not rerun benchmarks. The later Q4 replacement
measurements are in the report above. The maintained README contains
all model results with dates/hardware/methods. Selected earlier Qwen tuning measurements (historical, not the current batch):

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

Earlier October 19 public documentation cleanup (before the fresh benchmark batch): the
[public README](https://github.com/Biegle-W/local-llm-public#amd-latest-setup-and-results)
now presents two hardware result sets: latest dual-AMD setup and archived dual-NVIDIA.
Each model/backend has context, prefill, TTFT and decode fields, with measured
build/date, missing metrics and older-build timings labeled. Short and long-input
workloads are separate. The old public README is preserved in
`linux/hardware/README-ARCHIVE-2026-10-19.md` in the public repository; the dated
benchmark ledger retains all intermediate experiments. No benchmark, runtime,
profile, launcher or client endpoint changed during this documentation task.

| Symptom | Action |
|---|---|
| Terminal closes immediately | vLLM now preserves startup errors; inspect its launcher log. Check per-GPU free VRAM and runtime probe. |
| HTTP 401 | Configure the actual private Linux API key, not `local-strata`. |
| HTTP 404 / unknown model | Copy an exact enabled ID from `/v1/models`; do not use Q2, HyperQwen or retired IDs. |
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
run during consolidation. `python3 -B network/check.py` derives the expected catalog and contexts from enabled
local profiles and checks authentication, health and retired-Q2 rejection without
loading models. It writes nothing unless `--output` is supplied. `--generate`
remains an explicit optional generation test; it was not used during maintenance.

The latest October 18 authenticated API/generation recovery was checked from
Linux loopback. Earlier host self-access checks covered LAN/Tailscale; a separate
remote device must still test its own network/ACL path. The October 18 MoE
update ran bounded local model validation and refreshed catalogs;
no driver, BIOS, firewall or credential changes were required. The original
consolidation check above remains a timestamped historical observation.

## Where the originals went

`LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/` contains all nine pre-consolidation originals
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

## October 19 maintenance and launch paths

`llm-llama`, `llm-sglang`, `llm-vllm`, `llm-strata`, `dsh`, `turnstone`,
`comfyui` and `llm-upgrade-check` remain the supported PATH commands. Inventory
now targets two 24 GiB Navi31/amdgpu devices without requiring NVIDIA software;
it reports every PCI path so internal GPU x16 links are not mistaken for slot
bandwidth. A successful inventory is not an inference or P2P validation.

The separate Strata GUI is restored to
`/opt/appimages/Strata-0.2.0-beta-linux-amd-rx7900.AppImage`; its menu
entry points to the actual file. It was not launched and has its own worker and
settings. Keep the managed Strata Q3 launcher separate. [Menu details](../launchers/STRATA-APP.md).

[Maintenance record and documentation index](../hardware/WORKSPACE-MAINTENANCE-2026-10-19.md)
describes the archive and checks. Active models, candidates, profiles, credentials,
frontend data and source pins remain unchanged. The private client guide is preserved.
