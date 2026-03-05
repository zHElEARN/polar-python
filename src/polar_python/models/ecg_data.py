from dataclasses import dataclass


@dataclass
class ECGData:
    """Represents ECG data."""

    timestamp: int
    data: list[int]
