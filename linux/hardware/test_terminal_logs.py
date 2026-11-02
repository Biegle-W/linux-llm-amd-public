"""Desktop log viewers use no GPU and never own the backend process."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import terminal_logs as logs


class LogWindowTests(unittest.TestCase):
    def test_desktop_argv_preserves_paths_and_uses_cairo(self):
        for desktop in ({'DISPLAY': ':1'}, {'WAYLAND_DISPLAY': 'wayland-1'}):
            with self.subTest(desktop=desktop), patch.dict(os.environ, desktop, clear=True), \
                    patch.object(logs.shutil, 'which', return_value='/usr/bin/ptyxis'), \
                    patch.object(logs.subprocess, 'Popen') as popen:
                result = logs.open_log_window(Path('/tmp/log with spaces'), 'AMD server')
                self.assertIs(result, popen.return_value)
                args = popen.call_args.args[0]
                self.assertEqual(args[:6], ['/usr/bin/ptyxis', '--standalone',
                                 '--new-window', '--title=AMD server', '--', 'tail'])
                self.assertIn('--follow=name', args)
                self.assertIn('--retry', args)
                self.assertEqual(args[-1], '/tmp/log with spaces')
                options = popen.call_args.kwargs
                self.assertEqual(options['env']['GSK_RENDERER'], 'cairo')
                self.assertTrue(options['start_new_session'])
                self.assertNotIn('shell', options)

    def test_headless_session_never_spawns_viewer(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(logs.subprocess, 'Popen') as popen:
            self.assertIsNone(logs.open_log_window(Path('/tmp/log'), 'AMD server'))
            popen.assert_not_called()

    def test_missing_terminal_keeps_launch_headless(self):
        with patch.dict(os.environ, {'DISPLAY': ':1'}, clear=True), \
                patch.object(logs.shutil, 'which', return_value=None), \
                patch.object(logs.subprocess, 'Popen') as popen:
            self.assertIsNone(logs.open_log_window(Path('/tmp/log'), 'AMD server'))
            popen.assert_not_called()

    def test_living_viewer_is_reused(self):
        viewer = Mock(poll=Mock(return_value=None))
        with patch.object(logs.subprocess, 'Popen') as popen:
            self.assertIs(logs.open_log_window(Path('/tmp/log'), 'AMD server', viewer), viewer)
            popen.assert_not_called()

    def test_closed_viewer_is_reopened(self):
        viewer = Mock(poll=Mock(return_value=0))
        with patch.dict(os.environ, {'DISPLAY': ':1'}, clear=True), \
                patch.object(logs.shutil, 'which', return_value='/usr/bin/ptyxis'), \
                patch.object(logs.subprocess, 'Popen') as popen:
            self.assertIs(logs.open_log_window(Path('/tmp/log'), 'AMD server', viewer), popen.return_value)
            popen.assert_called_once()

    def test_viewer_spawn_failure_does_not_block_backend(self):
        with patch.dict(os.environ, {'DISPLAY': ':1'}, clear=True), \
                patch.object(logs.shutil, 'which', return_value='/usr/bin/ptyxis'), \
                patch.object(logs.subprocess, 'Popen', side_effect=OSError('unavailable')), \
                patch('builtins.print') as report:
            self.assertIsNone(logs.open_log_window(Path('/tmp/log'), 'AMD server'))
            self.assertIn('unavailable', report.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
