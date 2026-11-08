# GLM and DeepSeek RAM and VRAM-reserve tuning — November 8, 2026

Follow-up to a private investigation of why these two models ran slower on the AMD box than on the NVIDIA box.

Later the same morning the owner approved three of the recommendations:
- restore GLM's 40 GB RAM tier and drop the `32gb-v1` host-RAM profile;
- give DeepSeek a pre-filled RAM store with an expert profile, then try `--mmap-experts off`;
- step the VRAM reserve down to 2 GiB per card.

Each step was one change, run through the hub with the same prompts:
- two 400-token answers to a short prompt (the first after load, the second warm);
- a 4.8–4.9K-token document prompt with a 40-token answer, sent twice (the second hits the prompt cache).

After every step the script checked AER counters, link widths and amdgpu kernel lines, and it would have stopped on any error. AER fatal and nonfatal stayed 0 on both cards, and both links stayed at Gen4 x8.

## GLM-5.3-Flash (`glm-5.3-flash-maya`)

| Setting | Decode, 400-token answers (tok/s) | Prompt read, 4.9K tokens (tok/s) | Decode after the long prompt (tok/s) | Load + first answer |
|---|---:|---:|---:|---:|
| Before: RAM 8 GB, reserve 8 GiB | 2.6 | 6 (159-token prompt) | — | — |
| RAM 40 GB, reserve 8 GiB | 8.0 / 5.2 | 217 | 7.0 | 133 s |
| RAM 40 GB, reserve 4 GiB | 13.3 / 12.3 | 110 | 3.7 | 87 s |
| **RAM 40 GB, reserve 2 GiB (kept)** | **17.8 / 22.1** | **396** | **13.5 (32.1 cached)** | **83 s** |
| NVIDIA, for reference | 15.2 | 547 | — | — |

Disk time per token fell from 618 ms (RAM 8) to 114–178 ms at RAM 40. With the 2 GiB reserve GLM is now level with the NVIDIA box on decode and at about 70% of its prompt speed.

## DeepSeek-V4.1-Flash-1017 (`deepseek-v4.1-flash-1017-strata-unsloth-q1`)

| Setting | Decode, 400-token answers (tok/s) | Prompt read, 4.8K tokens (tok/s) | Decode after the long prompt (tok/s) | Load + first answer |
|---|---:|---:|---:|---:|
| Before: no expert profile, reserve 8 GiB | 5.6–6.3 (4.2 median, short answers) | 51 | — | 47 s |
| Expert profile, reserve 8 GiB | 3.8 / 7.6 | 99 | 3.9 | 118 s |
| Expert profile, reserve 4 GiB | 7.1 / 9.4 | 110 | 4.9 | 57 s |
| **Expert profile, reserve 2 GiB (kept)** | **7.5 / 10.1** | **120** | **5.6 (15.8 cached)** | **57–157 s** |
| Expert profile, reserve 2 GiB, `--mmap-experts off` (rejected) | 3.9 / 18.9 | 43 | 4.5 | 179 s |
| NVIDIA, for reference | 11.7–12.2 | 86–217 | — | — |

- The expert profile is a copy of the engine's `profile-2.00.bin`, stored at `dsh/data/strata-dsv41/deepseek-q1-expert-profile.bin` (gitignored). The engine adds its routing counts to that file as it runs. At load it reads the 3,927 hottest experts (27.2 GB) into the RAM store in about 24 s.
- At 2 GiB reserve, 2,285 + 2,011 experts fit in VRAM (2,580 in total before).
- **`--mmap-experts off` was rejected.**
  - It filled host RAM: 57 of 61 GB used, 4 GB available. The RAM store then kept giving memory back, down to 1,088 slots.
  - It cut prompt reads to 43 tok/s, and decode varied from 3.9 to 18.9 tok/s.
  - During that run the kernel logged `amdgpu 0000:13:00.0: Failed to upload overdrive table!` twice, on the Sapphire card. There was no AER error, reset or link change. It did not recur after the setting was reverted and RAM returned to 57 GB available.
- DeepSeek is about twice as fast as before but still about 20% behind NVIDIA on decode. The remaining gap fits the host side (i5 CPU lane, 64 GB RAM, P3 drives), which these steps did not change.

## Maya DeepSeek route (`deepseek-v4.1-flash-1017-maya-unsloth-q1`), later the same morning

At the owner's request the same two changes went onto the Maya DeepSeek route: an expert profile, and a reserve stepped down to 2 GiB. The profile is a copy of Maya's shipped `data/expert-profile-ds4.bin`, stored at `dsh/data/maya/deepseek-q1-expert-profile.bin` (gitignored). The route's `64gb-q1-v1` host-RAM tier, 28 GB warm cache and 20 threads are unchanged. The method and prompts were the same as above.

| Setting | Decode, 400-token answers (tok/s) | Prompt read, 4.8K tokens (tok/s) | Decode after the long prompt (tok/s) | Load + first answer |
|---|---:|---:|---:|---:|
| Before: no expert profile, reserve 8 GiB | 5.0 / 9.3 | 108 | 2.9 | 58 s |
| Expert profile, reserve 4 GiB | 7.0 / 11.8 | 139 | 1.6 | 51 s |
| **Expert profile, reserve 2 GiB (kept)** | **9.5 / 17.1** | **125** | **3.2 (19.6 cached)** | **133 s** |

- Quality: **64/64** on the harder suite, with no errors and no NaN events.
- AER, link width and kernel logs were clean after every step.
- On this box the Maya route is now faster than the Strata route on short-answer decode (9.5–17.1 vs 7.5–10.1 tok/s), with a similar prompt-read speed.

## Quality check on the kept settings

The harder 64-item suite from the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md) was run through the hub at temperature 0 with thinking off, and graded automatically.

| Route | Knowledge | Reasoning | Code | Format | Agent | Long | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| `glm-5.3-flash-maya` (RAM 40, reserve 2 GiB) | 30/30 | 10/12 | 10/10 | 4/4 | 5/5 | 3/3 | **62/64** |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1`, first run | 30/30 | 12/12 | 4/10 | 3/4 | 4/5 | 2/3 | 55/64 |
| same, second full run on a fresh engine | 30/30 | 12/12 | 10/10 | 4/4 | 5/5 | 3/3 | **64/64** |

- GLM's two misses were reasoning items (r10, string reversal; r11, a weekday). DeepSeek got both right.
- **DeepSeek hit one NaN event in the first run.**
  - During code item c05 the engine logged that the router met non-finite scores on CUDA1, the Sapphire card. Its NaN guard stopped the request with an error instead of returning a wrong answer.
  - The engine stayed affected: the next eight requests (c06–c10, f01, a01, L2) failed the same way. Later requests succeeded without a restart.
  - Of the 9 failures, all were NaN errors, not wrong answers.
  - No AER error, reset, link change or kernel error was logged.
- After an engine restart, those 13 items were rerun at the same settings and passed 12/13; the miss was f01, which wrapped its JSON in a code fence. A second full 64-item run then passed 64/64. There were no NaN events in either.
- That is 1 NaN event in about 141 DeepSeek requests at the new settings. The old settings passed 54/54 and 64/64 with none, so the new settings (expert profile or 2 GiB reserve) cannot be ruled out. **If it recurs, the first change is to raise the DeepSeek reserve to 4 GiB** (7.1–9.4 tok/s, 110 tok/s prompt). The Coder IQ2_XXS quant showed the same sticky-NaN pattern earlier on November 8.

## Guard changes (owner choice, November 8)

- `dsh/qualified_native_runtime.py`: the minimum requested reserve per card went from 8 GiB to 2 GiB (`MIN_RESERVE_MIB=2048`). GLM may use 2, 4, 6 or 8 GiB, and its later reserve must equal its first.
- `dsh/maya-router.py` and `dsh/strata-router.py`: the fixed 6 GiB whole-card free-VRAM check at startup now scales with the profile's reserve: reserve minus 1 GiB, between 1 and 6 GiB. Without this change the routers refused the 4 GiB and 2 GiB steps.
- The GLM profile now uses `MAYA_GLM_RAM_GB=40` with no `host_ram_profile`, and both GLM reserves are 2048 MiB.
- The Strata DeepSeek profile uses `--reserve-mib 2048` and the expert profile, and leaves `--mmap-experts` at the engine default.
- Both registry records were resealed (`config_sha256`).
- The Maya DeepSeek profile uses `--reserve-mib 2048` and its own expert profile (see above); its registry record was resealed.
- These runs were short. A longer owned soak at the new settings is still the main open check.
