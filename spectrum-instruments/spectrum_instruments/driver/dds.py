from dataclasses import dataclass
from enum import Enum
import logging
import spcm

from .gen import SignalGenerator


class PhaseMode(Enum):
    JUMP = spcm.SPC_DDS_PHASE_JUMP
    SHIFT = spcm.SPC_DDS_PHASE_SHIFT


class TransferMode(Enum):
    SINGLE = spcm.SPC_DDS_DTM_SINGLE
    DMA = spcm.SPC_DDS_DTM_DMA


@dataclass
class BaseCommand:
    tone: int
    channel: int


@dataclass(frozen=True)
class ConstCommand(BaseCommand):
    amplitude: float
    frequency: float
    phase: float = 0.0


@dataclass(frozen=True)
class RampCommand(BaseCommand):
    amplitude: float | None = None
    frequency: float | None = None


@dataclass(frozen=True)
class TriggerCommand:
    pass


Command = ConstCommand | RampCommand | TriggerCommand

channel0_to_core = set(range(8, 12)) | {20}
channel1_to_core = set(range(0, 20)) - channel0_to_core
channels_to_core = (channel0_to_core, channel1_to_core)


class DDS(SignalGenerator):
    def __init__(
        self,
        phase_mode: PhaseMode = PhaseMode.SHIFT,
        transfer_mode: TransferMode = TransferMode.DMA,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.card.card_mode = spcm.SPC_REP_STD_DDS

        self.dds = spcm.DDS(self.card, channels=self.channels)
        self.dds.reset()
        self.dds.phase_behaviour(phase_mode)
        self.dds.data_transfer_mode(transfer_mode)
        self.dds.cores_on_channel(
            1,
            spcm.SPCM_DDS_CORE8,
            spcm.SPCM_DDS_CORE9,
            spcm.SPCM_DDS_CORE10,
            spcm.SPCM_DDS_CORE11,
            spcm.SPCM_DDS_CORE20,
        )

    def start_single_playback(self, commands: [Command]):
        amp_lim = (self.dds.avail_amp_min(), self.dds.avail_amp_max())
        freq_lim = (self.dds.avail_freq_min(), self.dds.avail_freq_max())
        phase_lim = (self.dds.avail_phase_min(), self.dds.avail_phase_max())

        amp_slope_lim = (self.dds.avail_amp_slope_min(), self.dds.avail_amp_slope_max())
        freq_slope_lim = (
            self.dds.avail_freq_slope_min(),
            self.dds.avail_freq_slope_max(),
        )

        for command in commands:
            if command.channel not in (0, 1):
                raise ValueError(f"invalid channel: {command.channel}")
            cores = channels_to_core[command.channel]

            if command.tone > len(cores):
                raise ValueError(f"invalid tone: {command.tone}")
            core = cores[command.tone]

            if isinstance(command, ConstCommand):
                if command.amplitude is not None:
                    if not (amp_lim[0] <= command.amplitude <= amp_lim[1]):
                        raise ValueError(
                            f"amplitude {command.amplitude} out of range {amp_lim}"
                        )
                    self.dds.amp(core, command.amplitude)
                if command.frequency is not None:
                    if not (freq_lim[0] <= command.frequency <= freq_lim[1]):
                        raise ValueError(
                            f"frequency {command.frequency} out of range {freq_lim}"
                        )
                    self.dds.freq(core, command.frequency)
                if command.phase is not None:
                    if not (phase_lim[0] <= command.phase <= phase_lim[1]):
                        raise ValueError(
                            f"phase {command.phase} out of range {phase_lim}"
                        )
                    self.dds.phase(core, command.phase)
            elif isinstance(command, RampCommand):
                if command.amplitude is not None:
                    if not (amp_slope_lim[0] <= command.amplitude <= amp_slope_lim[1]):
                        raise ValueError(
                            f"amplitude slope {command.amplitude} out of range {amp_lim}"
                        )
                    self.dds.amp_slope(core, command.amplitude)
                if command.frequency is not None:
                    if not (
                        freq_slope_lim[0] <= command.frequency <= freq_slope_lim[1]
                    ):
                        raise ValueError(
                            f"frequency slope {command.frequency} out of range {freq_lim}"
                        )
                    self.dds.freq_slope(core, command.frequency)
            elif isinstance(command, TriggerCommand):
                self.dds.exec_at_trg()
            else:
                raise ValueError(f"unknown command type: {type(command)}")
        self.dds.write_to_card()

    def start_triggered_playback(self):
        super().start_triggered_playback()
        self.card.card_mode(spcm.SPC_REP_STD_SINGLERESTART)
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)
        logging.info("Card set to single restart mode and trigger enabled")

    def stop(self):
        self.card.stop()
