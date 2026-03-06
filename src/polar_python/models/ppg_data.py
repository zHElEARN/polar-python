from dataclasses import dataclass
from enum import IntEnum


@dataclass
class PPGData:
    """Represents photoplethysmogram data."""

    class PPGType(IntEnum):
        PPG1 = 1
        PPG3_AMBIENT1 = 4
        PPG3 = 7
        PPG17 = 5
        PPG21 = 6
        UNKNOWN = 18

    timestamp: int
    samples: list[list[int]]
    type: PPGType
