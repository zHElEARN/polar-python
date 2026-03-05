from dataclasses import dataclass


@dataclass
class HRData:
    """Represents heart rate data."""

    heartrate: int
    rr_intervals: list[float]
