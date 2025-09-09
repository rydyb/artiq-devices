import numpy as np
import spcm
import logging

from .gen import SignalGenerator


class AWG(SignalGenerator):
    def __init__(
        self,
        sample_rate: float,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sample_rate = sample_rate

        try:
            self.card.timeout(10 * spcm.units.s)
            self.card.loops(0)
            logging.info("Set SPC_LOOPS to 0")

            self.clock = spcm.Clock(self.card)
            self.clock.sample_rate(sample_rate * spcm.units.Hz)
            self.clock.clock_output(False)
            logging.info("Set sample rate to %s Samples per second", sample_rate)
        except spcm.SpcmException as error:
            logging.error("Error during initialization: %s", str(error))
            self.card.close()
            raise

    def transfer_waveform(self, samples: np.ndarray):
        if len(samples) % 32 != 0:
            raise spcm.SpcmException("number of samples must be a multiple of 32")

        max_sample_value = self.card.max_sample_value()
        number_samples = len(samples) * spcm.units.S
        transfer = spcm.DataTransfer(self.card)
        transfer.memory_size(number_samples)
        transfer.allocate_buffer(number_samples)
        logging.info(
            "Allocated buffer of size %s bytes for %s samples",
            number_samples,
            len(samples),
        )

        buffer = ((samples / samples.max()) * (max_sample_value - 1)).astype(np.int16)
        transfer.buffer[:] = buffer
        transfer.start_buffer_transfer(
            spcm.M2CMD_DATA_STARTDMA, spcm.M2CMD_DATA_WAITDMA
        )
        logging.info("Started buffer transfer with %s samples", len(samples))

    def start_external_triggered_playback(self):
        super().start_triggered_playback()

        self.card.card_mode(spcm.SPC_REP_STD_SINGLERESTART)
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)
        logging.info("Card set to single restart mode and trigger enabled")

    def start_continuous_playback(self):
        self.trigger.or_mask(spcm.SPC_TMASK_SOFTWARE)
        logging.info("Set trigger mask for continuous playback")

        self.card.card_mode(spcm.SPC_REP_STD_CONTINUOUS)
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)
        logging.info("Card set to continuous mode and trigger enabled")

    def stop_playback(self):
        if self.card is None:
            raise spcm.SpcmException("Card is not initialized")

        self.card.stop(spcm.M2CMD_CARD_STOP)
        logging.info("Stopped card playback")

    def pulse(self, frequency: float, duration: float):
        num_samples = ((int(duration * self.sample_rate) + 31) // 32) * 32
        logging.info(
            "Generating pulse with %s duration %s samples", duration, num_samples
        )

        t = np.arange(num_samples) / self.sample_rate
        x = np.sin(2 * np.pi * t * frequency)
        x[int(duration * self.sample_rate) :] = 0

        self.stop_playback()
        self.transfer_waveform(x)
        self.start_triggered_playback()

    def tone(self, frequency: float):
        num_samples = 3200
        logging.info("Generating tone with %s samples", num_samples)

        t = np.arange(num_samples) / self.sample_rate
        x = np.sin(2 * np.pi * t * frequency)

        self.stop_playback()
        self.transfer_waveform(x)
        self.start_continuous_playback()

    def sweep(self, center: float, span: float, duration: float):
        f_start = center - span / 2
        f_end = center + span / 2

        num_samples = ((int(duration * self.sample_rate) + 31) // 32) * 32
        logging.info("Generating sweep with %s samples", num_samples)

        t = np.arange(num_samples) / self.sample_rate
        f = np.linspace(f_start, f_end, num_samples)
        x = np.sin(2 * np.pi * t * f)

        self.stop_playback()
        self.transfer_waveform(x)
        self.start_triggered_playback()
