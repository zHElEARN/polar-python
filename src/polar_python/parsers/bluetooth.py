"""Bluetooth data parsing functions."""

from typing import List, Union
from .. import constants
from .ecg import parse_ecg_data
from .accelerometer import parse_acc_data
from .ppi import parse_ppi_data


def parse_bluetooth_data(
    data: List[int],
) -> Union[constants.ECGData, constants.ACCData, constants.PPIData]:
    """Parse Bluetooth data and return the appropriate data type."""
    try:
        data_type_index = data[0]
        data_type = constants.PMD_MEASUREMENT_TYPES[data_type_index]
        timestamp = (
            int.from_bytes(data[1:9], byteorder="little") + constants.TIMESTAMP_OFFSET
        )
        frame_type = data[9]

        if data_type == "ECG":
            return parse_ecg_data(data, timestamp)
        elif data_type == "ACC":
            return parse_acc_data(data, timestamp, frame_type)
        elif data_type == "PPI":
            return parse_ppi_data(data, timestamp)
        else:
            print(f"Unsupported data type: {data_type}")
            print(" ".join([f"{byte:02X}" for byte in data]))
            return None
            # raise ValueError(f"Unsupported data type: {data_type}")
    except IndexError as e:
        raise ValueError(
            "Failed to parse Bluetooth data: insufficient data length"
        ) from e
