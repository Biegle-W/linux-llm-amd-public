# DeepSeek-S retirement — October 26, 2026

At the user's request, DeepSeek-S is removed from Maya and Strata. The retained
DeepSeek choices are `deepseek-v4.1-flash-1017-maya` (Maya-XS + xs2) and
`deepseek-v4.1-flash-1017-strata-xs`. GLM Maya-S is a different model and remains.
The catalog now has **11 profiles**: four llama.cpp, one SGLang, two vLLM,
two Strata and two Maya. Runtime versions, XS configuration/pack fingerprints,
32K context, both-GPU placement, drafter, RAM/VRAM guards and DSH default are unchanged.

## Files removed and retained

Removed S shards **1–4**, `dspark.bin` / `dspark.json`, S-only Maya/Strata pack
metadata and two S-only expert-routing seeds. The S model profile JSONs, catalog
entries and Maya selector label are removed. Saved S selections migrate to XS in
the same DSH provider. The S installer/verifier selection is rejected; the old S
checksum manifest remains non-installable history. The active downloader and
Strata pack preparer no longer recreate S-only assets. Nightly updates stay paused.

| Removed assets | Logical bytes |
|---|---:|
| Four S-only GGUF shards | 178,193,155,104 |
| Old S drafter and JSON | 7,967,713,733 |
| S-only model-drive metadata | 17,816,258 |
| Two local S-only routing seeds | 122,880 |
| **Total, 28 files** | **186,178,807,975** |

Shared NVMe free space increased from **149,758,410,752** to **335,939,895,296**
bytes: **186,181,484,544 bytes (186.18 GB / 173.40 GiB)** reclaimed, including
filesystem allocation/directory overhead. No files were copied to another drive.

The `Maya-S` directory is deliberately retained with only Engram shards **5 and 6**:
**161,284,798,884 bytes**. Both XS packs reference these original filenames and
locations; deleting that directory would break XS. The three XS shards, matching
`dspark-xs2.bin/.json`, shared vision files, XS tokenizers/metadata and independent
XS routing seeds are retained. DeepSeek's remaining model-drive assets total
**281,866,295,003 bytes (281.87 GB / 262.51 GiB)**, shared between both engines.

## Validation and limits

A maintenance GPU-LOCK prevented hub launches during retirement. No inference
workers were running before deletion. The exact deletion list was checked against
the retained dependency set. All 34 protected files retained their identities,
sizes and modification times; small files also retained SHA-256. Each XS pack's
seven file references and all **48,795 tensor bounds** pass. Both pack seals and
config fingerprints match their existing validation. `maya/install.sh deepseek`
verifies the existing sealed XS pack without download, build or inference.
No new full weight hash pass was run; the previous published checksum evidence
is retained. Historical S timing/quality reports remain dated evidence.

All **35 CPU/temporary-loopback regression tests pass in each checkout**.
Coverage includes shared Engram/drafter removal detection,
retired S catalog rejection, non-installable historical manifests, saved-selection
migration, frontend security, ownership and updater rollback. Live API checks
verify 11 catalog entries, preserved XS IDs and rejection of both S IDs without
loading a worker. Host self-access is not a separate remote-peer test.

This is storage/catalog verification, **not a new inference or performance test**.
The live OS still exposes about 14.83 GiB RAM; Maya and Strata RAM-offloaded
profiles remain held by their unchanged RAM admission rules. No GPU trial,
service restart, new port, swap-policy change or updater activation was performed.

[Curated storage and dependency record](results/deepseek-s-retirement-2026-10-26.json).
