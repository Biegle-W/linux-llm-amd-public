# OpenCat free web search — October 30, 2026

**Compatibility update:** [Mixed client functions and dated news](OPENCAT-TOOLS-DATED-NEWS-2026-10-30.md) expands the original tool-list scope and adds actual RSS publication dates. The earlier results below remain historical evidence.

The owner reported that OpenCat still said it could not browse and requested a free search service without a paid API. Search-enabled Responses now use self-hosted SearXNG on loopback. The bridge performs no search credential lookup and has no paid fallback. The authenticated gateway continues to require the existing local API key.

## Service and request path

The selected local model plans a query through the unchanged guarded hub. The gateway POSTs only that query and search options to `http://127.0.0.1:10001/search`. SearXNG queries its configured keyless public engines, returns snippets and URLs, and the local model writes the answer with genuine URL citations. Full conversations and gateway credentials are not sent to search engines.

`network/search/start-search.py` creates a private local settings file under ignored `dsh/data/search/` and starts the pinned official container using Compose. Existing local configuration is preserved. Run it with Python from this checkout; Docker with Compose must be available. The container restarts unless explicitly stopped. No subscription or search API key is needed.

The service publishes only loopback port 10001, uses one CPU and a 384 MiB memory ceiling with no container swap, and has no GPU access. Its generated secret is local state, not a search-provider credential. Docker query/error log persistence is disabled, and gateway diagnostics contain only search counts/status or error codes. Authentication, catalog restrictions, hub ownership/admission, model guards, pins, held profiles and schedules remain.

Bing and Brave returned results in the initial neutral probes. Google denied access and DuckDuckGo returned CAPTCHA, so those two engines are excluded from this instance. Free public engines can change availability or rate-limit requests; a local service/provider error remains explicit and never invokes a paid fallback. Returned HTML is stripped, whitespace normalized, and domain/URL filters and result bounds remain enforced.

## Compatibility and verification

The latest iPhone attempt reached the Responses search branch, but the earlier query-free diagnostics recorded no completed search and did not identify its cause. This is evidence of routing, not proof of the original failure's cause. The new adapter logs error code and HTTP status without prompts or queries. A fresh iPhone retry remains necessary.

The existing ephemeral previous-response cache still expires after one hour or a gateway restart. After activation, start a new OpenCat conversation to avoid a stale response ID. Keep the same base URL ending in `/v1` and the same gateway key, select the enabled vLLM model, enable web search, and ask an explicit search question.

Search final text remains buffered after model generation, while typed search activity/keepalives stream during work. Search history, `store:false`, source annotations, supported web-tool choices, limits and explicit unsupported-mode errors retain the scope of the [earlier bridge report](OPENCAT-RESPONSES-WEB-SEARCH-2026-10-30.md). This update replaces that report's paid-provider description; its earlier results remain historical evidence.

Thirty-nine focused CPU/HTTP/SDK checks pass in each checkout: 26 search contracts and 13 native Responses checks. These cover keyless POST requests, disabled proxy inheritance, no authorization header, snippet conversion/filtering, redirects, oversized/malformed replies and explicit failure without fallback, as well as the existing loop, cancellation, history, schema, authentication and guard contracts.

Live authenticated JSON search returned genuine Python documentation citations with a required web-search choice. An auto-selected preview search streamed typed activity and citations after a prior assistant refusal; both final payloads pass strict SDK validation. Ephemeral history without a new search and ordinary native Responses also pass. The first JSON proof included the normal on-demand model reload; its duration is a functional request observation, not a performance benchmark. Only the idle gateway was restarted for activation; the guarded hub was preserved.

Verification results are recorded in the [curated free-search evidence](../hardware/results/opencat-free-search-2026-10-30.json). No new performance benchmark or held-model trial is part of this change.

References: [SearXNG container installation](https://docs.searxng.org/admin/installation-docker.html), [JSON search API](https://docs.searxng.org/dev/search_api.html), [engine configuration](https://docs.searxng.org/admin/settings/settings_engines.html).
