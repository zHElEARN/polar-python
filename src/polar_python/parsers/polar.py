from ..constants import TIMESTAMP_OFFSET, PmdMeasurementType
from ..models import SensorData
from .acc import parse_acc_data
from .ecg import parse_ecg_data
from .ppi import parse_ppi_data


def parse_polar_data(data: bytearray) -> SensorData | None:
    """Parse Polar data and return the appropriate data type."""
    data_type_index = data[0]
    data_type = PmdMeasurementType(data_type_index)
    timestamp = int.from_bytes(data[1:9], byteorder="little") + TIMESTAMP_OFFSET
    frame_type = data[9]

    match data_type:
        case PmdMeasurementType.ECG:
            return parse_ecg_data(data, timestamp)
        case PmdMeasurementType.ACC:
            return parse_acc_data(data, timestamp, frame_type)
        case PmdMeasurementType.PPI:
            return parse_ppi_data(data, timestamp)
        case _:
            raise ValueError(f"Unsupported data type: {data_type}, {data}")
