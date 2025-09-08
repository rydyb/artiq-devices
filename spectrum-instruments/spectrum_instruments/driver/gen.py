import spcm
import logging


class SignalGenerator:
    def __init__(
        self,
        serial_number: int,
        output_load: float,
        output_voltage: float,
        verbose: bool = False,
    ):
        self.card = spcm.Card(serial_number=serial_number, verbose=verbose).open()
        logging.info("Opened card handle for card with serial number %s", serial_number)

        self.serial_number = serial_number
        self.output_load = output_load
        self.output_voltage = output_voltage

        try:
            self.card.timeout(10 * spcm.units.s)
            self.card.loops(0)
            logging.info("Set SPC_LOOPS to 0")

            self.channel0 = spcm.Channels(self.card, spcm.CHANNEL0 | spcm.CHANNEL1)
            self.channel0.enable(True)
            self.channel0.output_load(self.output_load * spcm.units.ohm)
            self.channel0.amp(self.output_voltage * spcm.units.V)
            logging.info(
                "Enabled channel 0 with output voltage %s V at 50 Ohm", output_voltage
            )

            self.trigger = spcm.Trigger(self.card)
        except spcm.SpcmException as error:
            logging.error("Error during initialization: %s", str(error))
            self.card.close()
            raise

    def close(self):
        self.card.close()
        self.card = None
        self.channel0 = None
        self.clock = None
        self.trigger = None
        logging.info("Closed card handle")

    def start_triggered_playback(self):
        self.trigger.termination(0)
        self.trigger.or_mask(spcm.SPC_TMASK_EXT0)
        self.trigger.ext0_mode(spcm.SPC_TM_POS)
        self.trigger.ext0_coupling(spcm.COUPLING_DC)
        self.trigger.ext0_level0(1 * spcm.units.V)
        logging.info("Configured external trigger with positive edge detection at 1 V")

        self.card.card_mode(spcm.SPC_REP_STD_SINGLERESTART)
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)
        logging.info("Card set to single restart mode and trigger enabled")
