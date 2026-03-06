from dataclasses import dataclass

from ..parsers.compression import parse_delta_frames_all
from .pmd_data_frame import PmdDataFrame, PmdDataFrameType


@dataclass
class GyroData:
    """Represents gyroscope data."""

    timestamp: int
    data: list[tuple[float, float, float]]

    TYPE_0_SAMPLE_SIZE_IN_BYTES = 2
    TYPE_0_SAMPLE_SIZE_IN_BITS = TYPE_0_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_0_CHANNELS_IN_SAMPLE = 3

    TYPE_1_SAMPLE_SIZE_IN_BYTES = 4
    TYPE_1_SAMPLE_SIZE_IN_BITS = TYPE_1_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_1_CHANNELS_IN_SAMPLE = 3

    @classmethod
    def from_dataframe(cls, frame: PmdDataFrame) -> "GyroData":
        if frame.is_compressed_frame:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_compressed_type_0(frame)
            else:
                raise ValueError(f"Compressed FrameType: {frame.frame_type} is not supported by Gyro data parser")
        else:
            raise ValueError(f"Raw FrameType: {frame.frame_type} is not supported by Gyro data parser")

    @classmethod
    def _data_from_compressed_type_0(cls, frame: PmdDataFrame) -> "GyroData":
        """Parse compressed TYPE_0 gyro data."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_0_CHANNELS_IN_SAMPLE, resolution=cls.TYPE_0_SAMPLE_SIZE_IN_BITS, data_type="signed_int")

        factor = frame.factor

        gyr_samples = []
        for sample in samples:
            # Gyro data uses float after applying the factor
            x = float(sample[0]) * factor
            y = float(sample[1]) * factor
            z = float(sample[2]) * factor
            gyr_samples.append((x, y, z))

        return cls(timestamp=frame.timestamp, data=gyr_samples)
