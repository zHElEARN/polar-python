from dataclasses import dataclass

from ..parsers.compression import parse_delta_frames_all
from .pmd_data_frame import PmdDataFrame, PmdDataFrameType


@dataclass
class ACCData:
    """Represents accelerometer measurement data.

    Attributes:
        timestamp: The UNIX timestamp in nanoseconds.
        data: A list of tuples containing the x, y, and z axis values in milli-g (mG).
            Each tuple is structured as (x: int, y: int, z: int).
    """

    timestamp: int
    data: list[tuple[int, int, int]]

    TYPE_0_SAMPLE_SIZE_IN_BYTES = 1
    TYPE_0_SAMPLE_SIZE_IN_BITS = TYPE_0_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_0_CHANNELS_IN_SAMPLE = 3

    TYPE_1_SAMPLE_SIZE_IN_BYTES = 2
    TYPE_1_SAMPLE_SIZE_IN_BITS = TYPE_1_SAMPLE_SIZE_IN_BYTES * 8
    TYPE_1_CHANNELS_IN_SAMPLE = 3

    @classmethod
    def from_dataframe(cls, frame: PmdDataFrame) -> "ACCData":
        if frame.is_compressed_frame:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_compressed_type_0(frame)
            elif frame.frame_type == PmdDataFrameType.TYPE_1:
                return cls._data_from_compressed_type_1(frame)
            else:
                raise ValueError(f"Compressed FrameType: {frame.frame_type} is not supported by ACC data parser")
        else:
            if frame.frame_type == PmdDataFrameType.TYPE_0:
                return cls._data_from_raw_type_0(frame)
            elif frame.frame_type == PmdDataFrameType.TYPE_1:
                return cls._data_from_raw_type_1(frame)
            else:
                raise ValueError(f"Raw FrameType: {frame.frame_type} is not supported by ACC data parser")

    @classmethod
    def _data_from_raw_type_0(cls, frame: PmdDataFrame) -> "ACCData":
        """Parse raw TYPE_0 data (1 byte per axis)."""
        acc_samples = []
        offset = 0
        step = cls.TYPE_0_SAMPLE_SIZE_IN_BYTES
        content = frame.data_content

        while offset < len(content):
            if offset + step * cls.TYPE_0_CHANNELS_IN_SAMPLE > len(content):
                break

            x = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            y = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            z = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            acc_samples.append((x, y, z))

        return cls(timestamp=frame.timestamp, data=acc_samples)

    @classmethod
    def _data_from_raw_type_1(cls, frame: PmdDataFrame) -> "ACCData":
        """Parse raw TYPE_1 data (2 bytes per axis)."""
        acc_samples = []
        offset = 0
        step = cls.TYPE_1_SAMPLE_SIZE_IN_BYTES
        content = frame.data_content

        while offset < len(content):
            if offset + step * cls.TYPE_1_CHANNELS_IN_SAMPLE > len(content):
                break

            x = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            y = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            z = int.from_bytes(content[offset : offset + step], byteorder="little", signed=True)
            offset += step

            acc_samples.append((x, y, z))

        return cls(timestamp=frame.timestamp, data=acc_samples)

    @classmethod
    def _data_from_compressed_type_0(cls, frame: PmdDataFrame) -> "ACCData":
        """Parse compressed TYPE_0 data (Note: special Wolfi type, see SAGRFC85.3)."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_0_CHANNELS_IN_SAMPLE, resolution=16, data_type="signed_int")

        factor = frame.factor
        acc_factor = factor * 1000.0  # type 0 data arrives in G units, convert to milliG

        acc_samples = []
        for sample in samples:
            x = int(sample[0] * acc_factor)
            y = int(sample[1] * acc_factor)
            z = int(sample[2] * acc_factor)
            acc_samples.append((x, y, z))

        return cls(timestamp=frame.timestamp, data=acc_samples)

    @classmethod
    def _data_from_compressed_type_1(cls, frame: PmdDataFrame) -> "ACCData":
        """Parse compressed TYPE_1 data."""
        samples = parse_delta_frames_all(frame.data_content, channels=cls.TYPE_1_CHANNELS_IN_SAMPLE, resolution=cls.TYPE_1_SAMPLE_SIZE_IN_BITS, data_type="signed_int")

        factor = frame.factor

        acc_samples = []
        for sample in samples:
            if factor != 1.0:
                x = int(sample[0] * factor)
                y = int(sample[1] * factor)
                z = int(sample[2] * factor)
            else:
                x = sample[0]
                y = sample[1]
                z = sample[2]
            acc_samples.append((x, y, z))

        return cls(timestamp=frame.timestamp, data=acc_samples)
