from dataclasses import dataclass
from typing import List

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


@dataclass
class SettingType:
    type: str
    array_length: int
    values: List[int]


@dataclass
class MeasurementSettings:
    measurement_type: str
    error_code: str
    more_frames: bool
    settings: List[SettingType]
