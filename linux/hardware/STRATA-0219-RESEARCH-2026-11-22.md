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
- Inkling on `strata-inkling` was not run: the engine is built, but it needs the 19.35 GB SQ-20 file, which is not on the server.
- The route was not switched. The owner rule of November 17 keeps Flash-Next on the fork.

Data: [results](results/strata-0219-flash-next-2026-11-22.json).
