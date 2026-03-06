from dataclasses import dataclass
from enum import IntEnum

from ..parsers.compression import parse_delta_frames_all
from .pmd_data_frame import PmdDataFrame, PmdDataFrameType


class CalibrationStatus(IntEnum):
    """Represents the calibration status of the magnetometer."""

    NOT_AVAILABLE = -1
    UNKNOWN = 0
    POOR = 1
    OK = 2
    GOOD = 3

    @classmethod
    def get_by_id(cls, status_id: int) -> "CalibrationStatus":
        try:
            return cls(status_id)
        except ValueError:
            return cls.NOT_AVAILABLE


@dataclass
class MAGSample:
    """Represents a single magnetometer sample."""

    x: float
    y: float
    z: float
    calibration_status: CalibrationStatus = CalibrationStatus.NOT_AVAILABLE


@dataclass
class MAGData:
    """Represents magnetometer data."""

    timestamp: int
    data: list[MAGSample]

    TYPE_0_SAMPLE_SIZE_IN_BYTES = 2
    TYPE_0_SAMPLE_SIZE_IN_BITS = TYPE_0_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_0_CHANNELS_IN_SAMPLE = 3

    TYPE_1_SAMPLE_SIZE_IN_BYTES = 2
    TYPE_1_SAMPLE_SIZE_IN_BITS = TYPE_1_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_1_CHANNELS_IN_SAMPLE = 4

    @classmethod
    def from_dataframe(cls, frame: PmdDataFrame) -> "MAGData":
        if frame.is_compressed_frame:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_compressed_type_0(frame)
            elif frame.frame_type == PmdDataFrameType.TYPE_1:
                return cls._data_from_compressed_type_1(frame)
            else:
                raise ValueError(f"Compressed FrameType: {frame.frame_type} is not supported by Magnetometer data parser")
        else:
            raise ValueError(f"Raw FrameType: {frame.frame_type} is not supported by Magnetometer data parser")

    @classmethod
    def _data_from_compressed_type_0(cls, frame: PmdDataFrame) -> "MAGData":
        """Parse compressed TYPE_0 magnetometer data."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_0_CHANNELS_IN_SAMPLE, resolution=cls.TYPE_0_SAMPLE_SIZE_IN_BITS, data_type="signed_int")

        factor = frame.factor

        mag_samples = []
        for sample in samples:
            x = float(sample[0]) * factor
            y = float(sample[1]) * factor
            z = float(sample[2]) * factor
            mag_samples.append(MAGSample(x=x, y=y, z=z))

        return cls(timestamp=frame.timestamp, data=mag_samples)

    @classmethod
    def _data_from_compressed_type_1(cls, frame: PmdDataFrame) -> "MAGData":
        """Parse compressed TYPE_1 magnetometer data."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_1_CHANNELS_IN_SAMPLE, resolution=cls.TYPE_1_SAMPLE_SIZE_IN_BITS, data_type="signed_int")

        factor = frame.factor
        unit_conversion_factor = 1000.0  # type 1 data arrives in milliGauss units

        mag_samples = []
        for sample in samples:
            x = (float(sample[0]) * factor) / unit_conversion_factor
            y = (float(sample[1]) * factor) / unit_conversion_factor
            z = (float(sample[2]) * factor) / unit_conversion_factor

            status = CalibrationStatus.get_by_id(int(sample[3]))

            mag_samples.append(MAGSample(x=x, y=y, z=z, calibration_status=status))

        return cls(timestamp=frame.timestamp, data=mag_samples)
