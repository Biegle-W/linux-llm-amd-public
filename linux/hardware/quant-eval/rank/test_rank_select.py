"""Offline freeze tests. Set RANK_DATA and RANK_PUB when the archive is elsewhere."""
import importlib.util
import json
import os
import unittest
from pathlib import Path

import rank_select as select


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((select.HERE/'rank-items.json').read_text())
        cls.speeds = json.loads((select.HERE/'speeds.json').read_text())

    def test_complete_interleaved_coverage(self):
        order = self.manifest['order']
        counts = self.manifest['counts']
        self.assertEqual(len(order), len(set(order)))
        self.assertEqual(sum(counts.values()), len(order))
        self.assertEqual(set(counts), set(select.CATEGORIES))
        self.assertTrue(all(n > 0 for n in counts.values()))
        self.assertEqual(set(self.manifest['bfcl_counts']), set(select.TOOLS))
        self.assertEqual(sum(self.manifest['bfcl_counts'].values()), counts['tools'])
        for i, prefix in zip(order[:6], ('mmlu:', ('math:', 'aime'), 'code:', 'ifeval:', 'musr_', 'tools_')):
            self.assertTrue(i.startswith(prefix), i)

    def test_budget_fit_and_runtime_estimates(self):
        times = self.manifest['predicted_minutes']
        select.validate_speeds(self.speeds)
        self.assertEqual(times.keys(), self.speeds.keys())
        for route, model in self.speeds.items():
            with self.subTest(route=route):
                minutes = times[route]
                self.assertLessEqual(minutes['typical'], minutes['conservative'])
                self.assertLessEqual(minutes['conservative'], .85*model['budget_min'])
                per_item = self.manifest['item_seconds'][route]
                self.assertEqual(set(per_item), set(self.manifest['order']))
                self.assertTrue(all(s > 0 for s in per_item.values()))
                order = self.manifest['order']
                core_n = self.manifest['core_n']
                self.assertAlmostEqual(sum(per_item[i] for i in order[:core_n])/60, minutes['typical'], places=3)
                predicted = self.manifest['predicted_prefix'][route]
                self.assertLessEqual(core_n,predicted['conservative'])
                self.assertLessEqual(predicted['conservative'],predicted['typical'])
                expected = select.fit_prefix(order,{i:[t] for i,t in per_item.items()},model['budget_min']*60,0)
                self.assertEqual(predicted['typical'],expected)

    def test_nested_checkpoints(self):
        m = self.manifest
        self.assertEqual(m['schema'],2)
        points=m['prefix_checkpoints']
        self.assertEqual(sorted(set(points)),points)
        self.assertEqual((points[0],points[-1]),(m['core_n'],len(m['order'])))
        self.assertEqual(m['prefix_validation'][str(points[0])],m['validation'])
        self.assertEqual(set(map(str,points)),set(m['prefix_validation']))
        self.assertEqual(max(m['predicted_prefix'][r]['conservative'] for r,s in self.speeds.items()
                             if s['class']=='small'),len(m['order']))

    def test_prefix_never_skips_expensive_item(self):
        order=['a','b','c']; times={'a':(1,2),'b':(10,12),'c':(1,1)}
        self.assertEqual(select.fit_prefix(order,times,11,0),2)
        self.assertEqual(select.fit_prefix(order,times,11,1),1)

    def test_cap_simulation(self):
        row = select.Row('math', 'core', 'correct', 32, 160)
        self.assertTrue(select.passed(row,160))
        self.assertFalse(select.capped(row,160))
        self.assertFalse(select.passed(row,159))
        self.assertTrue(select.capped(row,159))
        original_cap = select.Row('math','core','capped',32,160)
        self.assertFalse(select.passed(original_cap,200))
        self.assertTrue(select.capped(original_cap,200))

    def test_split_determinism_and_family_isolation(self):
        routes = self.manifest['validation_routes']
        splits = list(select.splits(routes))
        self.assertEqual(splits, list(select.splits(routes)))
        self.assertEqual(len(splits), len({tuple(train) for train, _ in splits}))
        for train, test in splits:
            self.assertFalse(set(map(select.family,train)) & set(map(select.family,test)))
            self.assertEqual(sorted(train + test), sorted(routes))

    def test_ties(self):
        self.assertEqual(select.correlations([1,1], [1,2]), (None,None))
        rho,tau = select.correlations([1,1,3], [1,2,3])
        self.assertAlmostEqual(rho,(3/4)**.5)
        self.assertAlmostEqual(tau,(2/3)**.5)

    def test_archive_reproduces_frozen_files(self):
        pub = Path(os.environ.get('RANK_PUB', select.HERE.parent/'pub'))
        if not (pub/'analyze.py').is_file():
            spec = importlib.util.find_spec('analyze')
            if spec and spec.origin:
                pub = Path(spec.origin).parent
        data = Path(os.environ.get('RANK_DATA', pub.parent/'data'))
        if not data.exists() and 'RANK_DATA' not in os.environ:
            self.skipTest('saved archive unavailable; set RANK_DATA for full regeneration')
        generated, report = select.build(data,select.HERE/'speeds.json',pub)
        canonical = json.dumps(generated,indent=2,sort_keys=True)+'\n'
        self.assertEqual(canonical,(select.HERE/'rank-items.json').read_text())
        self.assertEqual(report,(select.HERE/'selection-report.md').read_text())


if __name__ == '__main__':
    unittest.main()
