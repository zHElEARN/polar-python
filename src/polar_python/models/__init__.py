from typing import TypeAlias

from .acc_data import ACCData
from .ecg_data import ECGData
from .gyro_data import GyroData
from .hr_data import HRData
from .measurement_settings import MeasurementSettings
from .pmd_data_frame import PmdDataFrame
from .ppg_data import PPGData
from .ppi_data import PPIData

SensorData: TypeAlias = ECGData | ACCData | PPIData | PPGData | GyroData

__all__ = [
    "ACCData",
    "ECGData",
    "HRData",
    "PPIData",
    "PPGData",
    "GyroData",
    "MeasurementSettings",
    "SensorData",
    "PmdDataFrame",
]
