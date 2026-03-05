from typing import TypeAlias

from .acc_data import ACCData
from .ecg_data import ECGData
from .hr_data import HRData
from .measurement_settings import MeasurementSettings
from .ppi_data import PPIData

SensorData: TypeAlias = ECGData | ACCData | PPIData

__all__ = [
    "ACCData",
    "ECGData",
    "HRData",
    "PPIData",
    "MeasurementSettings",
    "SensorData",
]
