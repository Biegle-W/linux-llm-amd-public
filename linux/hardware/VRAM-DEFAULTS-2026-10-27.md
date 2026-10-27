# VRAM-only defaults and selectable Flint — October 27, 2026

At the user's request, **Empero and Sage now default to all-GPU weights**, and
**Flint is selectable** in the normal llama.cpp catalog, DSH settings and
network API. Both RX 7900 XTX cards remain required. The retained source is
llama.cpp `2280f0fd163b03d4331d49e08460f66502e35854` / ROCm 7.2.3; no engine,
quantization, context, weight location, global DSH default or swap policy changed.

| Model API ID | Context | Placement / loading | MTP / vision | Batch / ubatch |
|---|---:|---|---|---:|
| `empero-qwen3.8-35b-a3b` | 262,144 | VRAM-only / DIO | MTP3 | 512 /512 |
| `sage-a1.5` | 65,536 | VRAM-only / DIO | MTP3; existing projector retained | 4096 /4096 |
| `flint-40b-a2.5b` | 32,768 | VRAM-only / DIO | Off; 128-token reasoning budget | 4096 /4096 |

`--n-gpu-layers 99`, `--fit off`, two-device 1:1 layer split, GPU embedding placement,
`--n-cpu-moe 0` and `--moe-cache-mib 0` keep model/expert weights on GPUs. DIO is a load
method, not SSD expert streaming during inference. Host staging/tokenization
still need RAM. Empero's smaller batch is the already-tested alternative to the
4096-token candidate that failed the host PSI gate. Sage retains its existing
sampling defaults and vision projector; no single-card deployment is claimed.

## Explicit placement admission and worker ownership

`dsh/moe-offload.json` remains the compatibility filename for both placement
plans. An explicit `memory_placement: vram_only` is required; deleting CPU
placement from an unmarked MoE still fails closed. Validation checks the catalog
label, zero CPU expert bytes/layers/cache, both GPU devices, fixed placement,
context, prompt batches and DIO preset against the plan. Super and Ornith retain
their CPU-backed plans and their original physical-RAM admission requirements.

VRAM-only admission requires **12 GiB OS-visible /7 GiB available RAM**, at least
21 GiB free VRAM per card before load, and the existing running RAM/VRAM guards.
The native worker tree gets **4 GiB memory.high /5 GiB memory.max /MemorySwapMax=0**.
The existing owned cgroup is pinned before exec; the router now requires exact
readback of those values before the payload gate opens. A real CPU test proves
that a mismatch cannot execute the payload. Existing low-churn limits, zero
sampled dedicated-VRAM spill and stricter engine scopes remain unchanged.

A compatible VRAM-only switch reuses the bounded worker. Switching to a
CPU-backed profile changes worker mode, but its physical-RAM requirement is
checked before stopping a working GPU model. On the current14.83 GiB host,
requesting Super is rejected while the usable loaded Flint model remains ready.
There is no hidden CPU weight fallback and no lower VRAM reserve.

## Normal-launch and API qualification

The normal `dsh/start-backend-terminal llama` → launcher → router → owned worker
path is used. Requests pass through the live hub and authenticated gateway;
there is no test-only model/profile override. The catalog has **12 profiles**,
including five llama.cpp choices, and only one model is loaded at a time.

All three pass arithmetic, JSON, tool-call round trips, authenticated SSE with
usage, context readback, long marker retrieval, full-history follow-up and an
actual continuous request loop of at least 35 seconds. Every live native process
is checked before/after against the exact bounded cgroup. Sage also passes the
existing synthetic red-shape/blue-circle image probe. The native UI returns 200
and its live model list includes Flint. DSH's saved global default stays Strata Q3.

| Model | Actual long input tokens | History input tokens | Result |
|---|---:|---:|---|
| empero-qwen3.8-35b-a3b | 257,996 | 258,044 | Passed |
| sage-a1.5 | 62,009 | 62,057 | Passed |
| flint-40b-a2.5b | 29,986 | 30,015 | Passed |

The launch/load/test/shutdown collectors have valid worker/host telemetry, zero
sampling/enforcement errors, zero worker swap and zero sampled dedicated-VRAM
spill. The bounded low-churn inference window is complete. Temperatures and
host swap I/O remain in the numeric record. All task-owned workers shut down
cleanly after validation; frontends and unrelated applications are preserved.

**65 relevant CPU regressions pass per checkout:** explicit GPU/CPU placement,
staging admission, incompatible-target preservation, strict scope readback and
payload gating, all five router guards, model-hub/catalog and saved DSH defaults.
CPU tests are separate from the real LLM qualification above.

The earlier zero-reasoning Flint candidate correctly retrieved all three 30K
markers but answered a subsequent middle-marker question incorrectly, both
cached and uncached. A 128-token reasoning budget corrects that original question while
retaining tools/JSON/SSE and all guards; it is the selected default. Earlier 47 tokens/s
non-thinking timings remain a separate experiment. No prompt-cache workaround
was applied. The native UI retest uses browser-standard gzip headers: an
identity-only HTTP client had received 415 from the embedded compressed UI.
The launcher shell can exit before child cleanup finishes; an explicit later
no-worker receipt and the final graceful-launcher check prove cleanup.

Long markers/history and synthetic tools/vision do not establish general model
quality or sustained full-window throughput. Native UI serving/catalog checks
are not a new pixel-based browser test; host-self API access is not a remote-peer
test. Earlier isolated rates remain in the [trial report](STORAGE-VRAM-2026-10-27.md),
with no new historical CPU-offload A/B speedup claim.

The additional catalog-route check found the configured LAN address unreachable
(`No route to host`); no network setting was changed. Authenticated loopback and Tailscale
checks both returned12 profiles including Flint. The normal
LLM integration above used authenticated loopback access.

## Updated categories

- **VRAM only:** Empero, Sage, Flint, Qwen27B (SGLang/vLLM), Nemotron Bolt.
- **CPU RAM MoE:** Nemotron Super IQ3, Ornith-1.5-122B.
- **SSD stream:** Strata Qwen3.8-Flash-Next IQ3, GLM Maya-S v2, DeepSeek XS
  (Maya/Strata). Strata's bounded RAM/GPU caches sit above an active SSD cold/PLE tier.

There are **10 weight sets /12 API profiles**. No model was downloaded or copied;
the total stays 776.24 GB including associated files and the small module cache.
The Super backup, GLM S24 rollback and DeepSeek S remain retired. Nightly engine
updates remain paused.

[Curated activation evidence](results/vram-defaults-2026-10-27.json) ·
[Current model storage](MODEL-STORAGE-INVENTORY.md).
