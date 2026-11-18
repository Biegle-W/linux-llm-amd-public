"""After a backend switch the next load waits a bounded time for the cards to report the old worker's VRAM as free."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'dsh'))
import amd_device
GIB = 1024**3


class VramReleaseWait(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.cards = []
        for name in ('a', 'b'):
            card = Path(tmp.name)/name; card.mkdir()
            (card/'mem_info_vram_total').write_text(str(24*GIB)); (card/'mem_info_vram_used').write_text(str(GIB))
            self.cards.append(card)

    def test_free_cards_pass_without_waiting(self):
        with patch.object(amd_device.time, 'sleep', side_effect=AssertionError('must not wait')):
            self.assertFalse(amd_device.free_vram_short(self.cards, 16*GIB))

    def test_exact_requirement_is_enough_and_one_byte_less_is_not(self):
        (self.cards[1]/'mem_info_vram_used').write_text(str(8*GIB))
        self.assertFalse(amd_device.free_vram_short(self.cards, 16*GIB, wait=0))
        (self.cards[1]/'mem_info_vram_used').write_text(str(8*GIB+1))
        self.assertTrue(amd_device.free_vram_short(self.cards, 16*GIB, wait=0))

    def test_memory_released_during_the_wait_is_accepted(self):
        (self.cards[0]/'mem_info_vram_used').write_text(str(20*GIB))
        naps = []
        def nap(seconds):
            naps.append(seconds)
            if len(naps) == 3:
                (self.cards[0]/'mem_info_vram_used').write_text(str(GIB))
        with patch.object(amd_device.time, 'sleep', side_effect=nap):
            self.assertFalse(amd_device.free_vram_short(self.cards, 16*GIB))
        self.assertEqual(len(naps), 3)

    def test_memory_never_released_is_refused_after_the_bounded_wait(self):
        (self.cards[0]/'mem_info_vram_used').write_text(str(20*GIB))
        clock = [0.0]
        def nap(seconds):
            clock[0] += seconds
        with patch.object(amd_device.time, 'sleep', side_effect=nap), \
             patch.object(amd_device.time, 'monotonic', side_effect=lambda: clock[0]):
            self.assertTrue(amd_device.free_vram_short(self.cards, 16*GIB))
        self.assertAlmostEqual(clock[0], amd_device.VRAM_RELEASE_WAIT_SECONDS, delta=0.3)

    def test_missing_telemetry_still_raises(self):
        (self.cards[0]/'mem_info_vram_used').unlink()
        with self.assertRaises(FileNotFoundError):
            amd_device.free_vram_short(self.cards, 16*GIB)


if __name__ == '__main__':
    unittest.main()
