# System storage cleanup and remaining staged-weight relocation — November 3, 2026

The owner requested removing unused builds, old environments and caches while preserving everything needed by current models/engines, and putting non-streaming weights on SATA. **About 251.4 GB reclaimed on the system drive:** 230.3 GB from unused payload/cache cleanup plus 21.1 GB of H3 staged weights moved to SATA. The measured system filesystem is **43% used, with approximately 481 GiB available** after the work. These are filesystem figures, not an inference-performance result.

## Removed and retained

| Removed | Scope |
|---|---|
| Old environment/build roots | 79 reviewed directories, including 13 unused virtual environments and 49 old build directories |
| Remaining downloaded SDK/wheel and compiled payloads | 113 additional files; source/evidence archives preserved |
| Inactive compiler temporaries | One historical compiler-temporary directory; available diagnostic sources retained separately |
| Package caches | Unused uv archives/cache indexes, pip cache and old Maya download/temp cache; installed environments retain their own files/hard links |

Current and held engine copies remain: normal vLLM, Bolt's separately pinned dev435 environment, SGLang, ComfyUI, main/held llama.cpp builds, Maya and both Strata builds. The selected ROCm 7.2.3 SDK, private host compiler, standalone Python, RCCL override and current JIT/compiled-kernel caches are retained. Installed Unsloth application/engines, user media, model assets, credentials and client state are preserved. No system package, service, model enablement, RAM hold or paused schedule was changed.

The normal global vLLM remains `0.33.0rc1.dev229+g3966924d5.rocm72`; Bolt remains `0.32.1rc1.dev435+gc50aca144.rocm72`. Two already-stale installed vLLM CLI shebangs were rebound to their respective current environment's Python; their script bodies and package/runtime settings are unchanged. Obsolete separate rollback/trial environments are gone; use the preserved current/pinned copies rather than deleted historical paths.

Raw benchmark logs, result JSON, top-level experiment scripts and source patches remain. Before build deletion, 357 small compiler/environment records were compressed into a local evidence archive; inactive-compiler source snippets and a file manifest were also saved. Rebuilding a discarded trial environment requires fresh preparation from its preserved source/pin records; no discarded candidate becomes qualified by this cleanup.

## Weight placement

All retained non-streaming LLM weight sets and RAM/VRAM-loaded graphics weights already use SATA. The remaining two derived H3 TP2 shard files plus their pair manifest—**3 files / 21,060,828,022 bytes**—now reside at:

`/mnt/shared/Graphics-Models/experimental/h3-hoststage-20261028/shards`

Every source/destination file passed full SHA-256 equality, and both shard hashes also match the original pair manifest pins. Only then were the system-drive originals removed. The [staged-weight registry](../graphics/staged-weight-locations.json) records the location and hashes. The candidate remains **SEALED-BUILD-ONLY / runtime_allowed=false**; no normal workflow uses these shards, and any future inode-bound trial admission must be re-sealed for the new files. Historical request timings used the old location and do not measure current SATA load time.

The current streaming weights stay on system NVMe under `/opt/local-llm/models/streaming/Maya` and `.../Strata`. These read expert data during inference and are intentionally retained there. Qwen main/DFlash2, Empero, Flint, Ornith, Bolt, Sage and Super W4A16 remain on sharedSATA1; no weight redownload or new model setup was performed. Normal image/video model paths remain sharedSATA1 `Graphics-Models`.

## Verification

- Audited 30,973 kept-tree symlinks. The only links into evicted archive stores were 1,051 disposable package-cache indexes; no external installed-runtime dependency was found.
- Protected-file comparison passes for **526,274 files/links**, including current engine sources/environments/SDK/compiler; **18 native-binary/profile hashes** are unchanged.
- All **six native engine dependency resolutions** remain unchanged with no missing library. All **four current Python/Torch environments** pass a CPU import/tensor check without initializing a GPU context.
- **57 focused CPU checks pass in each checkout**, covering storage/model-path preflights, profile behavior, runtime pins and GUI activation. The active model catalog/holds and numerical settings were preserved through the fingerprint checks.
- Both cleanup phases and weight-source deletion required idle/startup/GPU ownership guards and no live backend/open payload file. No inference or desktop service was stopped or restarted. No GPU inference or new performance benchmark was run.

No active cleanup/copy job or task GPU reservation remains. Both AMD repositories and the retained Shared runtime-handoff copy are maintained. Next action is normal use; no model hold is lifted and the engine updater remains paused.

[Curated cleanup results](results/system-storage-cleanup-2026-11-03.json).
