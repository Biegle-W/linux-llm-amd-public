import json,statistics,sys
from pathlib import Path
for m in sys.argv[2].split(','):
    d=json.loads((Path(sys.argv[1])/f'{m}.json').read_text())
    rows=[r for r in d.values() if r.get('usage') and not r.get('error')]
    first=d[next(iter(d))]
    rates=[r['usage']['completion_tokens']/r['seconds'] for r in rows if r['usage']['completion_tokens']>=100 and r is not first and not r.get('rerun_cap')]
    total=sum(r['seconds'] for r in rows if r is not first)
    print(f"{m}: load+first {first['seconds']:.0f}s | median gen {statistics.median(rates):.1f} tok/s (n={len(rates)}) | rest of suite {total/60:.1f} min, {sum(r['usage']['completion_tokens'] for r in rows)} tokens")
