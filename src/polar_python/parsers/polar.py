from typing import Callable

from ..constants import PmdMeasurementType
from ..models import ACCData, ECGData, GyroData, MAGData, PmdDataFrame, PPGData, PPIData, SensorData


def parse_polar_data(data: bytearray, get_factor_func: Callable[[PmdMeasurementType], float | None]) -> SensorData | None:
    """Parse Polar data and return the appropriate data type."""

    def safe_get_factor(measurement_type: PmdMeasurementType) -> float:
        factor = get_factor_func(measurement_type)
        return factor if factor is not None else 1.0

    data_frame = PmdDataFrame.from_bytes(data, safe_get_factor)

    match data_frame.measurement_type:
        case PmdMeasurementType.ECG:
            return ECGData.from_dataframe(data_frame)
        case PmdMeasurementType.ACC:
            return ACCData.from_dataframe(data_frame)
        case PmdMeasurementType.PPG:
            return PPGData.from_dataframe(data_frame)
        case PmdMeasurementType.PPI:
            return PPIData.from_dataframe(data_frame)
        case PmdMeasurementType.GYRO:
            return GyroData.from_dataframe(data_frame)
        case PmdMeasurementType.MAG:
            return MAGData.from_dataframe(data_frame)
        case _:
            raise ValueError(f"Unsupported data type: {data_frame.measurement_type}, raw_data: {data}")
