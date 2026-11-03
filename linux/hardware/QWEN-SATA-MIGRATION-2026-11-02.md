# Qwen main checkpoint and DFlash2 draft moved to SATA — November 2, 2026

The owner requested moving these VRAM-resident models off the system NVMe. Both now live on sharedSATA1. **29 files / 21,335,488,549 logical bytes** were copied and fully SHA-256 matched before the originals were removed, reclaiming **21,335,621,632 allocated bytes (21.336 GB)** on the system filesystem. No duplicate or symlink was left at the old locations.

| Content | Files | Logical bytes | Current directory |
|---|---:|---:|---|
| Qwen3.8 27B W4A16 AutoRound GPTQ | 17 | 20,054,848,547 | `/mnt/shared/vLLM-Models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` |
| Qwen DFlash2 W4A16 draft | 12 | 1,280,640,002 | `/mnt/shared/vLLM-Models/drafts/Qwen3.8-27B-DFlash2-W4A16` |

SGLang and vLLM share the main checkpoint. SGLang uses the separate DFlash2 draft; vLLM retains its existing MTP strategy. Only disk placement changed. These selected routes keep model weights in VRAM after loading; SATA can change cold-load/switch time, but no new load-time or throughput measurement was made.

## Engine paths and safeguards

Both normal launchers, router defaults and the SGLang main/draft profile now use SATA. Qwen's vLLM profile explicitly records the main path for mount preflight. Standalone launchers verify the required model drive before starting. SGLang checks both main and draft paths before replacing an owned worker; vLLM's storage check also precedes worker replacement. The mount helper recognizes both operational and sanitized example mount roots. Unknown/malformed draft paths fail closed. The tokenizer lookup in the benchmark helper reads the configured main path; the inactive speculative test helper uses the new paths. Historical result snapshots retain their dated source paths.

Full SHA-256 equality was established for every file. Source size/mtime and verified destination size/mtime were rechecked before original removal, with small-file hashes also rechecked. Cleanup required exact manifests, idle/startup/GPU ownership protection, no live backend listeners and no open source files or mappings detected. Every migration-owned lock is released and the copy job has finished.

33 CPU checks pass in each checkout, including storage admission, SGLang profile behavior and runtime-pin preservation. New regressions cover a single SATA check for main/draft, malformed or unknown draft refusal, sanitized mount-root handling and leaving an existing worker untouched when storage admission fails. Both launcher shell checks and actual read-only SATA/path admission pass. Model and draft index/weight files are present at the destination. No GPU inference or engine restart was required or performed.

Contexts, quantization, speculative strategies, cache allocations, runtime/source pins, guards, defaults, disabled-model/RAM holds and the paused updater are preserved. No boot-mount change is needed: sharedSATA1 already has the existing headless mount configuration. The system drive retains the Maya/Strata streaming assets. Sabrent remains retired; no dependency was reintroduced.

No remaining migration job or software step. Any later runtime test follows the owner-requested short harness check and owned unload policy; do not repeat GPU tests solely for this storage record.
