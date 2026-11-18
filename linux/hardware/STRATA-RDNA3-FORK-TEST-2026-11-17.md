# Strata RDNA3 fork against the current build — November 17, 2026

Owner request: research Radiance for the two RX 7900 XTX cards with the council, then test the lead it found. The council's
answer was that no Radiance route beats this server's LLM numbers, and that the one lead worth testing is not Radiance but
`nicejunjie/Strata-rdna3`, a fork of Strata tuned for the 7900 XTX. This is that test. The test itself changed nothing in production; the last two sections record what the owner then chose to apply.

## What was compared

One route, `qwen3.8-flash-next-iq3_xxs`, same model files, same six requests, temperature 0, thinking off, one request at a time:

| Arm | Engine | Settings |
|---|---|---|
| Production | Strata 0.2.15 (`c77572806996`), through the hub | the current profile: 256-token prompt chunks, 2-token drafts, 12 GiB RAM budget, layer split |
| Current build, tuned | the same binary, started beside the hub | `--prefill auto`, 4-token drafts, `--pipeline-windows 2`, adaptive expert swaps, 8 pool workers, 24 GiB RAM budget, 1536 MiB VRAM reserve |
| Fork, tuned | `Strata-rdna3` at `8b01b0c8512d` (engine 0.1.49.1), isolated build | the tuned settings above plus the fork's two-card tensor-parallel decode and its documented IQ3_S environment switches |

The fork was built outside the repository with the server's ROCm 7.2.3 toolchain and rocWMMA headers at the commit the fork pins.
Its older engine did not know `--lookup-max-t`; that option was dropped for the fork arm. Each tuned arm ran under the shared
resource guard on its own port while the hub was idle.

## Results

| Request | Production | Current build, tuned | Fork, tuned |
|---|---:|---:|---:|
| Prose, 256 tokens: decode tok/s | 50 | 52 | **129** |
| Code, 256 tokens: decode tok/s | 58 | 73 | **171** |
| Agent turn, 12,862-token prompt with 25 tools: prompt read tok/s | 909 | **2,074** | 1,344 |
| Same turn, start to finish | 14.8 s | **6.7 s** | 9.8 s |
| Follow-up with a short tool result (13,281 tokens re-read): prompt read tok/s | 938 | **2,247** | 1,609 |
| Same turn, start to finish | 14.8 s | **6.4 s** | 8.4 s |
| Long prompt, 47,716 tokens: prompt read tok/s | 932 | **3,043** | 1,289 |
| Long prompt: decode after it tok/s | 53 | 63 | **143** |
| Long prompt, 256-token answer, start to finish | 56.0 s | **19.8 s** | 38.8 s |
| Short prompt, 256 tokens of prose, start to finish | 5.5 s | 5.1 s | **2.1 s** |
| RAM in use while loaded | not sampled | 18.9 GiB | 37.9 GiB |

All three arms gave the same answers on the checked items: the tool call with the three hidden codes, the confirmation marker,
and the three codes of the long prompt. No NaN line in any engine log, no kernel fault, no GPU hold, no swap.

## What it means

- **Most of the prompt-reading gain is settings, not the fork.** The current build with tuned settings reads prompts 2.2 to
  3.3 times faster than production and faster than the fork. Strata 0.2.14 moved prompt reading to its own kernels; the
  fork is based on engine 0.1.49 and does not have them.
- **The decode gain is the fork's.** Two-card tensor-parallel decode gives 2.2 to 2.5 times the decode speed of the current
  build with the same tuned settings. Tuned settings alone add little to decode.
- **Which is faster for a whole request depends on the answer length.** With a long prompt and a short answer (tool calls, agent
  turns) the tuned current build wins. With a short prompt and a long answer the fork wins.
- The public warning that the fork reads short tool-result prompts about three times slower did not show here, but both
  arms re-read the whole 13K prompt (prompt cache off in every arm), so this test does not isolate a short append.

## Tuned settings applied to production (same day, owner approved)

The owner chose to apply the tuned settings to the production Flash-Next profile on the current build. A further run showed the 24 GiB RAM budget made no difference (identical speeds, the same 18.9 GiB in use), so the profile keeps its **12 GiB** budget and stays inside the existing memory guard; no guard code changed.

Changed in `dsh/strata-iq3-profile.json`: `--prefill` 256 → auto, `--spec` 2 → 4, `--spec-min-p` 0.7 → 0.5, `--pipeline-windows` 0 → 2, `--adapt-every` 0 → 1 with `--adapt-swaps 48`, `--pool-workers` 6 → 8, both VRAM reserves 1024 → 1536 MiB, `--no-spec-split` removed.

| Check on the tuned production profile, through the hub | Before | Tuned |
|---|---:|---:|
| Strict tool gate: first token, steps 1 / 2 | 7.0 s / 6.3 s | 5.1 s / 4.3 s (bare marker) |
| Agent turn, 12,862-token prompt: prompt read | 909 tok/s | 1,755 tok/s |
| Same turn, start to finish | 14.8 s | 7.8 s |
| Long prompt, 47,716 tokens: prompt read | 932 tok/s | 2,673 tok/s |
| Long prompt, 256-token answer, start to finish | 56.0 s | 21.9 s |
| Prose / code decode | 50 / 58 tok/s | 52 / 74 tok/s |
| Public suite, 216 items | 164 (75.9%, 69.8–81.1%) | 167 (77.3%, 71.3–82.4%) |
| Suite: wrong / cut off / malformed / request errors | 31 / 20 / 1 / 0 | 30 / 19 / 0 / 0 |
| Suite pace | 54.3 tok/s | 66.2 tok/s |

Item by item the suite has 158 right in both runs, 9 only after and 6 only before: no quality change is detected. Through the hub the prompt rates are 12–15% below the standalone tuned run above. No NaN line, no kernel fault, no hold. To revert, restore the profile from the commit before this one. At that point the fork was not installed; the next section records its installation.

## Fork installed as the only Flash-Next engine (same evening, owner decision)

The owner asked to keep only the fork for Flash-Next. Two facts were put to them first. The hub's memory guard allowed this route an 8 or 12 GiB expert RAM budget, and at 12 GiB the fork reads prompts at 567–726 tok/s, slower than the profile before today (agent turn 18.9 s, long prompt 86 s). At 24 GiB it reads at 1,289–1,609 tok/s. The owner approved a 24 GiB budget.

What changed:

- **Memory guard.** A new tier `64gb-qwen-v1` in `dsh/streaming_memory.py`: Qwen only, expert budget 12, 20 or 24 GiB, at least 60 GiB of physical RAM, the same 256K/32K KV layout, and budget plus 1 GiB available before loading (the Strata launcher adds the host KV copy, so this profile needs about 28.4 GiB available). The 32 GB tier is unchanged and still refuses 24. Tests: `hardware/test_streaming_memory_qwen64.py`.
- **Engine.** The fork at `8b01b0c8512d` (engine 0.1.49.1) replaces Strata 0.2.15 in the engine tree, built with the server's ROCm 7.2.3 toolchain, `STRATA_MMQ_KQUANTS=ON` and the rocWMMA headers at the commit the fork pins. The engine tree's tracked files, its `.git` and both binaries moved together, as the updater does. The previous build is kept whole outside the repository for rollback.
- **Profile** `dsh/strata-iq3-profile.json`: 24 GiB budget, two-card tensor-parallel decode, `--mtp-q4 all`, `--mtp-window 4096`, the fork's draft vocabulary, layer split 24, the fork's documented two-card IQ3 environment switches, `--lookup-max-t` removed (unknown to this engine), and `reasoning_effort: none` because the fork's server would otherwise think by default.

| Check through the hub | Previous build, tuned | Fork |
|---|---:|---:|
| Strict tool gate: first token, steps 1 / 2 | 5.1 s / 4.3 s | 5.8 s / 5.0 s (bare marker) |
| Load before the gate | 109 s | 87 s |
| Prose / code decode | 52 / 74 tok/s | 133 / 174 tok/s |
| Agent turn, 12,862-token prompt: prompt read | 1,755 tok/s | 1,484 tok/s |
| Same turn, start to finish | 7.8 s | 8.9 s |
| Follow-up turn, 13,281 tokens: start to finish | 7.5 s | 8.7 s |
| Long prompt, 47,716 tokens: prompt read | 2,673 tok/s | 1,368 tok/s |
| Long prompt, 256-token answer, start to finish | 21.9 s | 36.5 s |
| Public suite, 216 items | 167 (77.3%, 71.3–82.4%) | 166 (76.9%, 70.8–82.0%) |
| Suite: wrong / cut off / malformed / request errors | 30 / 19 / 0 / 0 | 31 / 19 / 0 / 0 |
| Suite pace | 66.2 tok/s | 94.6 tok/s |
| Suite generation time | 44 min | 32 min |
| RAM in use while loaded | 18.9 GiB | 37.4 GiB |

Item by item the suite has 158 right on both builds, 8 only on the fork and 9 only on the previous build: no quality change is detected. All benchmark answers were correct (three codes in the tool call, the marker, three codes in the long prompt). No NaN line, no kernel fault, no hold, no swap used. With the model loaded about 24 GiB of RAM stays available.

What this costs: prompt-heavy turns are 14% to 67% slower than on the tuned upstream build; the engine is based on 0.1.49 and lacks upstream's later fixes; upstream Strata updates no longer apply to this route. The update check will report Strata as behind upstream; that is expected. Updates for this route come from the fork's repository and are checked by hand.

Rollback: restore the previous engine tree and binaries from the saved set, then restore `dsh/strata-iq3-profile.json` from the commit before this one. The guard tier can stay; the old profile does not use it.

## No fixed expert RAM budget (later the same evening, owner decision)

The owner asked for the RAM policy of the NVIDIA server on this route: keep every expert the cards do not hold in RAM, with no fixed budget. Two candidates were run outside production first, six fixed requests each.

| Candidate | Experts held in RAM | Agent turn | Follow-up turn | Long prompt, 256-token answer |
|---|---:|---:|---:|---:|
| 24 GiB cap (installed that evening) | 21.42 GiB, page-locked | 8.9 s | 8.7 s | 36.5 s |
| 34 GiB cap | 21.42 GiB, page-locked | 8.5 s | 7.7 s | 69.7 s |
| No budget (`--resident-cpu-experts` alone) | 21.42 GiB, pageable | 7.2 s | 5.3 s | 22.9 s |

What this showed:

- **The engine's RAM copy has a ceiling of 21.4 GiB on this layout.** A larger cap holds nothing more. In every arm 5,390 of the 10,830 cache slots the prompt path borrows have no RAM copy, and their experts are read from the model file on each chunk.
- **Without a budget those reads go through the operating system's file cache** (the engine reports 12.3 GiB available for it) instead of unbuffered from the drive. That is where the prompt-path gain comes from.
- **The RAM copy is no longer page-locked**, so the kernel may swap it. Swap use reached 0.6–1.0 GiB in these runs.

What changed in the repository:

- **Profile** `dsh/strata-iq3-profile.json`: `--resident-budget-gib 24` removed, `expert_ram_mode: all-off-card` added.
- **Memory guard** `dsh/streaming_memory.py`: in tier `64gb-qwen-v1` the mode `all-off-card` takes `--resident-cpu-experts` and no budget flag, and counts 24 GiB at admission, so the same 25 GiB (28.4 GiB with the host KV copy) must be available before loading. (Replaced on November 18 by one 1 GiB free-RAM floor for every model: [guard policy](RESOURCE-GUARDS-2026-11-03.md).) `dsh/strata_runtime.py`, `hardware/check-strata-ready.py` and `hardware/prepare-candidates.py` read the figure through one helper. Tests in `hardware/test_streaming_memory_qwen64.py`; the hardware unit tests pass (661 run, 2 skipped).

| Check through the hub | 24 GiB cap | No fixed budget |
|---|---:|---:|
| Strict tool gate: first token, steps 1 / 2 | 5.8 s / 5.0 s | 8.4 s / 3.5 s (bare marker) |
| Load before the gate | 87 s | 87 s |
| Prose / code decode | 133 / 174 tok/s | 96 / 164 tok/s |
| Agent turn, 12,862-token prompt: prompt read | 1,484 tok/s | 1,738 tok/s |
| Same turn, start to finish | 8.9 s | 7.7 s |
| Follow-up turn, 13,281 tokens: start to finish | 8.7 s | 6.0 s |
| Long prompt, 47,716 tokens: prompt read | 1,368 tok/s | 2,018 tok/s |
| Long prompt, 256-token answer, start to finish | 36.5 s | 26.3 s |
| Public suite, 216 items | 166 (76.9%, 70.8–82.0%) | 169 (78.2%, 72.3–83.2%) |
| Suite: wrong / cut off / malformed / request errors | 31 / 19 / 0 / 0 | 30 / 17 / 0 / 0 |
| Suite pace | 94.6 tok/s | 120.0 tok/s |
| Suite generation time | 32 min | 24 min |
| RAM in use while loaded | 37.4 GiB | 36.8 GiB, plus about 25 GiB of file cache |
| Swap in use | 0 | 0.6–0.7 GiB |

Item by item the suite has 162 right on both settings, 7 only without the budget and 4 only with it: no quality change is detected. All benchmark answers were correct. No NaN line and no kernel fault. The short prose decode was slower in both runs without the budget (98 and 96 tok/s against 133–136), while the suite as a whole ran faster; the cause was not investigated. The first tool-gate step is slower (8.4 s against 5.8 s) with a cold file cache.

**Hold latched by an operator mistake, released by the owner.** The first strict tool gate for this setting did not run: its stage folder from the earlier fork run already existed. The rerun was started while the hub still had Flash-Next loaded from the suite. The updater's guard refused to run beside it ("Unrelated inference active; preserve it"), could not clear the hub's GPU client, and latched `GPU-LOCK` at 03:40 UTC on November 18 with no kernel fault listed. Work stopped. The owner released the hold; the file was archived as `GPU-LOCK.released-20261118T051623Z.private.json`. The gate then ran with the hub idle and passed.

Rollback of this step alone: put `--resident-budget-gib 24` back in the profile and remove `expert_ram_mode`.

## Limits

Six requests, one run each per arm; one 216-item suite run per installed configuration. Nothing past 48K tokens, no sustained run, no thinking mode. The fork lacks
upstream's server fixes since engine 0.1.49. The tuned settings were taken from the fork's documentation and one public
64 GB report, not searched for this server. RAM use of the production arm was not sampled.

Numbers: [`results/strata-rdna3-fork-test-2026-11-17.json`](results/strata-rdna3-fork-test-2026-11-17.json).
