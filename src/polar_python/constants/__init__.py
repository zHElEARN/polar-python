from typing import Final

from .pmd_control_operation_code import PmdControlOperationCode
from .pmd_control_point_error_code import PmdControlPointErrorCode
from .pmd_measurement_type import PmdMeasurementType
from .pmd_setting_type import PmdSettingType
from .polar_characteristic import PolarCharacteristic

# Epoch offset for Polar device timestamps (Jan 1, 2000)
TIMESTAMP_OFFSET: Final[int] = 946684800000000000

__all__ = [
    "PmdControlOperationCode",
    "PmdControlPointErrorCode",
    "PmdMeasurementType",
    "PmdSettingType",
    "PolarCharacteristic",
    "TIMESTAMP_OFFSET",
]
