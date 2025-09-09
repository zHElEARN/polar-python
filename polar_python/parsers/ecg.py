"""ECG (Electrocardiogram) data parsing functions."""

from typing import List
from .. import constants


def parse_ecg_data(data: List[int], timestamp: int) -> constants.ECGData:
    """Parse ECG data from a list of integers."""
    ecg_data = [
        int.from_bytes(data[i : i + 3], byteorder="little", signed=True)
        for i in range(10, len(data), 3)
    ]
    return constants.ECGData(timestamp=timestamp, data=ecg_data)
