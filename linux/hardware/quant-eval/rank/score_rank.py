#!/usr/bin/env python3
"""Report rank-tier scores from grade_pub JSON; --rescore DATA is historical only."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'pub'))
from analyze import CONFIG, STATUSES, exact_mcnemar, holm, wilson

NO_ATTEMPT = {'pending', 'missing', 'not_run'}
UNSCORED = NO_ATTEMPT | {'ungraded'}
KINDS = {'knowledge': 'mcq', 'reasoning': 'mcq', 'math': 'numeric',
         'instruction': 'ifeval', 'code': 'code', 'tools': 'tools'}
HISTORICAL_NOTE = ('Comparison only: saved answers from older engines, not a current-engine '
                   'or time-budget result. Scores simulate the frozen caps; selection used historical outcomes.')


def letter_groups(order, separated):
    """Insert/absorb: every unresolved pair shares a letter, no separated pair does."""
    columns = {frozenset(order)} if order else set()
    for a, b in separated:
        split = set()
        for col in columns:
            if a in col and b in col:
                split.update((col - {a}, col - {b}))
            else:
                split.add(col)
        columns = {s for s in split if not any(s < t for t in split)}
    result = {k: [] for k in order}
    for i, col in enumerate(sorted(columns, key=lambda c: [k not in c for k in order])):
        label = ''
        i += 1
        while i:
            i, digit = divmod(i - 1, 26)
            label = chr(65 + digit) + label
        for name in col:
            result[name].append(label)
    return result


def valid_ids(ids, field, empty_ok=False):
    if (not isinstance(ids, list) or (not ids and not empty_ok) or
            not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids))):
        raise ValueError(f'{field}: expected a list of unique item IDs')
    return ids


def cap_for(caps, key, category):
    for kind in (key, key.split(':')[0], category, KINDS.get(category)):
        if kind in caps:
            cap = caps[kind]
            if type(cap) is not int or cap <= 0:
                raise ValueError(f'invalid cap for {kind}')
            return cap
    raise ValueError(f'no frozen cap for {key} ({category})')


def classify(name, key, row, skipped, caps):
    if row is None:
        return 'not_run'
    status = row['status']
    if status not in STATUSES | {'not_run'}:
        raise ValueError(f'{name}/{key}: cannot score {status}')
    if type(row['correct']) is not bool or row['correct'] != (status == 'correct'):
        raise ValueError(f'{name}/{key}: inconsistent status and correct flag')
    if key in skipped:
        if status not in UNSCORED:
            raise ValueError(f'{name}/{key}: graded attempt contradicts runner not_run')
        return 'not_run'
    if status in NO_ATTEMPT:
        return 'not_run'
    if caps is not None and status not in {'ungraded', 'capped'}:
        tokens = (row.get('usage') or {}).get('completion_tokens')
        if type(tokens) is not int or tokens < 0:
            raise ValueError(f'{name}/{key}: cannot simulate cap without completion_tokens')
        if tokens > cap_for(caps, key, row['category']):
            return 'capped'
    return status


def times(run):
    if not run:
        return None, None
    elapsed, budget = run['elapsed_s'], run['budget_s']
    if (not all(type(x) in (float, int) and math.isfinite(x) for x in (elapsed, budget)) or
            elapsed < 0 or budget <= 0):
        raise ValueError('invalid runner elapsed_s or budget_s')
    return elapsed / 60, budget / 60


def _fixed(rank_items, routes, runs=None, historical=False, compare=True):
    """Score precisely this list. For a ranking, apply one Holm family to complete routes."""
    ids = valid_ids(rank_items['order'], 'order')
    runs = runs or {}
    if not routes or runs.keys() - routes.keys():
        raise ValueError('no graded routes or runner metadata for unknown route')
    cats = {}
    for rows in routes.values():
        for k in ids:
            if k in rows:
                cat = rows[k]['category']
                if not cat or cats.setdefault(k, cat) != cat:
                    raise ValueError(f'inconsistent category for {k}')
    observed = Counter(cats.values())
    declared = rank_items.get('counts')
    if declared is None:
        declared = observed.copy()
        if len(cats) < len(ids):
            declared['unknown'] += len(ids) - len(cats)
    if 'categories' in declared:
        declared = declared['categories']
    if (not all(type(v) is int and v >= 0 for v in declared.values()) or
            sum(declared.values()) != len(ids) or observed - Counter(declared)):
        raise ValueError('frozen category counts disagree with graded items')
    caps = rank_items['caps'] if historical else None
    r = {'category_counts': dict(declared), 'routes': {}, 'pairs': []}
    binary = {}
    for name, rows in sorted(routes.items()):
        run = runs.get(name)
        skipped = set(valid_ids(run['not_run'], 'not_run', empty_ok=True)) if run else set()
        if run and (type(run['complete']) is not bool or skipped - set(ids) or (run['complete'] and skipped)):
            raise ValueError(f'{name}: inconsistent runner completeness or not_run IDs')
        counts = Counter()
        per_cat = {c: {'correct': 0, 'scored': 0, 'n': n} for c, n in sorted(declared.items())}
        answers = {}
        for k in ids:
            status = classify(name, k, rows.get(k), skipped, caps)
            # With runner metadata, not_run is authoritative for attempts. An
            # attempted item missing from this grading pass is still ungraded.
            if run and status == 'not_run' and k not in skipped:
                status = 'ungraded'
            counts[status] += 1
            if status not in UNSCORED:
                answers[k] = int(status == 'correct')
                per_cat[cats[k]]['scored'] += 1
                per_cat[cats[k]]['correct'] += answers[k]
        k, n = sum(answers.values()), len(ids)
        complete = len(answers) == n and (run is None or run['complete'])
        elapsed, budget = times(run)
        r['routes'][name] = {'n': n, 'scored': len(answers), 'correct': k, 'complete': complete,
                             'percent': 100*k/n if complete else None,
                             'ci95_wilson': wilson(k, n) if complete else [None, None],
                             'categories': per_cat, 'status_counts': dict(sorted(counts.items())),
                             'capped': counts['capped'], 'malformed': counts['malformed'],
                             'not_run': counts['not_run'], 'ungraded': counts['ungraded'],
                             'elapsed_min': elapsed, 'budget_min': budget, 'groups': []}
        if complete and compare:
            binary[name] = answers
    order = sorted(binary, key=lambda x: (-r['routes'][x]['correct'], x))
    pairs = r['pairs']
    for a, b in combinations(order, 2):
        # Only complete routes enter the family: their common scored IDs are exactly ids.
        wins = sum(binary[a][k] > binary[b][k] for k in ids)
        losses = sum(binary[a][k] < binary[b][k] for k in ids)
        pairs.append({'a': a, 'b': b, 'n': len(ids), 'a_correct': sum(binary[a].values()),
                      'b_correct': sum(binary[b].values()), 'a_only': wins, 'b_only': losses,
                      'p_exact': exact_mcnemar(wins, losses)})
    adjust(pairs)
    groups = letter_groups(order, [(p['a'], p['b']) for p in pairs if p['separated']])
    for name in order:
        r['routes'][name]['groups'] = groups[name]
    r.update(ranking=order, incomplete=sorted(routes.keys() - binary.keys()),
             holm_family_size=len(pairs), alpha=CONFIG['alpha'])
    return r


def adjust(pairs):
    labels = [(p['a'], p['b']) for p in pairs]
    for p, adj in zip(pairs, holm([p['p_exact'] for p in pairs], labels)):
        p.update(p_holm=adj, separated=adj <= CONFIG['alpha'])


def score(rank_items, routes, runs=None, historical=False):
    ids = valid_ids(rank_items['order'], 'order')
    n = len(ids)
    c = rank_items.get('core_n', n)
    points = rank_items.get('prefix_checkpoints', [n])
    if type(c) is not int or not 1 <= c <= n:
        raise ValueError('core_n outside frozen order')
    if (not isinstance(points, list) or not points or points[-1] != n or
            any(type(p) is not int or not c <= p <= n for p in points) or points != sorted(set(points))):
        raise ValueError('prefix_checkpoints must increase from core_n or later and end at len(order)')
    runs = runs or {}
    full = _fixed(rank_items, routes, runs, historical, compare=False)
    diagnostics = full['routes']
    for name, s in diagnostics.items():
        rows, run = routes[name], runs.get(name)
        skipped = set(run['not_run']) if run else {k for k in ids if k not in rows or rows[k]['status'] in NO_ATTEMPT}
        answered = next((i for i, k in enumerate(ids) if k in skipped), n)
        scored = next((i for i, k in enumerate(ids) if k in skipped or k not in rows or rows[k]['status'] in UNSCORED), n)
        if run and 'answered_prefix' in run and (type(run['answered_prefix']) is not int or run['answered_prefix'] != answered):
            raise ValueError(f'{name}: answered_prefix contradicts not_run')
        if run and 'core_complete' in run and (type(run['core_complete']) is not bool or run['core_complete'] and answered < c):
            raise ValueError(f'{name}: core_complete contradicts not_run')
        core_ok = scored >= c and (not run or run.get('core_complete', True)) and (c < n or s['complete'])
        if not core_ok and s['complete']:
            s.update(complete=False, percent=None, ci95_wilson=[None, None])
        s.update(answered_prefix=answered, scored_prefix=scored, core_complete=bool(core_ok))
        del s['groups']  # Whole-run totals are diagnostics, not a ranking.

    extended, skipped_points, longest = [], [], {}
    for p in sorted({c, *points}):
        eligible = [r for r, s in diagnostics.items() if s['core_complete'] and s['scored_prefix'] >= p
                    and (p < n or s['complete'])]
        if p != c and len(eligible) < 3:
            skipped_points.append({'prefix_n': p, 'eligible_routes': eligible})
            if len(eligible) < 2:
                continue
        names = routes if p == c else eligible
        index = set(ids[:p])
        # Use a scope-local view of both the grader and the runner. A skipped
        # extension never vetoes a complete core; a grading hole does veto it.
        local_runs = {r: dict(runs[r], not_run=[k for k in runs[r]['not_run'] if k in index],
                              complete=r in eligible) for r in names if r in runs}
        plan = {'order': ids[:p], 'caps': rank_items.get('caps', {})}
        counts = rank_items.get('counts') if p == n else rank_items.get('core_counts') if p == c else None
        if counts is not None:
            plan['counts'] = counts
        result = _fixed(plan, {r: routes[r] for r in names}, local_runs, historical)
        block = {k: result[k] for k in ('category_counts', 'ranking', 'incomplete', 'routes', 'pairs', 'holm_family_size')}
        block['prefix_n'] = p
        if p == c:
            core = block
        elif len(eligible) >= 3:
            extended.append(block)
        # Overwrite in increasing checkpoint order, including two-route-only checkpoints.
        for pair in block['pairs']:
            longest[tuple(sorted((pair['a'], pair['b'])))] = pair.copy()
    latest = [longest[key] for key in sorted(longest)]
    adjust(latest)
    return {'schema_version': 2, 'historical': historical, 'note': HISTORICAL_NOTE if historical else
            'Supplied graded runs. Without run.json, coverage is inferred from grades; timing is unknown.',
            'item_ids': ids, 'core_n': c, 'prefix_checkpoints': points, 'alpha': CONFIG['alpha'],
            'category_counts': full['category_counts'], 'routes': diagnostics, 'core': core,
            'extended': extended, 'skipped_checkpoints': skipped_points, 'longest_common_pairs': latest,
            'longest_common_holm_family_size': len(latest)}


def scope_markdown(r):
    lines = []
    for title, names in [('Complete routes (score order)', r['ranking']), ('Incomplete routes (unranked)', r['incomplete'])]:
        lines.extend([f'### {title}', ''])
        if not names:
            lines.extend(['None.', ''])
            continue
        lines += ['| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |',
                  '|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|']
        for name in names:
            s = r['routes'][name]
            pct = '—' if s['percent'] is None else f"{s['percent']:.1f}%"
            ci = '—' if not s['complete'] else '–'.join(f'{100*x:.1f}%' for x in s['ci95_wilson'])
            time = '—' if s['elapsed_min'] is None else f"{s['elapsed_min']:.2f}/{s['budget_min']:g}"
            lines.append(f"| {name} | {' '.join(s['groups']) or '—'} | {'yes' if s['complete'] else 'no'} | "
                         f"{s['correct']}/{s['scored']} | {s['scored']}/{s['n']} | {pct} | {ci} | {s['capped']} | "
                         f"{s['malformed']} | {s['not_run']} | {s['ungraded']} | {time} |")
        lines.append('')
    cats = sorted(r['category_counts'])
    lines += ['### Per category (correct/scored; frozen N in header)', '',
              '| Route | ' + ' | '.join(f"{c} (N={r['category_counts'][c]})" for c in cats) + ' |',
              '|---|' + '---:|'*len(cats)]
    for name in r['ranking'] + r['incomplete']:
        cells = [f"{v['correct']}/{v['scored']}" for v in (r['routes'][name]['categories'][c] for c in cats)]
        lines.append('| ' + ' | '.join([name, *cells]) + ' |')
    lines += ['', f"### Exact paired McNemar tests (Holm family: {r['holm_family_size']})", '']
    return lines + pair_table(r['pairs'])


def pair_table(pairs):
    if not pairs:
        return ['No eligible pair.', '']
    lines = ['| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for p in pairs:
        lines.append(f"| {p['a']} | {p['b']} | {p['n']} | {p['a_correct']} | {p['b_correct']} | {p['a_only']} | {p['b_only']} | "
                     f"{p['p_exact']:.5g} | {p['p_holm']:.5g} | {'yes' if p['separated'] else 'no'} |")
    return lines + ['']


def markdown(r):
    lines = ['# Frozen rank-tier results', '', r['note'], '',
             'Only the core compares every core-complete route on the same items. Extensions require at least three '
             'routes with a fully graded prefix. Capped, malformed and started errors are wrong; not-run and ungraded are not.', '',
             'Wilson intervals are pointwise approximations for a fixed item mix. Each ranking and the longest-shared '
             'table uses its own exact two-sided McNemar/Holm family at α=0.05. No simultaneous guarantee across tables. '
             'Shared letters mean no detected difference, not equivalence. Minutes always refer to the whole run.', '']
    for label, scope in [('Core ranking', r['core']), *[('Extended ranking', e) for e in r['extended']]]:
        lines += [f"## {label}: first {scope['prefix_n']} items", ''] + scope_markdown(scope)
    if r['skipped_checkpoints']:
        lines += ['Extended rankings omitted (fewer than three eligible routes): ' + ', '.join(
            f"{s['prefix_n']} ({len(s['eligible_routes'])} routes)" for s in r['skipped_checkpoints']) + '.', '']
    lines += ['## Whole-run coverage (not a ranking)', '',
              '| Route | Core complete | Full complete | Answered prefix | Scored prefix | Correct/scored | Capped | Malformed | Not run | Ungraded |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for name, s in sorted(r['routes'].items()):
        lines.append(f"| {name} | {'yes' if s['core_complete'] else 'no'} | {'yes' if s['complete'] else 'no'} | "
                     f"{s['answered_prefix']} | {s['scored_prefix']} | {s['correct']}/{s['scored']} | "
                     f"{s['capped']} | {s['malformed']} | {s['not_run']} | {s['ungraded']} |")
    lines += ['', f"## Longest shared checkpoint per core-eligible pair (Holm family: {r['longest_common_holm_family_size']})", '',
              'Prefix lengths can differ between rows. These comparisons do not define a fleet ranking.', '']
    return '\n'.join(lines + pair_table(r['longest_common_pairs']))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_routes(paths, historical, rank_hash=None):
    routes, versions = {}, set()
    for path in paths:
        doc = read_json(path)
        versions.add((doc.get('items_sha256'), doc.get('grader_version')))
        if len(versions) > 1:
            raise ValueError('cannot compare different pub item manifests or grader versions')
        for route, rows in doc['routes'].items():
            recorded = doc.get('route_metadata', {}).get(route, {}).get('rank_items_sha256')
            if not historical and recorded is not None and recorded != rank_hash:
                raise ValueError(f'{route}: graded rank-item manifest hash mismatch')
            # Cumulative fast-all repeats core11 first attempts; the two Inkling runs
            # have the same route key but different engines and must not be pooled.
            name = route
            if historical and path.parent.name == 'inkling-q8-rdna3':
                name += '@inkling-q8-rdna3'
            if name in routes:
                if not historical or path.parent.name != 'pub-core-and-fast':
                    raise ValueError(f'duplicate route: {name}')
                old = routes[name]
                for key in rows.keys() & old.keys():
                    if any(rows[key].get(f) != old[key].get(f) for f in ('status', 'correct', 'category', 'usage')):
                        raise ValueError(f'conflicting archive grades for {name}/{key}')
                old.update(rows)
            else:
                routes[name] = rows
    return routes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('graded', nargs='*', type=Path, help='grade_pub JSON (one or more)')
    parser.add_argument('--rank-items', type=Path, default=HERE/'rank-items.json')
    parser.add_argument('--run', action='append', type=Path, default=[], help='runner run.json; repeat per route')
    parser.add_argument('--rescore', nargs='?', const=HERE.parent/'data', type=Path, metavar='DATA',
                        help='historical only: read DATA/*/graded*.json (default: ../data)')
    parser.add_argument('--output-prefix', '--prefix', type=Path, default=Path('rank-report'))
    args = parser.parse_args(argv)
    if args.rescore and (args.graded or args.run):
        parser.error('do not mix historical rescores with graded or --run inputs')
    paths = sorted(args.rescore.glob('*/graded*.json')) if args.rescore else args.graded
    if not paths:
        parser.error('no graded JSON inputs found')
    try:
        rank_bytes = args.rank_items.read_bytes()
        rank_hash = hashlib.sha256(rank_bytes).hexdigest()
        routes = load_routes(paths, bool(args.rescore), rank_hash)
        runs = {}
        for path in args.run:
            run = read_json(path)
            if run.get('rank_items_sha256', rank_hash) != rank_hash:
                raise ValueError(f"{run['route']}: runner rank-item manifest hash mismatch")
            if run['route'] in runs:
                raise ValueError(f"duplicate run metadata: {run['route']}")
            runs[run['route']] = run
        report = score(json.loads(rank_bytes), routes, runs, bool(args.rescore))
        report['rank_items_sha256'] = rank_hash
        args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
        for suffix, content in [('.json', json.dumps(report, indent=2, allow_nan=False)+'\n'), ('.md', markdown(report))]:
            dest = Path(str(args.output_prefix) + suffix)
            if dest.resolve() in {p.resolve() for p in [args.rank_items, *paths, *args.run]}:
                raise ValueError('report destination would overwrite an input')
            dest.write_text(content, encoding='utf-8')
            print(dest)
    except (KeyError, ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
