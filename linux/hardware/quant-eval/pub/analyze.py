#!/usr/bin/env python3
"""Fixed-mixture scores, Wilson intervals, exact paired McNemar/Holm, paired bootstrap."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random

CONFIG={'confidence_z':1.959963984540054,'alpha':.05,'bootstrap_samples':10000,'seed':20261110}
PENDING={'pending','missing','ungraded'}
STATUSES={'correct','wrong','capped','error','pending','missing','ungraded','empty','malformed','refusal'}


def wilson(k,n):
    if not n:return [None,None]
    z=CONFIG['confidence_z'];p=k/n;denom=1+z*z/n
    mid=(p+z*z/(2*n))/denom;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [max(0.,mid-half),min(1.,mid+half)]


def exact_mcnemar(b,c):
    n=b+c
    if n==0:return 1.
    terms=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)-n*math.log(2) for i in range(min(b,c)+1)]
    top=max(terms)
    return min(1.,2*math.exp(top)*sum(math.exp(t-top) for t in terms))


def holm(pvalues,labels=None,family_size=None):
    labels=list(range(len(pvalues))) if labels is None else labels
    m=len(pvalues) if family_size is None else family_size
    if m<len(pvalues):raise ValueError('family smaller than supplied hypotheses')
    order=sorted(range(len(pvalues)),key=lambda i:(pvalues[i],labels[i]));out=[0.]*len(order);running=0.
    for rank,i in enumerate(order):
        running=max(running,min(1.,(m-rank)*pvalues[i]));out[i]=running
    return out


def bootstrap_pair(a,b,strata,samples,seed):
    """Source/stratum-preserving PAIRS; prescribed noninterpolated order statistics."""
    if not a:return [None,None]
    if not(len(a)==len(b)==len(strata)):raise ValueError('unaligned bootstrap inputs')
    groups={}
    for x,y,s in zip(a,b,strata):groups.setdefault(s,[]).append(int(x)-int(y))
    rng=random.Random(seed);draws=[]
    for _ in range(samples):
        draws.append(sum(sum(rng.choice(groups[k]) for _ in groups[k]) for k in sorted(groups))/len(a))
    draws.sort()
    return [draws[math.floor(.025*(samples-1))],draws[math.ceil(.975*(samples-1))]]


def summarize(rows):
    counts=Counter(x['status'] for x in rows);flags=Counter(flag for x in rows for flag in set(x.get('flags',[])))
    n=len(rows);k=sum(x['correct'] for x in rows);pending=sum(counts[x] for x in PENDING);finished=n-pending
    capped=[x for x in rows if x['status']=='capped' and 'visible_correct' in x]
    return {'n':n,'correct':k,'complete':not pending,'pending_n':pending,'completed_n':finished,
            'score':k/n if n and not pending else None,'diagnostic_pending_as_zero_score':k/n if n else None,
            'ci95_wilson':wilson(k,n) if not pending else [None,None],
            'counts':dict(counts),'flags':dict(flags),'completed_only_accuracy':k/finished if finished else None,
            'capped_visible_n':len(capped),'capped_visible_accuracy':sum(x['visible_correct'] for x in capped)/len(capped) if capped else None}


def analyze(data,samples=None):
    samples=CONFIG['bootstrap_samples'] if samples is None else samples
    if samples<1:raise ValueError('bootstrap samples must be positive')
    ids=data['item_ids'];routes=data['routes'];names=sorted(routes);tier=data.get('tier')
    if not ids or not names or len(set(ids))!=len(ids):raise ValueError('empty/duplicate item IDs or routes')
    if not data.get('items_sha256'):raise ValueError('missing item manifest hash')
    for name,rows in routes.items():
        if set(rows)!=set(ids):raise ValueError('route item set differs:'+name)
        for key,r in rows.items():
            if r['status']=='grader_error':raise ValueError('grader defects must be repaired uniformly before analysis:'+name+':'+key)
            if r['status'] not in STATUSES:raise ValueError('unknown primary status')
            if type(r['correct']) is not bool or r['correct']!=(r['status']=='correct'):raise ValueError('inconsistent binary score')
            if not r.get('stratum'):raise ValueError('source/stratum metadata required:'+key)
    for key in ids:
        for field in ('category','tier','stratum'):
            if len({routes[name][key].get(field) for name in names})!=1:raise ValueError(field+' mismatch:'+key)
    complete=all(r['status'] not in PENDING for rows in routes.values() for r in rows.values())
    intended=(tier=='core' and len(ids)==216 and len(names)==12) or (tier=='all' and len(ids)==300 and len(names)==8)
    provenance=bool(data.get('manifest_verified')) and all(data.get('route_metadata',{}).get(name,{}).get('items_sha256')==data['items_sha256'] for name in names)
    primary=intended and complete and tier=='core' and provenance
    secondary=intended and complete and tier=='all' and provenance
    family=66 if tier=='core' else 28 if tier=='all' else len(names)*(len(names)-1)//2
    family=max(family,len(names)*(len(names)-1)//2)
    # Never turn fleet-stop omissions into failed model attempts or intended rankings.
    paired_ids=[key for key in ids if all(routes[name][key]['status'] not in PENDING for name in names)]
    result={'schema_version':2,'tier':tier,'items_sha256':data['items_sha256'],'grader_version':data.get('grader_version'),
      'complete':complete,'intended_design_shape':intended,'primary_confirmatory':primary,'secondary_exploratory':secondary,
      'primary_policy':'First attempt; capped and started-request errors are zero. Pending/ungraded makes the intended ranking incomplete.',
      'family_label':'primary core (66 pairs)' if primary else 'secondary exploratory fast-only (28 pairs)' if secondary else 'EXPLORATORY ONLY: incomplete fleet or non-design sample',
      'holm_family_size':family,'paired_item_ids':paired_ids,
      'interval_note':'Wilson 95% pointwise item-sampling approximation; fixed quotas, finite AIME pools and correlated tasks limit iid interpretation.',
      'bootstrap_note':'Paired source/stratum-preserving bootstrap; pointwise, not simultaneous; degenerate [0,0] does not establish equivalence.',
      'bootstrap_samples':samples,'routes':{},'pairs':[]}
    for field in ('route_metadata','run_date_utc','timeout_policy','manifest','manifest_verified'):
        result[field]=data.get(field)
    for name,rows in routes.items():
        total=summarize([rows[k] for k in ids])
        total['categories']={cat:summarize([rows[k] for k in ids if rows[k]['category']==cat]) for cat in sorted({r['category'] for r in rows.values()})}
        total['total_seconds']=sum(r.get('seconds') or 0 for r in rows.values())
        total['completion_tokens']=sum((r.get('usage') or {}).get('completion_tokens',0) or 0 for r in rows.values())
        result['routes'][name]=total
    for i,name in enumerate(names):
        for other in names[i+1:]:
            a=[routes[name][k]['correct'] for k in paired_ids];b=[routes[other][k]['correct'] for k in paired_ids]
            strata=[routes[name][k]['stratum'] for k in paired_ids]
            wins=sum(x and not y for x,y in zip(a,b));losses=sum(y and not x for x,y in zip(a,b))
            seed='20261110|bootstrap|'+name+'|'+other+'|'+str(tier)
            result['pairs'].append({'a':name,'b':other,'n':len(paired_ids),'a_only':wins,'b_only':losses,
              'difference':(wins-losses)/len(a) if a else None,'p_exact':exact_mcnemar(wins,losses),
              'ci95_paired_bootstrap':bootstrap_pair(a,b,strata,samples,seed),'bootstrap_seed':seed,
              'exploratory':not primary})
    adjusted=holm([p['p_exact'] for p in result['pairs']],[(p['a'],p['b']) for p in result['pairs']],family)
    for pair,p in zip(result['pairs'],adjusted):
        pair['p_holm']=p;pair['significant_holm_05']=bool(pair['n']) and p<=CONFIG['alpha']
        pair['primary_difference_supported']=primary and pair['significant_holm_05']
        pair['interpretation']='difference detected within stated family' if pair['significant_holm_05'] else 'not resolved by this test'
    return result


def pct(x):return 'NA' if x is None else f'{100*x:.1f}%'


def markdown(result):
    lines=['# Public benchmark quality report','',result['family_label'],f"Tier: {result['tier']}; item-manifest SHA-256: {result['items_sha256']}",'',result['primary_policy'],'',
      '| Route | Correct/N | Score | Wilson 95% | Capped | Error | Pending/ungraded | Malformed |',
      '|---|---:|---:|---|---:|---:|---:|---:|']
    for name,s in sorted(result['routes'].items()):
        c=s['counts'];lines.append(f"| {name} | {s['correct']}/{s['n']} | {pct(s['score'])} | {' – '.join(map(pct,s['ci95_wilson']))} | {c.get('capped',0)} | {c.get('error',0)} | {s['pending_n']} | {c.get('malformed',0)} |")
    lines+=['','## Per-category scores','','| Route | Category | Correct/N | Score | Wilson 95% | Caps | Errors | Pending | Malformed |','|---|---|---:|---:|---|---:|---:|---:|---:|']
    for name,s in sorted(result['routes'].items()):
        for cat,v in s['categories'].items():
            c=v['counts'];lines.append(f"| {name} | {cat} | {v['correct']}/{v['n']} | {pct(v['score'])} | {' – '.join(map(pct,v['ci95_wilson']))} | {c.get('capped',0)} | {c.get('error',0)} | {v['pending_n']} | {c.get('malformed',0)} |")
    names=sorted(result['routes']);lookup={frozenset((p['a'],p['b'])):p for p in result['pairs']}
    lines+=['','## Exact McNemar matrix (Holm-adjusted p)','','| Route | '+' | '.join(names)+' |','|---|'+'---:|'*len(names)]
    for name in names:
        lines.append('| '+name+' | '+' | '.join('—' if name==other else f"{lookup[frozenset((name,other))]['p_holm']:.4g}" for other in names)+' |')
    lines+=['','## Paired differences (A minus B)','','| A | B | n | A-only | B-only | Difference | Bootstrap 95% | Raw p | Holm p | Interpretation |','|---|---|---:|---:|---:|---:|---|---:|---:|---|']
    for p in result['pairs']:
        lines.append(f"| {p['a']} | {p['b']} | {p['n']} | {p['a_only']} | {p['b_only']} | {pct(p['difference'])} | {' – '.join(map(pct,p['ci95_paired_bootstrap']))} | {p['p_exact']:.4g} | {p['p_holm']:.4g} | {p['interpretation']} |")
    lines+=['','## Interpretation limits','',result['interval_note'],result['bootstrap_note'],
      'No unresolved difference establishes equivalence. No best-route claim follows from marginal confidence-interval overlap.',
      'No official full-benchmark, contamination-free, causal quantization or thinking-on claim is supported.',
      'Incomplete runs: pairs use only the exact common completed item IDs; pending-as-zero and completed-only scores in JSON are diagnostic, not primary rankings.',
      'Code is ungraded unless a disposable unprivileged no-network/no-host-mount container was verified.','']
    return '\n'.join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--output-prefix',type=Path)
    p.add_argument('--bootstrap-samples',type=int,default=10000);args=p.parse_args(argv)
    inp=args.input/'graded.json' if args.input.is_dir() else args.input
    result=analyze(json.loads(inp.read_text()),args.bootstrap_samples);prefix=args.output_prefix or inp.parent/'analysis'
    prefix.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');prefix.with_suffix('.md').write_text(markdown(result))
    print(prefix.with_suffix('.json'));print(prefix.with_suffix('.md'));return 0

if __name__=='__main__':raise SystemExit(main())
