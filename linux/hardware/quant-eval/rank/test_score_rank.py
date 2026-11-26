"""Offline scoring checks. Inputs contain synthetic item IDs and grades only."""
from itertools import combinations
import json
from pathlib import Path
import tempfile
import unittest

import score_rank as sr


def grade(status, category='math', tokens=2):
    return {'status': status, 'correct': status == 'correct', 'category': category,
            'usage': {'completion_tokens': tokens}}


class ScoreTests(unittest.TestCase):
    def test_wilson(self):
        # At n=1, k=1 the lower bound is 1/(1+z²), upper is 1.
        lo, hi = sr.wilson(1, 1)
        self.assertAlmostEqual(lo, 0.2065493144)
        self.assertAlmostEqual(hi, 1)
        lo, hi = sr.wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2365930905)
        self.assertAlmostEqual(hi, 0.7634069095)

    def test_exact_discordant_pairs(self):
        # For a split of 7:1 among eight discordances, 2*(1+8)/256.
        self.assertEqual(sr.exact_mcnemar(0, 0), 1)
        self.assertAlmostEqual(sr.exact_mcnemar(7, 1), 18/256)
        self.assertAlmostEqual(sr.exact_mcnemar(1, 7), 18/256)

    def test_holm_monotone(self):
        # Sorted raw .01,.02,.021 -> .03,.04,.021 before cumulative max.
        for p, expected in zip(sr.holm([.021, .01, .02]), [.04, .03, .04]):
            self.assertAlmostEqual(p, expected)

    def test_overlapping_letters(self):
        self.assertEqual(sr.letter_groups(['x', 'y', 'z'], [('x', 'z')]),
                         {'x': ['A'], 'y': ['A', 'B'], 'z': ['B']})
        # Check every possible separation graph on four routes.
        edges = list(combinations('wxyz', 2))
        for mask in range(1 << len(edges)):
            separated = [e for i, e in enumerate(edges) if mask & (1 << i)]
            groups = sr.letter_groups(list('wxyz'), separated)
            for a, b in edges:
                self.assertEqual(set(groups[a]).isdisjoint(groups[b]), (a, b) in separated)

    def test_incomplete_excluded_from_family(self):
        ids = list('abcdefgh')
        full = {k: grade('correct') for k in ids}
        mid = {k: grade('correct' if i < 4 else 'wrong') for i, k in enumerate(ids)}
        zero = {k: grade('wrong') for k in ids}
        partial = dict(full, b=grade('pending'), c=grade('ungraded'), d=grade('capped'), e=grade('malformed'))
        del partial['h']   # Missing row, not a failed answer.
        runs = {'partial': {'complete': False, 'not_run': ['b', 'h'], 'elapsed_s': 120, 'budget_s': 900}}
        report = sr.score({'order': ids, 'counts': {'math': 8}},
                          {'top': full, 'middle': mid, 'bottom': zero, 'partial': partial}, runs)['core']
        self.assertEqual(report['ranking'], ['top', 'middle', 'bottom'])
        self.assertEqual(report['incomplete'], ['partial'])
        self.assertEqual(report['holm_family_size'], 3)
        self.assertEqual([report['routes'][r]['groups'] for r in report['ranking']], [['A'], ['A', 'B'], ['B']])
        t = report['routes']['top']
        self.assertEqual(t['percent'], 100)
        self.assertEqual(t['categories'], {'math': {'correct': 8, 'scored': 8, 'n': 8}})
        pair = next(p for p in report['pairs'] if p['a'] == 'top' and p['b'] == 'bottom')
        self.assertEqual((pair['n'], pair['a_only'], pair['b_only']), (8, 8, 0))
        self.assertAlmostEqual(pair['p_holm'], 3*2/256)
        s = report['routes']['partial']
        self.assertFalse(s['complete'])
        self.assertEqual((s['scored'], s['correct'], s['n']), (5, 3, 8))
        self.assertEqual((s['not_run'], s['ungraded'], s['malformed'], s['capped']), (2, 1, 1, 1))
        self.assertEqual((s['elapsed_min'], s['budget_min']), (2, 15))
        self.assertIsNone(s['percent'])
        self.assertEqual(s['ci95_wilson'], [None, None])
        self.assertEqual(s['groups'], [])

    def test_incomplete_metadata_veto(self):
        report = sr.score({'order': ['a']}, {'r': {'a': grade('correct')}},
                          {'r': {'complete': False, 'not_run': [], 'elapsed_s': 0, 'budget_s': 1}})['core']
        self.assertEqual(report['ranking'], [])
        self.assertEqual(report['incomplete'], ['r'])
        self.assertEqual(report['pairs'], [])

    def test_attempted_but_grade_missing(self):
        report = sr.score({'order': ['a', 'b'], 'counts': {'math': 2}},
                          {'r': {'a': grade('correct')}},
                          {'r': {'complete': True, 'not_run': [], 'elapsed_s': 2, 'budget_s': 10}})
        s = report['routes']['r']
        self.assertEqual((s['not_run'], s['ungraded'], s['complete']), (0, 1, False))
        self.assertIsNone(s['percent'])

    def test_contradictions_and_defects(self):
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            sr.score({'order': ['a']}, {'r': {'a': grade('correct')}},
                     {'r': {'complete': False, 'not_run': ['a'], 'elapsed_s': 0, 'budget_s': 1}})
        with self.assertRaisesRegex(ValueError, 'grader_error'):
            sr.score({'order': ['a']}, {'r': {'a': grade('grader_error')}})
        with self.assertRaisesRegex(ValueError, 'category counts'):
            sr.score({'order': ['a'], 'counts': {'tools': 1}}, {'r': {'a': grade('wrong')}})

    def test_historical_cli_and_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b, c = 'aime24:a', 'aime25:b', 'math:c'
            rank = root/'items.json'
            rank.write_text(json.dumps({'order': [a, b, c], 'counts': {'math': 3},
                                        'caps': {'aime24': 4, 'aime25': 4, 'math': 8}}))
            archived = root/'data'/'snapshot'/'graded.json'
            archived.parent.mkdir(parents=True)
            archived.write_text(json.dumps({'routes': {'r': {a: grade('correct', tokens=4),
                    b: grade('correct', tokens=5), c: grade('capped', tokens=1), 'extra': grade('wrong')}}}))
            prefix = root/'report.v1'
            sr.main(['--rescore', str(root/'data'), '--rank-items', str(rank), '--prefix', str(prefix)])
            out = json.loads((root/'report.v1.json').read_text())
            self.assertTrue(out['historical'])
            self.assertEqual(out['routes']['r']['correct'], 1)
            self.assertEqual(out['routes']['r']['capped'], 2)
            self.assertIn('older engines', (root/'report.v1.md').read_text())
            self.assertNotIn('extra', out['item_ids'])

    def test_current_cli_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root/'items.json'
            manifest.write_text(json.dumps({'order': ['a', 'b'], 'counts': {'math': 2}}))
            files = []
            for name, last in [('full', 'wrong'), ('stop', 'pending')]:
                path = root/(name+'.json')
                path.write_text(json.dumps({'routes': {name: {'a': grade('correct'), 'b': grade(last)}}}))
                files.append(str(path))
            run = root/'run.json'
            run.write_text(json.dumps({'route': 'stop', 'complete': False, 'not_run': ['b'],
                                       'elapsed_s': 300, 'budget_s': 900}))
            sr.main([*files, '--run', str(run), '--rank-items', str(manifest), '--prefix', str(root/'out')])
            result = json.loads((root/'out.json').read_text())
            self.assertFalse(result['historical'])
            self.assertEqual(result['core']['ranking'], ['full'])
            self.assertEqual(result['core']['incomplete'], ['stop'])
            self.assertEqual(result['routes']['full']['percent'], 50)
            self.assertEqual(result['routes']['stop']['not_run'], 1)
            self.assertIn('5.00/15', (root/'out.md').read_text())

    def test_nested_families_and_two_route_final_checkpoint(self):
        ids = [str(i) for i in range(16)]
        plan = {'order': ids, 'core_n': 8, 'prefix_checkpoints': [8, 12, 16]}
        all_right = {k: grade('correct') for k in ids}
        routes = {'a': all_right, 'b': {k: grade('wrong') for k in ids},
                  'c': {k: grade('wrong' if 4 <= i < 8 else 'correct') for i, k in enumerate(ids[:13])},
                  'd': {k: grade('correct') for k in ids[:8]}, 'e': {k: grade('correct') for k in ids[1:]}}
        runs = {'c': {'not_run': ids[13:], 'elapsed_s': 60, 'budget_s': 90, 'complete': False,
                      'answered_prefix': 13, 'core_complete': True}}
        out = sr.score(plan, routes, runs)
        core = out['core']
        self.assertEqual(core['ranking'], ['a', 'd', 'c', 'b'])
        self.assertEqual(core['incomplete'], ['e'])
        self.assertEqual(core['holm_family_size'], 6)
        self.assertEqual(core['routes']['c']['correct'], 4)
        self.assertEqual(out['routes']['c']['answered_prefix'], 13)
        self.assertTrue(out['routes']['c']['core_complete'])
        self.assertFalse(out['routes']['c']['complete'])
        self.assertEqual(len(out['extended']), 1)
        ext = out['extended'][0]
        self.assertEqual((ext['prefix_n'], ext['ranking'], ext['holm_family_size']), (12, ['a', 'c', 'b'], 3))
        self.assertEqual(ext['routes']['c']['correct'], 8)
        self.assertEqual(out['skipped_checkpoints'], [{'prefix_n': 16, 'eligible_routes': ['a', 'b']}])
        def pair(block, a, b):
            return next(p for p in block if {p['a'], p['b']} == {a, b})
        self.assertAlmostEqual(pair(core['pairs'], 'a', 'b')['p_holm'], 6*2/2**8)
        self.assertAlmostEqual(pair(ext['pairs'], 'a', 'b')['p_holm'], 3*2/2**12)
        pairs = out['longest_common_pairs']
        self.assertEqual(len(pairs), 6)
        ab = pair(pairs, 'a', 'b')
        self.assertEqual((ab['n'], ab['a_only'], ab['b_only']), (16, 16, 0))
        self.assertAlmostEqual(ab['p_holm'], 6*2/2**16)
        self.assertEqual(pair(pairs, 'b', 'd')['n'], 8)
        self.assertEqual(pair(pairs, 'a', 'c')['n'], 12)
        self.assertIn('Extended ranking: first 12', sr.markdown(out))

    def test_nested_holes_runner_and_saved(self):
        ids = list('abcdef')
        plan = {'order': ids, 'core_n': 2, 'prefix_checkpoints': [4, 6], 'caps': {'math': 3}}
        full = {k: grade('correct') for k in ids}
        routes = {'a': full, 'b': full, 'gap': dict(full, c=grade('ungraded')),
                  'partial': {k: grade('correct') for k in 'abdef'}}
        out = sr.score(plan, routes, historical=True)
        self.assertEqual(out['routes']['partial']['scored'], 5)
        self.assertEqual(out['routes']['partial']['answered_prefix'], 2)
        self.assertEqual(out['routes']['gap']['answered_prefix'], 6)
        self.assertEqual(out['routes']['gap']['scored_prefix'], 2)
        self.assertEqual(out['core']['incomplete'], [])
        self.assertEqual(out['extended'], [])
        counts = sorted(p['n'] for p in out['longest_common_pairs'])
        self.assertEqual(counts, [2, 2, 2, 2, 2, 6])

    def test_abort_excludes_finished_core_and_short_prefix_stays_incomplete(self):
        ids = list('abc')
        full = {k: grade('correct') for k in ids}
        routes = {r: full for r in ('a', 'b', 'c', 'held')}
        routes['short'] = {'a': full['a']}
        run = dict(complete=True, not_run=[], elapsed_s=1, budget_s=2)
        runs = {'held': dict(run, answered_prefix=3, stop_reason='abort_file'),
                'short': dict(run, complete=False, not_run=ids[1:], answered_prefix=1, stop_reason='deadline')}
        out = sr.score({'order': ids, 'core_n': 2}, routes, runs)
        self.assertEqual(out['core']['incomplete'], ['held', 'short'])
        self.assertEqual(out['extended'][0]['ranking'], ['a', 'b', 'c'])
        self.assertTrue(all('held' not in (p['a'], p['b']) for p in out['longest_common_pairs']))
        self.assertEqual(out['core']['routes']['held']['stop_reason'], 'abort_file')
        self.assertIn('held (abort_file)', sr.markdown(out))

    def test_nested_validation(self):
        ids = list('abcd')
        plan = {'order': ids, 'core_n': 2, 'prefix_checkpoints': [2, 4]}
        routes = {'r': {k: grade('correct') for k in ids[:2]}}
        run = {'not_run': ids[2:], 'complete': False, 'elapsed_s': 1, 'budget_s': 2, 'core_complete': True}
        for bad in ([3], [2, 2, 4], [1, 4], [3, 2, 4], [True, 4]):
            with self.assertRaisesRegex(ValueError, 'prefix_checkpoints'):
                sr.score(dict(plan, prefix_checkpoints=bad), routes)
        with self.assertRaisesRegex(ValueError, 'answered_prefix'):
            sr.score(plan, routes, {'r': dict(run, answered_prefix=3)})
        veto = sr.score(plan, routes, {'r': dict(run, answered_prefix=2, core_complete=False)})
        self.assertEqual(veto['core']['incomplete'], ['r'])
        self.assertEqual(veto['longest_common_pairs'], [])


if __name__ == '__main__':
    unittest.main()
