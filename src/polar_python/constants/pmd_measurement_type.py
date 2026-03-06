from enum import IntEnum


class PmdMeasurementType(IntEnum):
    ECG = 0
    PPG = 1
    ACC = 2
    PPI = 3
    RFU = 4
    GYRO = 5
    MAG = 6
