"""Scoring rules of run_golden.py (block G): not-run mapping, known-bug flag and template-pair diagnosis. No model, no GPU."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_golden as rg


def row(t, status, details='', text='', cat='x'):
    return {'task_id': t, 'status': status, 'details': details, 'response_text': text, 'category': cat}


class T(unittest.TestCase):
    first, rest = rg.FIRST, ['code_canonical', 'safety_boundary']

    def test_refused_cases_are_not_run_not_wrong(self):
        rows = [row('template_tool_response', 'error', f'HTTP 400 from x: {rg.LIMIT_REASON}'),
                row('template_multi_turn', 'error', f'HTTP 400 from x: {rg.HOLD_REASON}'),
                row('function_call_single', 'error', 'HTTP 500 from x: boom')]
        cases, _ = rg.summarise(rows, self.first, self.rest)
        self.assertEqual(cases['template_tool_response']['status'], 'not_run')
        self.assertEqual(cases['template_multi_turn']['status'], 'not_run')
        self.assertEqual(cases['function_call_single']['status'], 'error')     # a real harness error stays one
        self.assertEqual(cases['code_canonical']['status'], 'not_run')         # never reached

    def test_pair_diagnosis(self):
        rows = [row('template_tool_response', 'failed'), row('template_tool_response_twin', 'passed'),
                row('template_multi_turn', 'failed'), row('template_multi_turn_twin', 'failed')]
        _, pairs = rg.summarise(rows, self.first, self.rest)
        self.assertEqual(pairs['template_tool_response'], 'template or parser broken')
        self.assertEqual(pairs['template_multi_turn'], 'model cannot answer; template not implicated')
        _, pairs = rg.summarise([row('template_multi_turn', 'passed')], self.first, self.rest)
        self.assertEqual(pairs['template_multi_turn'], 'incomplete')

    def test_curly_apostrophe_refusal_is_flagged(self):
        cases, _ = rg.summarise([row('safety_boundary', 'failed', text='I can’t help with that.')], self.first, self.rest)
        self.assertIn('pull/13', cases['safety_boundary']['known_gbench_bug'])
        cases, _ = rg.summarise([row('safety_boundary', 'failed', text='Here is the code.')], self.first, self.rest)
        self.assertNotIn('known_gbench_bug', cases['safety_boundary'])

    def test_template_and_tool_cases_run_first(self):
        self.assertEqual(rg.FIRST[:4], ['template_tool_response', 'template_tool_response_twin', 'template_multi_turn', 'template_multi_turn_twin'])
        self.assertLessEqual(rg.BLOCK_MINUTES['fast'], 2); self.assertLessEqual(rg.BLOCK_MINUTES['slow'], 5)


if __name__ == '__main__':
    unittest.main()
