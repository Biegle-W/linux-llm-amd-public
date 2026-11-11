# Public local quality harness

> **Frozen for the November 11 run on twelve routes.** `ornith-1.5-122b`, `flint-40b-a2.5b` and `sage-a1.5` were removed afterwards; drop them from `ROUTES` and `FAST_ROUTES` before any rerun. Current route ids are in the runtime handoff.

Python 3.14, standard library only. Copy this entire harness folder to the Linux server; no council workspace, pip packages, dataset caches, credentials, Docker image or other council files are needed. Source downloads use unauthenticated HTTPS. The server must have the chair-approved working unprivileged `bwrap` and its `/usr/bin/python3` runtime. `../DESIGN.md` documents the experiment; the commands below stand alone.

The frozen suite contains 216 core items for all twelve routes and 84 disjoint additional items for the eight routes at least 28 tok/s. No model has been measured here.

| Category | Core | Additional extended | Combined |
|---|---:|---:|---:|
| knowledge | 60 | 20 | 80 |
| math | 40 | 20 | 60 |
| code | 20 | 8 | 28 |
| instruction | 32 | 12 | 44 |
| tools | 32 | 12 | 44 |
| reasoning | 32 | 12 | 44 |
| Total | 216 | 84 | 300 |

## Exact server sequence

Run from inside the copied `harness` folder in a shell. Stop on any nonzero exit. Use a new result directory for a new experiment; the runner resumes existing first attempts without overwriting them.

```sh
set -eu

# 1. Build a draft: download locked sources, statically filter, hash-rank.
# This step never executes reference or test code.
python3.14 build_items.py --output candidates.jsonl --cache .pub-cache --audit build.audit.json

# 2. Validate references in the verified Linux bwrap sandbox and freeze.
# No HTTPS or original dataset cache is needed for this step.
python3.14 build_items.py --validate-code --input candidates.jsonl --output items.jsonl --cache .pub-sandbox --audit validate.audit.json

# 3. Verify the actual server sandbox and harness before starting fleet time.
python3.14 check_sandbox.py --temp-root .pub-sandbox
python3.14 -Werror selftest.py
python3.14 test_build_items.py

export PUB_ITEMS="$PWD/items.jsonl"
ROUTES='empero-qwen3.8-35b-a3b,glm-5.3-flash-maya,deepseek-v4.1-flash-1017-strata-unsloth-q1,deepseek-v4.1-flash-1017-maya-unsloth-q1,ornith-1.5-122b,flint-40b-a2.5b,ripple-65b-vllm,nemotron-3.5-bolt-vllm,qwen3.8-flash-next-iq3_xxs,sage-a1.5,qwen3.8-27b-vllm,qwen3.8-27b-sglang-dflash2'
FAST_ROUTES='empero-qwen3.8-35b-a3b,flint-40b-a2.5b,ripple-65b-vllm,nemotron-3.5-bolt-vllm,qwen3.8-flash-next-iq3_xxs,sage-a1.5,qwen3.8-27b-vllm,qwen3.8-27b-sglang-dflash2'

# 4. Core on all routes, in the predeclared order (local endpoint default).
python3.14 run_pub.py results "$ROUTES" --tier core

# 5. Additional items on the eight predeclared fast routes, same fleet clock.
python3.14 run_pub.py results "$FAST_ROUTES" --tier extended

# 6. Grade within the remaining 20-hour fleet budget. Preserve both families.
DEADLINE=$(python3.14 -c 'import json,time; f=json.load(open("results/fleet.json")); print(time.monotonic()+max(0,72000-max(time.time()-f["fleet_start"],f.get("max_elapsed_seen",0))))')
python3.14 grade_pub.py results "$ROUTES" --items items.jsonl --tier core --temp-root .pub-sandbox --deadline-monotonic "$DEADLINE"
python3.14 -c 'import shutil; shutil.copyfile("results/graded.json","results/graded-core.json")'
python3.14 grade_pub.py results "$FAST_ROUTES" --items items.jsonl --tier all --temp-root .pub-sandbox --deadline-monotonic "$DEADLINE"
python3.14 -c 'import shutil; shutil.copyfile("results/graded.json","results/graded-fast-all.json")'

# 7. Analyze identical item sets: primary 216-item family and secondary 300-item family.
python3.14 analyze.py results/graded-core.json --output-prefix results/analysis-core
python3.14 analyze.py results/graded-fast-all.json --output-prefix results/analysis-fast-all
```

`run_pub.py` exits 3 when its fleet guard stops inference. With `set -e`, inspect the saved pending IDs and budget before proceeding; do not reset the clock to bypass the ceiling. Completed results remain resumable. The grader deadline leaves expired items ungraded. Inspect caps, errors, missing and ungraded items before interpreting reports.

## Draft and freeze behavior

Build always emits a schema-3 draft with `frozen:false`, pending reference validation, 272 fixed non-code rows and **56 code candidates** (2 × the 20 core + 8 extra quota). `--draft` remains a compatibility alias. Code candidates carry `tier:candidate`, their zero-based hash rank and complete reference source outside the request body. The draft and its adjacent manifest plus `sources.lock.json` are sufficient for validation on another machine.

`--validate-code` verifies the artifact digest, configuration and source lock; it preflights `grade_pub.isolation_config`, then calls `grade_pub.validate_reference`, which calls `grade_pub.run_code` three times per candidate in fresh bwrap sandboxes. It validates all 56 candidates in rank order and selects the first 20 passing candidates as core, then the next 8 as extras. Acceptance requires all three passes and each run strictly below 8 seconds under the grading limits (5 s CPU, 10 s wall, 512 MiB address space, 1 MiB per output file). Startup probe time is excluded from reference timings.

`build.audit.json` records static exclusions. `validate.audit.json` records reference/test hashes, candidate ranks, every run's outcome and duration, exclusion reasons and selection decisions, including passing candidates beyond quota. Missing or failed isolation and grader defects abort; they never resample the pool. A quota shortfall also aborts: review exclusions before deliberately rebuilding/changing the candidate policy. No frozen artifact is written on a failed validation; any previous output belongs to its previous manifest and must not be treated as a new successful run.

Successful validation writes `items.jsonl` and `items.manifest.json`, removes draft reference/rank fields, checks all pool/domain/tier quotas, and records the candidate digest and three-run validation marker. `suite_pub` refuses drafts, old manifests without the validation marker, candidate fields and mismatched file hashes. Keep each JSONL with its adjacent manifest. Only `body` enters inference requests; gold, tests and reference source are never sent to the model.

bwrap uses the chair-approved namespace/mount layout, read-only `/usr`, no network or host home, private temporary work and resource limits. Startup probes verify isolation and fail closed. On macOS validation refuses without executing reference code; live sandbox execution is **not verified on this Mac**. The server sequence above must pass before measurement.

## Reproducibility and interpretation

`sources.lock.json` pins revisions, canonical full-row SHA-256, counts, URLs and license caveats. Online builds check upstream revisions; all cached rows are hash-verified. `--refresh` re-downloads and verifies source content; `--offline` requires a verified cache. Downloads are bounded below 50 MB each. `--update-lock` is a separately reviewed maintenance operation; never use it to silence source drift. Dataset code is never executed in the builder process.

Seed 20261110 ranks candidates by SHA-256 of `seed|pool|stratum|original_id`, with domain quotas for MMLU. Non-code pools take core first, then extras; code takes passing candidates in the same rank order. IDs and normalized problem texts must be unique. Requests hash-rank independently within tiers, core before extras. Budgets are 2048 for knowledge/instruction/tools/reasoning, 3072 for MATH/code and 4096 for AIME. Requests use temperature zero, nonstreaming, thinking off, and omit model.

IFEval drops the two language-detection case rules and retains number_words via `re.findall(r'\w+', text)` with parity tests. Its selected rules must be supported before freeze. Raw IFEval output is scored; scalar answer extraction strips thought tags for other categories.

The runner persists fleet timing, first attempts, usage, errors and projections, stops starting requests at 19.5 h and enforces a 20 h client deadline. Backend generation may continue after client disconnection; the chair must stop/drain the server to enforce the physical ceiling. Reference validation is separately timed preflight. Planned fleet time is 13.17 h with unmeasured output/overhead assumptions; full caps imply about 115 decode hours. Compare only identical manifests and tiers. Category difficulty, floors and saturation remain unmeasured.
