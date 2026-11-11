# Repository audit — November 11, 2026

**Result:** the current top-level documents were consistent; 18 files with stale wording, dead links and two failing unit tests are fixed. Everything that deletes data or changes runtime behaviour is listed below as an open owner decision and was not touched.

## Method

- Seven areas, each read by one auditor and then checked by a second, sceptical one: current documents, stale references, links and orphans, configuration integrity, the public mirror, code and tests, and server hygiene.
- 88 findings; 2 were refuted. Every fix applied here was re-read against the file before editing.
- Read-only on the server apart from the edits listed. A GPU test was running, so no model request, engine start, hub, systemd or GPU test was made.

## Fixed

| File | Fix |
|---|---|
| `network/LINUX-LLM-RUNTIME-HANDOFF.md` | Title date; live engine paths now name the November 9 manual build (private copy); the DeepSeek NaN item reflects the November 11 replay; the update timer is described as removed, the recovery service as still enabled; `publish.py` described as retired |
| `network/README.md`, `dsh/README.md` | Nine routes, not twelve; the 03:00 updater is retired; a pointer to an archive section that no longer exists is gone |
| `maya/README.md`, `strata-dsv41/README.md`, `turnstone/README.md`, `publication/README.md` | Marked as historical setup notes, with a pointer to the current source |
| `hardware/MODEL-STORAGE-INVENTORY.md` | Retitled; the November 3 inventory body is marked as history |
| `hardware/quant-eval/pub/README.md` | Note that three of the twelve frozen routes were removed afterwards |
| `graphics/workflows/flux3-klein/README.md` | Nine links to workflow files that are not vendored are now plain text |
| `hardware/DAILY-UPDATES.md`, `hardware/results/README.md`, `hardware/QUANT-QUALITY-COMPARISON-2026-11-08.md` | Four dead section anchors repointed |
| `sglang/research/flash-next-model-card.md` | Link to a missing licence file is now plain text |
| `dsh/tests/test_configure_local.py` | Two failing tests fixed: expected route count 7 → 9, and the paused-model case now uses a route that is really paused |
| Public mirror only | `VALIDATION.md` no longer describes a removed folder and a mixed-vendor machine; eight links to files outside the mirror are plain text |

Tests after the edits: `dsh/tests/test_configure_local.py` 7 of 7 pass (2 failed before); 175 pure unit tests in `hardware/` pass. Tests that start processes, bind sockets, use systemd or import the GPU stack were not run.

## Open decisions (not changed)

### Runtime

1. **Device order differs between launchers and `hardware/rocm-env.sh`.** `dsh/run-qualified-native-backend` and `dsh/run-strata-qwen-backend` export `ROCR_VISIBLE_DEVICES=1,0` right after sourcing `rocm-env.sh`, which sets `0,1` (the November 7 layout). The running Strata DeepSeek engine has `ROCR_VISIBLE_DEVICES=1,0` in its environment. The Maya and Strata routes therefore see the two cards in the opposite order to the one the handoff documents. Whether this matters for the DeepSeek NaN fault is not known; it has not been tested.
2. `dsh/strata-iq3-profile.json` records commit `ffa80d7`, version 0.2.10 and a binary hash from November 3. The installed Strata binary is the November 9 build (`504b143`, 0.2.13.1). Nothing enforces these fields. It also lists a library folder that does not exist (harmless).
3. The retired updater's `llm-daily-update.service` is still linked and its recovery service is still enabled at login.
4. Two `*.shared-settings.json` files are tracked although a `.gitignore` rule covers them. One of them is what turns reasoning off for the Strata Qwen route, so either un-track both or add an ignore exception.

### Public mirror out of date

5. Native engine references in `dsh/qualified-native-profiles.json` and the Maya and DeepSeek profiles predate the November 9 manual update; `maya/runtime.json` and `strata-dsv41/runtime.json` pins are weeks old.
6. `hardware/rocm-env.sh` and `dsh/strata-iq3-profile.json` still carry device order `1,0`, and `graphics/runtime_selection.py` rejects the order its own configuration declares.
7. Machine-derived identifiers are published: fan-controller device IDs and a kernel boot ID in two result files. They are not credentials.
8. `archives/README.md` links a repository it calls private.

### Stale code and settings

9. About ten test files cover only the retired updater. `dsh/scripts/validate-profile.py` launches a binary that no longer exists. `dsh/models.ini` points at weights that are gone (two tests still read the file). `turnstone/configure.py` defaults to a route that does not exist. `dsh/configure_local.py` keeps name maps for removed routes. `hardware/daily-update/publish.py` would overwrite the update ledger header with retired wording if it were ever run.
10. Unreferenced files: 6 dated reports, 8 result files, 13 one-off hardware scripts, and `hardware/nemotron_super.py` for a retired route.

### Disk (about 23 GB, all ignored by git)

11. vLLM compile cache: 17 GB, most of it older than the current build.
12. Superseded updater runs: about 3.0 GB. Old build and test folders under `hardware/generated`: about 1.4 GB.
13. A root `llama.cpp` checkout (1.1 GB) and an old `strata/build` (363 MB) that serve nothing.
14. `dsh/logs`: 703 MB, of which 607 MB is thermal traces.
15. A 12.8 MB stray binary in the repository root, old scratch folders, and an older Strata DeepSeek build outside the repository that production no longer references.

The system drive is at 73%.

## Checked and clean

- No tracked temporary or junk files; all tracked JSON parses.
- Sealed profile fingerprints are consistent with their registry.
- No credentials, private addresses or personal paths found in the public mirror.
- The shared-drive handoff copy is byte-identical to the private one.
- No GPU hold file is present.
