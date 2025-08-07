import time
import logging
from .kklib import NativeLib, ErrorCode, KK_ReportType

CMD_FREQ_AVG = bytes([0x43])
CMD_RATE_1S = bytes([0x29])

class FrequencyCounter:
    def __init__(self, device_host: str, peer_host: str, channels: int, timeout: float = 10.0, interval: float = 0.1, data_port: int = 48896):
        self.device_host = device_host
        self.peer_host = peer_host
        self.data_port = 48896
        self.channels = channels
        self.timeout = timeout
        self.interval = interval

        self._lib = NativeLib()
        self._sid = None

    def open(self):
        if self._sid is not None:
            raise RuntimeError("connection already open")

        self._sid = self._lib.get_source_id()
        logging.debug(f"received source id: {self._sid}")
        port = self.data_port

        logging.debug(f"setting server ip for peer to {self.peer_host} via data port {self.data_port}")
        result = self._lib.set_server_ip_for_peer(self._sid, self.peer_host)
        if result.result_code != ErrorCode.KK_NO_ERR:
            raise RuntimeError(f"Error setting peer ip: {result.data}")

        logging.debug(f"opening connection to {self.device_host} via {self.peer_host}:{self.data_port}")
        result = self._lib.open_connection(self._sid, f"{self.device_host}:{port}", False)
        if result.result_code != ErrorCode.KK_NO_ERR:
            raise RuntimeError(f"Error opening connection: {result.data}")

        logging.debug("configuring device for data stream")
        self._lib.send_command(self._sid, CMD_FREQ_AVG)
        self._lib.send_command(self._sid, CMD_RATE_1S)
        self._lib.send_command(self._sid, str(self.channels).encode('ascii'))

    def report(self) -> list[float]:
        if self._sid is None:
            raise RuntimeError("connection not open")

        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            report = self._lib.get_kk_report(self._sid)
            if report.get_report_type() == KK_ReportType.RT_DOUBLE:
                return report._floats
            time.sleep(self.interval)

        raise TimeoutError("timeout while waiting for report")

    def close(self):
        if self._sid is None:
            raise RuntimeError("connection not open")

        self._lib.close_connection(self._sid)
        self._sid = None
