from . import constants


def byte_to_bitmap(byte: int) -> list[bool]:
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]

    return [bit == '1' for bit in reversed_binary_string]


def parse_pmd_data(data: bytearray) -> constants.MeasurementSettings:
    measurement_type_index = data[2]
    error_code_index = data[3]
    more_frames = data[4] != 0

    measurement_type = constants.PMD_MEASUREMENT_TYPES[measurement_type_index] if measurement_type_index < len(
        constants.PMD_MEASUREMENT_TYPES) else "UNKNOWN"
    error_code = constants.PMD_CONTROL_POINT_ERROR_CODES[error_code_index] if error_code_index < len(
        constants.PMD_CONTROL_POINT_ERROR_CODES) else "UNKNOWN"

    settings = []
    index = 5
    while index < len(data):
        setting_type_index = data[index]
        setting_type = constants.PMD_SETTING_TYPES[setting_type_index] if setting_type_index < len(
            constants.PMD_SETTING_TYPES) else "UNKNOWN"
        array_length = data[index + 1]
        setting_values = []
        for i in range(array_length):
            value = int.from_bytes(
                data[index + 2 + 2 * i:index + 4 + 2 * i], 'little')
            setting_values.append(value)
        settings.append(constants.SettingType(
            type=setting_type,
            array_length=array_length,
            values=setting_values
        ))
        index += 2 + 2 * array_length

    return constants.MeasurementSettings(
        measurement_type=measurement_type,
        error_code=error_code,
        more_frames=more_frames,
        settings=settings
    )
