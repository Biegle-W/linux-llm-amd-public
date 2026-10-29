# Owner-requested model pause — October 29, 2026

The owner paused the five routes below until explicitly reporting that more RAM is available. The pause is durable in model configuration. RAM detection alone does not resume them. Existing weights, model settings, source/build pins and rollback evidence are retained.

| Paused route | Model ID | Previous blocker |
|---|---|---|
| Ornith / llama.cpp | `ornith-1.5-122b` | Retained normal profile needs 60 GiB OS-visible physical RAM |
| DeepSeek XS / Maya | `deepseek-v4.1-flash-1017-maya` | Retained profile needs 60 GiB physical / 52 GiB available RAM; experimental 32 GB tiers remain unselected |
| DeepSeek XS / Strata | `deepseek-v4.1-flash-1017-strata-xs` | Same retained RAM requirement; experimental 32 GB tiers remain unselected |
| Qwen Flash Next / Strata | `qwen3.8-flash-next-iq3_xxs` | Selected 32 GB profile needs 25 GiB available RAM; latest candidate and rollback-load attempts were admission-blocked |
| Qwen27B / SGLang DFlash2 | `qwen3.8-27b-sglang-dflash2` | Qualification was stopped by the VRAM-residency guard; actual eviction and RAM capacity as the cause are unproven. Its vLLM route remains enabled |

Seven working profiles remain enabled: **Empero, Super, Flint, Qwen27B/vLLM, Bolt/vLLM, Sage/vLLM and GLM/Maya**. All five paused routes are absent from both the live hub and authenticated network API catalogs. Direct launchers reject disabled selections before backend handover. Ornith retains its independent manual source/build pin; its original runtime model list remains intact, with an explicit pause applied separately.

The 03:00 full-registry nightly timer and recovery service remain enabled. Engines with no enabled profiles (Strata Qwen, separate Strata DeepSeek and SGLang) skip upstream checks, builds and GPU qualification. Maya tests only GLM; llama.cpp tests Empero/Super/Flint. vLLM retains its existing Bolt manual hold, qualifying only Qwen/Sage globally. No timer or unrelated schedule changed.

**84 focused CPU checks pass in each maintained checkout**, including explicit pause rejection before device/worker checks, no launcher handover/spawn for a fully paused backend, no nightly version fetch/build/GPU work for a fully paused engine, catalog filtering, llama manual holds and existing admission/router guards. Three older tests now use explicit enabled fixtures rather than assuming live Strata/SGLang activation. Live hub and authenticated API catalogs each show exactly seven profiles. No inference trial or service restart was needed.

Resume only after the owner's RAM notification, under the existing physical/available-RAM, VRAM, ownership, thermal, swap and performance guards. That notification does not bypass required model/runtime qualification. Do not auto-enable experimental profiles, promote a candidate, or replace retained pins merely because RAM is detected. Preserve the exact disabled configuration preimages and prior results until a reviewed resume is complete.

Strata's latest failed candidate and rollback-load attempt remains documented in [the retry report](STRATA-RETRY-SAMPLER-2026-10-29.md). Source/build restoration is byte-verified; a fresh restored-build load is still unverified. The owner pause supersedes its earlier instruction to retry once RAM becomes available. No pending task-owned GPU worker, lock or provisional installation remains.

**SGLang residency clarification — October 29:** The two graph-disabled attempts were terminated by the monitor's `vram_spill` rule after `drm-total-vram - drm-resident-vram` reached **121.273 MiB**. Both worker logs reported **6.00 GB available GPU memory** and completed application startup, before health/qualification finished. The graph-disabled and smaller-buffer attempts retained at least **17.07 / 17.61 GiB available host RAM**. These are guard stops; the saved evidence does not establish a physical-RAM admission failure or GPU out-of-memory failure. The [kernel counter definitions](https://docs.kernel.org/gpu/drm-usage-stats.html#memory) allow total buffers to include backing storage that is not yet instantiated, so this difference alone does not prove GPU-to-host eviction. Actual eviction versus transient/lazy-allocation accounting remains unresolved; the identical difference across both retries is a reason to audit the residency check, not proof of its cause. Additional system RAM is not an established fix. Original failure flags remain unchanged, no guard was relaxed, and no GPU trial was repeated. The owner pause remains in effect.
