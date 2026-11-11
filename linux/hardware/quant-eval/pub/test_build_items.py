"""Offline split-builder regressions. All reference execution is mocked."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_items as b
import grade_pub as g
import suite_pub


class BuilderReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        code = dict(next(s for s in b.CONFIG['sources'] if s['key']=='code'), counts=[2,1])
        ie = dict(next(s for s in b.CONFIG['sources'] if s['key']=='ifeval'), counts=[1,0])
        self.config = dict(b.CONFIG, sources=[code,ie])
        self.patch = patch.object(b, 'CONFIG', self.config)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        rows = [dict(task_id=str(i), libs=[], complete_prompt='def f():\n',
                     canonical_solution='    return 1\n', test='assert f() == 1',
                     entry_point='f', instruct_prompt=f'Return one for task {i}.') for i in range(8)]
        ie_rows = [dict(prompt='Avoid commas.', instruction_id_list=['punctuation:no_comma','length_constraints:number_words'], kwargs=[{},dict(relation='at least',num_words=1)])]
        sources = {}
        for spec, data in ((code,rows),(ie,ie_rows)):
            sources[spec['key']] = dict(repo=spec['repo'], config=spec['config'], split=spec['split'],
                revision='testrev', sha256=b.sha(b.canonical(data)), rows=len(data), urls=['synthetic'], license=spec['license'])
            (self.root/f'{spec["key"]}-testrev.json').write_bytes(b.canonical(data))
        self.lock = self.root/'lock.json'
        self.lock.write_text(json.dumps(dict(schema_version=2,sources=sources)))
        self.args = argparse.Namespace(cache=self.root, lock=self.lock, update_lock=False, offline=True,
            refresh=False, draft=False, audit=self.root/'build.audit.json', output=self.root/'candidates.jsonl', examples=None)
        with patch.object(g, 'run_code', side_effect=AssertionError('Build executed code')), contextlib.redirect_stdout(io.StringIO()):
            self.draft = b.build(self.args)
        self.args.input = self.args.output
        self.args.output = self.root/'items.jsonl'
        self.args.audit = self.root/'validate.audit.json'
        self.candidates = sorted([json.loads(l) for l in self.args.input.read_text().splitlines() if json.loads(l)['grader']=='code'], key=lambda i:i['candidate_rank'])

    def validate(self, outcomes, times=None):
        with patch.object(g, 'isolation_config', return_value=(('bwrap','mock','verified'),'')), patch.object(g, 'run_code', side_effect=outcomes) as run, contextlib.redirect_stdout(io.StringIO()):
            if times is None:
                result = b.validate_code(self.args)
            else:
                with patch.object(g.time, 'monotonic', side_effect=times):
                    result = b.validate_code(self.args)
        return result, run.call_count

    def audit(self):
        return json.loads(self.args.audit.read_text())

    def test_build_candidates_and_suite_refusal(self):
        self.assertFalse(self.draft['frozen'])
        self.assertEqual(len(self.candidates), 6)
        with self.assertRaisesRegex(RuntimeError, 'draft/unvalidated'):
            suite_pub.load_items(self.args.input)

    def test_ranked_selection_and_portable_validation(self):
        # Validation uses only the artifact + lock, no original source cache.
        for path in self.root.glob('*-testrev.json'):
            path.unlink()
        outcomes = [(True,'passed')]*18
        outcomes[1] = (False,'flaky')
        manifest, calls = self.validate(outcomes)
        self.assertEqual(calls,18)
        self.assertTrue(manifest['frozen'])
        rows = suite_pub.load_items(self.args.output,'all')
        core = {i['id'] for i in rows if i['grader']=='code' and i['tier']=='core'}
        extra = {i['id'] for i in rows if i['grader']=='code' and i['tier']=='extended'}
        self.assertEqual(core,{i['id'] for i in self.candidates[1:3]})
        self.assertEqual(extra,{self.candidates[3]['id']})
        self.assertTrue(all('reference_source' not in i and 'candidate_rank' not in i for i in rows))
        self.assertEqual([r['passed'] for r in self.audit()['code'][0]['runs']], [True,False,True])
        self.assertFalse(self.audit()['code'][-1]['selected'])

    def test_shortfall_no_freeze(self):
        with self.assertRaisesRegex(RuntimeError, 'need 3 passing candidates, have 0'):
            self.validate([(False,'failure')]*18)
        self.assertEqual(self.audit()['pending'], ['code_quota_shortfall'])
        self.assertFalse(self.args.output.exists())

    def test_borderline_excluded(self):
        manifest, _ = self.validate([(True,'passed')]*18, [0,1,2,10,11,12] + list(range(12,42)))
        self.assertTrue(manifest['frozen'])
        self.assertFalse(self.audit()['code'][0]['eligible'])
        self.assertEqual([r['seconds'] for r in self.audit()['code'][0]['runs']], [1,8,1])

    def test_preflight_fail_closed(self):
        with patch.object(g,'isolation_config',return_value=(None,'synthetic unavailable')), patch.object(g,'run_code') as run:
            with self.assertRaisesRegex(RuntimeError,'Reference isolation unavailable'):
                b.validate_code(self.args)
        run.assert_not_called()
        self.assertFalse(self.args.output.exists())
        self.assertEqual(self.audit()['pending'], ['reference_isolation_unavailable'])

    def test_midrun_isolation_aborts(self):
        with self.assertRaisesRegex(RuntimeError, 'Reference isolation unavailable'):
            self.validate([(None,'isolation_unavailable:synthetic')])
        self.assertIsNone(self.audit()['code'][0]['runs'][0]['passed'])
        self.assertFalse(self.args.output.exists())

    def test_grader_defect_aborts(self):
        with self.assertRaisesRegex(RuntimeError,'Reference grader defect'):
            self.validate([g.GraderDefect('invalid tests')])
        self.assertEqual(self.audit()['pending'],['reference_grader_defect'])
        self.assertFalse(self.args.output.exists())

    def test_tamper_fails_before_execution(self):
        self.args.input.write_bytes(self.args.input.read_bytes()+b'\n')
        with patch.object(g,'run_code') as run:
            with self.assertRaisesRegex(RuntimeError,'content/config changed'):
                b.validate_code(self.args)
        run.assert_not_called()

    def test_ifeval_authoritative_eligibility(self):
        spec = next(s for s in b.CONFIG['sources'] if s['key']=='ifeval')
        self.assertEqual(set(spec['rules']), g.SUPPORTED_IFEVAL - {'change_case:english_capital','change_case:english_lowercase'})
        self.assertEqual(len(spec['rules']),11)
        self.assertIn('length_constraints:number_words',spec['rules'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
