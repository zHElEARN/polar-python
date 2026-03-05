"""PMD (Physical Measurement Data) parsing functions."""

from ..constants import (
    PmdControlOperationCode,
    PmdControlPointErrorCode,
    PmdMeasurementType,
    PmdSettingType,
)
from ..models import MeasurementSettings


def parse_pmd_data(data: bytearray) -> MeasurementSettings:
    """Parse PMD data from a bytearray."""
    try:
        measurement_type_index = data[2]
        error_code_index = data[3]
        more_frames = data[4] != 0

        measurement_type = PmdMeasurementType(measurement_type_index).name
        error_code = PmdControlPointErrorCode(error_code_index)

        settings = []
        index = 5
        while index < len(data):
            setting_type_index = data[index]
            setting_type = PmdSettingType(setting_type_index)
            array_length = data[index + 1]
            field_size = setting_type.field_size
            setting_values = []
            for i in range(array_length):
                start_pos = index + 2 + i * field_size
                end_pos = start_pos + field_size
                if end_pos <= len(data):
                    if field_size == 1:
                        setting_values.append(data[start_pos])
                    else:
                        setting_values.append(
                            int.from_bytes(data[start_pos:end_pos], "little")
                        )
            settings.append(
                MeasurementSettings.SettingType(
                    type=setting_type, values=setting_values
                )
            )
            index += 2 + field_size * array_length

        return MeasurementSettings(
            measurement_type=measurement_type,
            error_code=error_code,
            more_frames=more_frames,
            settings=settings,
        )
    except IndexError as e:
        raise ValueError("Failed to parse PMD data: insufficient data length") from e


def build_measurement_settings(
    measurement_settings: MeasurementSettings,
) -> bytearray:
    """Build a bytearray from measurement settings."""
    data = bytearray()
    data.append(PmdControlOperationCode.START)

    measurement_type_index = measurement_settings.measurement_type.value
    data.append(measurement_type_index)

    for setting in measurement_settings.settings:
        setting_type_index = setting.type.value
        data.append(setting_type_index)
        data.append(setting.array_length)
        for value in setting.values:
            field_size = setting.type.field_size
            data.extend(value.to_bytes(field_size, "little"))

    return data
