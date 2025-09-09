from dataclasses import dataclass
from enum import Enum
import logging
import spcm
from typing import Optional, Union, List

from .gen import SignalGenerator


class PhaseMode(Enum):
    JUMP = spcm.SPCM_DDS_PHASE_JUMP
    SHIFT = spcm.SPCM_DDS_PHASE_SHIFT


class TransferMode(Enum):
    SINGLE = spcm.SPCM_DDS_DTM_SINGLE
    DMA = spcm.SPCM_DDS_DTM_DMA


@dataclass(frozen=True)
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
    amplitude: Optional[float] = None
    frequency: Optional[float] = None

@dataclass(frozen=True)
class InternalTriggerCommand:
    delay: float = 0.0

@dataclass(frozen=True)
class ExternalTriggerCommand:
    pass


Command = Union[ConstCommand, RampCommand, InternalTriggerCommand, ExternalTriggerCommand]

channel0_to_core = list(set(range(8, 12)) | {20})
channel1_to_core = list(set(range(0, 20)) - set(channel0_to_core))
channels_to_core = (channel0_to_core, channel1_to_core)


class DDS(SignalGenerator):
    def __init__(
        self,
        phase_mode: PhaseMode = PhaseMode.SHIFT,
        transfer_mode: TransferMode = TransferMode.DMA,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.card.card_mode(spcm.SPC_REP_STD_DDS)
        self.card.write_setup()
        logging.info("Card set to repetive standard DDS mode")

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
        logging.info(f"DDS set to phase mode {phase_mode.name}, transfer mode {transfer_mode.name} and maximum cores assigned to channel1")
        self.dds.write_to_card()

    def transfer(self, commands: List[Command]):
        amp_lim = (self.dds.avail_amp_min(), self.dds.avail_amp_max())
        freq_lim = (self.dds.avail_freq_min(), self.dds.avail_freq_max())
        phase_lim = (self.dds.avail_phase_min(), self.dds.avail_phase_max())

        amp_slope_lim = (self.dds.avail_amp_slope_min(), self.dds.avail_amp_slope_max())
        freq_slope_lim = (
            self.dds.avail_freq_slope_min(),
            self.dds.avail_freq_slope_max(),
        )

        self.dds.trg_src(spcm.SPCM_DDS_TRG_SRC_TIMER)

        for command in commands:
            logging.info(f"adding command {command}")

            if isinstance(command, (ConstCommand, RampCommand)):
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
            elif isinstance(command, InternalTriggerCommand):
                self.dds.trg_timer(command.delay)
            elif isinstance(command, ExternalTriggerCommand):
                self.dds.exec_at_trg()
            else:
                raise ValueError(f"unknown command type: {type(command)}")

        self.dds.exec_at_trg()
        self.dds.write_to_card()