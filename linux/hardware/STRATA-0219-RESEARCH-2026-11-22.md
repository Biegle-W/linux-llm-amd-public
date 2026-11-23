# Strata 0.2.19: research and Flash-Next comparison, November 22 2026

The owner reported that Strata 0.2.19 is much faster for Qwen3.8-Flash-Next and Inkling 2 Mini and asked for research and optimisation.
Nothing in production was changed: the Flash-Next route still runs the RDNA3 fork.

## What 0.2.19 changed (source review, v0.2.18 to v0.2.19, 55 commits)

- **Flash-Next on RX 7900 XTX.** Discrete RDNA3 cards get their own default switches for the first time: 24 exact ones and 11–12 matrix-core
  ones for prompt reading and decode. Three of the new kernel files say they were ported from the RDNA3 fork this server already runs
  (prompt MoE kernel `PF_F16=2`, `rdna_gr`, the GDN megakernel). New and not in the fork: decode expert mode 8 on these cards, the
  matrix-core DFlash2 drafter, the `P1A` prompt kernels (Q4_K/Q5_K only, not this IQ3_XXS file).
- **Still missing upstream:** two-card tensor-parallel decode. Upstream splits the layers between the cards; the megakernel does not run on a split.
- **Inkling 2 Mini.** A new engine, `strata-inkling`, with an AMD backend. On AMD it uses one card, forces thinking off, and has GPU
  kernels only for its own `.strata` files (SQ-20 is 19.35 GB and fits one 24 GB card). The UD-Q8_K_XL GGUF the llama.cpp route uses has no GPU expert
  path in it. The source gives no speed figure for any AMD card.
- The release notes give no RX 7900 XTX figure for Flash-Next IQ3_XXS, so it was measured here.

## Measurement

Upstream v0.2.19 (`c6f6427d`, engine 0.1.65) was built from source for gfx1100 with the server's ROCm 7.2.3 in a side folder
(`hardware/generated/strata-0219-2026-11-22/`). Each setup ran alone on its own port with the hub idle, on the same six requests used
on November 17. Same model files, same 262,144-token context, both cards. All speeds in tok/s; a range is the lowest and highest of the runs.

| Setup | Runs | Prose decode | Code decode | Agent turn, 12,862 tokens: read | Long prompt, 47,716 tokens: read | Long prompt: wait for first token | Decode after long prompt |
|---|---:|---:|---:|---:|---:|---:|---:|
| fork | 3 | 54–117 | 127–164 | 1,248–2,140 | 1,590–2,368 | 20.2–30.0 s | 105–134 |
| 0.2.19 defaults | 3 | 93–94 | 124–135 | 2,445–2,524 | 4,022–4,076 | 11.7–11.9 s | 113–115 |
| 0.2.19, bf16 hyper-connection read | 3 | 77–106 | 116–141 | 2,361–2,603 | 4,112–4,163 | 11.5–11.6 s | 105–120 |

- **Prompt reading: 0.2.19 is faster and steadier.** The long prompt is read at about 4,100 tok/s on every run against 1,590–2,368 on the fork, so the
  wait for the first token drops from 20–30 s to under 12 s.
- **Decode: the fork is still ahead on code** (127–164 against 116–141) and about level on prose. Decode right after a tool-call prompt is level.
- **RAM: 0.2.19 used about 19 GB against 37 GB** for the fork with the same settings (9 GB of experts in RAM; the fork's tensor-parallel layout keeps more off the cards).
- Against upstream 0.2.15 measured on November 17 with the same requests (prose 52, code 73, long prompt 3,043), 0.2.19 is clearly faster.
- No GPU fault, hang or hold in 19 runs.

### Settings tried

| Setup | Runs | Prose decode | Code decode | Agent turn, 12,862 tokens: read | Long prompt, 47,716 tokens: read | Long prompt: wait for first token | Decode after long prompt |
|---|---:|---:|---:|---:|---:|---:|---:|
| fork, decode mode 8 | 1 | 100 | 158 | 1,854 | 2,242 | 21.3 s | 103 |
| fork, chunked GDN off | 1 | 104 | 164 | 2,274 | 2,383 | 20.0 s | 121 |
| 0.2.19, gfx11 defaults off | 1 | 83 | 123 | 1,504 | 2,759 | 17.3 s | 80 |
| 0.2.19, matrix-core set off | 1 | 94 | 127 | 2,123 | 3,149 | 15.2 s | 114 |
| 0.2.19, pipeline windows 0 | 1 | 60 | 83 | 2,495 | 4,061 | 11.8 s | 69 |
| 0.2.19, draft layer on first card | 1 | 64 | 107 | 2,330 | 4,097 | 11.6 s | 82 |
| 0.2.19, layer split 24 | 1 | 77 | 122 | 2,267 | 3,615 | 13.2 s | 98 |
| 0.2.19, 6 draft tokens | 1 | 98 | 128 | 2,544 | 4,143 | 11.5 s | 107 |
| 0.2.19, draft threshold 0.4 | 1 | 99 | 133 | 2,560 | 4,145 | 11.5 s | 118 |
| 0.2.19, 6 pool workers | 1 | 107 | 135 | 2,580 | 4,116 | 11.6 s | 117 |

- 0.2.19's own RDNA3 defaults are worth a lot: with them off, the long prompt is read at 2,759 instead of about 4,050 and decode is 10–30% slower.
- Keeping the hyper-connection weights in bf16 (`STRATA_HC_Q8=0`, what the fork route also uses) costs no measurable speed, so it is the setting to use: the 8-bit default can change answers slightly.
- Turning the matrix-core set off, pipeline windows off, the draft layer on the first card, a 24-layer split, six draft tokens, a lower draft threshold and six pool workers were all slower or no different.
- On the fork, decode mode 8 and turning chunked GDN off made no difference outside run-to-run noise.

## Not done

- No quality or tool test of 0.2.19 on this model (speed only), no long or sustained run, no context above 47,716 tokens.
- Single runs for most settings; the fork varies a lot between identical runs.
- Inkling was measured afterwards (below).
- The fork route was not switched; the owner asked for separate entries instead (below).

## New routes (owner, November 22–23: "Have all of them on different entry")

Every engine now has its own hub entry; nothing was removed. Pick one by its model name.

| Model name | Engine | Cards | Context | Note |
|---|---|---|---:|---|
| `qwen3.8-flash-next-iq3_xxs` | Strata RDNA3 fork (unchanged, still the default Flash-Next) | both, tensor-parallel decode | 262,144 | faster code decode |
| `qwen3.8-flash-next-iq3_xxs-upstream` | upstream Strata 0.2.19 | both, layer split | 262,144 | about twice the prompt-reading speed, half the RAM |
| `inkling-2-mini-q8` | llama.cpp RDNA3 branch (unchanged) | both | 131,072 | thinking available |
| `inkling-2-mini-sq-20-strata` | upstream Strata 0.2.19 `strata-inkling` | second card only | 131,072 | about twice the decode speed, thinking always off |

Both new entries are sealed packages (engine binary, Strata Control source, configs and weight files hashed in
`dsh/qualified-strata-qwen-profiles.json`) and each passed the strict tool round trip through the hub with no hold or memory-guard event.
The hub code gained a second sealed Strata family for Inkling (`strata-inkling`, one card, card order checked so it can never land on
the display card); an independent review found four problems in the first draft, all fixed, with new unit tests (677 pass).

### Inkling 2 Mini SQ-20 on Strata 0.2.19

The SQ-20 file (19.35 GB, plus the 0.64 GB vision part) came from `strata-engine/Inkling-2-Mini-Strata`; both hashes match the ones
pinned in the 0.2.19 source. It sits on the streaming NVMe drive (`LLM-Models/Inkling-2-Mini-Strata`). The engine needed one local fix to
link (built without position-independent code); the tokenizer was converted with Strata's own tool.

| | llama.cpp route (`inkling-2-mini-q8`) | Strata 0.2.19 (`inkling-2-mini-sq-20-strata`) |
|---|---:|---:|
| Code answer decode (visible tokens) | 43–46 tok/s | 86–90 tok/s |
| Prose decode, 256 tokens | — | 171–385 tok/s (the draft model guesses prose well) |
| Agent turn, 13,040 tokens: prompt read | 1,508 tok/s (one prompt) | 1,310–1,944 tok/s |
| 38,131-token prompt: read | — | 1,761–1,903 tok/s |
| 111,731-token prompt: read | — | 1,174 tok/s (101 s in all) |
| Load | 48.7 s | about 30 s |
| VRAM | both cards | 19.2 GB idle on the second card, 24.0 GB at the 111,731-token prompt |
| Quick test: harness core / extra | not run (existing route) | 12 of 12 / 8 of 8 |
| Function calls (16) / general (10) | 10 / 4 (rescored from saved answers) | 11 / 4 |

- **Thinking is always off in this engine**, but the model still produces hidden reasoning that the server throws away. Those tokens count
  against `max_tokens`: a 256-token code request came back empty, and 6 of the 10 general items hit the 2,048–3,072-token limit with no
  visible answer. Give it a generous `max_tokens`.
- **Context cache in 8 bits** (`--kv fp8`). With the default 16-bit cache the 131,072 context loads but a 111,731-token prompt ran out of card
  memory and the engine stopped (no kernel GPU error, no hold). With 8 bits that prompt worked, peaking at 24.0 of 24.6 GB. A prompt near the
  full 131,072 tokens was not tried and may still not fit.
- Short-request speed with the 8-bit cache was close to the 16-bit runs (prompt read a little lower).
- It uses one card only: on AMD the engine has no two-card mode.

### Not done

- No 216-item suite and no sustained run on either new route; no Flash-Next prompt over 47,716 tokens on 0.2.19.
- Neither new route is the default. The fork stays the default Flash-Next and the llama.cpp route the default Inkling.

## Update to Strata 0.2.20 (November 23)

0.2.20 (tag `v0.2.20`, `a34979fc`, engines 0.1.66) came out the next day: 81 commits. It was built from source in
`hardware/generated/strata-0220-2026-11-23/` (the Inkling engine needed the same no-PIE link fix plus the quant library on the link line).
Relevant here: Inkling on two AMD cards (expert parallel: experts split between the cards, everything else on the first card),
Inkling running Unsloth GGUF experts on AMD cards, a fix so hidden reasoning no longer eats `max_tokens`, multi-GPU fixes. The server now
checks the model name in each request (0.2.19 ignored it); the hub always sends the right name.

**Flash-Next, same settings, three alternating runs each (tok/s):**

| | 0.2.19 | 0.2.20 |
|---|---:|---:|
| Prose decode | 101–109 | 82–106 |
| Code decode | 112–143 | 119–146 |
| Agent turn, 12,862 tokens: read | 1,972–2,548 | 2,364–2,554 |
| Long prompt, 47,716 tokens: read | 4,148–4,172 | 4,137–4,149 |
| Decode after long prompt | 93–119 | 107–127 |

No difference outside run-to-run noise; same expert-cache layout (13,312 + 9,937 slots).

**Inkling 2 Mini SQ-20:**

| | 0.2.19, one card (was the entry) | 0.2.20, one card (now the entry) | 0.2.20, both cards, 262K, 16-bit cache (not an entry) |
|---|---:|---:|---:|
| Code decode, 1,500-token limit | 87 | 89 | 81–84 |
| 256-token code request | empty (hidden reasoning used it all) | 829 characters of code | about 800 characters |
| 38K-token prompt: read | 1,752 | 1,750 | 2,020 |
| 112K-token prompt: read | 1,171 | 1,172 | 1,396 |
| 217,533-token prompt | does not fit | does not fit | 961 tok/s, correct answer |
| VRAM (display card / second card) | 0 / 24.0 GB | 0 / 24.0 GB | 9.6 / 23.2 GB |

Tool calls worked in all three. With two cards the engine put 8.9 GB of experts on the display card and 5.7 GB on the second card,
which keeps the model, the context cache and the drafter; the cards talk to each other directly (`p2p=on`).

**Promoted (owner policy: update unless it breaks):** both entries, `qwen3.8-flash-next-iq3_xxs-upstream` and `inkling-2-mini-sq-20-strata`,
now run 0.2.20 with unchanged settings; both were resealed and passed the strict tool round trip through the hub again.
The two-card 262K Inkling setup is not an entry: it would use 9.6 GB of the display card.

Data: [results](results/strata-0219-flash-next-2026-11-22.json).
