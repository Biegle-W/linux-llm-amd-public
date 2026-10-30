# OpenCat Responses: executable web search — October 30, 2026

The authenticated local API now executes `web_search`/`web_search_preview` requests using the existing configured DSH DeepSeek Search API provider. Live JSON and SSE requests on Qwen27B/vLLM return real search activity and URL citations. Search-history continuation and ordinary Responses also pass. Both checkouts pass 90 relevant CPU/HTTP/SDK checks. A successful retry in the iPhone app itself remains unconfirmed.

## Why endpoint support was insufficient

The earlier repair exposed native `POST /v1/responses`, which made text generation reachable. It did not install a hosted search executor. The gateway passed tools through, while the selected local engine had no configured browser tool server to perform the web request. The client can therefore reach the model without obtaining a live search. The user reported this with OpenCat's search switch enabled.

## Execution and provenance

`dsh/responses_web_search.py` handles requests declaring a supported web-search tool, or a previous response ID belonging to this bridge. All authentication, source-network, request-framing and enabled-model checks happen before this branch. Every model round still passes through the existing guarded hub; profile admission, worker ownership, RAM/VRAM protections, queue limits, pins and holds remain.

The local model selects a structured search query. The server executes that query against the configured DeepSeek Search API, then returns numbered titles, snippets, dates and URLs to the local model for its answer. Only the selected query, count and result-content option go to the external provider; the full conversation and bearer credentials are not included. The provider key never enters model context. There is no substitute cloud LLM generation step.

Actual searches produce `web_search_call` output items and typed progress events. Matching source references receive `url_citation` annotations derived from returned URLs. Required search fails explicitly if a model does not issue its required call; auto/none can complete without falsely claiming a search. Errors and truncated operations are not converted into successful search answers.

The provider key comes from `DEEPSEEK_API_KEY` in the service environment, or the existing ignored DSH credential reference of that name. The latter requires PyYAML, verified in the gateway interpreter here. No key is copied into source, reports or replies. Diagnostics record only bridge selection and completion counts/status; they omit prompts, queries, source contents and credentials.

## Supported scope and bounds

- Text `web_search`, `web_search_preview` and their supported dated aliases; auto, none and single-tool required selection. A forced named web choice is normalized to `required` in the response for SDK compatibility.
- Allowed-domain filtering is enforced on returned URLs as well as the provider query. Approximate location is supplied to the local query planner. Low/medium/high context selects bounded result counts and snippets.
- At most three searches per request and two concurrent bridge requests. Model output budgets apply across internal rounds. Provider requests have a bounded timeout and redirects are rejected.
- JSON and SSE are supported. Search events and keepalive comments arrive while planning/search runs. Final assistant text is buffered until generation completes, then delivered as typed text chunks with citations; it is not token-by-token model forwarding on this branch. Ordinary Responses retain their native streaming path.
- `previous_response_id` continuation uses an ephemeral cache, limited to 16 MiB of serialized payloads, 128 entries and one hour. `store:false` avoids retention. Cache contents are never written to disk and disappear on gateway restart. Native previous-response IDs remain backend-owned.
- Disconnects prevent subsequent query/model rounds. A provider request already dispatched may finish within its bounded timeout. Hosted code tools, mixed tool sets, image search, cache-only search, background mode and Conversations mode are rejected explicitly. This adds no arbitrary URL fetch, retrieval/delete/cancel endpoint or recurring job.

## Verification and activation

The existing provider returned HTTP 200 and real python.org results for a neutral probe. The selected local vLLM model independently demonstrated a valid structured search-function call before integration.

Twenty-three search-specific CPU/HTTP/SDK checks cover real executor flow through a fixture hub, citation indices, event ordering, required/auto/none behavior, cancellation, bounds, ephemeral history, source filtering, provider failures, authentication, held-model rejection and GPU reservation enforcement. Thirteen native Responses, 45 transport/admission and nine hub checks also pass in each checkout: 90 total. SDK schema checks use installed OpenAI SDK 3.31.0; the CPU tests also remain importable without installing it globally.

Live checks on the selected `qwen3.8-27b-vllm` route pass: real JSON search with a python.org filter, auto-selected preview search through SSE with typed completion/citations, previous-response history without a new search, and the plain native Responses path. A final forced-search response also passes strict SDK schema validation after activation: completed status, normalized `required` choice and one executed search. Only the idle gateway is restarted for activation; hub/model guards, production selections and scheduled jobs remain. The separate Strata trial is not resumed.

OpenCat keeps the same `/v1` base URL and API key. Enable its web-search option and ask an explicit search/current-information question. If it still fails, match the exact error and time to the query-free bridge-selection log before changing app or model settings.

References: [Responses web-search semantics](https://developers.openai.com/api/docs/guides/tools-web-search), [DSH provider implementation](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/web/web-deepseek-api). [Curated verification](../hardware/results/opencat-responses-web-search-2026-10-30.json).
