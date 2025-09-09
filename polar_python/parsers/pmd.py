"""PMD (Physical Measurement Data) parsing functions."""

from .. import constants


def parse_pmd_data(data: bytearray) -> constants.MeasurementSettings:
    """Parse PMD data from a bytearray."""
    try:
        measurement_type_index = data[2]
        error_code_index = data[3]
        more_frames = data[4] != 0

        measurement_type = (
            constants.PMD_MEASUREMENT_TYPES[measurement_type_index]
            if measurement_type_index < len(constants.PMD_MEASUREMENT_TYPES)
            else "UNKNOWN"
        )
        error_code = (
            constants.PMD_CONTROL_POINT_ERROR_CODES[error_code_index]
            if error_code_index < len(constants.PMD_CONTROL_POINT_ERROR_CODES)
            else "UNKNOWN"
        )

        settings = []
        index = 5
        while index < len(data):
            setting_type_index = data[index]
            setting_type = (
                constants.PMD_SETTING_TYPES[setting_type_index]
                if setting_type_index < len(constants.PMD_SETTING_TYPES)
                else "UNKNOWN"
            )
            array_length = data[index + 1]
            field_size = constants.PMD_SETTING_TYPES_TO_FIELD_SIZES.get(setting_type, 2)
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
                constants.SettingType(type=setting_type, values=setting_values)
            )
            index += 2 + field_size * array_length

        return constants.MeasurementSettings(
            measurement_type=measurement_type,
            error_code=error_code,
            more_frames=more_frames,
            settings=settings,
        )
    except IndexError as e:
        raise ValueError("Failed to parse PMD data: insufficient data length") from e


def build_measurement_settings(
    measurement_settings: constants.MeasurementSettings,
) -> bytearray:
    """Build a bytearray from measurement settings."""
    data = bytearray()
    data.append(constants.PMD_CONTROL_OPERATION_CODE["START"])

    measurement_type_index = constants.PMD_MEASUREMENT_TYPES.index(
        measurement_settings.measurement_type
    )
    data.append(measurement_type_index)

    for setting in measurement_settings.settings:
        setting_type_index = constants.PMD_SETTING_TYPES.index(setting.type)
        data.append(setting_type_index)
        data.append(setting.array_length)
        for value in setting.values:
            field_size = constants.PMD_SETTING_TYPES_TO_FIELD_SIZES.get(setting.type, 2)
            data.extend(value.to_bytes(field_size, "little"))

    return data
