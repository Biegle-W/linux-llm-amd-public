# Local LLM on dual AMD RX 7900 XTX

Sanitized public reference for a separately maintained private operational repository. The Linux tree is in [`linux/`](linux/). Example paths use `/opt/local-llm`, `/mnt/shared` and `/mnt/shared-nvme`; configure them locally.

Ten qualified routes are served through one OpenAI-compatible API on TCP 10000. The [runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) lists them with their settings, guards and pins. State on this page: November 25, 2026.

## Project overview

### Hardware and serving architecture

- **Machine:** Intel i5-13600KF, 64 GB DDR5 (61.5 GiB visible), two Radeon RX 7900 XTX 24 GB cards (gfx1100, RDNA3) behind a PCIe switch (Gen4 x16 uplink, x8 per card). The first card also drives the display. Kernel `7.0.14-42-vmpt1` is the owner-selected default (source: [handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md#hardware-and-kernel)).
- **One API, one model at a time.** Clients use one OpenAI-compatible gateway on TCP 10000. It supports Chat Completions and native Responses (`POST /v1/responses`). The gateway forwards to a local hub service. The hub starts the requested model's engine, or switches to it, through managed launchers. It holds one backend at a time and unloads an idle backend after 600 s. Catalog and health requests never load a model. Authenticated `/v1/models` is the live list. Retired names get "Unknown or retired model" (sources: handoff, [network](linux/network/README.md), [changelog](linux/hardware/CHANGELOG.md)).
- **Guards:** a 100 °C stop for CPU, GPU and SSD; one 1 GiB free-RAM floor for every model load (since November 18); VRAM headroom and spill checks; a supervisor heartbeat; phase time budgets. GPU work is serialized behind `hardware/generated/GPU-LOCK`, which becomes a fault hold after a GPU fault (source: handoff, Guards).

**Engines in production** (source: handoff, *Runtime and source identities*; Strata 0.2.20 from the [Strata report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md)):

| Engine | Version | Used for |
|---|---|---|
| vLLM (ROCm) | `0.33.0rc1.dev229+g3966924d5.rocm72` | Weights fully in VRAM, two-card tensor parallel: `qwen3.8-27b-vllm`, `ripple-65b-vllm` |
| SGLang (gfx1100 build) | `f84475ccf593` | Weights fully in VRAM, two-card tensor parallel, with a DFlash2 draft model: `qwen3.8-27b-sglang-dflash2` |
| Strata | upstream `v0.2.22` (`b28ca95e3e68`; `strata` and `strata-inkling` 0.1.69, `strata-hy4` 0.1.67), built from source (November 25) | Large mixture-of-experts model streamed from SSD (`qwen3.8-flash-next-iq3_xxs`), Inkling 2 Mini through its `strata-inkling` engine (`inkling-2-mini-sq-20-strata-2gpu`), and Hy4-Flash through its `strata-hy4` engine (`hy4-flash-sq-64-strata`) |
| Strata DeepSeek | `13eedf552417`, frozen (upstream removed this engine) | `deepseek-v4.1-flash-1017-strata-unsloth-q1` |
| Maya | `53885cef8faf` (1.1.81 plus two README-only commits, November 25) | SSD-streamed models with an expert RAM tier: `glm-5.3-flash-maya`, `deepseek-v4.1-flash-1017-maya-unsloth-q1` |
| llama.cpp | installed build b12782 (`b671865c7bd4`, November 26); pull request ggml-org/llama.cpp#32891 at `5f4d222898dd` | `kolibri-1.1-iq4_xs` runs on its own pinned build of the pull request (unmerged); no route uses the installed release |
| ComfyUI | 0.45.5 | Image and video ([graphics](linux/graphics/README.md)); not part of the LLM hub |

### Enabled models

Speed figures come from the standard short tool-call check: one DSH read-tool round trip with about 6.4K prompt tokens and 25 tool definitions, decode measured on a 54–171-token answer, and prompt read from a cold start. Where a route has another measurement, the table says so. **Quality** is the short tool-use score out of 100, the ranking standard since November 24 (owner; the NVIDIA server's test, rebuilt here: [report](linux/hardware/TOOLUSE-SHORT-TEST-2026-11-24.md)). The old 216-item public-suite score (MMLU-Pro, MATH-500, AIME, BigCodeBench, IFEval, BFCL and MuSR; 95% interval about ±6 points) follows in brackets. All figures are short checks, not sustained or full-context benchmarks. Source: [current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md) unless noted.

| Hub name | Engine | Weights / quant | Context | Placement | Decode tok/s | Prompt read tok/s | Quality: tool-use /100 (old 216) |
|---|---|---|---:|---|---:|---:|---|
| `qwen3.8-flash-next-iq3_xxs` | Strata 0.2.22 | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | 262,144 | SSD streaming, both cards (layer split 26) | 86.3¹; on 0.2.20: code 119–146, prose 82–106² | 740¹; on 0.2.20: 4,137–4,149 at 47,716 tokens² | 52.9 (169/216¹) |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S | 32,768 | SSD streaming, `64gb-q1-v1` RAM tier | 6.8 (9.5–17.1 on 400-token answers) | 35 | 62.2 (168/216) |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | same UD-IQ1_S weights | 32,768 | SSD streaming, RAM store off | 5.6 with the store on; 10.7–12.2 on 400-token answers with it off⁵ | 111 with the store on; 125–143 with it off⁵ | 64.0 (166/216) |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | Qwen3.8-27B AutoRound W4A16 + DFlash2 drafter | 163,840 | VRAM, both cards | 211.2 | 1,736 | 74.6 (163/216) |
| `qwen3.8-27b-vllm` | vLLM TP2 | Qwen3.8-27B AutoRound W4A16 | 163,840 | VRAM, both cards | 155.1 | 1,766 | 71.5 (157/216) |
| `glm-5.3-flash-maya` | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS | 32,768 | SSD streaming, 40 GB RAM tier | 5.2 (17.8–22.1 on 400-token answers) | 57 | 72.1 (136/216) |
| `ripple-65b-vllm` | vLLM TP2 | Ripple-65B-Preview GPTQ W4A16 | 65,536 | VRAM, both cards | 28.0 | 764 | 62.2 (134/216³) |
| `inkling-2-mini-sq-20-strata-2gpu` | Strata 0.2.22 `strata-inkling` | Inkling 2 Mini SQ-20 `.strata` + vision | 262,144 | VRAM, both cards, expert parallel (second card leads; about 9.6 GB on the display card) | 81–84 (code, 1,500-token limit)² | 2,020 at 38K; 1,396 at 112K; 961 at 217,533 tokens² | 60.4; quick test 12/12 and 8/8 harness, 11/16 function calls, 4/10 general⁴; no 216-item run |
| `hy4-flash-sq-64-strata` | Strata 0.2.22 `strata-hy4` | Tencent Hy4-Flash SQ-64 `.strata` + Engram Q8 + vision | 32,768 | Both cards, expert parallel: about 34 GB of experts in VRAM and 22 GB in RAM, nothing streamed from SSD; about 36 GiB of RAM left | 73.2⁸; 41–45 on 256-token answers⁹ | 613⁸; 833 on a 10.9K-token agent prompt⁹ | 72.1⁹; quick test 12/12 and 8/8 harness, 9/16 function calls, 5/10 general (one card, Strata 0.2.18, November 22); no 216-item run |
| `kolibri-1.1-iq4_xs` | llama.cpp, pull-request build | Aleph Alpha Kolibri 1.1 IQ4_XS GGUF (40.2 GB) | 262,144 | VRAM, both cards (layer split 1:1, 16-bit cache; about 2.2 GB left free per card) | 80⁶; 77 short, 52 at 21K, 26 at 84K, 12 at 238K tokens⁷ | 2,470⁶; 1,413 at 84K, 666 at 238K⁷ | 45.6; quick test G 14/14, harness 8/12 and 7/8, function calls 12/16, general 7/10⁷; no 216-item run |

1. Measured on the Strata RDNA3 fork, which was replaced and deleted on November 23. The weights are the same, and quality was not rerun (owner rule).
2. Source: [Strata 0.2.19/0.2.20 report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md). These requests differ from the table's standard 6.4K-token tool check.
3. 65 of Ripple's 216 answers were cut off at the token limit while still reasoning, so its score is a lower bound.
4. Scored on the retired one-card entry `inkling-2-mini-sq-20-strata` (Strata 0.2.19), which used the same weights. Thinking is always off on this route.
5. The route has run with the RAM store off since November 12. The standard tool check (5.6 and 111) was measured with the store on and has not been rerun. The store-off figures are 400-token answers through the hub on November 12. The 166 was scored with the store off on engine `13eedf552417` (sources: current results, handoff open item 2).
6. Strict tool check through the hub on November 24: an 82-token answer to a 6,351-token prompt from a cold start, load 83 s.
7. Source: [Kolibri 1.1 report](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md). Measured on the side server before the route was added, with the same build and settings, one request at a time.
8. Strict tool check through the hub on November 25, when the route was added: a 69-token answer to a 6,239-token prompt from a cold start, load 35 s, at least 2.4 GiB free on each card. The follow-up turn reused the prompt cache (first token 0.8 s).
9. Source: [Hy4-Flash retry report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md). Measured on a side server on November 24 with the same engine and settings, before the route was added.

Every enabled route has passed a tool round trip through the hub. The latest check for each route:
- Flash-Next, the two-card Inkling and Hy4-Flash: strict tool check, November 25, on Strata 0.2.22 ([engine update ledger](linux/hardware/DAILY-UPDATES.md)).
- Kolibri 1.1: strict tool check, November 24, on the pull-request build ([report](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md)).
- Both Maya routes: strict tool check, November 25, on Maya 1.1.81 ([engine update ledger](linux/hardware/DAILY-UPDATES.md)).
- Strata DeepSeek: strict tool check, November 12, on `13eedf552417` (changelog).
- Both Qwen3.8-27B routes and Ripple: guarded short tool-call check, November 7 and November 9. vLLM and SGLang have had no update since (changelog, handoff).

### Trials (not hub routes)

New models tried on side servers. Adding one to the hub is the owner's decision.

| Model | Date | Engine | Placement | Decode tok/s | Prompt read tok/s | Quick quality test |
|---|---|---|---|---:|---:|---|
| **Hy4-Flash SQ-64** | **Nov 24** | **Strata 0.2.21.1 side server (`strata-hy4` 0.1.67)** | **both cards, expert parallel, 34 GB of experts in VRAM and 22 GB in RAM, 32,768 context; about 36 GiB of RAM left** | **41–45** | **833 (10.9K-token agent prompt)** | **short tool-use test 72.1** (31/40, episodes 6/9); became the hub route `hy4-flash-sq-64-strata` on November 25 ([report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md)) |
| Hy4-Flash Maya-M | Nov 25 | Maya 1.1.78 side copy, tensor parallel (`--tp 2`, experts partly in RAM) | both cards, 35–45% of experts on the cards | 7–22 | 167–292 | not run (no faster than the layer split; [report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md#maya-m-tensor-parallel-november-25)) |
| Hy4-Flash Maya-M | Nov 24 | Maya 1.1.78 side copy | both cards, layer split (tensor parallel does not fit) | 16–22 | 280–301 | not run (slower than Strata on every request) |
| Hy4-Flash SQ-64 | Nov 22 | Strata 0.2.18 side install | one card, 32,768 context | 26–30 | 1,146 | harness 12/12 and 8/8, function calls 9/16, general 5/10 |
| Hy4-Flash Maya-M | Nov 22 | Maya 1.1.73 side copy | both cards | 13–32 | — | harness 11/12 and 8/8, function calls 9/16, general 6/10 |

Kolibri 1.1 was tried on a side server first and became the hub route `kolibri-1.1-iq4_xs` on November 24 (table above). No engine other than llama.cpp can run it on these cards yet: Aleph Alpha's vLLM plugin needs NVIDIA H100 or B200, and vLLM, SGLang and the rest support only Kolibri 1. Hy4-Flash SQ-64 on Strata became the hub route `hy4-flash-sq-64-strata` on November 25. Reports: [Kolibri 1.1](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md), [Hy4-Flash on Strata](linux/hardware/HY4-FLASH-SQ64-2026-11-22.md), [Hy4-Flash on Maya](linux/hardware/HY4-FLASH-MAYA-M-2026-11-22.md).

### Retired models

| Name | Retired | Weights |
|---|---|---|
| `inkling-2-mini-sq-20-strata` (one card) | November 23, replaced by the two-card entry | Kept; the two-card entry uses them and they must not be deleted |
| `inkling-2-mini-q8` (llama.cpp) | November 23 | Kept (22 GB, Q8 and mmproj) |
| `empero-qwen3.8-35b-a3b` (llama.cpp) | November 23 | Kept (19 GB) |
| `nemotron-3.5-bolt-vllm` (vLLM) | November 23 | Kept (41 GB) |
| `qwen3.8-flash-next-iq3_xxs-upstream` | November 23, merged into the main Flash-Next name | Same weights as the main name |
| `ornith-1.5-122b`, `sage-a1.5`, `flint-40b-a2.5b` | November 11 | Deleted (114 GB freed) |
| Flash-Next UD-IQ1_M, both DeepSeek Coder IQ2_XXS routes | November 8 | Deleted |
| `nemotron-3.5-super-iq3`, `deepseek-v4.1-flash-1017-strata-xs`, `deepseek-v4.1-flash-1017-maya` | November 2 | Deleted (registry rows kept disabled) |

The registry entries of the routes retired on November 23 stay disabled. They are re-enabled only on the owner's instruction. Clients still set to a retired Inkling, or to `llama-local`, get `inkling-2-mini-sq-20-strata-2gpu`. Clients set to Empero or Bolt fall back to `qwen3.8-27b-sglang-dflash2`. On November 23 the Strata RDNA3 fork engine and its 0.2.19 build were also deleted, so no fork rollback exists. Sources: live registry flags, the handoff, the [changelog](linux/hardware/CHANGELOG.md) and the [storage inventory](linux/hardware/MODEL-STORAGE-INVENTORY.md).

### How models are tested

- **New model or new weight file: [quick quality test](linux/hardware/quant-eval/quick/README.md), run once** (owner, November 22; block G added November 23). The total budget is 15 minutes for a fast model (about 80 tok/s or more) and 60 minutes for a slow one.
  - **Block G, first:** the gBench Golden Set (pinned 0.5.0.post1), 16 fixed serving checks, about 11 on a text-only route. Its chat-template pairs and tool calls separate a broken template or tool parser from a weak model. The time limit is 2 minutes (fast) or 5 minutes (slow). Against a scripted stand-in its worst case is 1.6 of 2 and 3.5 of 5 minutes. First real run: Kolibri 1.1 on November 24, 14 of 14 in 0.2 minutes.
  - **Block A:** 12 core and 8 extra tool tasks inside the DSH agent harness, in a no-network jail. It takes 6 minutes for a fast model (core tasks run twice) and 30 for a slow one.
  - **Blocks B and C:** 16 function-call items, then 10 core and 34 extra general items, all taken from the 216-item public suite. Twenty-six items show large differences only, not close rankings.
  - Runs so far: two Hy4-Flash trials on November 22 and the one-card Inkling SQ-20 on November 23 (blocks A to C, 11 minutes each), and Kolibri 1.1 on November 24 (all blocks, 3 minutes) (sources: [current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md#quick-quality-test-new-models-from-november-22), [plan](linux/hardware/QUICK-QUALITY-PLAN-2026-11-22.md)).
- **Quality ranking: the broad [rank tier](linux/hardware/quant-eval/rank/README.md)** (owner, November 25: knowledge, math, code, instructions, reasoning and some tool calls; 15 minutes for smaller models, 30 for large ones; the main quality ranking since November 26, owner: "Yes, make it main"). Every route answers the same 30-item core, then keeps going in a fixed order up to 144 items while the next one fits its budget. First run on all ten routes November 25–26 ([report](linux/hardware/RANK-TEST-2026-11-26.md)): on the 45 items every route reached, Flash-Next 37, Qwen3.8-27B SGLang 36, DeepSeek on Maya 35, Kolibri and Qwen3.8-27B vLLM 34, DeepSeek on Strata 33, Ripple 29, Hy4-Flash 28, Inkling 23, GLM 22; only four pairs are separated (Flash-Next and SGLang above Inkling, SGLang and DeepSeek on Maya above GLM). Inkling on Strata, Hy4-Flash and Kolibri lose some answers to formatting the frozen grader cannot read (a format-tolerant re-grade is in the report).
- **Tool-use ranking: the [short tool-use test](linux/hardware/quant-eval/tooluse/README.md)** (the main quality ranking from November 24 to 26, kept as the tool-calling ranking; the NVIDIA server's method, rebuilt from BFCL v4 with seed 20261122). 40 single-turn tool-call items and 9 multi-turn episodes through the hub, 49 items for models in VRAM and 55 for the larger ones; score = 50 x single-turn / 40 + 50 x episodes / 9. All nine routes then enabled ran it on November 24, and Hy4-Flash ran it on its side server the same day before it became the tenth route (Qwen3.8-27B SGLang 74.6 first, GLM and Hy4-Flash 72.1, Kolibri 45.6 last; [report](linux/hardware/TOOLUSE-SHORT-TEST-2026-11-24.md)).
- **Existing routes are not rerun.** The 216-item public suite runs only when the owner asks.
- **Engine update: strict tool check.** Each update is built in isolation and installed provisionally. Then every enabled route on that engine gets one strict two-step DSH read-tool round trip through the hub, followed by review and promotion, with rollback on failure. A minor slowdown is never a reason to reject an update (sources: [engine update ledger](linux/hardware/DAILY-UPDATES.md), [method](linux/hardware/daily-update/README.md)).
- **Unit tests:** `python3 -m unittest discover -s hardware -p "test_*.py"`. 683 tests pass, 2 skipped (November 25).

### Where to find results

- [Short tool-use test, November 24](linux/hardware/TOOLUSE-SHORT-TEST-2026-11-24.md): the tool-calling ranking (the main ranking until November 26) of the nine routes then enabled (Hy4-Flash: [its report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md)), with [results JSON](linux/hardware/results/tooluse-short-2026-11-24.json).
- [Current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md): speed table, the broad quality ranking, the tool-use ranking, the old 216-item ranking and the quick-test table.
- [Kolibri 1.1 trial](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md) and its [results JSON](linux/hardware/results/kolibri-1.1-trial-2026-11-24.json).
- [Strata 0.2.19/0.2.20 report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md): Flash-Next and Inkling on upstream Strata, the fork comparison, and the November 23 update to 0.2.20.
- [Engine update ledger](linux/hardware/DAILY-UPDATES.md): engine version changes and their checks, latest November 26 (llama.cpp b12782; November 25: Strata 0.2.22, Maya 1.1.81 and llama.cpp b12738). The November 23 Strata 0.2.20 update is in the Strata report and the changelog.
- [Changelog](linux/hardware/CHANGELOG.md): every change, with links to dated reports.
- [Validation](VALIDATION.md): validation scope of this public reference.

### Latest changes (November 17–26)

- **Nov 26:** daily engine update. llama.cpp updated to build b12782 (no route uses it; kernel tests on each card and a guarded two-card smoke passed). vLLM, SGLang, Maya and Strata are current; vLLM 0.34.0 is out only for ROCm 10.0 and was not installed ([ledger](linux/hardware/DAILY-UPDATES.md)).
- **Nov 26:** the broad ranking test is now the main quality ranking (owner); the short tool-use test stays as the tool-calling ranking.
- **Nov 25–26:** broad ranking test run on all ten routes, 4 hours ([report](linux/hardware/RANK-TEST-2026-11-26.md)): Flash-Next, Qwen3.8-27B SGLang and DeepSeek on Maya lead on the 45 shared items; GLM and Inkling last; most of the order is not statistically separated.
- **Nov 25:** broad quality ranking test built (rank tier: 30-item core for every route, up to 144 items within 15 or 30 minutes; not run on any route yet; [how it works](linux/hardware/quant-eval/rank/README.md)).
- **Nov 25:** daily engine update. Strata 0.2.22 (Flash-Next, two-card Inkling, Hy4-Flash), Maya 1.1.81 (GLM, DeepSeek) and llama.cpp b12738 promoted after upstream research, a side-by-side speed run or per-card parity tests, and the strict tool check on every affected route. Speed is unchanged in the side-by-side run, which sends `temperature: 0`. Behaviour change: on Strata 0.2.22 a request that names no sampling settings gets the model card's sampling instead of greedy decoding (Flash-Next; Inkling also moved from greedy to temperature 1.0). For Flash-Next this roughly halves decode on such requests: 51–57 against 94–103 tok/s with `temperature: 0` in a side test (the hub check: about 90 against 139 tok/s in the engine log). Requests that set `temperature` are unaffected. Later the same evening the owner then had greedy restored as the route default (a `"sampling": {"temperature": 0}` block in the route config, resealed); the strict hub recheck after it: load 119 s, 6,335-token prompt first token 4.5 s, 84 answer tokens at 139.0 tok/s in the engine log (138.9 on November 24), drafts accepted 60 of 66, lowest free VRAM 1.65 GiB per card. Requests that set their own sampling still get it. Strata DeepSeek has no update (upstream deleted that engine); vLLM and SGLang are current ([ledger](linux/hardware/DAILY-UPDATES.md)).
- **Nov 25:** Hy4-Flash Maya-M tried in tensor parallel across both cards after a council research pass (owner request). It loads in about a minute with the start-up measurement skipped, but decodes at 7–22 tok/s, no faster than the layer split and far from the Strata route ([report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md#maya-m-tensor-parallel-november-25)).
- **Nov 25:** Hy4-Flash SQ-64 added as the hub route `hy4-flash-sq-64-strata` (owner decision): Strata 0.2.21.1 `strata-hy4` across both cards, the same sealed settings as the November 24 trial (experts capped at 32 GB in VRAM). Strict tool check through the hub passed (load 35 s). Its short tool-use score, 72.1, ties GLM for second in the ranking; it decodes at 41–45 tok/s and leaves about 36 GiB of RAM free ([report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md)).
- **Nov 24:** Hy4-Flash retried on the updated engines with the downloaded weights. On Strata 0.2.21.1 across both cards it decodes at 41–45 tok/s (26–30 on one card on November 22), leaves about 36 GiB of RAM free (about 4 GB before) and scores 72.1 on the short tool-use test, level with GLM; Maya-M on Maya 1.1.78 is slower. Still a trial; adding it as a route is the owner's call ([report](linux/hardware/HY4-FLASH-RETRY-2026-11-24.md)).
- **Nov 24:** Strata 0.2.21.1 (Flash-Next and the two-card Inkling) and Maya 1.1.78 (GLM and DeepSeek) promoted after a side-by-side speed run and the strict tool check. Inkling reads a 13K agent prompt faster (5.8 against 7.7 s) and now reuses the prompt cache on the next turn; Flash-Next is unchanged; DeepSeek on Maya reads its first prompt faster, GLM decodes slightly slower ([ledger](linux/hardware/DAILY-UPDATES.md)).
- **Nov 24:** the short tool-use test (the NVIDIA server's ranking test) was rebuilt here from BFCL v4 and run on all nine routes; it was the quality ranking until November 26. Top three: Qwen3.8-27B on SGLang 74.6, GLM-5.3-Flash 72.1, Qwen3.8-27B on vLLM 71.5 ([report](linux/hardware/TOOLUSE-SHORT-TEST-2026-11-24.md)).
- **Nov 24:** llama.cpp updated to build b12681 (`d141011c2578`, 52 commits). No enabled route uses the installed build, so it was checked on a guarded side server on both cards: answers, a tool round trip and a 42,619-token prompt passed. Kolibri stays on its pull-request pin, which has not moved ([ledger](linux/hardware/DAILY-UPDATES.md)).
- **Nov 24:** Kolibri 1.1 added as the hub route `kolibri-1.1-iq4_xs` (owner decision). It runs on its own pinned build of the llama.cpp pull request, on both cards with 262,144 context. The strict tool check passed through the hub (load 83 s, decode 80 tok/s). The hub now serves nine models ([report](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md)).
- **Nov 24:** Kolibri 1.1 tried on a side build of the llama.cpp pull request: it loads on both cards with the full 262,144 context and finds a code word at 238K tokens; quick test G 14/14, harness 8/12, function calls 12/16, general 7/10. Not a hub route ([report](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md)).
- **Nov 23:** standing rule: when a new model does not fit, retired weights may be deleted without asking again, only as much as needed ([handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md)).
- **Nov 23:** gBench Golden Set added as block G of the quick quality test ([changelog](linux/hardware/CHANGELOG.md), [quick test](linux/hardware/quant-eval/quick/README.md)).
- **Nov 23:** Inkling 2 Mini kept only as `inkling-2-mini-sq-20-strata-2gpu`; `inkling-2-mini-sq-20-strata` and `inkling-2-mini-q8` retired with weights kept. The hub then served eight models, with no llama.cpp route until Kolibri 1.1 on November 24 ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 23:** `empero-qwen3.8-35b-a3b` and `nemotron-3.5-bolt-vllm` retired with weights kept; the hub then listed ten models ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 23:** Strata RDNA3 fork and the 0.2.19 build deleted (about 1.6 GB); `strata/` keeps only `.venv` ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 23:** Flash-Next switched from the fork to sealed upstream Strata 0.2.20. It reads long prompts about twice as fast, uses about half the RAM (19 against 37 GB) and decodes code about 10% slower ([report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md)).
- **Nov 23:** two-card Inkling SQ-20 entry added (262,144 context, code decode 81–84 tok/s) ([report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md)).
- **Nov 23:** both upstream Strata entries updated to 0.2.20, resealed, and passed the strict tool check ([report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md)).
- **Nov 23:** one-card Inkling SQ-20 on Strata 0.2.19 added as its own route (code decode 86–90 tok/s; quick test 12/12 and 8/8 harness, 11/16 function calls, 4/10 general); retired later the same day ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 22:** Flash-Next on upstream Strata 0.2.19 added as its own entry at the owner's request, beside the fork route ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 22:** upstream Strata 0.2.19 measured against the fork: faster prompt reading, about half the RAM, slower code decode; nothing switched ([report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md)).
- **Nov 22:** two Hy4-Flash trials (on Strata 0.2.18 and on Maya 1.1.73) ran the quick test; neither became a hub route ([current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md#quick-quality-test-new-models-from-november-22)).
- **Nov 22:** llama.cpp `1fb8a269603b` and Maya 1.1.73 promoted; ComfyUI 0.46.0 researched and not installed ([ledger](linux/hardware/DAILY-UPDATES.md)).
- **Nov 22:** quick quality test built; it replaces the 216-item suite as the routine test ([plan](linux/hardware/QUICK-QUALITY-PLAN-2026-11-22.md)).
- **Nov 22:** cleanup deleted superseded trial builds and two old archives (10.9 GB and 3.2 GB) ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 18:** one 1 GiB free-RAM floor for every model load; Maya and Strata DeepSeek wait up to 15 s for VRAM release after a switch ([changelog](linux/hardware/CHANGELOG.md)).
- **Nov 17:** Flash-Next tuned, then moved to the RDNA3 fork with no fixed expert RAM budget; public suite 169 of 216 ([changelog](linux/hardware/CHANGELOG.md)).

## Rules

**Scope and publishing**
- This server maintains only two AMD repos: the private operational repository and this public reference. Other Linux NVIDIA and Windows repos, and old snapshots, are references unless the owner assigns them.
- After authorized changes, keep both repos, the results and the handoff in step. Reviewed commits and normal (non-force) pushes to both `origin/main` branches are authorized. Verify the remote refs afterwards, preserve unrelated changes, and report exact blockers.
- The operational handoff has a byte-identical private copy on the shared SATA drive (`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md`). That copy is the private text, not this public one.
- Public edits are targeted and hand-sanitized: no home or mount paths, LAN or tailnet addresses, or identity names. Public profiles use `/opt/local-llm` paths. The `PRIVATE` regex of the retired publisher in `linux/hardware/daily-update/publish.py` is the check.
- Never publish credentials, personal or client settings, chat state, raw private logs, model weights, environments or runtime binaries. Private agent workflow, checkpoints and context tools stay out of public exports and the shared handoff.

**Runtime safety**
- Preserve installed paths, exact source and weight pins, manual runtime pins, every guard, the owner-selected kernel default (`7.0.14-42-vmpt1`, with the stock kernel installed as fallback), unrelated applications and paused schedules. Documentation upkeep never authorizes a trial, engine upgrade, restart, hold release or schedule change.
- GPU work is serialized behind an owned `hardware/generated/GPU-LOCK`. A lock you do not own, or unknown KFD ownership, blocks you. After a GPU fault the lock is a fault hold: no GPU work, retries or reboots until the owner releases it.
- Qualified native profiles are sealed (`config_sha256`) in `dsh/qualified-native-profiles.json` and, for the upstream Strata packages, in `dsh/qualified-strata-qwen-profiles.json`. The Strata file holds three seals: `qwen3.8-flash-next-iq3_xxs`, `inkling-2-mini-sq-20-strata-2gpu`, and the retired `inkling-2-mini-sq-20-strata`, whose seal is kept while its route is disabled. Editing a sealed profile breaks admission until it is requalified and resealed; never fake a seal.

**Engines and models**
- Engine update policy (owner, November 7): always take the latest engine version unless it breaks something. A minor slowdown is never a reason to reject.
- Which version (owner, November 22): the target is the latest version best supported on these RDNA3 cards, not simply the newest release. Check RX 7900-specific forks and branches and what their authors run in production, and prefer a version tested on gfx1100 over an untested newer head. Current outcome (owner, November 23): Flash-Next and Inkling run upstream Strata 0.2.20 (`a34979fc94f3`), not the RDNA3 fork. The fork tree and its 0.2.19 build were deleted, so no fork rollback exists. No llama.cpp route is enabled, so a llama.cpp update has no route to check until one is added.
- Engine update steps run one at a time (November 22): never start a guarded GPU stage while a build is running or the CPU is hot, and never reuse a stage folder after a failed stage. Both mistakes latched a hold that day. Strata updates are built in a fresh stage folder, measured, resealed and given the strict tool check; never in `strata/`.
- Engine updates are manual since November 9 (owner): upstream is checked by hand, and each update is built in isolation, qualified and promoted by hand. The scheduled nightly updater is retired and no timer runs it. Method and the retired script are in [the updater README](linux/hardware/daily-update/README.md).
- Quality testing (owner, November 22; block G added November 23): a new model or new weight file gets the [quick quality test](linux/hardware/quant-eval/quick/README.md) once. Block G (gBench Golden Set) runs first, then harness tool tasks, then public-suite items, within 15 minutes for a fast model or 60 for a slow one. Existing routes are not rerun, and the 216-item suite runs only when the owner asks. The quality ranking is the [short tool-use test](linux/hardware/quant-eval/tooluse/README.md) (owner, November 24).
- New engines or models need isolated qualification before promotion. For a new model, check a gfx1100 vLLM or SGLang INT4 route before keeping it on GGUF.
- Deleting weights or data is the owner's call, with one standing exception (owner, November 23). When a new model does not fit, the retired weights listed in the handoff may be deleted without asking again. Delete only as much as the new model needs, and report the deletion. Never delete the Inkling SQ-20 `.strata` files, which `inkling-2-mini-sq-20-strata-2gpu` uses. Weights of enabled routes still need the owner's OK. After a deletion, drop the route's entries.

**Storage (90% limit)**
- No drive may go above 90% used. Before any download or copy, run `python3 dsh/shared_storage.py --place static|streaming --size-gb N`. It refuses when the drive would pass 90%. For `streaming` it creates the target folder; for `static` the folder must already exist.
  - `static` goes to the shared SATA drive's `vLLM-Models`.
  - `streaming` goes to the shared NVMe drive's `LLM-Models`.
- Existing streaming packs stay in `models/streaming/` on the system drive. Never move validated assets as housekeeping.
- The check is advisory: downloaders do not call it themselves.
- Usage on November 24: shared SATA drive (`/mnt/shared`) 36% (332G of 932G), shared NVMe drive (`/mnt/shared-nvme`) 30% (272G of 932G), system drive 74% (612G of 882G).

**Writing**
- Use English for all communication and GitHub content.
- Keep current docs short and current. Replace superseded state instead of adding to it. Each change gets one line in the [changelog](linux/hardware/CHANGELOG.md) and a dated report for its evidence.

## Layout

Paths below are inside `linux/`.

| Path | What it holds |
|---|---|
| `dsh/` | Hub (`model_hub.py`), routers, runtimes, route registries and profiles, DSH frontend |
| `network/` | API gateway, systemd units, the runtime handoff |
| `hardware/` | Operational scripts (`rocm-env.sh`, guards), unit tests `test_*.py`, dated reports `*-2026-*.md`, `results/` JSON |
| `hardware/quant-eval/quick/` | Quick quality test: block G (`run_golden.py`), block A (`run_quick.py`), graders and stand-ins |
| `hardware/daily-update/` | Retired nightly updater, publisher and systemd unit sources (kept for version checks and reference) |
| `hardware/generated/` | Ignored live state: `GPU-LOCK`, the sealed upstream Strata 0.2.20 build `strata-0220-2026-11-23/` (production for Flash-Next and Inkling), trial side installs |
| `vllm/`, `sglang/`, `maya/`, `strata-dsv41/`, `graphics/` | Engine launchers and pins; ignored venvs and sources sit beside them |
| `strata/` | Only `.venv`, the Python environment the Strata launchers use (the RDNA3 fork tree was deleted on November 23); keep it |
| `bin/`, `launchers/` | `llm-*` CLI wrappers and desktop launchers |
| `models/streaming/` | Ignored streaming weights for Strata and Maya |
| `llm-tools/` | Ignored toolchains: Python, ROCm SDK, RCCL, caches |

Dated reports stay flat in `hardware/` because many links and a few code strings point at them; find them through the [changelog](linux/hardware/CHANGELOG.md).

## Doc map

| Need | Read |
|---|---|
| Current state, routes, guards, pins, open items | [Runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) |
| Current measurements | [Current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md) |
| Flash-Next and Inkling on upstream Strata | [Strata 0.2.19/0.2.20 report](linux/hardware/STRATA-0219-RESEARCH-2026-11-22.md) |
| What changed and when | [Changelog](linux/hardware/CHANGELOG.md) |
| Broad quality ranking, time-boxed | [Results, November 26](linux/hardware/RANK-TEST-2026-11-26.md), [rank tier](linux/hardware/quant-eval/rank/README.md), [design](linux/hardware/quant-eval/rank/DESIGN.md) |
| Quality test for a new model | [Quick quality test](linux/hardware/quant-eval/quick/README.md), [plan](linux/hardware/QUICK-QUALITY-PLAN-2026-11-22.md) |
| Engine updates (manual since November 9) | [Ledger](linux/hardware/DAILY-UPDATES.md), [method](linux/hardware/daily-update/README.md) |
| Drives and weight files | [Storage inventory](linux/hardware/MODEL-STORAGE-INVENTORY.md) |
| Card layout and crash runbook | [AMD working setup](linux/hardware/AMD-WORKING-SETUP-2026-11-07.md) (November 7 state) |
| Website summary (what biegle.ca reads) | [docs/WEBSITE-SUMMARY.md](docs/WEBSITE-SUMMARY.md) |
| Model trials | [Kolibri 1.1](linux/hardware/KOLIBRI-1.1-TRIAL-2026-11-24.md), [Hy4-Flash on Strata](linux/hardware/HY4-FLASH-SQ64-2026-11-22.md), [Hy4-Flash on Maya](linux/hardware/HY4-FLASH-MAYA-M-2026-11-22.md) |
| Clients and gateway | [Network](linux/network/README.md), [DSH](linux/dsh/README.md) |
| Image and video | [Graphics](linux/graphics/README.md) |
| Validation scope | [Validation](VALIDATION.md) |
| Agent startup reading | [AGENTS](AGENTS.md) |
| Older measurements | [Benchmark history](linux/hardware/BENCHMARK-HISTORY.md) |
| Retired setups | [Archives](archives/README.md) |
