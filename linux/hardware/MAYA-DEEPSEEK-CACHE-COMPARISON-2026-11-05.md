# Maya DeepSeek: passing baseline versus 36 GB cache candidate

**The cache setting is a candidate difference, not a proved cause of the crash. There was no persistent 36 GB cache to delete.** Source inspection shows `--ssd-cache 36` requests an anonymous host-RAM expert store. Its memory belongs to the engine process and was removed by process termination/reboot. The failed run never logged successful store initialization.

At the owner's request, one regenerable persistent tuning file was removed from the affected Maya model's live pack: **`lt-picks.txt`, 3,046 bytes, 69 records**. An exact private evidence copy remains outside runtime lookup paths. This is a precautionary reset, not a validated repair. The persistent GPU hold and the original failed cleanup result remain unchanged; no GPU test was run.

## Compared runs

| Item | Passing morning run | Failed evening candidate |
|---|---|---|
| Local time, November 5 EST | 04:14:18–04:18:39 | Started 18:44:48; first SMU error 18:45:06 |
| Model | DeepSeek UD-IQ1_S, original backing | Same backing |
| Selected Maya source | `c1670044bbc09310f35f9d00f7596c50ae8a38f1` | Same source/executable target |
| Model placement/context | Qualified two-card order, 32K, one request | Same intended placement/context |
| Requested reserve | 8 GiB per card | Same |
| Explicit expert profile | `none` | Same |
| Intended model-profile delta | No explicit SSD-cache option | Appended `--ssd-cache 36`; no environment updates |
| Ready/inference | Loaded in 51.964 s; two strict tool steps passed; clean unload | Not ready; zero inference requests; original owned cleanup failed |
| Actual sampled scope memory policy | No `MemoryHigh`; hard limit about 60.55 GiB | Same policy |

The comparison uses the passing result, retained morning engine log, candidate plan, current restored baseline, actual saved cgroup telemetry and selected source. Trial log/validation metadata differ. The older per-case resource metadata describes 42/44GiB limits, but actual scope samples show the current larger hard limit; it must not be mistaken for the enforced limit. These are different boots and different host/page-cache conditions, not a controlled A/B.

## What the 36 GB option changes

In selected source `src/ds4/ds4_model.cu`, `load_experts_mx()` first loads the GPU-resident experts through host staging and GPU copies. The `store_request()` branch calls `init_store()` afterward, once that loading and host-copy work has completed. Initialization prints its store description before the store's preload work.

`src/ds4/ds4_store.hpp` holds the expert cache in process-owned slots. Chunks grow through `os::anon_alloc`, are released through `os::anon_free`, and contain experts read from the original GGUF files. This is a read cache, not a rewritten model or persistent 36GB data file. It can change memory allocation, I/O and thread behavior once initialized, so a bug or interaction cannot be excluded without further evidence. Its name does not mean a disk cache survived the reboot.

The failed log ends during model loading, before ready or a successful RAM-store message. The last completed sample showed 8.05GiB in the worker, 52.57GiB minimum available host RAM, about 7.71GiB minimum free VRAM per card, and no recorded owned swap/spill or cgroup OOM. The first SMU timeout preceded the watchdog latch. These observations do not establish a full 36GB allocation, capacity failure or stale-cache reuse. Missing logs and unsampled later activity prevent proving the exact instruction where the run stopped.

## Persistent caches and cleanup

| Cache/state | Inspection | Action |
|---|---|---|
| 36 GB expert RAM store | Anonymous process memory; no persistent store file | Already gone after the crash/reboot; no disk deletion applies |
| Maya Q1 `lt-picks.txt` | Saved hipBLASLt algorithm choices; generated during the successful morning run, unchanged byte-for-byte from the pre-failure snapshot | Removed from this model's live pack after checking no open owner; exact evidence copy preserved privately |
| Conversation slots | Default source behavior is disabled unless explicitly enabled; affected pack has no slots directory | Nothing present to delete |
| Expert routing profile | Both compared configurations explicitly use `--expert-profile none` | No old routing profile selected |
| Model weights, pack metadata, tokenizer and binaries | Immutable/runtime references | Preserved; config/registry/source/binary/metadata hashes and backing-file size/inode/mtime remained unchanged |
| Shared Mesa/vLLM/comgr and other application caches | Separate namespaces, not the requested 36GB expert store | Preserved; no evidence supports a global purge |

The tuning file is separate from the expert RAM store. `src/ds4/ds4_lt.cu` keys saved choices by GPU architecture, hipBLASLt version and matrix shape, and asks the library whether a saved algorithm still supports that shape/workspace before using it. This reduces simple stale-version reuse; it does not prove every accepted algorithm bug-free. The file's unchanged pre-failure contents provide no evidence that this crash corrupted it.

The removed file was already excluded from the immutable model seal by the earlier reviewed runtime-cache classification. No seal was relaxed or reissued for cleanup. On a future separately authorized load, an absent tuning file may cause fresh algorithm measurements. That additional cold-start work remains unqualified and is blocked by the current GPU hold.

## Outcome

**Could enabling the option have contributed? Possibly; it changes a runtime path, but the available record does not show successful initialization or identify a cache defect. Could old 36 GB cached contents persist and crash a future run? This implementation creates no such persistent store.** The one live model-specific tuning cache was cleared as requested; clearing it is not proof of safety or a reason to retry.

The selected Maya DeepSeek baseline still has no `--ssd-cache` option. GLM RAM8, all route selections, the persistent fault hold and the original failed guard are preserved. RAM40 remains unrun and blocked. No model/GPU/sensor test, reset, reboot, service restart, global page-cache drop or runtime-setting change was performed.

[Curated comparison and cleanup](results/MAYA-DEEPSEEK-CACHE-COMPARISON-2026-11-05.json) · [Full-day review](AMD-DAY-REVIEW-2026-11-05.md) · [Stock/custom comparison](AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md)
