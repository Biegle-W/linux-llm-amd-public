# DeepSeek DSpark at production settings — October 20, 2026

Codex's Maya screening tested DeepSeek's DSpark draft model only at 8 threads and 8K
context ([MAYA-2026-10-20.md](MAYA-2026-10-20.md)). The user asked for a retest at the
retained production settings. The decision rule was fixed before measuring:
keep DSpark only if every check passes, the geometric mean of
{code decode, prose decode, native ~7K prefill} improves by at least 5% over the mean of two
production runs, and no metric is more than 5% worse.

**Setup:**
- Maya v1.1.17 / `8d9a9b5d`, DeepSeek-V4.1-Flash-1017 Maya-S.
- 32K context, layer groups on both RX 7900 XTX cards, 8 GiB native reserve with at
  least 6 GiB actual startup headroom, and 24 CPU threads.
- Each arm got its own copy of the production expert-routing seed. Production files were
  verified unchanged afterwards.
- Each arm ran `serve-maya-candidate.py`, then `validate-maya.py` (functional checks plus
  ~7K retrieval), then `benchmark-maya-selection.py --context 32768`
  (3 excluded warmups + 3 timed 128-output requests per task).
- Hardware: i9-13900KS, 64 GB.

| Arm | Code decode t/s | Prose decode t/s | Native ~7K PP t/s | Short TTFT code / prose s |
|---|---:|---:|---:|---:|
| A1 `--dspark none` (production) | 11.73 | 6.94 | 155.2 | 0.149 / 0.305 |
| **B `--dspark on`** | **6.66** | **5.66** | 149.3 | 0.361 / 0.515 |
| A2 `--dspark none` (production) | 8.23 | 7.65 | 150.9 | 0.159 / 0.264 |

All three arms passed the functional checks, retrieval, guards and the 6 GiB startup check.

Against the A mean, B changed by **−33.3% code decode, −22.4% prose decode and
−2.5% prefill**, a **−20.4% geometric mean**. **DSpark is rejected; production stays `--dspark none`.**

DSpark accepted **376 of 443** drafted tokens (84.9%), so draft quality is not the problem.
The added draft and verification work costs more than it saves here. Why was not measured;
one possibility is extra expert fetches from RAM-mapped experts per verified token.

DeepSeek's own decode is noisy: the A1 and A2 code medians differ by 30%. B was still below
**both** production runs on code and on prose. Three trials per task do not establish
statistical significance.

**First attempt.** All arms were refused by Maya's admission rule (52 GiB available RAM before
load). Desktop apps left 50.4 GiB. After Chrome was closed (53.3 GiB) the trial ran.
The same rule applies to the normal DeepSeek launcher.

Evidence: [numeric record](results/deepseek-dspark-production-2026-10-20.json). Raw files are in ignored
`hardware/generated/deepseek-dspark-24-2026-10-20/`. The DSpark weights remain on the shared NVMe.
