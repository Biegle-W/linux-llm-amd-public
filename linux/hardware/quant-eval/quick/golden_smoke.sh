#!/bin/bash
# End-to-end and timing check of run_golden.py against golden_stub.py. Runs no model and uses no GPU.
#   golden_smoke.sh <local tokenizer folder> [out]
# Cases: a fast route; a slow route at 7 tok/s with ordinary answer lengths; the worst case for each class,
# where every answer runs to gBench's 512-token cap (5 tok/s slow, 80 tok/s fast); and a GPU hold mid-run.
set -u
cd "$(dirname "$0")"; TOK=$1; OUT=${2:-/tmp/golden-smoke-$$}; rm -rf "$OUT"; mkdir -p "$OUT"
PY=../gbench/.venv/bin/python
DS=$($PY -c 'import gbench,os;print(os.path.dirname(gbench.__file__)+"/golden_dataset")')
run() {  # name class stub-args... -- run_golden args...
  local name=$1 cls=$2; shift 2; local sargs=(); while [ "$1" != -- ]; do sargs+=("$1"); shift; done; shift
  python3 golden_stub.py 18092 "$DS" --model stub-route --require-thinking-off "${sargs[@]}" & local S=$!; sleep 1
  local t0=$(date +%s)
  python3 run_golden.py "$OUT/$name" stub-route --url http://127.0.0.1:18092 --class "$cls" --tokenizer "$TOK" "$@" > "$OUT/$name.out" 2>&1
  echo "== $name ($cls): $(( $(date +%s) - t0 ))s wall"; tail -1 "$OUT/$name.out"
  kill $S; wait $S 2>/dev/null
}
run fast fast --
run slow-typical slow --tok-s 7 --
run slow-worst slow --tok-s 5 --pad-tokens 600 --
run fast-worst fast --tok-s 80 --pad-tokens 600 --
run hold slow --tok-s 5 --pad-tokens 600 -- --abort-file "$OUT/hold-later" &
sleep 40; touch "$OUT/hold-later"; wait
python3 - "$OUT" <<'PY'
import json, sys
o = sys.argv[1]
for n in ['fast', 'slow-typical', 'slow-worst', 'fast-worst', 'hold']:
    s = json.load(open(f'{o}/{n}/summary.json'))
    st = {k: v['status'] for k, v in s['cases'].items()}
    print(n, '| used', s['minutes_used'], 'of', s['block_minutes'], 'min | within', s['within_block'],
          '| passed', s['passed'], '/', s['applicable'], '| not run', s['not_run'], '| errors', s['harness_errors'],
          '| refused', s['requests']['refused_after_limit'], '| 512-cap', s['requests']['hit_512_cap'])
    print('   first six:', [st[t] for t in list(st)[:6]], '| code:', st.get('code_canonical'), '| pairs:', s['template_pairs'])
PY
