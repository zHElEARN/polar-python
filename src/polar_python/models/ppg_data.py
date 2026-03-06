from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

from ..constants import PmdMeasurementType
from ..parsers.compression import parse_delta_frames_all
from .pmd_data_frame import PmdDataFrame, PmdDataFrameType


class PPGType(IntEnum):
    """Enumeration of PPG data types."""

    PPG1 = 1
    PPG3_AMBIENT1 = 4
    PPG3 = 7
    PPG17 = 5
    PPG21 = 6
    UNKNOWN = 18


@dataclass
class PPGData:
    """Represents photoplethysmogram data."""

    timestamp: int
    samples: list[list[int]]
    type: PPGType

    TYPE_0_SAMPLE_SIZE_IN_BYTES = 3
    TYPE_0_SAMPLE_SIZE_IN_BITS = TYPE_0_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_0_CHANNELS_IN_SAMPLE = 4

    @classmethod
    def from_dataframe(cls, frame: PmdDataFrame, get_factor: Callable[[PmdMeasurementType], float] = lambda _: 1.0) -> "PPGData":
        if frame.is_compressed_frame:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_compressed_type_0(frame, get_factor)
            else:
                raise ValueError(f"Compressed FrameType: {frame.frame_type.name} is not currently supported by PPG data parser")
        else:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_raw_type_0(frame)
            else:
                raise ValueError(f"Raw FrameType: {frame.frame_type.name} is not currently supported by PPG data parser")

    @classmethod
    def _data_from_raw_type_0(cls, frame: PmdDataFrame) -> "PPGData":
        """Parse raw TYPE_0 data (PPG3_AMBIENT1)."""
        ppg_samples = []
        offset = 0
        step = cls.TYPE_0_SAMPLE_SIZE_IN_BYTES
        content = frame.data_content

        while offset < len(content):
            if offset + step * cls.TYPE_0_CHANNELS_IN_SAMPLE > len(content):
                break

            sample = []
            for _ in range(cls.TYPE_0_CHANNELS_IN_SAMPLE):
                val = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
                sample.append(val)
                offset += step

            ppg_samples.append(sample)

        return cls(timestamp=frame.timestamp, samples=ppg_samples, type=PPGType.PPG3_AMBIENT1)

    @classmethod
    def _data_from_compressed_type_0(cls, frame: PmdDataFrame, _unused_get_factor: Callable[[PmdMeasurementType], float]) -> "PPGData":
        """Parse compressed TYPE_0 data (PPG3_AMBIENT1)."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_0_CHANNELS_IN_SAMPLE, resolution=cls.TYPE_0_SAMPLE_SIZE_IN_BITS, data_type="signed_int")

        ppg_samples = []
        for sample in samples:
            ppg0 = sample[0]
            ppg1 = sample[1]
            ppg2 = sample[2]
            ambient = sample[3]
            ppg_samples.append([ppg0, ppg1, ppg2, ambient])

        return cls(timestamp=frame.timestamp, samples=ppg_samples, type=PPGType.PPG3_AMBIENT1)
