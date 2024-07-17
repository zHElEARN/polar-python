from dataclasses import dataclass
from typing import List, Optional, Tuple

HEART_RATE_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
PMD_CONTROL_POINT_UUID = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA_UUID = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

PMD_MEASUREMENT_TYPES = [
    "ECG",
    "PPG",
    "ACC",
    "PPI",
    "RFU",
    "GYRO",
    "MAG"
]

PMD_CONTROL_POINT_ERROR_CODES = [
    'SUCCESS',
    'ERROR INVALID OP CODE',
    'ERROR INVALID MEASUREMENT TYPE',
    'ERROR NOT SUPPORTED',
    'ERROR INVALID LENGTH',
    'ERROR INVALID PARAMETER',
    'ERROR ALREADY IN STATE',
    'ERROR INVALID RESOLUTION',
    'ERROR INVALID SAMPLE RATE',
    'ERROR INVALID RANGE',
    'ERROR INVALID MTU',
    'ERROR INVALID NUMBER OF CHANNELS',
    'ERROR INVALID STATE',
    'ERROR DEVICE IN CHARGER'
]

PMD_CONTROL_OPERATION_CODE = {
    "GET": 0x01,
    "START": 0x02,
    "STOP": 0x03
}

PMD_SETTING_TYPES = [
    'SAMPLE_RATE',
    'RESOLUTION',
    'RANGE',
    'RFU',
    'CHANNELS'
]

TIMESTAMP_OFFSET = 946684800000000000


@dataclass
class SettingType:
    type: str
    array_length: int
    values: List[int]


@dataclass
class MeasurementSettings:
    measurement_type: str
    settings: List[SettingType]
    error_code: Optional[str] = None
    more_frames: Optional[bool] = None


@dataclass
class ACCData:
    timestamp: int
    data: List[Tuple[int, int, int]]


@dataclass
class ECGData:
    timestamp: int
    data: List[int]


@dataclass
class HRData:
    heartrate: int
    rr_intervals: List[float]