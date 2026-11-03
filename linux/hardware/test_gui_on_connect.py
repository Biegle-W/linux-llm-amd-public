"""No display, USB devices or display-manager changes are required by these tests."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

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
        self.assertFalse(gui.activate({'ready': True}, run, activity=True))
        self.assertEqual(run.call_count, 1)

    def test_presence_without_input_never_starts_desktop(self):
        run = Mock()
        self.assertFalse(gui.activate({'ready': True}, run))
        run.assert_not_called()

    def test_input_without_display_never_starts_desktop(self):
        run = Mock()
        self.assertFalse(gui.activate({'ready': False}, run, activity=True))
        run.assert_not_called()

    def test_ready_input_starts_only_display_manager(self):
        run = Mock(side_effect=[Mock(returncode=3), Mock(returncode=0)])
        self.assertTrue(gui.activate({'ready': True}, run, activity=True))
        self.assertEqual(run.call_args.args[0], ['systemctl', 'start', 'display-manager.service'])
        self.assertTrue(run.call_args.kwargs['check'])

    def test_unknown_manager_state_fails_closed(self):
        run = Mock(return_value=Mock(returncode=1))
        self.assertFalse(gui.activate({'ready': True}, run, activity=True))
        self.assertEqual(run.call_count, 1)

    def test_device_metadata_limits_activity_to_usb_inputs(self):
        self.device(1, 'KEYBOARD'); self.device(2, 'MOUSE', 'bluetooth')
        found = gui.input_devices(self.inputs, self.udev)
        self.assertEqual(list(found), [Path('/dev/input/event1')])


class ActivityTests(unittest.TestCase):
    keyboard = {'keyboard': True, 'mouse': False}
    mouse = {'keyboard': False, 'mouse': True}

    def event(self, kind, code, value, when=103):
        return gui.EVENT.pack(when, 0, kind, code, value)

    def test_keyboard_press_wakes_but_repeat_release_and_startup_do_not(self):
        self.assertTrue(gui.input_activity(self.event(1, 30, 1), self.keyboard, 102))
        for value, when in [(0, 103), (2, 103), (1, 100)]:
            with self.subTest(value=value, when=when):
                self.assertFalse(gui.input_activity(self.event(1, 30, value, when), self.keyboard, 102))

    def test_mouse_motion_click_and_wheel_wake(self):
        for kind, code, value in [(2, 0, 1), (2, 1, -1), (1, 0x110, 1), (2, 8, 1), (2, 11, 120)]:
            with self.subTest(kind=kind, code=code):
                self.assertTrue(gui.input_activity(self.event(kind, code, value), self.mouse, 102))

    def test_passive_device_reports_and_zero_motion_do_not_wake(self):
        for kind, code, value in [(0, 0, 0), (4, 4, 30), (17, 0, 1), (2, 0, 0), (3, 0, 123)]:
            self.assertFalse(gui.input_activity(self.event(kind, code, value), self.mouse, 102))

    def test_wrong_device_class_does_not_wake(self):
        self.assertFalse(gui.input_activity(self.event(1, 30, 1), self.mouse, 102))
        self.assertFalse(gui.input_activity(self.event(2, 0, 1), self.keyboard, 102))

    def test_stream_filters_old_event_even_if_processed_after_arming(self):
        read, write = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        watcher = gui.InputWatch(); watcher.handles[Path('/fake')] = (read, self.keyboard, 102)
        self.addCleanup(watcher.close); self.addCleanup(os.close, write)
        os.write(write, self.event(1, 30, 1, 101))
        self.assertFalse(watcher.poll(0))
        os.write(write, self.event(1, 30, 1, 103))
        self.assertTrue(watcher.poll(0))

    def test_unplug_closes_reader_and_never_wakes(self):
        read, write = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        watcher = gui.InputWatch(); watcher.handles[Path('/fake')] = (read, self.mouse, 102)
        self.addCleanup(watcher.close); os.close(write)
        self.assertFalse(watcher.poll(0)); self.assertFalse(watcher.handles)

    def test_clock_setup_failure_closes_device_and_fails_closed(self):
        watcher = gui.InputWatch(); path = Path('/fake')
        with patch.object(gui.os, 'open', return_value=99), patch.object(gui.os, 'close') as close, \
                patch.object(gui.fcntl, 'ioctl', side_effect=OSError):
            watcher.sync({path: self.mouse})
        close.assert_called_once_with(99); self.assertFalse(watcher.handles)

    def test_new_reader_arms_after_monotonic_settling_period(self):
        watcher = gui.InputWatch(); path = Path('/fake')
        with patch.object(gui.os, 'open', return_value=99), patch.object(gui.fcntl, 'ioctl') as clock, \
                patch.object(gui.time, 'monotonic', return_value=100):
            watcher.sync({path: self.keyboard})
        self.assertEqual(watcher.handles[path][2], 102)
        self.assertEqual(clock.call_args.args[1], gui.EVIOCSCLOCKID)

    def test_desktop_active_closes_readers_without_reading_input(self):
        watcher = Mock()
        with patch.object(gui, 'desktop_active', return_value=True), patch.object(gui.time, 'sleep'):
            gui.watch_once(watcher, ('HDMI-A', 'DP'))
        watcher.close.assert_called_once(); watcher.poll.assert_not_called(); watcher.sync.assert_not_called()

    def test_boot_with_all_devices_and_no_activity_stays_headless(self):
        watcher = Mock(); watcher.poll.return_value = False
        with patch.object(gui, 'desktop_active', return_value=False), \
                patch.object(gui, 'detect', return_value={'ready': True}), \
                patch.object(gui, 'input_devices', return_value={}), patch.object(gui, 'activate') as activate:
            gui.watch_once(watcher, ('HDMI-A', 'DP'))
        activate.assert_not_called()

    def test_event_readiness_is_rechecked_before_starting_gui(self):
        watcher = Mock(); watcher.poll.return_value = True
        with patch.object(gui, 'desktop_active', return_value=False), \
                patch.object(gui, 'detect', side_effect=[{'ready': True}, {'ready': False}]), \
                patch.object(gui, 'input_devices', return_value={}), patch.object(gui, 'subprocess') as subprocess:
            gui.watch_once(watcher, ('HDMI-A', 'DP'))
        subprocess.run.assert_not_called(); watcher.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
