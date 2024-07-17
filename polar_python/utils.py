from . import constants
from typing import List


def byte_to_bitmap(byte: int) -> list[bool]:
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]

    return [bit == '1' for bit in reversed_binary_string]


def parse_pmd_data(data: bytearray) -> constants.MeasurementSettings:
    measurement_type_index = data[2]
    error_code_index = data[3]
    more_frames = data[4] != 0

    measurement_type = constants.PMD_MEASUREMENT_TYPES[measurement_type_index] if measurement_type_index < len(
        constants.PMD_MEASUREMENT_TYPES) else "UNKNOWN"
    error_code = constants.PMD_CONTROL_POINT_ERROR_CODES[error_code_index] if error_code_index < len(
        constants.PMD_CONTROL_POINT_ERROR_CODES) else "UNKNOWN"

    settings = []
    index = 5
    while index < len(data):
        setting_type_index = data[index]
        setting_type = constants.PMD_SETTING_TYPES[setting_type_index] if setting_type_index < len(
            constants.PMD_SETTING_TYPES) else "UNKNOWN"
        array_length = data[index + 1]
        setting_values = []
        for i in range(array_length):
            value = int.from_bytes(
                data[index + 2 + 2 * i:index + 4 + 2 * i], 'little')
            setting_values.append(value)
        settings.append(constants.SettingType(
            type=setting_type,
            array_length=array_length,
            values=setting_values
        ))
        index += 2 + 2 * array_length

    return constants.MeasurementSettings(
        measurement_type=measurement_type,
        error_code=error_code,
        more_frames=more_frames,
        settings=settings
    )


def build_measurement_settings(measurement_settings: constants.MeasurementSettings) -> bytearray:
    data = bytearray()
    data.append(constants.PMD_CONTROL_OPERATION_CODE["START"])

    measurement_type_index = constants.PMD_MEASUREMENT_TYPES.index(measurement_settings.measurement_type)
    data.append(measurement_type_index)

    for setting in measurement_settings.settings:
        setting_type_index = constants.PMD_SETTING_TYPES.index(setting.type)
        data.append(setting_type_index)

        data.append(setting.array_length)

        for value in setting.values:
            data.extend(value.to_bytes(2, 'little'))

    return data

def parse_ecg_data(data: List[int], timestamp: int) -> constants.ECGData:
    ecg_data = []
    for i in range(10, len(data), 3):
        value = int.from_bytes(data[i:i+3], byteorder='little', signed=True)
        ecg_data.append(value)
    return constants.ECGData(timestamp=timestamp, data=ecg_data)

def parse_acc_data(data: List[int], timestamp: int, frame_type: int) -> constants.ACCData:
    acc_data = []
    if frame_type == 0x00:
        for i in range(10, len(data), 3):
            x = int.from_bytes(data[i:i+1], byteorder='little', signed=True)
            y = int.from_bytes(data[i+1:i+2], byteorder='little', signed=True)
            z = int.from_bytes(data[i+2:i+3], byteorder='little', signed=True)
            acc_data.append((x, y, z))
    elif frame_type == 0x01:
        for i in range(10, len(data), 6):
            x = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
            y = int.from_bytes(data[i+2:i+4], byteorder='little', signed=True)
            z = int.from_bytes(data[i+4:i+6], byteorder='little', signed=True)
            acc_data.append((x, y, z))
    elif frame_type == 0x02:
        for i in range(10, len(data), 9):
            x = int.from_bytes(data[i:i+3], byteorder='little', signed=True)
            y = int.from_bytes(data[i+3:i+6], byteorder='little', signed=True)
            z = int.from_bytes(data[i+6:i+9], byteorder='little', signed=True)
            acc_data.append((x, y, z))
    return constants.ACCData(timestamp=timestamp, data=acc_data)

def parse_bluetooth_data(data: List[int]):
    data_type_index = data[0]
    data_type = constants.PMD_MEASUREMENT_TYPES[data_type_index]
    
    timestamp = int.from_bytes(data[1:9], byteorder='little') + constants.TIMESTAMP_OFFSET
    frame_type = data[9]
    
    if data_type == "ECG":
        return parse_ecg_data(data, timestamp)
    elif data_type == "ACC":
        return parse_acc_data(data, timestamp, frame_type)
    else:
        raise ValueError(f"Unsupported data type: {data_type}")
    
def parse_heartrate_data(data):
    heartrate = int.from_bytes(data[1:2], byteorder="little", signed=False)
    rr_intervals = []

    if len(list(data)) > 2:
        offset = 2
        while offset < len(list(data)):
            rr_interval_raw = int.from_bytes(data[offset:offset+2], byteorder="little", signed=False)
            rr_intervals.append(rr_interval_raw / 1024.0 * 1024.0)

            offset += 2

    return constants.HRData(heartrate, rr_intervals)