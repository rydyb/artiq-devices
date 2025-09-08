import unittest
import spectrum_instruments


class TestGeneric(unittest.TestCase):
    def test_list_devices(self):
        devices = spectrum_instruments.list_devices()
        assert isinstance(devices, list)
        assert all(isinstance(dev, dict) for dev in devices)
        assert all("device_identifier" in dev for dev in devices)
        assert all("serial_number" in dev for dev in devices)
        assert all("family" in dev for dev in devices)
        assert all("num_channels" in dev for dev in devices)
        assert all("product_name" in dev for dev in devices)


class TestSignalGenerator(unittest.TestCase):
    def setUp(self):
        self.sg = spectrum_instruments.SignalGenerator(
            serial_number=18996,
            sample_rate=1e9,
            output_voltage=1.0,
            verbose=False,
        )

    def tearDown(self):
        try:
            self.sg.close()
        except Exception:
            pass

    def test_initialization(self):
        pass


if __name__ == "__main__":
    unittest.main()
