"""CPU execution of the replayable ROCm-only multicast dispatch correction."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'sglang/apply-rocm-fixes.py').read_text();tree=ast.parse(source)
ns={};nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in ['one','rocm_multimem_fallback']];assert len(nodes)==2
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'apply-rocm-fixes.py','exec'),ns)
transform=ns['rocm_multimem_fallback']
FIXTURE='''class Gatherer:
    _UNINIT = object()
    def __init__(self, enabled=True):
        self._state = self._UNINIT if enabled else None
        if self._state is self._UNINIT:
            probe()
    def __call__(self, value):
        if self._state is self._UNINIT:
            raise AssertionError('Unsupported multicast allocation attempted')
        return fallback(value)
'''
class MultimemDispatch(unittest.TestCase):
    def build(self,hip):
        scope={'torch':SimpleNamespace(version=SimpleNamespace(hip=hip)),'probe':Mock(),'fallback':Mock(return_value='gathered')}
        exec(compile(transform(FIXTURE),'patched-multimem.py','exec'),scope);return scope
    def test_rocm_uses_existing_fallback_without_probing_or_allocating_multicast(self):
        s=self.build('7.2');g=s['Gatherer']();self.assertIsNone(g._state);s['probe'].assert_not_called();self.assertEqual(g('tensor'),'gathered');s['fallback'].assert_called_once_with('tensor')
    def test_cuda_path_is_unchanged(self):
        s=self.build(None);g=s['Gatherer']();self.assertIs(g._state,g._UNINIT);s['probe'].assert_called_once()
    def test_explicitly_disabled_path_stays_disabled(self):
        for hip in ['7.2',None]:
            s=self.build(hip);g=s['Gatherer'](False);self.assertIsNone(g._state);s['probe'].assert_not_called()
    def test_patch_is_idempotent_and_unexpected_source_is_rejected(self):
        patched=transform(FIXTURE);self.assertEqual(transform(patched),patched)
        with self.assertRaises(AssertionError):transform('class Changed: pass')
if __name__=='__main__':unittest.main()
