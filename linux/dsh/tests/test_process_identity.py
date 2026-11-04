import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend_switch as backend
import inference_swap as swap


class IdentityTests(unittest.TestCase):
    def test_identity_avoids_vm_details_and_keeps_kernel_start(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root/'123'
            p.mkdir()
            (p/'stat').write_text('123 (worker (pinning)) S 42 '+'0 '*17+'777\n')
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('argument-page read')), \
                 patch.object(os, 'readlink', side_effect=AssertionError('cwd read')):
                result = backend.process_identity(123, proc_root=root)
            self.assertEqual((result.pid, result.parent, result.start, result.state), (123, 42, '777', 'S'))
            self.assertEqual((result.args, result.cwd), ((), ''))

    def test_other_uid_is_rejected_before_identity_read(self):
        from types import SimpleNamespace
        with patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=os.getuid()+1)), \
             patch.object(Path, 'read_text', side_effect=AssertionError('foreign process read')):
            self.assertIsNone(backend.process_identity(123))

    def test_missing_or_malformed_identity_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertIsNone(backend.process_identity(123, proc_root=root))
            (root/'123').mkdir()
            (root/'123/stat').write_text('incomplete')
            self.assertIsNone(backend.process_identity(123, proc_root=root))

    def test_owned_signal_uses_pidfd_and_fast_identity(self):
        original = backend.Process(123, 1, '777', (), '', 'S')
        with patch.object(backend, 'process', side_effect=AssertionError('VM details read')), \
             patch.object(backend, 'process_identity', return_value=original), \
             patch.object(os, 'pidfd_open', return_value=9), \
             patch.object(os, 'close') as close, \
             patch.object(signal, 'pidfd_send_signal') as send:
            backend.send(original, signal.SIGTERM, identity_only=True)
        send.assert_called_once_with(9, signal.SIGTERM)
        close.assert_called_once_with(9)

    def test_reused_pid_or_zombie_is_never_signalled(self):
        original = backend.Process(123, 1, '777', (), '', 'S')
        for current in [None, backend.Process(123, 1, '778', (), '', 'S'),
                        backend.Process(123, 1, '777', (), '', 'Z')]:
            with self.subTest(current=current), \
                 patch.object(backend, 'process_identity', return_value=current), \
                 patch.object(os, 'pidfd_open', return_value=9), \
                 patch.object(os, 'close'), \
                 patch.object(signal, 'pidfd_send_signal') as send:
                backend.send(original, signal.SIGTERM, identity_only=True)
            send.assert_not_called()

    def test_scope_rechecks_membership_with_fast_identity(self):
        original_relative = Path.relative_to
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cg = root/'owned.scope'
            cg.mkdir()
            (cg/'cgroup.procs').write_text('123\n')
            proc = root/'proc/123'
            proc.mkdir(parents=True)
            scope = object.__new__(swap.OwnedScope)
            scope.directory = cg
            scope.closed = False
            member = backend.Process(123, 1, '777', (), '', 'S')
            def relative(path, other, *args, **kwargs):
                if path == cg and other == '/sys/fs/cgroup':
                    return Path('user.slice/owned.scope')
                return original_relative(path, other, *args, **kwargs)
            def mapped_path(value):
                return root/'proc' if value == '/proc' else Path(value)
            for membership, expected in [('0::/user.slice/owned.scope', True),
                    ('0::/user.slice/owned.scope/child', True),
                    ('0::/user.slice/unrelated.scope', False),
                    ('0::/user.slice/owned.scope-other', False)]:
                (proc/'cgroup').write_text(membership+'\n')
                with self.subTest(membership=membership), \
                     patch.object(scope, 'populated', return_value=True), \
                     patch.object(Path, 'relative_to', relative), \
                     patch.object(swap, 'Path', side_effect=mapped_path), \
                     patch.object(swap, 'process', side_effect=AssertionError('VM details read')), \
                     patch.object(swap, 'process_identity', return_value=member):
                    self.assertEqual(bool(scope.snapshot()), expected)


if __name__ == '__main__':
    unittest.main()
