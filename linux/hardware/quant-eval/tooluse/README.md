# Fast AMD tool-use benchmark

Fast AMD scores one model served through an OpenAI-compatible chat completions
endpoint. It reproduces NVIDIA's published method using BFCL v4 and seed
`20261122`, on NVIDIA's frozen item list, which both servers share since
November 26, 2026 (`benchmarks/shared/tooluse-short-manifest.json`). This short
benchmark measures tool use on six specific BFCL pools. It does not produce a
full BFCL leaderboard score or measure general reasoning or serving throughput.

Use Python 3.13 or later on Linux. The package uses only the standard library
and runs each multi-turn episode in a forked worker so the deadline covers
local tool execution and grading as well as network requests.

```sh
python3 -m fast_amd.build_manifest --src bfcl-src --out fast_amd/manifest.json
python3 -m fast_amd.run MODEL small --base-url http://127.0.0.1:8000 --out runs/model-small
python3 -m fast_amd.report --out runs/report MODEL=runs/model-small
python3 -m unittest discover -s tests
```

The checked-in manifest is ready to run. The runner verifies it against the
local BFCL source snapshot before making requests. Small runs attempt 40
single-turn items and nine core episodes. Use `large` to add six episodes and
report a second score over all 15. Use `--abort-file PATH` to stop before the
next item if that file exists. The `--load-cap`, `--item-budget`, and
`--hard-limit` overrides take seconds.

The runner writes per-item model replies to `fast.jsonl` and aggregate scores
and coverage to `fast-result.json`. Exit codes are 0 for a completed or cut run,
2 for invalid inputs, 3 for a setup failure, and 4 for an abort. The fixed score
uses all planned items in the denominator. Incomplete runs also report a
covered-only score when both parts have at least one scored item. A core score
based on fewer than three scored episodes is marked as not meaningful.

Function calls in multi-turn episodes execute against in-memory BFCL
environments. The local snapshot omits BFCL's loader and long-context
fixtures. Tools are assembled in involved-class order and each class's
document order. Withheld tools are appended in the order given for the
reveal turn. The three multi-turn pools use no long-context fixtures.
The MathAPI logarithm uses a Decimal-backed adapter for the unavailable
`mpmath` import. No selected reference episode calls that method.

## On the AMD server (November 24, 2026)

The owner made this short tool-use test the ranking on both servers. It was rebuilt here from BFCL v4 because the
NVIDIA server's frozen item list was not in this repository, and drew other items than NVIDIA's. **Since November 26
(owner: "same models and benchmarks" on both servers) the items are NVIDIA's frozen list**, committed in
[`benchmarks/shared/`](../../../benchmarks/shared/README.md): `build_manifest.py` takes the 55 ids, their order and
the core episodes from there and checks that each one is runnable here. All 55 replay their reference answers
correctly in the unit tests. Scores from before November 26 used the old items and are not comparable with these.

- **BFCL files:** `python3 fetch_bfcl.py` downloads the pinned files listed in `fast_amd/manifest.json` into
  `bfcl-src/` and checks each sha256. `bfcl-src/` holds dataset content and is not committed.
- **All routes, one after another:** `fast_chain.sh OUTDIR route:small|large ...` runs each route through the hub
  (`127.0.0.1:30100`). Before each route it stops on a GPU hold (`hardware/generated/GPU-LOCK`, also checked between
  items), a running build or a game, waits for the CPU to cool to 60 C, and refuses to start while the hub serves
  another client or model. Load cap 300 s; hard limit 1,020 s (small) or 3,720 s (large).
- **Collect:** `python3 collect.py` writes the scores (no item text and no model replies) to
  `hardware/results/tooluse-short-2026-11-24.json`.
- **Groups:** small (49 items) for models that fit in VRAM; large (55 items, adds 6 episodes) for the SSD-streamed
  models and Ripple. The ranking score uses the 40 single-turn items and the 9 core episodes in both groups.
