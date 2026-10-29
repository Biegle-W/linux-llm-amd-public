# Split llama.cpp qualification — October 29, 2026

The owner authorized updating llama.cpp for Empero, Super and Flint while retaining the old source/build only for the normal Ornith profile. Qualification of current upstream `eb4e244be77a906a183cd4a00fd51d9ad3200955` started through the existing guarded updater at 13:30 EDT; **no new llama.cpp promotion is claimed yet**.

Ornith is the normal llama profile blocked by its unchanged 60 GiB physical-RAM requirement on this 30.56 GiB host. That is an admission limit, not evidence of incompatibility with a newer engine. The earlier isolated 32 GB placement remains separate and is not promoted or rerun.

## Durable split

Ornith has an explicit `source_overrides` entry in `dsh/llama-runtime.json` with an independent source directory, exact `source_commit` and matching `manual_runtime_pin`: `2280f0fd163b03d4331d49e08460f66502e35854`. Its same-source HIP build completed at its permanent location; ELF runtime search paths do not depend on the global build directory. Its loader source-pin verification passes. This preparation did not load Ornith or qualify its RAM-held normal profile.

The updater validates each explicitly held source and binary before an update, excludes only valid manual holds, and requires all remaining models in both baseline and candidate records. Candidate installation clears ordinary qualification overrides so Empero, Super and Flint actually use the new global source, while preserving Ornith's manual hold. Rollback restores the exact previous JSON and global source/build. Invalid or missing held builds and an empty unpinned catalog fail closed. Nightly updates retain this exception until the owner removes it after separate qualification.

The publisher reports the held source alongside the global source and exports a sanitized example pin. **52 CPU regressions pass in each checkout**, including eight focused hold/publication checks plus source routing, ownership, complete coverage, lifecycle memory and rollback checks. Profiles, quantization, contexts, memory/VRAM guards and the 03:00 full-registry timer remain unchanged.

## Qualification status

The first three-model baseline passed Empero and Super, then stopped before candidate installation because Flint failed marker retrieval. The shared client allowed only 64 total output tokens despite Flint’s unchanged 128-token reasoning budget; earlier successful Flint marker samples used 145 tokens. The failed run and measurements are retained. A follow-up will use the repaired client under the same standard gates. The first job exited successfully, cleared its GPU reservation and never installed a provisional candidate. The temporary manual service override was removed; the next 03:00 timer retains the full registry. Earlier completed updater measurements/logs were archived before any stage reset. The vLLM promotion is already complete: Qwen/Sage use dev229; Bolt remains on its separate dev435 pin. Strata's prior rejection and verified rollback remain; no Strata retry is included.

## Marker request repair

The client now reads the selected preset’s bounded reasoning budget and adds the same 64-token answer allowance: Flint gets 192 total output tokens; Empero and Super keep 64. The model’s reasoning budget, weights, quantization, context, prompts and all three required markers are unchanged. Missing/unbounded reasoning budgets fail closed. Failed trials are saved before assertions, including finish reason and whether visible content was produced; no raw response text is published. **61 CPU regressions pass in each checkout**, including five new reasoning/evidence checks and the original memory-window checks. This repairs a client cap; it does not treat the failed baseline as a model incompatibility or relax any promotion gate.
