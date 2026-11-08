# Quant quality comparison: Flash-Next and DeepSeek — November 7–8, 2026

The owner asked to compare the quality of "Qwen3.8-Flash-Next UD-IQ1_M and Qwen3.8-Flash-Next IQ3_XXS, same for DeepSeek-V4.1-Flash-1017 ISTA-Coder IQ2_XXS and DeepSeek-V4.1-Flash-1017 UD-IQ1_S", decide which quant to keep for each model, and compare their speed.

## Method

- **Test set:** 54 items with answer keys, all graded automatically ([`hardware/quant-eval/`](quant-eval/)).

  | Category | Items | How graded |
  |---|---:|---|
  | Multi-step math | 18 | final `ANSWER:` line |
  | Python coding | 12 | the model's code run against unit tests |
  | Knowledge and reasoning | 14 | short answers |
  | Exact output format | 6 | JSON, bullets, exact strings |
  | Tool calls | 4 | arguments checked, plus one answer from a tool result |

- **Same engine within each pair:** both pairs ran on Strata through the normal hub (127.0.0.1:30100).
- **Settings:** temperature 0 (greedy) with thinking off.
- **Truncated answers:** answers cut off by the token cap were re-run with a 2048-token cap. Greedy decoding makes that the same as using the bigger cap from the start. Two Flash-Next math answers on each quant needed it, and both then passed.
- **Speed:** median generation speed over answers of 100+ tokens. Load times are from the guarded short tool test on November 7, a cold load with the backing-file integrity check.

## Results

| Route (quant) | Math | Code | Knowledge | Format | Tools | **Total** | Generation | Cold load |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.8-flash-next-iq3_xxs` (GSQ-RCO IQ3_XXS) | 18/18 | 12/12 | 13/14 | 6/6 | 4/4 | **53/54** | 52.5 tok/s | 107.5 s |
| `qwen3.8-flash-next-unsloth-iq1_m` (Unsloth UD-IQ1_M) | 18/18 | 12/12 | 13/14 | 5/6 | 4/4 | **52/54** | 57.9 tok/s | 59.0 s |
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` (ISTA Coder IQ2_XXS) | 18/18 | 12/12 | 11/14 | 6/6 | 4/4 | **51/54** | 15.3 tok/s | 687.8 s |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` (Unsloth UD-IQ1_S) | 18/18 | 12/12 | 14/14 | 6/6 | 4/4 | **54/54** | 3.4 tok/s | 62.2 s |

**Where the answers differed:**
- **Flash-Next:**
  - Both quants answered the bat-and-ball question with 10 cents; the answer is 5.
  - IQ1_M reversed "banana" as `ANAB`, a character-level slip that IQ3_XXS did not make.
- **DeepSeek Coder IQ2_XXS:** three wrong answers that UD-IQ1_S got right.
  - "Gabriel García García" instead of García Márquez.
  - "Potassium" for atomic number 26 instead of iron.
  - "2" for Sally's sisters instead of 1.

The Coder pack keeps 192 of the 384 routed experts: an expert-pruned, coding-focused build. Its math, code, format and tool results are perfect, but its general knowledge has gaps.

## Decision

- **Flash-Next: keep IQ3_XXS.**
  - **Quality** is essentially tied (53 against 52), and the one IQ1_M-only miss is a token-level corruption.
  - **Speed:** IQ1_M decodes about 10% faster.
  - **Updates:** IQ3_XXS runs on the production Strata engine, which the nightly updater keeps current. IQ1_M was pinned to an isolated Strata 0.2.11 package (`strata-0211-unsloth42`) that never received updates.
  - **What was removed:** the route `qwen3.8-flash-next-unsloth-iq1_m`, from `dsh/strata-profiles.json`, `dsh/qualified-strata-qwen-profiles.json` and `dsh/strata-unsloth-iq1_m-profile.json`.
  - **Deleted (owner confirmed November 8, "IQ3_XXS, remove IQ1_M"):** the 65 GB weights folder `sharedNVME1/LLM-Models/Strata-Unsloth-Qwen3.8-Flash-Next-UD-IQ1_M-V3.1-d96201194f10` and the 2.1 GB isolated engine package `strata-0211-unsloth42`.
- **DeepSeek: pending owner choice.** The [harder rerun](#deepseek-rerun-with-a-harder-suite-november-8-0305-0410) widened the quality gap (UD-IQ1_S 64/64, Coder 59/64) and showed an intermittent NaN lock-up on the Coder. The Coder is still about 3–5 times faster.
  - **UD-IQ1_S** has the better quality (54/54 against 51/54), with the difference all in general knowledge.
  - **Coder IQ2_XXS** is about 4.5 times faster on Strata (15.3 against 3.4 tok/s): a 1,000-token answer takes about 1 minute against 5 minutes. On Maya the gap is larger: 17.3 against 1.2 tok/s on November 7.

## Found along the way

The IQ1_M route had been refusing to start since the 18:35 Strata promotion on November 7. The updater's reinstall rewrote the modification time of two shared Strata files, `strata/data/expert-profile.bin` and `strata/tools/hip/gfx1100-hipblaslt-100202.txt`. Their contents were unchanged and matched the sealed SHA-256.

`dsh/strata_qwen_qualification.py` now treats a changed modification time like a changed exFAT inode: it falls back to the sealed SHA-256, while a size or device change still refuses. Modified weights are still refused, and all 16 tests pass.

## DeepSeek rerun with a harder suite (November 8, 03:05–04:10)

The owner asked to "compare the two deepseek again". The first suite had saturated: both quants were perfect on math, code, format and tools. A new 64-item suite ([`suite2.py`](quant-eval/suite2.py), graded by [`grade2.py`](quant-eval/grade2.py)) targets the areas where they differed, plus long context and multi-step agent turns. The coding tests were first checked against reference solutions, and all 10 pass. The settings were the same: Strata through the hub, temperature 0, thinking off.

| Category | Items | Coder IQ2_XXS | UD-IQ1_S |
|---|---:|---:|---:|
| Knowledge | 30 | 27 | **30** |
| Trick reasoning | 12 | 11 | **12** |
| Harder coding (unit tests) | 10 | 9 | **10** |
| Exact format | 4 | 4 | 4 |
| Multi-step agent tool calls | 5 | 5 | 5 |
| Questions on a 4,800-token document | 3 | 3 | 3 |
| **Total** | **64** | **59** | **64** |

**Coder misses:**
- Tungsten's symbol given as "Tw"; it is W.
- Chekhov named as the author of *Crime and Punishment*; it is Dostoevsky.
- Rio de Janeiro named as Brazil's capital; it is Brasília.
- "necessary" reversed as `yessecen`.
- An expression evaluator that crashed with `UnboundLocalError`.

Across both suites the Coder scores 110/118 and UD-IQ1_S scores 118/118.

**Speed** (measured with [`speed2.py`](quant-eval/speed2.py) over streaming; the second run of each pair is warm):

| | Coder IQ2_XXS | UD-IQ1_S |
|---|---:|---:|
| Cold load, including the integrity check | 442 s; 1,174 s on the first launch (see below) | 47 s |
| Generation, 400-token answer | 9.6 tok/s cold, 14.2 warm | 5.6 cold, 6.3 warm |
| Median generation over the suite | 16.9 tok/s | 4.2 tok/s |
| Reading a 4,786-token prompt | 261 tok/s (18 s to first token) | 51 tok/s (95 s to first token) |
| Whole 64-item suite after load | 5.1 min | 21.8 min |

Coder generation gets faster as more of its experts move from the CPU lane into VRAM. The engine logged 73% of experts on the CPU at the first token and 6% after the long prompt.

**Coder reliability events:**
- **NaN lock-up:**
  - **What happened:** right after the suite, the Coder's first 400-token streaming answer stopped at token 276 with "the model's numbers went non-finite (NaN reached the router)".
  - **Effect:** every later request then failed at token 0 with "the router's weight is not finite (layer 39…)" until the engine was restarted.
  - **Retest:** after a fresh load the same requests ran cleanly, so the fault is intermittent. Even so, one occurrence leaves the route unusable until it is unloaded.
- **Integrity refusal on the first launch:**
  - **Why every launch rehashes:** the Coder's weight files are on an exFAT drive (`sharedNVME1`), where inode numbers change, so each launch rehashes them.
  - **What happened:** tonight's first launch was refused with "Qualified native backing content changed". The relaunch passed, and a separate full rehash afterwards matched all six files.
  - **Likely cause:** a transient read problem. It was not explained.

UD-IQ1_S had no errors.

## Not covered

These are short, greedy, thinking-off tests. Long context, thinking mode, sustained throughput and agentic multi-step coding were not measured.
