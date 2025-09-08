import spcm
import unittest
import numpy as np
from spectrum_instruments import *


class TestAWG(unittest.TestCase):
    def setUp(self):
        self.awg = AWG(
            serial_number=18996,
            sample_rate=1e9,
            output_voltage=1.0,
            verbose=False,
        )

    def tearDown(self):
        try:
            self.awg.close()
        except Exception:
            pass

    def test_transfer_waveform_raises_on_bad_length(self):
        bad = np.zeros(10, dtype=float)  # not multiple of 32
        with self.assertRaises(spcm.SpcmException):
            self.awg.transfer_waveform(bad)

    def test_transfer_waveform_hardware(self):
        good = np.linspace(-1, 1, 32, dtype=float)
        try:
            self.awg.transfer_waveform(good)
        except Exception as e:
            self.fail(f"transfer_waveform raised unexpectedly: {e}")

    def test_arm_external_trigger_hardware(self):
        try:
            self.awg.start_triggered_playback()
        except Exception as e:
            self.fail(f"arm_external_trigger raised unexpectedly: {e}")

    def test_continuous_playback_hardware(self):
        try:
            self.awg.start_continuous_playback()
        except Exception as e:
            self.fail(f"continuous_playback raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main()
