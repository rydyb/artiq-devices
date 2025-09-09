import time
import unittest
from spectrum_instruments import *


class TestDDS(unittest.TestCase):
    def setUp(self):
        self.dds = DDS(
            serial_number=18925,
            verbose=True,
            output_voltage=1.0,
        )

    def tearDown(self):
        try:
            self.dds.close()
        except Exception:
            pass

    def test_start_single_playback(self):
        self.dds.transfer(
            [
                ConstCommand(channel=0, tone=0, frequency=1e6, amplitude=0.5, phase=0),
                ConstCommand(channel=1, tone=0, frequency=1e3, amplitude=0.1),
                InternalTriggerCommand(delay=2.0),
                ConstCommand(channel=1, tone=0, frequency=1e3, amplitude=0.0),
                InternalTriggerCommand(delay=2.0),
                RampCommand(channel=0, tone=0, frequency=1e6),
            ]
        )

        self.dds.arm_internal_trigger()
        self.dds.force_internal_trigger()

        time.sleep(5)


if __name__ == "__main__":
    unittest.main()
