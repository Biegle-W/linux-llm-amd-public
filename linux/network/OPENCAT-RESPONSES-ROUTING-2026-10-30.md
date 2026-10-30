# OpenCat iPhone: native Responses API routing — October 30, 2026

The authenticated gateway now exposes `POST /v1/responses` through the existing guarded model hub and native engine APIs. The selected SGLang backend passes Responses JSON, SDK-assembled typed streaming with conversation history, and a Chat Completions regression. Both checkouts pass 67 relevant CPU routing/transport checks. A successful iPhone retry itself remains unverified.

## Confirmed cause

OpenCat could fetch the model catalog, but its chat request used `/v1/responses`. The gateway rejected that path before contacting the backend, returning HTTP 404 with `not_found` and “Only OpenAI chat/completion endpoints are exposed.” The client reported the same error. This was a route restriction, separate from the earlier SGLang telemetry shutdown and DSH activity-timer repair.

The installed llama.cpp, SGLang, both vLLM runtime selections and Maya have native Responses implementations. The change forwards request bodies to those implementations; it does not translate conversations or fabricate Responses output. Existing enabled model IDs, API base URL and bearer key remain valid.

## Routing and streaming

The gateway and hub accept the new POST path. SGLang, vLLM, Maya and Strata router allowlists admit it; the llama router already forwards native paths. The same catalog validation, source-network filter, authentication, FIFO admission, GPU reservation, startup, owned-worker and memory protections apply. Owner-held profiles stay excluded.

Responses uses typed SSE lifecycle events rather than Chat Completions' `[DONE]` terminator. Both relays now finish on `response.completed`, `response.incomplete` or `response.failed`. Successful native events, tool deltas and loading comments remain intact. Failed native responses retain their envelope with private error details redacted. Relay/admission failures use typed Responses errors; truncated streams remain failures. Existing Chat Completions behavior is unchanged.

References: [official Responses streaming events](https://developers.openai.com/api/reference/resources/responses/streaming-events) and [migration semantics](https://developers.openai.com/api/docs/guides/migrate-to-responses).

## Validation and activation

- Thirteen new CPU checks cover native JSON/body preservation, text/tool events at every HTTP chunk boundary, typed completion/incomplete/failure, truncation, redaction, authentication, catalog rejection, reservation enforcement and Maya routing. The 45 existing admission/transport and nine hub checks also pass in each checkout: 67 total per checkout.
- Only the idle hub and authenticated gateway services were restarted. The model had already undergone its normal inactivity unload, so no active inference was interrupted. The updater was inactive and no GPU reservation was held.
- The installed OpenAI SDK 3.31.0 completes a real nonstream Responses request and assembles a real streamed response with the earlier conversation marker preserved, using the enabled SGLang profile. A subsequent `/v1/chat/completions` request also completes. This is scoped functional verification, not a new model benchmark.
- API key, network access policy, engine pins, contexts, swap/eviction protection, scheduled jobs and RAM-held trials are unchanged.

This exposes the native **POST create** path only. Retrieve/delete/cancel, hosted tools, images, background operation and stored response IDs are not newly implemented at the gateway; request semantics remain the selected engine's responsibility. Native inference is functionally verified on SGLang here; other engines have source/fixture routing evidence, not new GPU qualification.

Keep the same API URL and key in OpenCat and retry. If another error appears, record its time, model and exact message so it can be matched to the request. [Curated evidence](../hardware/results/opencat-responses-routing-2026-10-30.json).
