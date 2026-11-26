# Warm-route timing model · November 25, 2026

Use one serial request per item. For a prompt of P tokens and an expected completion of C tokens, the modeled seconds are `overhead_s + P / prefill_tok_s + min(C, cap) / decode_tok_s`. Sum the seconds over the frozen list. The clock starts after route readiness and one warm-up request. Loading and grading are outside the budget. The class and budget follow the ten-route brief.

Use that route’s own prompt and completion counts on the same item when available. Include capped and wrong answers in timing. For a missing completion, multiply the item’s cross-route median length by the route’s verbosity before applying the cap. Multiplying an already route-specific length would count verbosity twice. Report typical and conservative totals using the same token assumptions. The conservative scenario combines slower rates with a larger short-request allowance. It has no assigned probability and cannot guarantee the deadline.

## Planning inputs

Each pair gives typical / conservative. Rates are tokens per second and overhead is seconds per request. The last column shows the cost of a 500-token prompt and 250 emitted tokens with a cap of at least 250. It illustrates the model at fixed lengths.

| Route | Budget min | Decode | Prefill | Overhead | Verbosity | Example seconds |
|---|---:|---:|---:|---:|---:|---:|
| Qwen 27B vLLM | 15 | 155.1 / 126.5 | 1766 / 743 | 0.146 / 0.205 | 1.3187 | 2.0 / 2.9 |
| Qwen 27B SGLang | 15 | 211.2 / 158.9 | 1736 / 531 | 0.244 / 0.289 | 1.3008 | 1.7 / 2.8 |
| Flash-Next | 15 | 139 / 86.4 | 1480 / 990 | 0.716 / 0.766 | 1.1854 | 2.9 / 4.2 |
| Kolibri | 15 | 80.3 / 77.2 | 2466 / 2412 | 0.054 / 0.06 | 0.6084 | 3.4 / 3.5 |
| Inkling 2 GPU | 15 | 81 / 64 | 1219 / 598 | 0 / 0.05 | 1.6013 | 3.5 / 4.8 |
| Ripple | 30 | 28 / 28 | 764 / 700 | 0.009 / 0.05 | 1.7565 | 9.6 / 9.7 |
| DeepSeek Maya | 30 | 7.2 / 6.8 | 72.5 / 35 | 8.494 / 16.973 | 0.7044 | 50.1 / 68.0 |
| DeepSeek Strata | 30 | 10 / 8 | 134 / 79 | 9.129 / 13.614 | 0.7088 | 37.9 / 51.2 |
| GLM Maya | 30 | 10.8 / 5.2 | 162 / 57 | 2.301 / 2.363 | 0.1286 | 28.5 / 59.2 |
| Hy4 SQ-64 | 30 | 43.5 / 41 | 830 / 613 | 2.589 / 2.879 | 0.2964 | 8.9 / 9.8 |

## Calibration against the public suite

Fit each recorded route or proxy separately by ordinary least squares, using `seconds = h + p × prompt_tokens + c × completion_tokens`. The table shows `1/c` and `1/p`, the fitted intercept h and the median absolute residual on the fitting data. Include all measured items with token counts. The 300-item saved file supplies the four corresponding routes and already includes their 216 core items. The fixed design uses these fits as historical baselines. For current throughput, multiply the fitted rates by the displayed current/fit ratios (rounded here) or use the calibrated rates in JSON directly. These ratios include differences in request mix and represent planning adjustments, not causal engine speedups.

| Route | Records | Fit decode | Fit prefill | Fit h (s) | Median abs. error (s) | Current/fit decode | Current/fit prefill | Nov 24 tool test (min) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen 27B vLLM | 300 | 126.5 | 743.1 | 0.03 | 0.555 | 1.226 | 2.377 | 3.46 |
| Qwen 27B SGLang | 300 | 158.86 | 530.75 | 0.155 | 1.036 | 1.329 | 3.271 | 3.21 |
| Flash-Next | 300 | 57.67 | 495.24 | 0.353 | 0.517 | 2.41 | 2.988 | 9.11 |
| Kolibri | 26 | 77.17 | 2412.26 | 0.045 | 0.02 | 1.041 | 1.022 | 2.65 |
| Inkling 2 GPU | 216 | 44.65 | 1218.68 | -0.176 | 0.066 | 1.814 | 1.0 | 9.95 |
| Ripple | 300 | 28.56 | 700.02 | -0.13 | 0.06 | 0.98 | 1.091 | 35.34 |
| DeepSeek Maya | 216 | 19.19 | 41.61 | 21.478 | 14.436 | 0.375 | 1.742 | 56.0 |
| DeepSeek Strata | 216 | 18.81 | 44.58 | 23.553 | 11.742 | 0.532 | 3.006 | 56.0 |
| GLM Maya | 216 | 20.99 | 89.89 | 3.384 | 1.426 | 0.515 | 1.802 | 35.24 |
| Hy4 SQ-64 | 26 | 26.93 | 354.4 | 2.028 | 0.786 | 1.615 | 2.342 | 47 |

The final column comes from `docs/results/tooluse-short-2026-11-24.json`, dividing each run’s `item_seconds` by 60. Hy4’s 47 minutes comes from the separate side-server trial in `docs/CURRENT-AMD-BENCHMARKS.md`. These are whole-workload observations on a different mix of single-turn and multi-turn items at temperature 0.6. The DeepSeek runs reached the 56-minute item budget during extra episodes. Dividing those totals by 49 would confound multi-request episodes with individual request latency.

### Fixed request cost

The supplied public results record wall seconds and token counts. The supplied short tool results record load and aggregate item time. Neither provides per-request first-token times for short prompts. Published first-token checks (for example, GLM’s 37 seconds on 6K tokens) include a substantial prompt pass. Treating that interval as fixed overhead would charge for the prompt twice.

Infer short-prompt first-token latency from the historical records. Keep prompts up to 512 tokens and take the twelve shortest completions per route, sorting ties by prompt length and elapsed seconds. Approximate the time before decode by subtracting the fitted historical decode cost from the elapsed time. Subtract the historical fitted prompt cost to isolate fixed overhead, then use the median of those twelve residuals, floored at zero. For the conservative model use their linearly interpolated 75th percentile, floored at 0.05 seconds and at the typical cost. The 0.05-second minimum is a planning allowance. Small negative residuals for Inkling are consistent with measurement error at this scale. No direct short-prompt first-token trace is available to confirm the carry-over to the new engines. Both DeepSeek fits have substantial residual variation.

### Rate sources and engine changes

The Nov 25 figures refer to the brief’s current speed facts. The strict tool table and update notes refer to `docs/CURRENT-AMD-BENCHMARKS.md`.

- **Qwen 27B vLLM and SGLang.** Use the table’s strict tool decode and prompt read rates for typical cost. For slow cost, use the lower-throughput public-suite fits, rounded to the precision shown.
- **Flash-Next.** The saved suite decodes at 57.7 tokens/s. Upstream replaced the former engine. Use the Nov 25 short-answer figure of 139. The update notes report about twice the fork’s long-prompt read speed. Apply that gain to the fork’s strict 740 for typical prefill and twice the saved suite fit of 495 for the slower scenario. For slow decode, apply the reported 10% code slowdown to 96, the fork’s low end on its fixed request set. These are cross-workload transfers.
- **Kolibri.** The current table gives 80.3 and 2,466. Its 26-item same-build quick run gives 77.2 and 2,412 after rounding. This is the broadest same-weight calibration available.
- **Inkling.** Use 81 from the two-card code range of 81–84. The brief gives 64–90, so use 64 for slow decode. Current SQ-20 prefill is missing. Use the 1,219 fit from the retired RDNA3 Q8 run and 598 from the upstream Q8 run for slow prefill. The two engines on Q8 are family proxies for prompt speed and answer length, with the RDNA3 run supplying the production model’s length and overhead assumptions.
- **Ripple.** The strict figures are 28 and 764. The suite fits 28.56 and 700.02. Use the lower of each pair for the slow case, rounded as shown.
- **DeepSeek Maya.** The Nov 25 figures are 7.2 decode and 35–110 prefill. Typical prefill of 72.5 is the range midpoint. Slow decode of 6.8 comes from the older strict test and 35 is the low prompt reading. The historical suite fits about 19 decode. Extrapolating that throughput would substantially shorten current forecasts.
- **DeepSeek Strata.** Use 10 and 8, the midpoint and low end of the brief’s 8–12. The store-off warm test gives 125–143 prefill with a low observation of 79. Use 134 and 79. Use the store-off public run for the historical fit.
- **GLM Maya.** Use 10.8 current decode and an effective prefill of about 162 (6,000 prompt tokens / 37 seconds). The latter includes first-token overhead, making the additive timing estimate slightly conservative at that prompt length. The slow case uses the older strict figures of 5.2 and 57.
- **Hy4 SQ-64.** The brief’s current decode range of 41–46 gives 43.5 and 41. Use 830 prefill from the 10.9K-token prompt and 613 from the older strict check for the slow case. The one-card 26-item SQ-64 run supplies timing and verbosity history. The Maya-M trial used a different engine and quantization.

### Length reference and audit inputs

For each of the 216 core IDs, take the median completion length over the eight route families/engine entries with complete core records in the table. This fixed panel excludes Kolibri and Hy4, and includes both Qwen 27B engines, Flash-Next, Inkling Q8 RDNA3, Ripple, both DeepSeek engines and GLM. Divide the route’s summed observed completions by the summed reference medians over exactly its measured core IDs. This ratio of totals preserves each route’s observed total token volume across its matched sample. Capped records measure output through the old cap. Neither the ratio nor those records reveal how much longer an uncapped answer would have been.

Inkling and Ripple keep reasoning with thinking disabled. Their 1.60× and 1.76× length estimates include those tokens. Applying a lower cap can reduce their predicted time while increasing truncations and lowering their scores. For Kolibri and Hy4, use their own 26-item samples. Their length ratios have limited coverage across categories. When route-specific observations exist for a given item, those observations also capture category differences that a single route-level multiplier loses.

| Route or proxy | Source for fit, short-request residuals and observed lengths | Matched length IDs |
|---|---|---:|
| Qwen 27B vLLM | `data/pub-core-and-fast/graded-fast-all.json` | 216 |
| Qwen 27B SGLang | `data/pub-core-and-fast/graded-fast-all.json` | 216 |
| Flash-Next | `data/pub-core-and-fast/graded-fast-all.json` | 216 |
| Kolibri | `data/quick-kolibri/graded.json` | 26 |
| Inkling 2 GPU | `data/inkling-q8-rdna3/graded.json` | 216 |
| Ripple | `data/pub-core-and-fast/graded-fast-all.json` | 216 |
| DeepSeek Maya | `data/pub-core-and-fast/graded-core11.json` | 216 |
| DeepSeek Strata | `data/strata-deepseek-nostore/graded.json` | 216 |
| GLM Maya | `data/pub-core-and-fast/graded-core11.json` | 216 |
| Hy4 SQ-64 | `data/quick-hy4-sq64/graded.json` | 26 |

Two supplemental fits check the available family evidence. The upstream Inkling Q8 hub run (`data/inkling-q8-hub/graded.json`, 216 items) fits 30.42 decode, 597.71 prefill and −0.189 seconds intercept. The alternate Hy4 Maya-M trial (`data/quick-hy4-maya-m/graded.json`, 26 measured items) fits 25.85 decode, 147.53 prefill and 4.147 seconds intercept. The JSON records the chosen route or proxy and rate provenance per row. Production validation requires a timed run of the frozen list on the current engines.
