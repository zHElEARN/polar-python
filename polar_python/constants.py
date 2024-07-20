from dataclasses import dataclass
from typing import List, Optional, Tuple

# UUIDs for Polar device characteristics
HEART_RATE_CHAR_UUID: str = "00002a37-0000-1000-8000-00805f9b34fb"
PMD_CONTROL_POINT_UUID: str = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA_UUID: str = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

# PMD Measurement Types
PMD_MEASUREMENT_TYPES: List[str] = ["ECG", "PPG", "ACC", "PPI", "RFU", "GYRO", "MAG"]

# PMD Control Point Error Codes
PMD_CONTROL_POINT_ERROR_CODES: List[str] = [
    "SUCCESS",
    "ERROR INVALID OP CODE",
    "ERROR INVALID MEASUREMENT TYPE",
    "ERROR NOT SUPPORTED",
    "ERROR INVALID LENGTH",
    "ERROR INVALID PARAMETER",
    "ERROR ALREADY IN STATE",
    "ERROR INVALID RESOLUTION",
    "ERROR INVALID SAMPLE RATE",
    "ERROR INVALID RANGE",
    "ERROR INVALID MTU",
    "ERROR INVALID NUMBER OF CHANNELS",
    "ERROR INVALID STATE",
    "ERROR DEVICE IN CHARGER",
]

# PMD Control Operation Codes
PMD_CONTROL_OPERATION_CODE: dict = {"GET": 0x01, "START": 0x02, "STOP": 0x03}

# PMD Setting Types
PMD_SETTING_TYPES: List[str] = ["SAMPLE_RATE", "RESOLUTION", "RANGE", "RFU", "CHANNELS"]

# Timestamp Offset
TIMESTAMP_OFFSET: int = 946684800000000000


@dataclass
class SettingType:
    """Represents a setting type with its array length and possible values."""

    type: str
    array_length: int
    values: List[int]


@dataclass
class MeasurementSettings:
    """Represents measurement settings for a specific type."""

    measurement_type: str
    settings: List[SettingType]
    error_code: Optional[str] = None
    more_frames: Optional[bool] = None


@dataclass
class ACCData:
    """Represents accelerometer data."""

    timestamp: int
    data: List[Tuple[int, int, int]]


@dataclass
class ECGData:
    """Represents ECG data."""

    timestamp: int
    data: List[int]


@dataclass
class HRData:
    """Represents heart rate data."""

    heartrate: int
    rr_intervals: List[float]
