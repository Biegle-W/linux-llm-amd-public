# Qwen3.8-Flash-Next IQ3_XXS: Unsloth UD-IQ3_XXS V3.1 vs GSQ-RCO, November 8, 2026

The owner asked for a second comparison of the Unsloth UD-IQ3_XXS V3.1 quant against the current GSQ-RCO IQ3_XXS route (`qwen3.8-flash-next-iq3_xxs`), on quality and speed. The [November 4 comparison](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md) used only six fixtures.

**Result: keep GSQ-RCO.** Quality is the same within one item. Unsloth reads long prompts about 35% slower, decodes about 15% slower after a long prompt, and its GGUF is about 10% larger.

## How it was run

- Both quants ran through the hub at 127.0.0.1:30100, one after the other, on the same Strata engine and settings. Only the pack, GGUF and tokenizer paths differed.
- The Unsloth route was temporary. With the owner's approval it had a sealed record in `dsh/qualified-strata-qwen-profiles.json`. The record, the route and its profile were removed after the run, and both files match git again.
- Unsloth's per-layer embedding (PLE) table is in GGUF shard 4 of 4, so `--ple-gguf` points at shard 4 while `--native` points at shard 1.
- For each model:
  - the speed probe: two 400-token answers, then a 5,515-token prompt with a 40-token answer, twice;
  - the 54-item suite;
  - the harder 64-item suite.
- Settings: temperature 0, thinking off. On the 54-item suite, items that hit the 700-token limit were rerun at 2,048 tokens, the same as in the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md): m03 and m16 for both models.
- Grading was automatic. An independent check read every failure and 20 random passes by hand and found no grading errors.

## Quality

| Suite | GSQ-RCO IQ3_XXS | Unsloth UD-IQ3_XXS | Misses |
|---|---:|---:|---|
| 54-item | **53/54** | **53/54** | both: k08 (bat-and-ball, answered 10 cents) |
| 64-item (harder) | 62/64 | **63/64** | both: r10 (reverse "necessary"); GSQ: a01 |

- On a01 GSQ read a second file instead of fixing a bug it had already found (`a - b` where `a + b` was meant). Unsloth wrote the fix. That one agent item is the only difference.
- GSQ's 53/54 matches its earlier result in the quant comparison.

## Speed

| | GSQ-RCO | Unsloth | Unsloth vs GSQ |
|---|---:|---:|---:|
| Load + first answer | 96.8 s | 99.2 s | +2% |
| Decode, 400-token answers (tok/s) | 50.2 / 52.4 | 46.9 / 52.2 | -3% |
| Prompt read, 5,515 tokens (tok/s) | 777 / 821 | 512 / 530 | **-35%** |
| Decode after the long prompt (tok/s) | 50.0 / 49.4 | 39.9 / 43.4 | **-17%** |
| GGUF size | 75.8 GB | 83.6 GB | +10% |

Decode on short prompts is nearly level, as on November 4. The new probe adds a long prompt, and that is where Unsloth falls behind: it reads prompts at about two-thirds of GSQ's speed and decodes more slowly afterwards.

## Health

- AER fatal and nonfatal counters stayed at 0 on both cards, and both links stayed at Gen4 x8.
- At 16:09:39 the kernel logged `amdgpu 0000:13:00.0: Failed to upload overdrive table!` twice, on the Sapphire card, while Unsloth moved from the 54-item to the 64-item suite. There was no reset, AER error or link change, and the remaining 64 requests all completed. The same message appeared once before on November 8, during the rejected `--mmap-experts off` DeepSeek run.

## Router fix found during this run

- The November 8 reserve change (commit f332a6d) made `dsh/strata-router.py` compute the DeepSeek startup floor for every Strata route.
- Qwen profiles have no `--reserve-mib`, so any Qwen route that loaded after that commit failed at readiness with `ValueError: list.index(x): x not in list`. That includes the production GSQ route.
- The logs show it fired only once, on this comparison's first Unsloth start, so no production request failed.
- The floor is now computed only for `deepseek41` routes. An independent review checked every Strata profile and found no other code path that assumes `--reserve-mib`.

## Unsloth files

The Unsloth download (78 GB GGUF and a 1.4 GB pack) is on sharedNVME1, which has 830 GB free. No route uses it. **Deleted later on November 8 at the owner's request**, after the comparison engine was unloaded.
