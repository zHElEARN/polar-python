from ..constants import PmdMeasurementType
from ..models import ACCData, ECGData, GyroData, PmdDataFrame, PPGData, PPIData, SensorData


def parse_polar_data(data: bytearray) -> SensorData | None:
    """Parse Polar data and return the appropriate data type."""
    data_frame = PmdDataFrame.from_bytes(data)

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
        case _:
            raise ValueError(f"Unsupported data type: {data_frame.measurement_type}, raw_data: {data}")
