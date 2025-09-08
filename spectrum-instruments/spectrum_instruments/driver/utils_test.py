import unittest
import spectrum_instruments


class TestUtils(unittest.TestCase):
    def test_list_devices(self):
        devices = spectrum_instruments.list_devices()
        assert isinstance(devices, list)
        assert all(isinstance(dev, dict) for dev in devices)
        assert all("device_identifier" in dev for dev in devices)
        assert all("serial_number" in dev for dev in devices)
        assert all("family" in dev for dev in devices)
        assert all("num_channels" in dev for dev in devices)
        assert all("product_name" in dev for dev in devices)


if __name__ == "__main__":
    unittest.main()
