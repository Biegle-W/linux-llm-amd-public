# Sabrent model relocation to the system drive — November 2, 2026

All remaining Sabrent data-volume files were copied and fully SHA-256 matched before the originals were removed. **148 files / 176,775,668,158 logical bytes** were preserved. The Sabrent data volume is empty and cleanly unmounted; its boot-mount entry is removed. Both facts were independently verified after the owner ran the authenticated cleanup. The system filesystem has about **229 GiB available / 73% used** after relocation (rounded filesystem figures).

| Preserved content | Files | Logical bytes | Destination |
|---|---:|---:|---|
| Maya weights, packs and metadata | 16 | 97,645,915,182 | `/opt/local-llm/models/streaming/Maya` |
| Strata GGUF expert backing, support and draft assets | 38 | 79,128,921,409 | `/opt/local-llm/models/streaming/Strata` |
| macOS volume metadata | 94 | 831,567 | Separate local preservation directory, outside the model tree |

`.Spotlight-V100` contains macOS Spotlight indexing data; `.fseventsd` contains macOS filesystem-event records. These are prior Mac volume metadata, not model weights or Linux engine dependencies. They were preserved separately before their source folders were removed.

## Runtime paths and verification

Configured Maya/Strata profile, tokenizer, GGUF and installer paths now use `models/streaming/` on the system NVMe. Two small copied metadata files contained absolute paths and were rebound after every original/destination hash matched. Maya's configuration proof was rebound to the new paths only after checking its original fingerprint; the binary and numerical/runtime settings were preserved. No engine/model restart or new inference occurred.

`shared_storage.STREAM_MODELS` now resolves to the checkout's `models/streaming` directory. Only sharedSATA1 remains in external mount discovery. Missing system streaming storage is refused; the helper does not mount the retired Sabrent or download replacements. The login mount unit description and Maya installer guidance are updated. Historical export sanitization retains the old mount-path constant; it does not admit or mount that volume.

- 41 CPU checks pass in each repository, covering model storage, Maya and Strata lifecycle behavior.
- Actual read-only Maya source/binary/config binding and before-handover RAM checks pass with relocated paths; Strata required weight assets are present.
- Every source/destination file passed full SHA-256 equality before cutover. Before source removal, the exact source manifest, unchanged destination sizes/timestamps and small-file/relocated-metadata hashes were rechecked.
- Source removal ran under idle, startup and GPU ownership guards with no backend listener or open source file detected. All migration-owned locks are released; no active migration copy or inference job remains.

Both DeepSeek routes remain retired/disabled, Strata Qwen remains paused, and runtime/source pins, numerical settings, DSH defaults, memory/swap/thermal/ownership guards and the paused updater are preserved. This is storage verification, not a new GPU qualification or speed result. Historical Sabrent benchmark paths remain dated evidence; this relocation supersedes their storage location.

## Verified removal preparation

The owner ran the authenticated administrator cleanup. The exact Sabrent boot-mount entry was removed from `/etc/fstab` after a local backup, the system manager was reloaded, and the data partition was cleanly unmounted. Independent checks confirm the boot entry and data-volume mount are absent. The earlier unauthenticated UDisks refusal is resolved; no forced unmount occurred. The separate small Sabrent partition remains unmounted and was not changed. **Shut down the PC before physically removing this internal NVMe.** Linux root and EFI boot partitions are on the separate system drive. Physical removal has not been observed.

Static/checkpoint storage remains sharedSATA1. New and retained streaming packs use system `models/streaming/`; retain the below-90% storage admission rule. No additional download, RAM-hold removal or GPU trial is authorized by this relocation. No migration job or software-cleanup blocker remains. Next action: shut down before physically removing the Sabrent; do not remove it while the PC is running.
