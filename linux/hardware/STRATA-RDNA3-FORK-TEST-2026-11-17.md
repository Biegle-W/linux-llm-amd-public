# Strata RDNA3 fork against the current build — November 17, 2026

Owner request: research Radiance for the two RX 7900 XTX cards with the council, then test the lead it found. The council's
answer was that no Radiance route beats this server's LLM numbers, and that the one lead worth testing is not Radiance but
`nicejunjie/Strata-rdna3`, a fork of Strata tuned for the 7900 XTX. This is that test. **Production was not changed.**

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

Item by item the suite has 158 right in both runs, 9 only after and 6 only before: no quality change is detected. Through the hub the prompt rates are 12–15% below the standalone tuned run above. No NaN line, no kernel fault, no hold. To revert, restore the profile from the commit before this one. The fork was **not** installed; its decode advantage remains available as a separate decision.

## Limits

Six requests, one run each. No 216-item suite, nothing past 48K tokens, no sustained run, no thinking mode. The fork lacks
upstream's server fixes since engine 0.1.49. The tuned settings were taken from the fork's documentation and one public
64 GB report, not searched for this server. RAM use of the production arm was not sampled.

Numbers: [`results/strata-rdna3-fork-test-2026-11-17.json`](results/strata-rdna3-fork-test-2026-11-17.json).
