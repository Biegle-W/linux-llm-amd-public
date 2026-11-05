# Current AMD results — November 5, 2026

For selected routes, current runtime pins and access, read the [runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md). This index identifies completed evidence; it does not queue new tests.

## Latest qualification

- **27 bounded cases complete:** 21 passed functional and guard checks, 6 failed/inconclusive. Cases include capacity/observation variants of the same model, not 27 distinct models. Owned cleanup is verified for all 27.
- All 7 router cases, 7 graphics workflows and 3 extended graphics copy-observation cases passed. Saved stage records contain 12,049 complete CPU/both-GPU temperature samples. All software temperature ceilings remain 100°C.
- The activation package passed 160 CPU checks; the sanitized export passed 35 additional CPU checks. Live read-only catalog/auth/health, exact 17 runtime files and source/native-seal checks passed with zero inference requests.
- Nine qualified normal routes are enabled by explicit owner approval. Maya Coder (normal 8 GiB reserve), Maya Q1, Strata Q1, GLM, PLE and Super INT4 EP2 remain held. Deleted XS and Super IQ3 stay retired.
- Empero/Flint/Ornith have direct inference peer-copy evidence. Qwen/vLLM, Bolt, Sage and Qwen/SGLang have successful TP2 requests with both-direction RCCL P2P/IPC evidence. Native layer groups and default graphics component placement have no direct-copy P2P claim. The separate H3 fcys TP2 result remains isolated.

[Methods, exact failures and limits](ALL-MODEL-P2P-2026-11-05.md) · [27-case numeric results](results/ALL-MODEL-P2P-2026-11-05.json) · [Research/source ledger](ALL-MODEL-P2P-RESEARCH-2026-11-05.md) · [10 reviewed image/video outputs](../graphics/results/p2p-2026-11-05/README.md)

## Performance evidence and limits

These are short functional/transport checks, not a throughput comparison, full-window-quality test or sustained-stability qualification. Preserve native, first-token, request and whole-workflow timing distinctions. Do not reuse another host's forum speed as a local result.

[November 4 matched Unsloth/Flint comparison](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md): neither candidate improved the retained short checks, so GSQ and Flint selections remain unchanged. No completed GPU check or failed profile was repeated for publication or cleanup.

For an older measurement, use the [benchmark history](BENCHMARK-HISTORY.md) and dated report with its hardware, capacity, source, workload and guard policy. The [earlier overview guide](history/documentation-2026-11-05/CURRENT-AMD-BENCHMARKS.reference.md) is archived; older holds and settings are superseded by the current handoff.
