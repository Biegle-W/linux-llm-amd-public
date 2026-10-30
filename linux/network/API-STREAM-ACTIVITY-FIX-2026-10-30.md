# DSH HTTP stream activity repair — October 30, 2026

A local DSH pi-ai adapter defect is repaired and the frontend is active. The original reported conversation has not been replayed: its selected provider/model route still needs confirmation. Authenticated gateway health and the eight-model catalog pass; no inference profile, memory guard, engine pin or model-test hold changed.

## Failure mechanism and local evidence

The reported error is `pi-ai stream idle timeout after 300000ms`. The installed DSH adapter waits on converted assistant chunks, so HTTP/SSE loading comments can arrive without resetting its idle timer. This is independently described in the [upstream reproduction and proposed transport hook](https://github.com/deepseek-ai/deepseek-harness/discussions/9311).

The recent Bolt log records 874.30 seconds of weight loading plus 97.90 seconds of engine initialization, longer than a five-minute idle interval. SGLang also served successful requests during the incident period. These observations support investigating cold-start timeout handling; they do not identify the original request route or establish a storage failure.

The composed local-provider profiles already specify 86,400,000 ms timeouts. Consequently the precise route that selected the reported 300,000 ms default remains unconfirmed; do not describe that mismatch as resolved merely by changing unrelated settings.

## Repair

`dsh/apply-stream-activity.py` adds a per-request fetch activity observer to the installed `openai-completions` adapter. Response headers and nonempty body chunks pulse its existing watchdog before SDK parsing. Response bytes, errors and cancellation stay intact. It does not fabricate assistant content, disable the watchdog or change timeout values.

`dsh/start-dsh.py` replays the scoped repair on a fresh frontend launch. Exact preimages and checksums live in ignored local data; `--check` verifies the repair and `--undo` restores a matching preimage. Unknown or conflicting bundle shapes require review rather than overwriting another hook. The installed third-party bundle and backups are not redistributed.

## Validation and limits

Stack: DSH 0.2.1-rc.2, pi-ai 1.3.0, Node 24.21.0. No GPU/model load was required.

- Original installed adapter copy: a synthetic stream sending loading comments every 50 ms times out at 504 ms under a 500 ms idle bound, before its completion at 1.4 seconds.
- Repaired installed adapter with the real pi-ai SDK: the same delayed completion succeeds at approximately 1,417 ms, including text, usage and finish chunks.
- Four transport regressions pass: active versus silent concurrent streams, explicit caller cancellation, preservation of HTTP 429/Retry-After/URL/JSON, and null-body HTTP 204.
- Five existing native-frontend CPU regressions pass with temporary idle-tracker state; no real inference was launched.
- The DSH frontend was restarted through its normal launcher. Its authenticated web page returns HTTP 200. An initial shutdown race and an anonymous-readiness check were corrected; the original bundle rollback was exercised and the final short-lived frontend token was rotated.

This is a verified adapter/transport repair and authenticated frontend readiness check, not a replay of the user's full failed conversation or a new engine benchmark. The next verification is the original provider/model request. All paused RAM-dependent work remains waiting for explicit user confirmation. [Curated evidence](../hardware/results/api-stream-activity-fix-2026-10-30.json).
