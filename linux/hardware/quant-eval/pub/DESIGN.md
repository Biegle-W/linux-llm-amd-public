# Public local quality test: frozen design v1

Design date: 2026-11-10. This document governs the subsequent builder/grader alignment tasks; the existing harness configuration is provisional. Read the **Verification (kimi)** section of `datasets.md` before using earlier survey claims. No model has been measured for this design. Accuracy ranges for custom subsets are hypotheses, not verified benchmark results.

## 1. Decision and estimand

Run **216 identical core items on all 12 routes**, then **84 additional identical items on the eight faster routes**, giving 300 items on those routes. Primary outcome is first-attempt, thinking-off, zero-temperature, item-level accuracy on the core, including response failures and truncations as failures. Each item has equal weight; the category mixture below defines this particular test, not a universal measure of intelligence. Also report each category separately. The extension is secondary and cannot change a comparison involving a route that only ran the core.

No thinking-on arm and no scored repeats in v1. These would spend scarce slow-route time on fewer independent questions; thinking-on also requires a different runner configuration and substantially changes the task. Temperature zero does not guarantee deterministic engine output. Engine-to-engine differences are observable deployment differences, not isolated estimates of model quality or quantization damage.

Exclude ZebraLogic because its license attribution is not established in the survey's verification, and exclude LiveBench coding because compressed private-test decoding and official task adapters add avoidable risk. Exclude symbolic HMMT answers, language-detection IFEval rules, and true long-context tasks. MuSR supplies moderate-context reasoning, not a long-context benchmark.

## 2. Sources, exact quotas, eligibility, budgets

“Extra” means disjoint additional items, not the cumulative total. Pools use the listed source/config/split. Licenses/provenance are inherited from the survey verification and must appear per item and in the source lock. The MATH-500 mirror does not itself declare a license; record `MIT (upstream MATH); mirror license unset`, not a newly verified mirror license.

| Category | Pool | Core | Extra | max_tokens | Planned mean output/item |
|---|---|---:|---:|---:|---:|
| knowledge | TIGER-Lab/MMLU-Pro, default/test | 60 | 20 | 2048 | 100 |
| math | HuggingFaceH4/MATH-500, default/test, L4–5 rational answers | 24 | 20 | 3072 | 450 |
| math | math-ai/aime24, default/test | 8 | 0 | 4096 | 450 |
| math | math-ai/aime25, default/test | 8 | 0 | 4096 | 450 |
| code | bigcode/bigcodebench, default/v0.1.4, stdlib-only | 20 | 8 | 3072 | 350 |
| instruction | google/IFEval, default/train, supported 2–3 constraints | 32 | 12 | 2048 | 180 |
| tools | BFCL v4 parallel_multiple | 16 | 4 | 2048 | 100 |
| tools | BFCL v4 multiple | 8 | 4 | 2048 | 100 |
| tools | BFCL v4 irrelevance | 8 | 4 | 2048 | 100 |
| reasoning | TAUR-Lab/MuSR, default/object_placements | 16 | 6 | 2048 | 160 |
| reasoning | TAUR-Lab/MuSR, default/team_allocation | 16 | 6 | 2048 | 160 |
| **Total** | | **216** | **84** | | |

Core category counts: knowledge 60, math 40, code 20, instruction 32, tools 32, reasoning 32. Cumulative fast-route counts: knowledge 80, math 60, code 28, instruction 44, tools 44, reasoning 44. Treat math as one category despite three pools.

MMLU-Pro quotas, core/extra: physics 10/4, chemistry 10/4, engineering 10/4, computer science 10/4, law 10/2, economics 10/2. Use original option order; no few-shot examples, no answer-bearing `cot_content`. These domains are a reproducible selection, not a verified difficulty filter.

MATH eligibility: original `level` 4 or 5 and gold representable as a signed integer or exact rational. Accept `\\frac`, `\\dfrac`, `\\tfrac` with integer numerator and nonzero integer denominator, and `a/b`; normalize with `fractions.Fraction`. Strip only enclosing math delimiters/boxed wrapper and harmless spaces. No symbolic expressions, radicals, tuples, intervals, approximate decimal gold, or units. Do not select based on model responses. Do not impose a difficulty filter on AIME; sample from all 30 questions of each year, preserving original problem text and stable original ID. Selection of only eight per year deliberately limits the cost of a possible floor.

BigCodeBench eligibility: every declared library must have a root in `sys.stdlib_module_names` on Python 3.14 (plus `__future__`); all imports in supplied tests and reference implementation must likewise be stdlib. Exclude external files/services, explicit network access, subprocess/fork requirements, interactive or GUI tasks, and unavailable platform modules. Run the upstream reference implementation with its supplied tests in the same sandbox before freezing the eligible pool; require every test to pass within the grading limits below. **[changed by red team]** Repeat this reference run three times in fresh sandboxes and exclude any item with flaky, seed-dependent, or resource-borderline results. This is an eligibility check, not evidence about model output. Never execute reference or test code in the builder process. Record each exclusion ID and reason in a local build audit file. If fewer than 28 eligible tasks remain, fail loudly; no silent easier substitute. Preserve official test source and function signature; never put tests, reference implementation, or gold into the request.

IFEval eligibility: 2–3 constraints, all from this allowlist:
`punctuation:no_comma`, `change_case:english_capital`, `change_case:english_lowercase`, `keywords:existence`, `keywords:forbidden_words`, `keywords:frequency`, `length_constraints:number_words`, `detectable_format:json_format`, `startend:end_checker`, `startend:quotation`, `detectable_format:title`, `detectable_format:number_bullet_lists`, `detectable_format:number_highlighted_sections`.
Use pinned official checker semantics for these IDs, including tokenization, boundary matching, Markdown handling, and threshold relations. The current simplified checkers must be audited during alignment; approximate whitespace counts or regexes must not be described as official scoring. If exact stdlib parity for an ID is unavailable, remove that ID from eligibility **before** freezing items, document the removal and obtain the same 44-item quota from the remaining eligible pool; rebuild manifests before any inference. No language/script substitutes for `langdetect`. Score prompt-strict (all constraints pass); optional instruction-strict is diagnostic only.

BFCL files are `BFCL_v4_{parallel_multiple,multiple,irrelevance}.json` under `ShishirPatil/gorilla/berkeley-function-call-leaderboard/bfcl_eval/data/`, with matching `possible_answer` files for call-requiring pools. Use the exact verified URL patterns in datasets.md, pinned to a commit. Restrict to a single request turn and Python function schemas convertible losslessly to OpenAI tools. Reject unknown schema types or ambiguous name conversion. Irrelevance needs no answer file: success means a valid completed response with no calls. This tests selection/arguments/abstention, not execution of a real tool or multi-turn agency.

MuSR: use narrative and question unmodified, parse stringified choices with `ast.literal_eval` (never `eval`); map `answer_index` to original choice order. Do not combine narratives or invent distractors.

## 3. Deterministic selection and immutable artifacts

Seed is **20261110**. For each pool/stratum, determine all eligible original IDs first. When a source lacks an ID, use its locked source row index as a decimal string; duplicate IDs are fatal. Rank eligible records by `(SHA256(UTF8("20261110|" + pool_key + "|" + stratum_key + "|" + original_id)).hexdigest(), original_id)`. Pool keys are `mmlu`, `math`, `aime24`, `aime25`, `code`, `ifeval`, `tools_parallel_multiple`, `tools_multiple`, `tools_irrelevance`, `musr_object`, `musr_team`; stratum is the domain for MMLU and `all` otherwise. Take the first core quota, then the next extra quota. Do not use Python's randomized `hash()`. This replaces the provisional RNG shuffle in the current builder.

Source revisions, row counts, full canonical row-data SHA-256 hashes, license caveats and source URLs are locked before sampling. Paginated HF viewer rows are not immutable revision URLs: check upstream revision before and after the fetch AND compare full canonical content hash to the reviewed lock; reject truncated cells, missing/reordered pages, source drift, or unexpected schema. An offline cache must pass the same content hash. `--update-lock` is a separate reviewed maintenance action, never automatic during a run. Fail if a quota cannot be met.

Item IDs include pool key plus original ID; core and extras are disjoint. Reject duplicate normalized problem texts across pools (normalize line endings and collapse whitespace); fail with both IDs for review rather than silently resample. Record source, revision, original ID, category, tier, license, prompt, grading metadata, test source and sampler/config version. Canonical JSON serialization is UTF-8, `sort_keys=True`, `ensure_ascii=False`, separators `(',', ':')`; each item is one JSONL line plus newline. Manifest hashes the exact item file and configuration, and has counts by category/pool/tier. Every result/report records the item-manifest hash, run date, route ID, served weight/engine configuration, runner/grader version, and timeout policy. Credentials are unnecessary.

Request order is hash-ranked independently within each tier by `SHA256(UTF8("20261110|order|" + item_id))`, tie by ID. All routes see this same order. `PUB_TIER=core` selects core; `extended` selects extras only; `all` selects core followed by extras. Do not let `all` accidentally interleave extras ahead of core. Freeze the whole item manifest before seeing any route answer.

## 4. Exact requests

Common request fields: `temperature=0`, `stream=False`, category's `max_tokens`, and `chat_template_kwargs={"enable_thinking": false, "thinking": false}`. The runner supplies `model`. Do not set provider-specific stop strings, seeds, logit biases or response formats. Hidden or inline reasoning counts against output cost even with thinking disabled. Preserve separate `reasoning_content`/`reasoning`, `content`, `tool_calls`, finish reason, usage and elapsed seconds.

For MCQ, numeric and code tasks, system message is exactly:

```text
Solve the task carefully. Follow the requested final-answer format.
```

MCQ user template (MMLU and MuSR):

```text
{question}

{options}

Return your final answer as ANSWER: X, where X is the correct option letter.
```

`options` is newline-joined `A. {choice}`, `B. {choice}`, etc.; retain original option text. For MuSR, `question` is `{narrative}\n\n{question}`. No solution or explanation is supplied. The instruction requests a final answer, without forbidding concise working; it does not claim that all engines actually stop reasoning.

Math user template:

```text
{problem}

Return your final answer as ANSWER: <number>, using an integer or an exact fraction.
```

Code user template:

```text
Implement the following Python task using only the standard library. Return the complete implementation in a single Python code block, with no tests.

{instruct_prompt}
```

Use the BigCodeBench `instruct_prompt` and its specified function interface. The complete response must define that function and required imports. Do not append canonical implementation text to a candidate; do not score a completion-only fragment as a full implementation. Validate this assembly against the reference before freezing.

IFEval: exactly one user message containing the original `prompt`, no system message, no added formatting instruction. Raw response content is scored, not a cleaned version.

Tools: **[changed by red team]** assert that BFCL's outer `question` list contains exactly one turn and use `question[0]` as the API `messages`; preserve that turn unchanged and add no system text. Convert function definitions to OpenAI `tools` with `tool_choice="auto"`. Convert Python schema type names recursively: `dict→object`, `list/tuple→array`, `float→number`, `int→integer`, `str→string`, `bool→boolean`; preserve descriptions, enum values, nesting and required lists. Replace `.` in function names by `_` consistently in tool schemas and gold; reject collisions or names outside OpenAI's allowed character/length rules. Record reversible mapping. Do not instruct the model to write a tool-call-shaped string. Only structured `message.tool_calls` can earn a call-requiring success. No tools are actually invoked during inference.

## 5. Runtime plan and ceiling

Serial inference only, one resident route at a time. Core route order:

1. empero-qwen3.8-35b-a3b
2. glm-5.3-flash-maya
3. deepseek-v4.1-flash-1017-strata-unsloth-q1
4. deepseek-v4.1-flash-1017-maya-unsloth-q1
5. ornith-1.5-122b
6. flint-40b-a2.5b
7. ripple-65b-vllm
8. nemotron-3.5-bolt-vllm
9. qwen3.8-flash-next-iq3_xxs
10. sage-a1.5
11. qwen3.8-27b-vllm
12. qwen3.8-27b-sglang-dflash2

This gets a quick integration check and the major time risks early. Optional single unscored warmup per load: user `Reply OK.`, max_tokens 32, same thinking settings; include its wall time in the log. Core comes first for every route; do extras afterward in the same relative route order on the eight routes whose brief decode speed is **at least 28 tok/s**. Extra membership is predeclared, never selected by score. Reuse the final loaded fast route for its extras first if desired; any such scheduling change is logged and does not alter item order.

Planning output, not caps: core tokens = `60*100 + 40*450 + 20*350 + 32*180 + 32*100 + 32*160 = 45,080`; extra tokens = `20*100 + 20*450 + 8*350 + 12*180 + 12*100 + 12*160 = 19,080`. These means are **unmeasured assumptions**. All emitted reasoning and tool argument tokens count. Divide tokens by brief decode speed, then by 3600:

| Route | tok/s used | Core decode h | Extra decode h | Total decode h |
|---|---:|---:|---:|---:|
| empero-qwen3.8-35b-a3b | 173 | 0.072 | 0.031 | 0.103 |
| flint-40b-a2.5b | 64 | 0.196 | 0.083 | 0.278 |
| ornith-1.5-122b | 11.6 | 1.080 | — | 1.080 |
| qwen3.8-27b-vllm | 155 | 0.081 | 0.034 | 0.115 |
| qwen3.8-27b-sglang-dflash2 | 211 | 0.059 | 0.025 | 0.084 |
| nemotron-3.5-bolt-vllm | 40 | 0.313 | 0.133 | 0.446 |
| sage-a1.5 | 140 | 0.089 | 0.038 | 0.127 |
| ripple-65b-vllm | 28 | 0.447 | 0.189 | 0.637 |
| qwen3.8-flash-next-iq3_xxs | 66 | 0.190 | 0.080 | 0.270 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | 5.6 | 2.236 | — | 2.236 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | 5.6 | 2.236 | — | 2.236 |
| glm-5.3-flash-maya | 5.2 | 2.408 | — | 2.408 |
| **Fleet** | | **9.408** | **0.612** | **10.020** |

The two DeepSeek routes use the pessimistic end of 5.6–6.8. There are `216*12 + 84*8 = 3264` scored requests. Allow mean 2 s/request for prefill/request overhead (1.813 h), 60 s/load for 12 initial loads plus eight extra-phase loads (0.333 h), and 1.0 h for serial grading: **[changed by red team] 13.17 h planned wall time**. The grading allowance covers 304 code candidates, whose 10 s wall timeouts alone can take 0.844 h; reference-pool validation is separately timed preflight. Load time, prefill time and grading time are not verified. Reusing a resident route saves one load. A 25% output-token overrun adds 2.51 h; at 5 s/request overhead instead of 2 s, planned wall time becomes 15.89 h. Doubling output adds 10.02 h and would exceed 20 h including overhead.

**max_tokens is not an expected length.** Full caps are 520,192 tokens/core route and 200,704 tokens/extra route, giving approximately **115 h of decode** across this schedule. Claiming a deterministic 12–20 h bound from these caps would be false. Do not reduce caps mid-run to force the estimate to fit.

A small `run_pub.py` wrapper/update to the reference runner is required: retain its result schema/resume behavior, add a monotonic fleet-start timestamp persisted across invocations, per-attempt log, and hard elapsed-time guard. Check elapsed time before every request, with client deadline `min(1200 s, remaining fleet budget)`; do not start further work at 19.5 h, and terminate client waiting at 20 h. Request cancellation may not stop backend generation; the chair must stop/drain the active server generation to enforce a physical compute ceiling. **[changed by red team]** The 20 h deadline also covers grading: grade incrementally or reserve sufficient remaining time, and leave anything ungraded at the deadline pending rather than overrun. The supplied `run_suite.py` alone has a 5400-second timeout and cannot enforce this fleet ceiling.

After each route's first 24 scored core items, log actual emitted tokens, time and projected route/fleet duration; these 24 stay in the primary sample. Do not adapt questions, caps, route membership or grading to their answers. If projected time exceeds 18 h, omit **all** extra work; finish the full common core if possible. Do not substitute a shorter item set after observing outcomes. If the full core cannot finish by the ceiling, stop and mark the run incomplete; publish coverage and only explicitly labeled exploratory comparisons on identical completed item IDs, not the intended 216-item ranking. If extras only partly finish, primary core results remain valid; do not compare partial 300-item totals. Preserve pending IDs and timeout errors separately.

Do not score repeated attempts or best-of-N. HTTP, malformed response and timeout failures in a started request are zero-credit first-attempt outcomes, with their logs retained. Missing items because the fleet stopped are pending, not inference failures; primary reporting is incomplete even if a diagnostic denominator of 216 assigns them zero. Restarting a process resumes IDs without replacing existing failed/capped responses. Infrastructure debugging reruns must use a separate results directory and be identified separately.

## 6. Scoring contract

All primary item scores are binary. Successful completion may have finish `stop` or, for structured tool calls, `tool_calls`. A response with `finish == "length"` is always primary zero and has a distinct capped flag, even if its visible partial answer would pass; report visible-answer accuracy on capped cases only as diagnostic. Error, empty required answer, refusal, malformed answer and failed tests are primary zero, with separate counts. Unsupported grader types, corrupted gold, reference-test failure or implementation exceptions are **grader defects**, not model mistakes: stop analysis and repair/regrade every route uniformly. Never silently drop an item for one route.

For answer extraction (MCQ/math only), remove complete `<think>…</think>` blocks and stray closing/opening tag tokens from content; if a complete prefix has a closing `</think>` without an opening tag, treat the prefix as reasoning and take the suffix. Never use the separate reasoning field to rescue a missing final answer. An unmatched opening think block hides its remaining text. Do not clean code interiors or IFEval raw output. Mark extraction path for audit.

MCQ: locate the last explicit `ANSWER: X`/`Final answer: X` marker; if its payload is not exactly one valid, optionally parenthesized option letter, mark the response malformed and do not fall back to an earlier answer. Otherwise use that letter. If there is no explicit marker, use the last boxed letter; otherwise require a response consisting only of an optional `Answer` prefix and a single optionally parenthesized letter. Match case-insensitively. Do not grab the last free-standing letter from arbitrary prose. **[changed by red team]** This final-explicit-wins rule also applies to malformed explicit values, removing ambiguity between precedence and fallback. Math: same precedence for explicit numeric markers, then final balanced boxed value, then an entire bare number/fraction; a malformed final explicit value likewise forbids fallback. **[changed by red team]** Normalize candidate math delimiters and `\frac`, `\dfrac`, `\tfrac` by the same rules as gold, then parse with Fraction; allow equivalent exact decimal candidate answers, correctly comma-grouped integers and AIME leading zeros. After an otherwise explicit scalar, allow benign trailing punctuation, an optional ordinal suffix, and an optional trailing unit from a frozen allowlist that includes `day`/`days` (so `47th day` can match 47); never discard arbitrary prose. No tolerance-based match, expression evaluation, arbitrary-number search, or integer pulled from working. Inspect ambiguous extraction cases as a shared grader QA exercise before publishing, without route-specific changes.

Code: extract one Python fence (or an entirely raw Python response); reject ambiguous multiple implementation blocks rather than concatenate arbitrary prose. Run candidate plus upstream tests in a new temporary directory with `python3 -I`, CPU limit 5 s, parent wall timeout 10 s, address-space limit 512 MiB on Linux, file size/output cap 1 MiB, no stdin, process-group cleanup, and subprocess/fork/network denial. No `eval` of model output in-process. Tests must actually execute at least one test; syntax/import/time/memory/runtime/test failure is zero. **[changed by red team]** Use an unprivileged disposable container/VM with no host home/workspace mounts or credentials and with network disabled; `unshare -n` may supplement but not replace that boundary. Isolation is fail-closed: if it cannot be verified, do not execute reference or candidate code; mark code results ungraded and the run incomplete. Python audit hooks and resource limits are not a complete security boundary. Reference baseline and candidate must have identical assembly, limits and isolation; audit test-count/results and record isolation evidence. Do not download dependencies or run installation commands from generated code.

Tools: parse `tool_calls[*].function.arguments` as JSON objects. Require an exact multiset match of function names and argument dictionaries to BFCL accepted alternatives; call order and JSON key order do not matter, but missing/extra/duplicate calls and unexpected parameters fail. Match each call to one distinct gold call using bipartite/backtracking assignment, not greedy pairing. Respect BFCL's per-parameter accepted-alternative representation and typed nested values; do not indiscriminately coerce strings to numbers or booleans to integers. Omitted optional parameters are allowed only when the gold semantics explicitly allow omission. A prose representation of a call never substitutes for structured calls. Irrelevance passes only on a valid nonempty completed response and zero calls (an API error/empty response does not pass).

IFEval: primary is raw-content prompt-strict, all supported original constraints pass. No removal of thought tags, case folding of the whole output, whitespace trimming, or code-fence stripping except where the pinned official checker itself does so. Moderate-context MuSR uses the MCQ contract. Report capped/error/empty/refusal/test-failure counts as overlapping diagnostic flags where appropriate, alongside one mutually exclusive primary status per item.

## 7. Statistical analysis and interpretation

Primary score is `sum(binary_success)/216`, with exact selected IDs retained. Report Wilson 95% pointwise intervals per route (z=1.959963984540054), including failures in the denominator. These intervals describe uncertainty under an item-sampling approximation for this fixed mixture, not uncertainty from repeated engine runs or all future tasks. Stratification, a small sample of finite AIME pools, and correlated benchmark questions limit a literal iid interpretation. A per-category table gives successes, n, accuracy, Wilson interval, caps, errors, pending and malformed counts. Categories with n=20–60 have wide intervals; do not use them to assert narrow rankings.

Expected Wilson **half-widths** (percentage points):

| Actual accuracy | Core n=216 | Cumulative fast n=300 |
|---|---:|---:|
| 50% | 6.61 | 5.62 |
| 60% | 6.48 | 5.51 |
| 75% | 5.74 | 4.88 |

Full CI widths are twice these values. Do not infer a significant paired difference from nonoverlap/overlap of these marginal intervals.

For each pair A,B, align by manifest and exact item IDs. Let b=A-only successes, c=B-only successes, m=b+c. Difference is `(b-c)/n`. Exact two-sided McNemar p-value is `min(1, 2*sum(comb(m,k) for k in range(min(b,c)+1))/2**m)`; p=1 for m=0. Use stable arithmetic/recurrences if needed. No continuity-corrected chi-square approximation for small m. Report b, c, n, difference, raw p and Holm-adjusted p. A test assumes independent pairs; repeated variants of the same problem must not masquerade as independent items.

Primary comparison family is all **66** unordered pairs of 12 core routes. Holm step-down at familywise alpha .05: sort raw p ascending with route-name tie break; adjusted p at rank i is `min(1,max(previous,(66-i+1)*p_i))` for i=1..66. Declare a primary difference only if adjusted p<=.05; otherwise say “not resolved by this test,” not “equivalent.” Do not announce a uniquely best route unless its relevant core comparisons support that claim. The fast-only 300-item analysis is a **secondary exploratory** family of 28 pairs; apply Holm within those 28 and label it secondary. It is not an additional confirmatory ranking. For a single family covering both analyses, provide an optional Holm correction across all 94 hypotheses.

Provide paired, **source/stratum-preserving** bootstrap intervals: for each pair, sample with replacement within each frozen sampling stratum, keeping original stratum counts; carry A and B's outcomes together for every draw, aggregate with original item weights. Strata are the MMLU domains and each other source pool. 10,000 replicates, RNG `random.Random("20261110|bootstrap|" + smaller_route + "|" + larger_route + "|" + tier)`, where smaller/larger means lexicographic route-ID order **[changed by red team]**; report 2.5th and 97.5th percentiles using sorted order statistics indices floor(.025*(B-1)) and ceil(.975*(B-1)). Flip interval sign if displaying the reversed pair. These are pointwise estimation intervals, not simultaneous 66-pair intervals; McNemar/Holm governs significance. At b=c=0, bootstrap may degenerate to [0,0], which is not evidence of equivalence. Do not bootstrap routes independently or pool core and extras with missing values. An ordinary category-only stratified bootstrap is insufficient when source quotas differ within math/tools/reasoning.

Approximate 80%-power minimum detectable paired differences use `(z_(1-alpha/2)+0.84162)*sqrt(q/n)`, where q is the probability of discordance; this normal approximation is for planning and exact discrete power may differ. q is unknown, so give scenarios, not one promised sensitivity:

| Discordance q | Core unadjusted .05 | Core conservative first Holm threshold .05/66 | Fast n=300 unadjusted | Fast conservative .05/28 |
|---|---:|---:|---:|---:|
| .20 | 8.5 pp | 12.8 pp | 7.2 pp | 10.2 pp |
| .30 | 10.4 pp | 15.7 pp | 8.9 pp | 12.5 pp |
| .50 | 13.5 pp | 20.3 pp | 11.4 pp | 16.2 pp |

Observed discordance can refine a post-run sensitivity description, not retrospectively justify selective hypothesis testing. Very similar engines may have low discordance, but a tiny number of changed answers still gives discrete, weak evidence. This experiment will not reliably resolve 1–3 pp fleet differences. Repeats are absent, so results cannot distinguish backend nondeterminism from stable item-level differences.

## 8. Limits and release checklist

Public tests may be in training data. AIME, MATH, MMLU-Pro, IFEval and BigCodeBench are familiar public benchmarks; 2024/2025 origin does not imply contamination-free in late 2026. Procedural origin also does not guarantee that published instances were unseen. Do not claim zero contamination. We measure selected subsets with zero-shot local templates, not official full benchmark protocols, few-shot/CoT scores, pass@k, majority voting or tool-execution leaderboards. No verified source establishes a 40–80% accuracy band for these exact subsets; a floor or saturation remains possible.

Quantized IQ1/IQ2/IQ3/IQ4, GPTQ and AutoRound deployments, offloading and serving engines differ from published full-precision evaluations and from one another. Thinking is disabled by request but some routes still reason inline, spend budget differently, or ignore that flag. Tool schemas/adapters and response parsing affect deployment scores. There is no isolation of causal quantization effects, no inference about a model's best thinking-on capability, no security benchmark, no real long-context conclusion, and no universal leaderboard ranking.

Before inference: align harness with this design; freeze source/config/item manifests; finish reference-code and IFEval parity checks; run offline right/wrong/capped/tag-leak/malformed and sandbox selftests, **[changed by red team]** including LaTeX fractions, `47th day`, nested BFCL turns/typed values, and isolation-failure refusal; verify requests contain no gold; record available isolation; implement the fleet guard. Before reporting: validate identical manifests, denominators and IDs; audit caps/errors/pending and grader defects; publish core and secondary tables separately, usage and actual fleet time, paired counts and adjusted p-values; describe unresolved differences plainly. Any post-freeze amendment needs a new design/manifest version and disclosure; never overwrite prior results to manufacture a cleaner ranking.

## Red-team findings

1. **Difficulty is still a hypothesis.** The 16 AIME items can floor while BFCL/IFEval can saturate; eight items per AIME year cannot support separate yearly claims. **Fix:** before final freezing, optionally pilot 24–36 *disjoint eligible* items on one fast and one slow route, with predeclared pool-level floor/saturation thresholds and separately accounted time; change only whole pools before freezing, never selected IDs based on their scores. Without that pilot, retain the limitation and judge each category rather than assuming a 40–80% overall band.
2. **Decode arithmetic is correct, grading was not conservative.** Recomputed totals are 45,080 core tokens, 19,080 extra tokens, 10.020 decode h, 1.813 request-overhead h, 0.333 load h, and 115.001 h at full output caps. **Fix applied:** 304 code candidates make the old 0.1 h grading allowance inconsistent with the 10 s cap (0.844 h maximum); the plan is now 13.17 h with 1.0 h grading, a 5 s/request scenario is stated, and grading is inside the 20 h deadline.
3. **The code sandbox was fail-open.** Recording failed `unshare -n` and proceeding could expose the host network, and `python3 -I` is not a security boundary for generated or downloaded code. **Fix applied:** require a verified unprivileged disposable container/VM with no network, host home/workspace mounts, or credentials; otherwise leave code ungraded and the run incomplete.
4. **Math extraction could reject correct conventional answers.** The old rules did not clearly accept candidate `\frac{1}{2}` or the brief's known `47th day` case. **Fix applied:** candidate LaTeX fractions use the same normalization as gold, a frozen minimal unit allowlist is permitted only after an explicit scalar, comma grouping must be valid, and these cases are required selftests.
5. **BFCL is fetchable, but its nesting must not be flattened.** Fresh unauthenticated `curl` checks of the `parallel_multiple` question and `possible_answer` URLs both returned HTTP 200 (347,080 and 74,602 bytes), 200 aligned IDs, one turn per question, and typed nested alternatives such as `multiples: [[3, 5]]`. **Fix applied:** use `question[0]`, not the outer list, as API messages; retain typed nested matching and pin both files to the same reviewed commit.
6. **The statistics section is sound for the stated fixed-item estimand.** Recomputed Wilson half-widths and all power-table entries match; exact McNemar, Holm, paired stratified bootstrap, and incomplete-run restrictions are appropriate, with independence/generalization limits already disclosed. **Fix applied:** “smaller/larger route” now means lexicographic route-ID order so bootstrap streams are reproducible.
7. **A single reference pass can admit flaky code items.** Randomized or timing-sensitive BigCodeBench tests could then produce route-independent false misses. **Fix applied:** before freezing, require three passing reference runs in fresh sandboxes and exclude flaky, seed-dependent, or resource-borderline items.
8. **Extraction precedence was internally ambiguous.** Selecting only a *valid* final explicit answer could accidentally revive an earlier boxed/bare answer after a malformed final marker. **Fix applied:** the last explicit marker now wins whether valid or malformed; malformed final values prohibit fallback for both MCQ and math.
