# Bolt checkpoint storage move — October 26, 2026

## Completed and verified

- Relocated `Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` from sharedSATA2 to
  `sharedSATA1/vLLM-Models/` using a staging directory and a maintenance lock.
- Verified the source and destination volume UUIDs, capacity below 90%, and absence
  of inference workers before copying. Every one of the 33 files matched SHA-256:
  43,645,320,930 logical bytes (40.65 GiB). All nine shards referenced by the
  checkpoint index exist. Only after verification was the original model directory
  removed. No other model or unrelated file was deleted.
- Bolt's active profile and standalone launcher use SATA1, including the reasoning
  parser inside the checkpoint. Configured-volume discovery no longer requires or
  attempts to mount SATA2. New static model placement uses SATA1; streaming packs
  still use system NVMe, nothing new goes on Shared NVMe, and the 90% limit remains.
- All 16 storage CPU tests pass in each checkout. Launcher shell syntax and diff
  whitespace checks pass. Independent review found no security or logic defects.
- Runtime versions, quantization, context, dual-GPU settings, and inference guards
  are unchanged. No inference trial, reduced-RAM retest, updater activation, NAS
  installation, firewall change or new network listener was performed.

## Administrator action still required

The retired drive is **still mounted** and its old `/etc/fstab` entry remains.
Both direct and user-manager unmount attempts were denied by polkit, and
noninteractive sudo is unavailable. Do not unplug the drive live.

From a local or SSH terminal, use a masked sudo prompt to:

1. Unmount the actual retired SATA2 mount point with `sudo umount <mountpoint>`.
2. Run `sudoedit /etc/fstab` and remove only the retired SATA2 UUID entry.
3. Run `sudo systemctl daemon-reload`, then verify the retired mount is absent.

The live host's exact mount and UUID are recorded privately; public examples use
placeholder paths/UUIDs and are not executable host-specific cleanup instructions.
Never send the administrator password through messaging chat. Alternatively,
shutting the machine down fully makes physical removal safe, but the obsolete
fstab entry still needs cleanup to avoid a device wait on a later boot.

## Evidence and interpretation

[Curated numeric evidence](results/bolt-storage-move-2026-10-26.json) records counts,
bytes and a digest of the complete verified manifest. The complete per-file source
and destination manifests remain in the ignored operational migration state.
SHA-256 equality establishes copied-file integrity; it is not a new inference,
performance or reboot qualification. Previous benchmark evidence remains dated.
