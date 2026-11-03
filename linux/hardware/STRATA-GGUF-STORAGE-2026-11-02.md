# Strata GGUF expert backing and storage cleanup — November 2, 2026

The owner requested one weight copy suitable for the latest Strata. The original Qwen Flash Next GGUFs are retained as the expert backing. The duplicate pack `experts.bin` and unused MTP conversion intermediates are removed. **49.018 GB reclaimed; Sabrent free space is 823.060 GB.** Sizes are decimal filesystem figures measured after cleanup.

## Retained layout

| Directory within the saved Strata model area | Allocated GB | Role |
|---|---:|---|
| models | 76.749 | Original GGUF shards (75.840 GB logical) plus vision projector and small metadata |
| packs | 1.550 | Required dense/support data, native expert offsets and index/tokenizer metadata; no copied expert blob |
| mtp | 0.825 | Actual `mtp/rt` draft runtime pack plus provenance notes |
| DeepSeek metadata | 0.010 | Small historical metadata only; old DeepSeek weights remain removed |
| Total | 79.134 | One main expert weight backing plus required runtime/draft support |

The retained original GGUFs contain the PLE table and expert tensors. The approximately 1.54 GB dense/support pack and MTP runtime are not another complete model copy. This cleanup does not remove required support data merely to eliminate directories.

## Loader review and verification

The retained installed engine/source is still `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`; its binary SHA-256 is `e2734244e6389ac6c549abff76a1ee96529c7f91398503fb7b4e8c909b001f6d`. Its `FileExpertSource::open` maps GGUF tensor spans when native metadata and `--native` are present and the copied blob is absent. The selected profile already uses `--mmap-experts` and `--native`.

The latest stable release checked was [Strata v0.2.9](https://github.com/Niko1221/Strata/releases/tag/v0.2.9), commit `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`. Its [expert loader](https://github.com/Niko1221/Strata/blob/c62d5e3a15b40ea51c96aae9e8d36928965f53ab/src/core/expert_source.cpp) retains the same GGUF backing path. Latest source compatibility is reviewed, not a claim that this newer engine was installed or GPU-qualified on this host.

Before deletion, a CPU inspection verified native metadata types, offsets, tensor bounds and all 48 layers with 512 experts each. Every byte of the 42,912,972,800-byte copied expert blob was compared against the matching original GGUF gate/up/down slices; all matched. This was integrity checking, not model inference or a throughput benchmark. The existing profile uses `mtp/rt`; the separate raw tensor extraction and intermediate MTP GGUF are conversion inputs, not required runtime inputs.

The maintained admission code now requires the native metadata and original GGUFs in native mmap mode rather than insisting on the redundant expert blob. Non-mmap mode retains its copied-blob requirement. Dense, PLE, tokenizer and MTP dependencies remain mandatory and nonempty. Four CPU asset-dependency tests (including each missing/empty dependency and non-mmap behavior) and eleven existing memory/owned-stop guard checks pass in each repository. Post-removal checks confirm all selected runtime assets remain present.

## Preserved state and next action

The Qwen/Strata route remains owner-paused. No runtime upgrade, model load, inference test or schedule was activated. RAM/VRAM floors, budgets, context, pins, ownership and swap policies are unchanged. Previous integration validation remains historical evidence; the changed GGUF backing is marked pending a new short harness check after actual RAM installation and owner instruction. v0.2.9 engine review/qualification is separate from this storage cleanup.

Do not regenerate the duplicate expert blob or MTP intermediates during routine startup. Retain configuration/provenance rather than copied payload rollback files; the duplicate can be reconstructed from retained originals if a separately reviewed rollback needs it. Before future activation, verify actual capacity and loader compatibility, run only one short DSH tool-call round trip, then verify owned unload.

[Structured results](results/strata-gguf-storage-2026-11-02.json) · [Post-RAM roadmap](P2P-96GB-ROADMAP-2026-10-30.md)
