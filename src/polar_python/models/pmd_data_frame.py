from dataclasses import dataclass
from enum import IntEnum

from ..constants import TIMESTAMP_OFFSET, PmdMeasurementType


class PmdDataFrameType(IntEnum):
    TYPE_0 = 0
    TYPE_1 = 1
    TYPE_2 = 2
    TYPE_3 = 3
    TYPE_4 = 4
    TYPE_5 = 5
    TYPE_6 = 6
    TYPE_7 = 7
    TYPE_8 = 8
    TYPE_9 = 9
    TYPE_10 = 10
    TYPE_13 = 13
    TYPE_14 = 14


@dataclass
class PmdDataFrame:
    measurement_type: PmdMeasurementType
    timestamp: int
    frame_type: PmdDataFrameType
    is_compressed_frame: bool
    data_content: bytearray

    DELTA_FRAME_BIT_MASK = 0x80
    DATA_FRAME_BIT_MASK = 0x7F

    @classmethod
    def from_bytes(cls, data: bytearray) -> "PmdDataFrame":
        if len(data) < 10:
            raise ValueError("Data is too short to parse PmdDataFrame")

        measurement_type = PmdMeasurementType(data[0])
        timestamp = int.from_bytes(data[1:9], byteorder="little") + TIMESTAMP_OFFSET
        frame_type_byte = data[9]

        frame_type_val = frame_type_byte & cls.DATA_FRAME_BIT_MASK
        try:
            frame_type = PmdDataFrameType(frame_type_val)
        except ValueError:
            raise ValueError(f"FrameType id: {frame_type_val} is not implemented")

        is_compressed_frame = (frame_type_byte & cls.DELTA_FRAME_BIT_MASK) > 0

        data_content = data[10:]

        return cls(measurement_type=measurement_type, timestamp=timestamp, frame_type=frame_type, is_compressed_frame=is_compressed_frame, data_content=data_content)
