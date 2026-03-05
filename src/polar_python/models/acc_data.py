from dataclasses import dataclass


@dataclass
class ACCData:
    """Represents accelerometer data."""

    timestamp: int
    data: list[tuple[int, int, int]]
