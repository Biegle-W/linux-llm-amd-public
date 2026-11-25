# Hy4-Flash retried on the new engines — November 24, 2026

**Owner, November 24:** "update the engines to the latest version and try again with the downloaded weights." The weights from the November 22 trials were reused (nothing downloaded). Both engines were updated first ([ledger](DAILY-UPDATES.md)). This is a trial on side servers, not a hub route; adding it is the owner's decision.

## Result

**Hy4-Flash SQ-64 on Strata 0.2.21.1 (`strata-hy4` 0.1.67), both cards, expert parallel, is the setup to use.** It scored **72.1** on the short tool-use test (31/40 single-turn, 6/9 core episodes, 7/15 in the large group: 62.1), the same score as GLM-5.3-Flash and second only to Qwen3.8-27B on SGLang (74.6) in the [November 24 ranking](TOOLUSE-SHORT-TEST-2026-11-24.md). It decodes at 41–45 tok/s and leaves about 36 GiB of RAM available, where the November 22 one-card run decoded at 26–30 tok/s with about 4 GB to spare.

| Setup | Load to ready | Decode tok/s (prose / code) | 10.9K-token agent prompt | Its follow-up turn | RAM available while loaded (GiB) | Tool-use score |
|---|---:|---:|---:|---:|---:|---:|
| **Strata 0.2.21.1, both cards, expert parallel** | under 1 min (30–60 s) | 41.3 / 45.2 | 13.1 s (833 tok/s) | 2.0 s | about 36 | **72.1** |
| Strata 0.2.21.1, both cards, layer split `auto` | under 1 min (about 30 s) | 40.3 / 44.9 | 13.8 s (787 tok/s) | 2.0 s | about 36 | not run |
| Maya 1.1.78 Maya-M, both cards, its default plan (layer split 24/18) | about 12 min (see below) | 15.8 / 21.9 | 36.2 s (301 tok/s) | 2.9 s | about 57, mostly page cache* | not run |
| Maya 1.1.78 Maya-M, both cards, `--tp 0` (layer split 17/25) | about 7 min (see below) | 18.1 / 20.5 | 38.9 s (280 tok/s) | 3.0 s | about 57, mostly page cache* | not run |
| *November 22: Strata 0.2.18 SQ-64, one card* | 50 s | 26–30 | prompt read 1,146 tok/s | — | about 4 GB | — |

- Same fixed request set for every setup, one at a time, temperature 0, 32,768 context (the 47.7K-token request was skipped because it does not fit). Decode is over a 256-token answer.
- \* Maya computes the experts it keeps off the cards on the CPU straight from the model file, so its RAM is file cache that counts as available; using it for other work would evict those experts and slow Maya. Strata holds its 21.7 GB of CPU experts in its own memory, so its 36 GiB is real headroom.
- **Placement (Strata, expert parallel):** 34.4 GB of experts in VRAM (22.0 GB on one card; 12.4 GB on the other beside the 5.5 GB trunk), 21.7 GB of experts in RAM, nothing on SSD. Right after the tool-use test, still loaded, the cards held 21.8 and 20.6 GiB.
- **Tool-use test:** large group (55 items) through the side server, the same harness, items and settings as the ranking; every item covered, no timeout, 47 minutes of items. Pools: parallel 12/15, irrelevance 10/15, simple 9/10, multi-turn base 3/5, missing parameter 2/5, missing function 2/5.

## What changed from November 22, and what went wrong first

- **Two cards on Strata.** `strata-hy4` 0.1.67 spreads experts over both cards with peer copies (`--gpus`, `HY4_HIP_PEERS=1`) and keeps the rest in RAM. `HY4_DEC_PCIE_SHARE=0` was set (upstream issue 6848: decode about 25% slower with CPU experts otherwise). No conversation cache folder (upstream issue 6953).
- **First attempt stopped by the resource guard.** Left to its own plan, the engine put 24.5 GB of experts on one card (beside its buffers) and left less than 128 MiB free; the side server's guard stopped it within 40 s. No GPU fault, no hold. The working run caps experts in VRAM at 32 GB (`--vram-experts-gb 32.0 --ram-experts-gb 24.5`).
- **Maya's first start measures the machine.** Every Maya 1.1.78 start in this trial timed the prompt path first, for 308–349 s (it says the next starts skip this, but the second start of each layout measured again), and the default plan also restarted once to keep more VRAM free. The 7–12 minute loads are therefore what to expect on each start. The first attempt timed out in the test harness for that reason only. Maya's tensor parallel (`--tp 2`, the decode path upstream sped up) was not taken: each card would need 36.2 GB of VRAM for this pack, so its default fell back to a layer split. Maya-M is slower than Strata here on every request.
- Not addressed: upstream reports repetition with Hy4-Flash on long answers (issue 6530; a sampler workaround exists) and no prompt-cache reuse across separate conversations (issues 6996 and 6652). The follow-up turn above does reuse its own conversation's prompt.

## If it becomes a route

A hub route would be a sealed Strata config like Flash-Next's: `strata-hy4` from the 0.2.21.1 package, both cards, the VRAM cap above, 32,768 context, and the three SQ-64, Engram and Vision files on the shared NVMe drive (130 GB). It needs the owner's decision, a strict tool check through the hub, and the usual docs. It loads in under a minute, and with about 36 GiB of RAM left it can stay loaded beside a desktop.

## Evidence

Side-server logs and per-item replies stay in the private stage folders (`hardware/generated/strata-0221-2026-11-24/`, `hardware/generated/hy4-maya-trial-2026-11-24/`, `hardware/generated/fast-tooluse-2026-11-24/trial-hy4-flash-sq-64-hy4ep/`). Scores and timings: [results/hy4-flash-retry-2026-11-24.json](results/hy4-flash-retry-2026-11-24.json).
