import spcm
import logging


class SignalGenerator:
    def __init__(
        self,
        serial_number: int,
        output_voltage: float,
        output_load: float = 50.0,
        verbose: bool = False,
    ):
        self.card = spcm.Card(serial_number=serial_number, verbose=verbose).open()
        logging.info("Opened card handle for card with serial number %s", serial_number)

        self.serial_number = serial_number
        self.output_load = output_load
        self.output_voltage = output_voltage

        try:
            self.channels = spcm.Channels(self.card, spcm.CHANNEL0 | spcm.CHANNEL1)
            self.channels.enable(True)
            self.channels.output_load(self.output_load * spcm.units.ohm)
            self.channels.amp(self.output_voltage * spcm.units.V)
            logging.info(
                "Enabled channel 0 with output voltage %s V at 50 Ohm", output_voltage
            )

            self.trigger = spcm.Trigger(self.card, channels=self.channels)
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

    def arm_external_trigger(self):
        self.trigger.termination(0)
        self.trigger.or_mask(spcm.SPC_TMASK_EXT0)
        self.trigger.ext0_mode(spcm.SPC_TM_POS)
        self.trigger.ext0_coupling(spcm.COUPLING_DC)
        self.trigger.ext0_level0(1 * spcm.units.V)
        logging.info("Configured external trigger with positive edge detection at 1 V")

        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

    def arm_internal_trigger(self):
        self.trigger.or_mask(spcm.SPC_TM_NONE)
        logging.info("Configured internal trigger")

        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

    def force_internal_trigger(self):
        self.trigger.force()
        logging.info("Triggered internal trigger")