# Hy4-Flash Maya-M on Maya 1.1.73, both cards — November 22, 2026

The owner asked whether Hy4-Flash could use both cards and free RAM, and then asked for Maya-M to be tested. It runs on both cards and leaves the RAM available. It is no faster than the Strata pack, and reads prompts about four times slower. It is a trial on a side copy, not a hub route.

## Result

| | Maya-M on Maya 1.1.73 | SQ-64 on Strata 0.2.18 (earlier today) |
|---|---|---|
| Cards | both (layer split: layers 0–16 on the display card, 17–41 on the second) | second card only |
| VRAM | 45.5 GB over both cards (22.9 and 22.6 GB) | 24.3 GB |
| RAM still available while loaded | 56–57 GB | 4.1–4.4 GB |
| Load | 21 s, plus 28 s warm-up (a first start on a PC adds about 5 minutes of one-time measuring) | 50 s |
| Decode | 13–32 tok/s on a 400-token answer; median 26.5 tok/s over the 70 longer answers of the quality test (range 6.8–44.1) | 26–30 tok/s |
| Prompt reading, 6,624 tokens | 248 and 329 tok/s | 1,146 tok/s |
| Prompt cache on follow-ups | works (6,624 of 6,641 tokens reused; 3.9 s) | not used by the harness |
| Context | 32,768 | 32,768 |
| CPU | up to 89 °C under load (14 threads compute experts) | — |

How it runs here: 7,626 of the 20,992 routed experts (36%) sit in VRAM; the rest are computed by 14 CPU threads straight from the model file. The file is memory-mapped, so the engine shows 52–55 GB resident, but that is page cache the system can take back: 56–57 GB stayed available throughout and swap did not grow. If other programs take that memory, the experts are read from the NVMe drive instead and it gets slower; that was not tested. Tencent's draft block was chosen over no drafting by the engine's own first-start timing; about two thirds of drafted tokens were accepted. Tensor parallel was not taken (it needs 36 GB on one card).

Decode speed varied a lot between requests (the same 400-token prompt gave 13.2, 20.0, 14.9 and 31.8 tok/s). The engine moves the most-used experts into VRAM between requests, which is the likely cause; it was not isolated.

## Quick quality test

Slow class, temperature 0, one attempt, about 11 minutes in total (harness 6.5 minutes).

| Block | Maya-M (3–4 bit) | SQ-64 on Strata |
|---|---:|---:|
| Harness tasks, core (12) | 11 | 12 |
| Harness tasks, extra (8) | 8 | 8 |
| Function calls (16) | 9 | 9 |
| General (10) | 6 | 5 |

The one failed harness task (`edit_config`) hit the six-step limit after nine tool calls; the Strata pack passed it in six steps. One task and one item of difference do not separate the two packs.

## Why it is not a route

- **No speed gain.** The reason to move was RAM, and that worked; speed did not improve, and prompt reading is much slower. A long first prompt (the hub's agents send 5,000–10,000 tokens) takes 20–40 s to read here against about 6 s on Strata.
- **It needs the display card.** Like the DeepSeek and GLM routes, it cannot load while a game is using that card.
- **Untested by its authors on these cards.** Maya's authors have not run Hy4-Flash on RX 7900 cards themselves. No fault, hang or wrong output was seen in this session (about 22 minutes loaded, 114 answers).
- **Not tested:** contexts above 32,768, long reasoning, vision, sustained load, behaviour when other programs take the RAM, the 216-item suite (owner's rule).

## Where things are

- Side copy: `hardware/generated/hy4-maya-trial-2026-11-22/` (ignored by Git): a copy of the installed Maya 1.1.73 tree (`f9a053dcb5a9`) with its already-built `maya-hy4`, its own home folder, config and logs. Nothing was compiled. The production Maya tree and the DeepSeek and GLM routes were not touched. One Python package (`jsonschema`) was installed into the copy's own environment by Maya's setup.
- Files: the streaming NVMe drive, folder `LLM-Models/Hy4-Flash-Maya/Hy4-Flash-Maya-M`, 132 GB (model 68.4 GB, lookup table 63.4 GB, draft block 7.5 GB, drafter 0.9 GB, vision 0.8 GB), all checked against the sizes and SHA-256 in Maya's own table. Maya and Strata cannot read each other's Hy4 files, so the Strata pack (130 GB) is still there too; the drive is 28% used.
- The side server is stopped and its memory released. To start it again: `run-maya-hy4-flash-maya-m.sh` in the side copy, with the isolated environment, the hub idle and no hold; it listens on 127.0.0.1:30032.

Results: [JSON](results/hy4-flash-maya-m-2026-11-22.json) · [Strata SQ-64 report](HY4-FLASH-SQ64-2026-11-22.md).
