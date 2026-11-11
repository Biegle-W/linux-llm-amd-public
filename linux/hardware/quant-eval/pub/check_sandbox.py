#!/usr/bin/env python3
"""Server smoke check: nonzero on missing isolation (never a successful skip)."""
import argparse
from pathlib import Path
import sys
import grade_pub as g


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-root', type=Path, required=True)
    args = parser.parse_args()
    args.temp_root.mkdir(parents=True, exist_ok=True)
    config, reason = g.isolation_config(args.temp_root)
    if config is None:
        print('FAIL-CLOSED: NO CODE EXECUTED: '+reason, file=sys.stderr)
        return 2
    print(config[2])
    cases = [
        ('pass', 'def f(): return 42', {'tests':'assert f()==42'}, True),
        ('wrong', 'def f(): return 0', {'tests':'assert f()==42'}, False),
        ('timeout', 'while True: pass', {'tests':'assert True', 'timeout':.5}, False),
        ('fork_denied', 'import os\nos.fork()', {'tests':'assert True'}, False),
        ('unittest', 'def f(): return 42', {'mode':'unittest','tests':'import unittest\nclass Tests(unittest.TestCase):\n def test_f(self): self.assertEqual(f(),42)'}, True),
        ('unittest_mock_patch', 'import os\ndef f(): return len(os.listdir("."))',
         {'mode':'unittest','tests':'import unittest\nfrom unittest.mock import patch\nclass Tests(unittest.TestCase):\n def test_f(self):\n  with patch("os.listdir", return_value=["a", "b"]):\n   self.assertEqual(f(),2)'}, True),
    ]
    failed = False
    for name, code, extra, expected in cases:
        spec = {'mode':'assertions'}
        spec.update(extra)
        ok, detail = g.run_code(code, spec, args.temp_root)
        print(name, repr(ok), detail)
        failed |= ok is not expected
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
