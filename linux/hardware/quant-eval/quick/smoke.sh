#!/bin/bash
# End-to-end check of the quick-test runner and jail with the scripted stand-in. Runs no model and uses no GPU.
cd "$(dirname "$0")"; OUT=${1:-/tmp/quick-smoke-$$}; rm -rf "$OUT"
python3.14 stub_model.py 18077 > /dev/null 2>&1 & S=$!; sleep 1
timeout 300 python3.14 run_quick.py "$OUT" stub --url http://127.0.0.1:18077 --tasks no_tool_sum,failed_command --passes 1 | grep -E "PASS|fail|tool_score"
kill $S
python3 - "$OUT" <<'PY'
import json, sys
res = ' '.join(str(json.loads(l).get('result')) for l in open(sys.argv[1] + '/failed_command.turn1.events.jsonl') if '"tool_result"' in l)
print('jail network:', 'OPEN (bad)' if 'NET-OPEN' in res else 'closed' if 'NET-CLOSED' in res else 'unknown')
print('jail home is the throwaway one:', 'HOME=/jhome' in res)
print('host home shows only the harness install:', 'HOSTHOME=Desktop\n' in res)
PY
