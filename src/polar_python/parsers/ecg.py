"""ECG (Electrocardiogram) data parsing functions."""

from typing import Sequence

from ..models import ECGData


def parse_ecg_data(data: Sequence[int], timestamp: int) -> ECGData:
    """Parse ECG data from a list of integers."""
    ecg_data = [
        int.from_bytes(data[i : i + 3], byteorder="little", signed=True)
        for i in range(10, len(data), 3)
    ]
    return ECGData(timestamp=timestamp, data=ecg_data)
