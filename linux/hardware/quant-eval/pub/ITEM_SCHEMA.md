# Item schema (codex/hermes integration)

Every `items.jsonl` row has `id`, `category`, `tier` (`core` or additional `extended`, disjoint), `source`, `source_revision`, `license`, `original_id`, `body` (OpenAI request without model), `gold`, `meta`, `grader`. Grader keys never enter `body`.

- `mcq`: gold letter; `meta.choices` is the ordered option list.
- `numeric`: gold exact integer/rational answer string.
- `grid`: gold `{"answer": {"header": [...], "rows": [...]}}`.
- `code`: gold has `test` (official unittest source) and `entry_point`; `meta.complete_prompt` and `meta.libs` provide provenance. The model returns a complete implementation.
- `ifeval`: gold has `instruction_id_list` and `kwargs`; the builder restricts to the grader's implemented stdlib rules.
- `tools`: gold is a BFCL `ground_truth` list of function-to-allowed-arguments objects. Dots in function names are changed to underscores in both gold and advertised tools to meet OpenAI tool-name constraints. `meta.tool_name_map` preserves the mapping, and `meta.functions` preserves the original definitions. BFCL `dict`/`float` etc. schema types become JSON Schema `object`/`number` etc.

`suite_pub.load_items(path=None, tier=None)` verifies the adjacent manifest and returns item objects. `requests()` returns `(id, category, body)` tuples. `PUB_ITEMS` selects the items file; `PUB_TIER` defaults to core, with extended meaning additional items and all meaning both tiers. The builder's top-level `CONFIG` table holds the design choices; counts/templates follow the red-teamed design and the chair's split-validation decision.


Schema-3 `candidates.jsonl` is an unfrozen build artifact: non-code rows have their final tiers, while 56 code candidates use `tier:candidate`, `candidate_rank` and `reference_source` (outside `body`). `build_items.py --validate-code` checks three isolated runs per candidate, selects passing rows by rank (20 core, then 8 extra), strips those candidate fields, and writes frozen `items.jsonl`. The manifest records `frozen`, `pending`, `reference_validation_runs:3`, `candidates_sha256`, exact item/config/source-lock/audit hashes and counts. Drafts and legacy manifests without validation provenance cannot be loaded by `suite_pub`.
