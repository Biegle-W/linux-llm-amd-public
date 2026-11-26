#!/usr/bin/env python3
"""Freeze a budgeted rank tier from saved grades. No inference or network access."""
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, zip_longest
import hashlib
import json
from math import ceil, isfinite, log1p, sqrt
from pathlib import Path
import random
from statistics import mean, median

HERE = Path(__file__).resolve().parent
SEED = 20261125
SPLITS = 128
CATEGORIES = ('knowledge', 'math', 'code', 'instruction', 'reasoning', 'tools')
# Largest remainder quotas; reserve three BFCL subtypes and all six categories.
WEIGHTS = (0.25, 0.15, 0.14, 0.15, 0.14, 0.17)
TOOLS = ('multiple', 'parallel_multiple', 'irrelevance')
PENDING = {'pending', 'missing', 'ungraded', 'not_run', 'not run'}
MAYA = 'deepseek-v4.1-flash-1017-maya-unsloth-q1'
INK = 'inkling-2-mini-sq-20-strata-2gpu'
RIPPLE = 'ripple-65b-vllm'
PROFILES = {
    'standard': (2048, 3072, 3072, 2048, 2048, 2048, 4096),
    'moderate': (1536, 2048, 2048, 1536, 1536, 1024, 2048),
    'short': (1024, 1536, 1536, 1024, 1024, 768, 1536),
}
# Choice uses only the budget, then coverage, then the more generous caps.
SIZES = (24, 26, 28, 30, 32, 34, 36, 40, 48, 56)
RULE = ('Require complete core coverage and variable post-cap outcomes. Rank within '
        'category by item-rest association, middle difficulty, censoring and token cost. '
        'Require each available BFCL subtype, MATH-500 and AIME. Select the largest '
        'candidate meeting every conservative 85% time limit, breaking size ties by looser caps.')


def caps_for(profile):
    values = PROFILES[profile]
    return dict(zip(CATEGORIES, values[:6]), aime24=values[-1], aime25=values[-1])


def kind(item, category):
    prefix = item.split(':')[0]
    return prefix if prefix in ('aime24', 'aime25') else category


@dataclass(frozen=True)
class Row:
    category: str
    tier: str
    status: str
    prompt: int
    completion: int


def load_runs(data):
    runs = {}
    for path in sorted(Path(data).glob('*/graded*.json')):
        for name, records in json.loads(path.read_text())['routes'].items():
            key = name + '@inkling-q8-rdna3' if path.parent.name == 'inkling-q8-rdna3' else name
            target = runs.setdefault(key, {})
            for item, value in records.items():
                if value['status'] in PENDING:
                    continue
                usage = value.get('usage') or {}
                # In this archive several engines omit both fields on failed requests.
                if usage.get('completion_tokens') is None and value['status'] == 'correct':
                    raise ValueError(f'missing completion length on a correct result: {key} {item}')
                row = Row(value['category'], value['tier'], value['status'],
                          usage.get('prompt_tokens') or 0, usage.get('completion_tokens') or 0)
                if item in target and target[item] != row:
                    raise ValueError(f'conflicting overlapping grades: {key} {item}')
                target[item] = row
    return runs


def capped(row, cap):
    return row.status == 'capped' or row.completion > cap


def passed(row, cap):
    return row.status == 'correct' and row.completion <= cap


def quotas(size):
    q = {cat: int(size*w) for cat, w in zip(CATEGORIES, WEIGHTS)}
    rest = sorted(zip(CATEGORIES, WEIGHTS), key=lambda cw: -(size*cw[1] - q[cw[0]]))
    for cat, _ in rest[:size-sum(q.values())]:
        q[cat] += 1
    return q


def priority_lists(runs, train, core, caps, totals):
    groups = defaultdict(list)
    for item in core:
        rows = [runs[r][item] for r in train]
        category = rows[0].category
        cap = caps[kind(item, category)]
        wins, losses = [], []
        for r, row in zip(train, rows):
            # Remove the uncapped item from the original total before estimating association.
            rest = totals[r] - (row.status == 'correct')
            (wins if passed(row, cap) else losses).append(rest)
        if not wins or not losses:
            continue
        p = len(wins)/len(rows)
        association = (mean(wins)-mean(losses)) * sqrt(p*(1-p))
        # Approximate the slow deployment using only training-family observations.
        reference = [runs[r][item] for r in train if family(r)==family(MAYA)] or rows
        cost = median(min(row.completion, cap)/7.2 + row.prompt/35 for row in reference)
        utility = (association/10 + 2*sqrt(p*(1-p)) - .75*log1p(cost/10)
                   - .6*sum(capped(row, cap) for row in rows)/len(rows))
        groups[category].append((-utility, item))
    return {cat: [i for _, i in sorted(group)] for cat, group in groups.items()}


def choose(groups, size):
    columns = []
    for cat, count in quotas(size).items():
        ranked = groups[cat]
        required = (tuple('tools_'+s for s in TOOLS) if cat == 'tools'
                    else ('aime', 'math:') if cat == 'math' else ())
        fixed = [next((i for i in ranked if i.startswith(prefix)), None) for prefix in required]
        if None in fixed or len(ranked) < count:
            return None
        keep = set(fixed + [i for i in ranked if i not in fixed][:count-len(fixed)])
        columns.append([i for i in ranked if i in keep])
    return [i for group in zip_longest(*columns) for i in group if i is not None]


def nested(groups, size):
    """Extend the same core by largest category deficit; never skip within a queue."""
    order = choose(groups, size)
    if order is None:
        return []
    used = set(order)
    counts = quotas(size)
    queues = {cat: [i for i in reversed(groups[cat]) if i not in used] for cat in CATEGORIES}
    weights = dict(zip(CATEGORIES, (25, 15, 14, 15, 14, 17)))
    while available := [cat for cat in CATEGORIES if queues[cat]]:
        cat = max(available, key=lambda c: (len(order)+1)*weights[c] - 100*counts[c])
        order.append(queues[cat].pop())
        counts[cat] += 1
    return order


def fit_prefix(order, times, budget_seconds, scenario):
    elapsed = 0
    for n, item in enumerate(order):
        elapsed += times[item][scenario]
        if elapsed > budget_seconds:
            return n
    return len(order)


def family(route):
    if route.startswith('qwen3.8-27b-'):
        return 'qwen3.8-27b'
    if route.startswith('deepseek-v4.1-flash-1017-'):
        return 'deepseek-v4.1-flash-1017'
    return route


def splits(routes, holdout_families=None):
    families = sorted(set(map(family, routes)))
    train_n = len(families)//2 if holdout_families is None else len(families)-holdout_families
    options = list(combinations(families, train_n))
    sample = random.Random(SEED).sample(options, min(SPLITS, len(options)))
    for train in sample:
        yield [r for r in routes if family(r) in train], [r for r in routes if family(r) not in train]


def percentile(values, q):
    return sorted(values)[max(0, ceil(q*len(values))-1)]


def average_ranks(values):
    return [sum(v < x for v in values) + (values.count(x)-1)/2 for x in values]


def correlations(x, y):
    a, b = average_ranks(x), average_ranks(y)
    ma, mb = mean(a), mean(b)
    denom = sqrt(sum((i-ma)**2 for i in a)*sum((i-mb)**2 for i in b))
    rho = sum((i-ma)*(j-mb) for i, j in zip(a,b))/denom if denom else None
    directions, distinct_x, distinct_y = 0, 0, 0
    for i,j in combinations(range(len(x)),2):
        delta = (x[i]-x[j])*(y[i]-y[j])
        directions += (delta>0)-(delta<0)
        distinct_x += x[i] != x[j]
        distinct_y += y[i] != y[j]
    den = sqrt(distinct_x*distinct_y)
    return rho, directions/den if den else None


def separated_pairs(routes, runs, core, pub):
    pairs = list(combinations(routes, 2))
    pvalues = []
    for a,b in pairs:
        differences = [(runs[a][i].status=='correct')-(runs[b][i].status=='correct') for i in core]
        pvalues.append(pub.exact_mcnemar(differences.count(1), differences.count(-1)))
    return [pair for pair,p in zip(pairs, pub.holm(pvalues, pairs)) if p <= .05]


def summary(values):
    values = [v for v in values if v is not None]
    if not values:
        return {'mean': None, 'p05': None, 'n': 0}
    return {'mean': round(mean(values),4), 'p05': round(percentile(values,.05),4), 'n':len(values)}


def validate(runs, routes, core, totals, separated, nested_spec=None, holdout_families=None):
    results = defaultdict(lambda: defaultdict(list))
    for train, test in splits(routes,holdout_families):
        for profile in (PROFILES if nested_spec is None else [nested_spec[0]]):
            caps = caps_for(profile)
            groups = priority_lists(runs, train, core, caps, totals)
            sequence = nested(groups,nested_spec[1]) if nested_spec else []
            for size in (SIZES if nested_spec is None else nested_spec[2]):
                records = results[size,profile]
                records['attempts'].append(1)
                order = choose(groups,size) if nested_spec is None else sequence[:size]
                if order is None or len(order) != size:
                    continue
                scores = {r: sum(passed(runs[r][i],caps[kind(i,runs[r][i].category)]) for i in order)
                          for r in test}
                rho,tau = correlations(list(scores.values()),[totals[r] for r in test])
                records['rho'].append(rho)
                records['tau'].append(tau)
                for a,b in separated:
                    if a in scores and b in scores:
                        records['agreement'].append((scores[a]-scores[b])*(totals[a]-totals[b]) > 0)
    return {key: {'splits':len(z['attempts']), 'feasible_splits':len(z['rho']),
                  'spearman':summary(z['rho']), 'kendall_tau_b':summary(z['tau']),
                  'separated_pair_order_agreement':round(mean(z['agreement']),4) if z['agreement'] else None,
                  'held_out_separated_pair_comparisons':len(z['agreement']), 'full_separated_pairs':len(separated)}
            for key,z in results.items()}


def representative(runs,routes,core):
    result={}
    for i in core:
        rows=[runs[r][i] for r in routes if runs[r][i].prompt and runs[r][i].completion]
        result[i]={'prompt_tokens':median(v.prompt for v in rows),
                   'completion_tokens':median(v.completion for v in rows)}
    return result


def route_seconds(runs, speeds, costs, categories, order, caps):
    estimates = {}
    aliases={INK:'inkling-2-mini-q8@inkling-q8-rdna3', 'hy4-flash-sq-64-strata':'hy4-flash-sq-64'}
    for route,speed in speeds.items():
        archive = runs.get(aliases.get(route,route),{})
        seconds = {}
        for i in order:
            baseline = costs[i]
            row = archive.get(i)
            prompt = row.prompt if row and row.prompt else baseline['prompt_tokens']
            length = row.completion if row and row.completion else baseline['completion_tokens']*speed['verbosity']
            cap = caps[kind(i,categories[i])]
            def estimate(params):
                return (params['overhead_s'] + prompt/params['prefill_tok_s']
                        + min(cap,length)/params['decode_tok_s'])
            typical = estimate(speed)
            slow = speed.get('conservative')
            if not slow:
                slow = dict(speed,decode_tok_s=speed['decode_tok_s']*.90,
                            prefill_tok_s=speed['prefill_tok_s']*.75,overhead_s=speed['overhead_s']*1.25)
            conservative = max(typical,estimate(slow))
            seconds[i] = (typical,conservative)
        estimates[route]=seconds
    return estimates


def rescore(runs, order, caps):
    scores={}
    for r, rows in sorted(runs.items()):
        observed = [(rows[i],caps[kind(i,rows[i].category)]) for i in order if i in rows]
        original = sum(row.status=='correct' for row,_ in observed)
        correct = sum(passed(row,cap) for row,cap in observed)
        scores[r] = {'correct':correct, 'attempted':len(observed), 'not_run':len(order)-len(observed),
                     'capped':sum(capped(row,cap) for row,cap in observed),
                     'original_correct':original, 'correct_lost_to_lower_cap':original-correct}
    return scores


def read_pub(pub_dir):
    import importlib.util
    spec = importlib.util.spec_from_file_location('rank_pub_analysis',Path(pub_dir)/'analyze.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_speeds(speeds):
    small = {INK, 'kolibri-1.1-iq4_xs', 'qwen3.8-27b-sglang-dflash2',
             'qwen3.8-flash-next-iq3_xxs', 'qwen3.8-27b-vllm'}
    large = {MAYA, RIPPLE, 'deepseek-v4.1-flash-1017-strata-unsloth-q1',
             'hy4-flash-sq-64-strata', 'glm-5.3-flash-maya'}
    if set(speeds) != small | large:
        raise ValueError('speed table must cover exactly the ten target routes')
    for route, row in speeds.items():
        expected = ('small', 15) if route in small else ('large', 30)
        if (row['class'], row['budget_min']) != expected:
            raise ValueError(f'incorrect route class or budget: {route}')
        if not isfinite(row['verbosity']) or row['verbosity'] <= 0:
            raise ValueError(f'invalid verbosity: {route}')
        for params in (row, row.get('conservative', row)):
            for key in ('decode_tok_s', 'prefill_tok_s', 'overhead_s'):
                value = params[key]
                if not isfinite(value) or value < 0 or (key != 'overhead_s' and value == 0):
                    raise ValueError(f'invalid {key}: {route}')


def build(data,speed_file,pub_dir):
    runs=load_runs(data)
    speed_data=Path(speed_file).read_bytes()
    speeds=json.loads(speed_data)
    speeds=speeds.get('routes',speeds)
    validate_speeds(speeds)
    pool={i:row for rows in runs.values() for i,row in rows.items()}
    core=sorted(i for i,row in pool.items() if row.tier=='core')
    if len(core)!=216 or len(pool)!=300:
        raise ValueError('expected the 216 core and 84 additional archived ids')
    routes=sorted(r for r,rows in runs.items() if '@' not in r and all(i in rows for i in core))
    totals={r:sum(runs[r][i].status=='correct' for i in core) for r in routes}
    separated=separated_pairs(routes,runs,core,read_pub(pub_dir))
    validation=validate(runs,routes,core,totals,separated)
    categories={i:row.category for i,row in pool.items()}
    panel=[RIPPLE,MAYA,'deepseek-v4.1-flash-1017-strata-unsloth-q1','glm-5.3-flash-maya',
           'qwen3.8-flash-next-iq3_xxs','qwen3.8-27b-vllm','qwen3.8-27b-sglang-dflash2',
           'inkling-2-mini-q8@inkling-q8-rdna3']
    costs=representative(runs,panel,core)
    candidates=[]
    for profile in PROFILES:
        caps=caps_for(profile)
        groups=priority_lists(runs,routes,core,caps,totals)
        for size in SIZES:
            order=choose(groups,size)
            if order is None:
                continue
            seconds=route_seconds(runs,speeds,costs,categories,order,caps)
            minutes={r:{label:sum(p[k] for p in times.values())/60
                        for k,label in enumerate(('typical','conservative'))} for r,times in seconds.items()}
            fits=all(pair['conservative']<=.85*speeds[r]['budget_min'] for r,pair in minutes.items())
            candidates.append((size,profile,fits,order,minutes,seconds,validation[size,profile]))
    feasible=[row for row in candidates if row[2]]
    if not feasible:
        raise ValueError('no candidate fits the 85% conservative time limits')
    size,profile,_,order,minutes,seconds,metrics=max(feasible,key=lambda row:row[0])
    caps = caps_for(profile)
    order = nested(priority_lists(runs,routes,core,caps,totals),size)
    seconds = route_seconds(runs,speeds,costs,categories,order,caps)
    length = max(fit_prefix(order,seconds[r],60*s['budget_min'],1)
                 for r,s in speeds.items() if s['class']=='small')
    order = order[:length]
    checkpoints = sorted(set(range(size,length+1,15)) | {length})
    prefix_cv = validate(runs,routes,core,totals,separated,(profile,size,checkpoints))
    sparse = [n for n in checkpoints if not prefix_cv[n,profile]['feasible_splits']]
    secondary = validate(runs,routes,core,totals,separated,(profile,size,sparse),3) if sparse else {}
    predicted_prefix = {r:{k:fit_prefix(order,t,60*speeds[r]['budget_min'],j)
                           for j,k in enumerate(('typical','conservative'))} for r,t in seconds.items()}
    artifact={
        'schema':2,'frozen':'2026-11-25','seed':SEED,'rule':RULE,'pool_size':len(pool),
        'core_n':size,'core_counts':dict(Counter(categories[i] for i in order[:size])),
        'prefix_checkpoints':checkpoints,'predicted_prefix':predicted_prefix,
        'prefix_validation':{str(n):prefix_cv[n,profile] for n in checkpoints},
        'prefix_validation_hold_three_families_out':{str(n):secondary[n,profile] for n in sparse},
        'eligible_core':len(core),'profile':profile,'caps':caps_for(profile),
        'counts':dict(Counter(categories[i] for i in order)),
        'bfcl_counts':dict(Counter(i.split(':')[0].removeprefix('tools_') for i in order if categories[i]=='tools')),
        'order':order,'item_costs':{i:costs[i] for i in order},
        'speeds_sha256':hashlib.sha256(speed_data).hexdigest(),
        'item_seconds':{r:{i:round(times[i][0],4) for i in order} for r,times in seconds.items()},
        'predicted_minutes':{r:{k:round(m,4) for k,m in pair.items()} for r,pair in minutes.items()},
        'validation':metrics,'validation_routes':routes,'rescored_saved_runs':rescore(runs,order,caps_for(profile))}
    alternatives = {p: rescore(runs, order, caps_for(p)) for p in PROFILES}
    return artifact, report(artifact,candidates,speeds,alternatives)


def report(a,candidates,speeds,alternatives):
    chosen=a['profile']
    order=a['order']
    lines=['# Selection and budget trade-off','',
           f"Every route starts the same {a['core_n']}-item core, followed by a shared extension up to {len(order)} items, using the {chosen} caps throughout. Only the core must fit 85% of every conservative budget. The table compares candidate cores; validation scores did not enter the size/cap decision.",'',
           '| Items | Caps | Feasible splits | Held-out Spearman | Held-out Kendall τ-b | DeepSeek Maya min, typical / slow | Inkling min, typical / slow | All budgets fit |',
           '|---:|---|---:|---:|---:|---:|---:|---|']
    for n,p,fit,_,m,_,v in sorted(candidates,key=lambda x:(x[0],list(PROFILES).index(x[1]))):
        def pair(r):
            return f"{m[r]['typical']:.2f} / {m[r]['conservative']:.2f}"
        lines.append(f"| {n} | {p} | {v['feasible_splits']}/{v['splits']} | {v['spearman']['mean']} | {v['kendall_tau_b']['mean']} | {pair(MAYA)} | {pair(INK)} | {'yes' if fit else 'no'} |")
    lines.extend(['','## Coverage and selection','',
        'The pool has 300 IDs. Eligibility requires observations on every complete route, leaving 216 core IDs. The extra 84 were measured only on eight faster routes. This restriction allows paired scoring and timing on the slow routes. The retained items span MATH-500 and AIME. The archived BFCL pool contains multiple, parallel_multiple and irrelevance. It has no simple items.',
        '', 'Category target shares are 25% knowledge, 15% math, 14% code, 15% instruction, 14% reasoning and 17% tools. Knowledge retains the largest share from the full suite. The other shares keep broad category coverage under the time limit. Largest-remainder rounding gives the counts in the manifest. Order rotates through categories until each quota is exhausted.',
        '', 'On each training panel, exclude items with unanimous simulated outcomes. For each remaining item, compare the mean original core score of passers and failers, removing the item itself from those totals. The association term rewards alignment with the full-suite ordering. Middle difficulty, fewer truncated answers and shorter prompts and completions also improve priority. The cost term uses a training-only DeepSeek-family median when available and a training-panel median otherwise. It weights prompt and answer lengths by 35 and 7.2 tokens/s. Within each category the best-scoring items fill the quota, reserving one per available tool subtype and one each for AIME and MATH-500. IDs break ties.',
        '', '## Held-out check','',
        f"The validation panel has {len(a['validation_routes'])} complete routes. One Inkling snapshot represents the family. Qwen-27B engines stay together, as do the two DeepSeek deployments. Seed {SEED} samples {SPLITS} distinct training sets of half the route families (rounded down). For each candidate, the selector re-estimates priorities and picks fresh IDs using only those training grades and lengths. It scores the remaining routes on those IDs against each route’s original 216-item total. Full-route token estimates used to forecast the final budget do not enter fold priorities.",
        '', 'A fold can be infeasible if too few mixed-outcome items remain for a quota. The table reports successful folds. Average ranks handle ties in Spearman, and Kendall uses τ-b. Fifth percentiles are nearest-rank. A separated pair passes the full-suite two-sided exact McNemar test after Holm adjustment across all pairs of complete routes. Agreement counts ties as disagreement and pools only comparisons where both routes were held out. Overlapping folds are correlated. These statistics describe historical deployments and selection of this size/profile, not a blind evaluation of the final frozen IDs.',
        '', '## Timing and censoring','',
        'Per request, time equals fixed overhead plus prompt tokens divided by prefill speed plus capped completion tokens divided by decode speed. Typical and slow scenarios share lengths and use their respective speed parameters. Measured route-specific token counts take precedence, with the retired RDNA3 Inkling and partial Hy4 SQ-64 as family proxies. On missing items the model multiplies the median completion length from the eight-route calibration panel by the route verbosity. Prompt lengths fall back to the panel median. Time excludes loading, warm-up and grading. Engine changes, response lengths, retries outside the harness and contention can change wall time. The deadline guard remains necessary.',
        '', 'A saved correct answer loses credit only when its completion length exceeds the new cap. Previously capped answers stay wrong. The archive cannot predict changes in decoding caused by changing engines or max_tokens. Missing quick-run items are excluded from attempted totals.',
        '', 'Cap sensitivity holds the frozen IDs fixed while changing only the caps. The standard, moderate and short cap profiles use the following values.', '',
        '| Profile | Knowledge | Math | Code | Instruction | Reasoning | Tools | AIME |',
        '|---|---:|---:|---:|---:|---:|---:|---:|',
        *['| '+name+' | '+' | '.join(str(x) for x in values)+' |' for name,values in PROFILES.items()],
        '', '| Historical route | Cap profile | Correct at original caps | Simulated correct | Simulated capped |',
        '|---|---|---:|---:|---:|'])
    for r in (RIPPLE,'inkling-2-mini-q8','inkling-2-mini-q8@inkling-q8-rdna3'):
        for p, scores in alternatives.items():
            row = scores[r]
            lines.append(f"| {r} | {p} | {row['original_correct']} | {row['correct']} | {row['capped']} |")
    v = a['validation']
    lines.extend(['',f"The chosen configuration gave mean Spearman {v['spearman']['mean']:.4f} "
                  f"(5th percentile {v['spearman']['p05']:.4f}) and mean Kendall τ-b "
                  f"{v['kendall_tau_b']['mean']:.4f} (5th percentile {v['kendall_tau_b']['p05']:.4f}). "
                  f"Pair ordering agreed in {100*v['separated_pair_order_agreement']:.2f}% of "
                  f"{v['held_out_separated_pair_comparisons']} held-out comparisons. The full suite "
                  f"separated {v['full_separated_pairs']} distinct pairs."])
    lines.extend(['','## Nested checkpoints','',
        'The core above is unchanged. Each next ID is the highest-priority remaining ID in the category furthest below its target share at the next prefix length; exhausted categories are skipped and ties follow the fixed category order. The final length is the longest prefix any small route can fit at conservative speed in 15 minutes. The 84 incompletely observed extra IDs are never used.', '',
        '| Category | Core | Whole list |','|---|---:|---:|',
        *[f"| {cat} | {a['core_counts'][cat]} | {a['counts'][cat]} |" for cat in CATEGORIES], '',
        'The four non-AIME core math IDs are all prealgebra; category coverage does not imply broad math subdomain coverage. Cap sensitivity above uses the whole list. Below each family split reselects its own core and extension before scoring held-out routes. Agreement means matching direction, not replicating statistical significance.', '',
        '| Prefix | Feasible folds | Spearman mean / p05 | Kendall τ-b mean / p05 | Separated-pair agreement | Comparisons |', '|---:|---:|---:|---:|---:|---:|'])
    for n in a['prefix_checkpoints']:
        v=a['prefix_validation'][str(n)]
        lines.append(f"| {n} | {v['feasible_splits']}/{v['splits']} | {v['spearman']['mean']} / {v['spearman']['p05']} | {v['kendall_tau_b']['mean']} / {v['kendall_tau_b']['p05']} | {v['separated_pair_order_agreement']} | {v['held_out_separated_pair_comparisons']} |")
    if a['prefix_validation_hold_three_families_out']:
        lines.extend(['','When no half-split can supply enough mixed-outcome IDs, its statistics are unavailable. As a separate sensitivity check for those checkpoints, hold out three whole families instead. This provides more selection data but fewer held-out routes; its statistics are not directly comparable to the half-splits.', '', '| Prefix | Feasible folds | Spearman mean / p05 | Kendall τ-b mean / p05 | Separated-pair agreement | Comparisons |', '|---:|---:|---:|---:|---:|---:|'])
        for n,v in a['prefix_validation_hold_three_families_out'].items():
            lines.append(f"| {n} | {v['feasible_splits']}/{v['splits']} | {v['spearman']['mean']} / {v['spearman']['p05']} | {v['kendall_tau_b']['mean']} / {v['kendall_tau_b']['p05']} | {v['separated_pair_order_agreement']} | {v['held_out_separated_pair_comparisons']} |")
    lines.extend(['','## Current-route time forecast','', 'Minutes are core-only (`predicted_minutes`). Prefix counts use the entire route budget and stop before the first item that would exceed it. Neither scenario is a measured runtime or guarantee.', '', '| Route | Budget min | Core typical min | Core conservative min | Typical prefix | Conservative prefix |','|---|---:|---:|---:|---:|---:|'])
    for r,m in a['predicted_minutes'].items():
        p=a['predicted_prefix'][r]
        lines.append(f"| {r} | {speeds[r]['budget_min']} | {m['typical']:.2f} | {m['conservative']:.2f} | {p['typical']} | {p['conservative']} |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=HERE.parent/'data')
    parser.add_argument('--speeds',type=Path,default=HERE/'speeds.json')
    parser.add_argument('--pub',type=Path,default=HERE.parent/'pub')
    parser.add_argument('--out',type=Path,default=HERE/'rank-items.json')
    parser.add_argument('--report',type=Path,default=HERE/'selection-report.md')
    args=parser.parse_args()
    artifact,md=build(args.data,args.speeds,args.pub)
    args.out.write_text(json.dumps(artifact,indent=2,sort_keys=True)+'\n')
    args.report.write_text(md)


if __name__=='__main__':
    main()
