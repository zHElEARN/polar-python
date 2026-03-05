from enum import Enum, IntEnum
from typing import Final

# Epoch offset for Polar device timestamps (Jan 1, 2000)
TIMESTAMP_OFFSET: Final[int] = 946684800000000000


class PolarCharacteristic(str, Enum):
    """UUIDs for Polar device characteristics."""

    HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"
    PMD_CONTROL_POINT = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
    PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"


class PmdMeasurementType(IntEnum):
    ECG = 0
    PPG = 1
    ACC = 2
    PPI = 3
    RFU = 4
    GYRO = 5
    MAG = 6


class PmdControlPointErrorCode(IntEnum):
    SUCCESS = 0
    ERROR_INVALID_OP_CODE = 1
    ERROR_INVALID_MEASUREMENT_TYPE = 2
    ERROR_NOT_SUPPORTED = 3
    ERROR_INVALID_LENGTH = 4
    ERROR_INVALID_PARAMETER = 5
    ERROR_ALREADY_IN_STATE = 6
    ERROR_INVALID_RESOLUTION = 7
    ERROR_INVALID_SAMPLE_RATE = 8
    ERROR_INVALID_RANGE = 9
    ERROR_INVALID_MTU = 10
    ERROR_INVALID_NUMBER_OF_CHANNELS = 11
    ERROR_INVALID_STATE = 12
    ERROR_DEVICE_IN_CHARGER = 13


class PmdControlOperationCode(IntEnum):
    GET = 0x01
    START = 0x02
    STOP = 0x03


class PmdSettingType(IntEnum):
    SAMPLE_RATE = 0
    RESOLUTION = 1
    RANGE = 2
    RANGE_MILLIUNIT = 3
    CHANNELS = 4
    FACTOR = 5
    SECURITY = 6

    @property
    def field_size(self) -> int:
        """Get the field size in bytes for the setting type."""
        match self:
            case PmdSettingType.RANGE_MILLIUNIT | PmdSettingType.FACTOR:
                return 4
            case PmdSettingType.CHANNELS:
                return 1
            case PmdSettingType.SECURITY:
                return 16
            case (
                PmdSettingType.SAMPLE_RATE
                | PmdSettingType.RESOLUTION
                | PmdSettingType.RANGE
            ):
                return 2
            case _:
                return 2
