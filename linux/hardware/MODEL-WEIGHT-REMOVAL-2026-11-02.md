# Owner-requested weight removal and replacement staging — November 2, 2026

**Super IQ3 and old DeepSeek weight backing removed: approximately 341.625 GB reclaimed. Sabrent model volume now has 774.042 GB free.** Figures are decimal filesystem bytes, sampled immediately after deletion; no health/fault report is included.

| Removed payload | Allocated bytes before removal | Next route |
|---|---:|---|
| Nemotron Super IQ3 GGUF weight set | 59,764,506,624 | Existing Super mixed INT4/INT8 checkpoint, vLLM first, after RAM admission and qualification |
| DeepSeek Maya-XS plus shared Maya-S components, DSpark and vision backing used by Maya/Strata | 281,859,063,808 | Latest compatible Unsloth Q1 checkpoint and new engine-specific packs after RAM upgrade |

The owner explicitly requested removal of these old weights to prepare for the replacement routes. This supersedes earlier instructions to retain this particular IQ3 fallback and the old shared DeepSeek weight dependencies. No payload backup is retained by this task. Configuration preimages, manifests and historical results remain; restoring the old models would require reacquiring their weight files.

## Runtime state

- Super IQ3 is disabled in the catalog and paused runtime list; its native HIP preset stanza is removed. No automatic llama.cpp fallback is selected. The separately stored Super INT4 checkpoint is retained and is not advertised as working or enabled.
- Both DeepSeek routes remain disabled, now explicitly marked as missing weights. Their old local-validation status is retired; new Unsloth weights cannot inherit the old pack validation.
- Small saved DeepSeek pack metadata/configuration remains for reference; it cannot run without the removed backing files. GLM/Maya, Qwen/Strata weights and all unrelated models are preserved.
- Seven enabled routes remain: Empero, Flint, Qwen 27B SGLang, Qwen 27B vLLM, Bolt, Sage and GLM/Maya. Generated DSH settings are refreshed while preserving unrelated providers/history. The live hub catalog confirms the same seven routes without a model load or service restart.
- All guard values, runtime build pins, other RAM holds and the paused updater remain. No task GPU ownership or reservation remains.

## Replacement preparation

**Super:** retain the existing W4A16 Merlin mixed INT4/INT8 checkpoint and the [previous vLLM source/admission evidence](SUPER-INT4-ENGINES-2026-10-31.md). After RAM is actually installed and the owner requests execution, recalculate physical RAM/VRAM/cache/workspace admission, then use only a short DSH tool-call round trip and verified unload. Do not enable an unqualified profile or infer full-model compatibility from earlier small-kernel checks.

**DeepSeek:** follow the [post-RAM Unsloth Q1 queue](P2P-96GB-ROADMAP-2026-10-30.md). Refresh the latest compatible revision, choose Q1_S/Q1_M after format/capacity review, verify shard hashes and tokenizer/engram/draft requirements, and build fresh engine-specific packs/manifests. The old payload is now absent; preserve configuration and metadata references rather than assuming an on-disk rollback exists. New non-streaming checkpoints use SATA1; new streaming packs use the system NVMe under `models/streaming/`. Review each engine's currently restricted path validation before adding those packs. Every drive must remain below 90% used; no download or conversion starts now.

One short actual harness check per admitted requested route, owned unload before switching, no long/full-context benchmark. Historical speed/test results remain dated evidence, not claims about currently installed deleted weights.

## Verification

Both target directories were checked for additional hard links and open same-user file mappings/descriptors before removal. Idle activity/startup/GPU ownership locks protected catalog edits and deletion. Full file metadata manifests and configuration preimages are private. Target payload directories are absent, old Super is absent from the live hub, normal placement validation passes, and seven focused provider/configuration checks pass per checkout. No GPU test was required or run. Original benchmark samples were not changed.

[Curated results](results/model-weight-removal-2026-11-02.json) · [Short-check plan](FUTURE-MODEL-TEST-PLAN-2026-11-02.md)
