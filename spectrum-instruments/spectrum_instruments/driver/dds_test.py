import unittest
from spectrum_instruments import *


class TestDDS(unittest.TestCase):
    def setUp(self):
        self.dds = DDS(
            serial_number=18996,
            verbose=False,
        )

    def tearDown(self):
        try:
            self.dds.close()
        except Exception:
            pass

    def test_start_single_playback(self):
        try:
            self.dds.start_single_playback(
                [
                    Const(channel=0, tone=0, frequency=1e6, amplitude=0.5, phase=0),
                    Const(channel=1, tone=0, frequency=1e3, amplitude=0.1),
                ]
            )
        except Exception as e:
            self.fail(f"start_single_playback raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main()
