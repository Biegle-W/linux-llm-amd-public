"""No display, USB devices or display-manager changes are required by these tests."""
import importlib.util
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('gui_on_connect', Path(__file__).resolve().parents[1] / 'network/gui_on_connect.py')
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.drm, self.inputs, self.udev = [self.root / x for x in ('drm', 'input', 'udev')]
        for p in (self.drm, self.inputs, self.udev): p.mkdir()

    def display(self, name='card0-HDMI-A-1', status='connected'):
        p = self.drm / name / 'status'; p.parent.mkdir(exist_ok=True); p.write_text(status)

    def device(self, number, kind, bus='usb'):
        p = self.inputs / f'event{number}' / 'dev'; p.parent.mkdir(); p.write_text(f'13:{number}')
        (self.udev / f'c13:{number}').write_text(f'E:ID_BUS={bus}\nE:ID_INPUT_{kind}=1\n')

    def detect(self, connectors=('HDMI-A',)):
        return gui.detect(self.drm, self.inputs, self.udev, connectors)

    def test_all_three_conditions_are_required(self):
        self.display(); self.device(1, 'KEYBOARD'); self.device(2, 'MOUSE')
        self.assertTrue(self.detect()['ready'])
        for missing in ['display', 'keyboard', 'mouse']:
            with self.subTest(missing=missing):
                if missing == 'display':
                    self.display(status='disconnected')
                else:
                    (self.udev / ('c13:1' if missing == 'keyboard' else 'c13:2')).unlink()
                self.assertFalse(self.detect()['ready'])
                self.display()
                if missing != 'display':
                    kind = 'KEYBOARD' if missing == 'keyboard' else 'MOUSE'
                    number = 1 if missing == 'keyboard' else 2
                    (self.udev / f'c13:{number}').write_text(f'E:ID_BUS=usb\nE:ID_INPUT_{kind}=1\n')

    def test_displayport_requires_configuration(self):
        self.display('card2-DP-4'); self.device(1, 'KEYBOARD'); self.device(2, 'MOUSE')
        self.assertFalse(self.detect()['ready'])
        self.assertTrue(self.detect(('HDMI-A', 'DP'))['ready'])

    def test_non_usb_input_does_not_qualify(self):
        self.display(); self.device(1, 'KEYBOARD', 'bluetooth'); self.device(2, 'MOUSE')
        self.assertFalse(self.detect()['ready'])

    def test_composite_receiver_and_multiple_gpu_ports(self):
        self.display('card2-HDMI-A-6'); self.device(1, 'KEYBOARD')
        with (self.udev / 'c13:1').open('a') as f: f.write('E:ID_INPUT_MOUSE=1\n')
        self.assertTrue(self.detect()['ready'])

    def test_missing_udev_database_fails_closed(self):
        self.display(); self.device(1, 'KEYBOARD'); self.device(2, 'MOUSE')
        for p in self.udev.iterdir(): p.unlink()
        self.assertFalse(self.detect()['ready'])

    def test_disconnected_or_unknown_connector_is_not_present(self):
        self.display(status='unknown'); self.device(1, 'KEYBOARD'); self.device(2, 'MOUSE')
        self.assertFalse(self.detect()['ready'])

    def test_unready_state_never_changes_a_service(self):
        run = Mock()
        self.assertFalse(gui.activate({'ready': False}, run))
        run.assert_not_called()

    def test_existing_desktop_is_left_running(self):
        run = Mock(return_value=Mock(returncode=0))
        self.assertFalse(gui.activate({'ready': True}, run))
        self.assertEqual(run.call_count, 1)

    def test_ready_state_starts_only_display_manager(self):
        run = Mock(side_effect=[Mock(returncode=3), Mock(returncode=0)])
        self.assertTrue(gui.activate({'ready': True}, run))
        self.assertEqual(run.call_args.args[0], ['systemctl', 'start', 'display-manager.service'])
        self.assertTrue(run.call_args.kwargs['check'])


if __name__ == '__main__':
    unittest.main()
