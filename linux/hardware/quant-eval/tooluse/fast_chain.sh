#!/bin/bash
# Nov 24 (owner: "Use the short tool-use test as the ranking", "Rebuild it on AMD"): short tool-use test on every enabled route, one after another, through the hub.
# usage: fast_chain.sh OUTDIR route:group [route:group ...]
# Guards: no GPU hold (also the abort file between items), no build, CPU <= 60 C, hub idle at the start, nobody else's model loaded between routes, no game.
R=~/Desktop/local-llm; LOCK=$R/hardware/generated/GPU-LOCK; HUB=http://127.0.0.1:30100; H=$R/hardware/quant-eval/tooluse
O=$1; shift
maxt() { for z in /sys/class/hwmon/hwmon*; do [ "$(cat $z/name 2>/dev/null)" = coretemp ] && for t in $z/temp*_input; do echo $(( $(cat $t)/1000 )); done; done | sort -n | tail -1; }
hub() { curl -s -m 5 $HUB/health; }
log() { echo "$(date -Is) $*" | tee -a $O/chain.out; }
mkdir -p $O
for i in $(seq 1 90); do hub | grep -q '"active_backend": null' && break; /bin/sleep 10; done
hub | grep -q '"active_backend": null' || { log "HUB-BUSY at start"; exit 6; }
prev=""
for rg in "$@"; do
  route=${rg%%:*}; group=${rg##*:}
  [ -e $LOCK ] && { log "LOCK present; stop"; exit 5; }
  [ "$(pgrep -f 'cc1plus|ninja' | wc -l)" = 0 ] || { log "a build is running; stop"; exit 8; }
  pgrep -if 'steam|proton|wine|gamescope' > /dev/null && { log "a game is running; stop"; exit 10; }
  for i in $(seq 1 120); do [ "$(maxt)" -le 60 ] && break; /bin/sleep 5; done
  [ "$(maxt)" -le 60 ] || { log "CPU $(maxt) C; stop"; exit 9; }
  h=$(hub); am=$(echo "$h" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("active_model") or "-", d.get("inflight",0)+d.get("queued",0))')
  read am_model am_busy <<< "$am"
  if [ "$am_model" != "-" ] && [ "$am_model" != "$prev" ]; then log "someone else's model is loaded ($am_model); stop"; exit 6; fi
  if [ "${am_busy:-1}" != 0 ]; then log "hub has other requests; stop"; exit 6; fi
  [ $group = small ] && HL=1020 || HL=3720
  log "start $route $group cpu $(maxt) C"
  (cd $H && timeout $((HL+60)) python3 -B -m fast_amd.run $route $group --base-url $HUB --out $O/$route --abort-file $LOCK --load-cap 300 --hard-limit $HL > $O/$route.log 2>&1)
  rc=$?
  log "end $route rc=$rc $(python3 -c "import json;r=json.load(open('$O/$route/fast-result.json'));print(r.get('status'),r.get('score'))" 2>/dev/null)"
  [ $rc = 4 ] && { log "aborted by hold; stop"; exit 4; }
  prev=$route
done
log "chain done"
