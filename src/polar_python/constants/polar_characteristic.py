from enum import Enum


class PolarCharacteristic(str, Enum):
    """UUIDs for Polar device characteristics."""

    HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"
    PMD_CONTROL_POINT = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
    PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
