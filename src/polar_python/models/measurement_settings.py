from dataclasses import dataclass

from ..constants import (
    PmdControlOperationCode,
    PmdControlPointErrorCode,
    PmdMeasurementType,
    PmdSettingType,
)


@dataclass
class MeasurementSettings:
    """Represents the configuration settings for a PMD data stream.

    This data model is utilized for both sending configuration requests to the
    Polar device and parsing the subsequent response. Consequently, attributes
    like `error_code` and `more_frames` are typically only populated when this
    object is constructed from a device response.

    Attributes:
        measurement_type: The specific type of measurement stream (e.g., ECG, ACC).
        settings: A list of SettingType objects defining the stream's configuration.
        error_code: An optional error code returned by the device response.
        more_frames: An optional flag indicating if the device response spans multiple frames.
    """

    @dataclass
    class SettingType:
        """Represents an individual configuration setting and its values.

        Attributes:
            type: The specific setting being configured (e.g., sample rate, resolution).
            values: A list of integer values associated with this setting.
                When sending a configuration request to the device, this list typically
                contains only a single chosen value. However, when receiving available
                settings from the device, this list may contain one or multiple supported values.
        """

        type: PmdSettingType
        values: list[int]

        @property
        def array_length(self) -> int:
            """Calculate array length from the values list."""
            return len(self.values)

    measurement_type: PmdMeasurementType
    settings: list[SettingType]
    error_code: PmdControlPointErrorCode | None = None
    more_frames: bool | None = None

    @classmethod
    def from_bytes(cls, data: bytearray) -> "MeasurementSettings":
        """Parse PMD data from a bytearray (Response from device)."""
        measurement_type_index = data[2]
        error_code_index = data[3]
        more_frames = data[4] != 0

        measurement_type = PmdMeasurementType(measurement_type_index)
        error_code = PmdControlPointErrorCode(error_code_index)

        settings = []
        index = 5
        while index < len(data):
            if index + 1 >= len(data):
                break

            setting_type_index = data[index]
            setting_type = PmdSettingType(setting_type_index)
            if setting_type == PmdSettingType.UNKNOWN:
                break

            array_length = data[index + 1]
            field_size = setting_type.field_size

            if index + 2 + field_size * array_length > len(data):
                break

            setting_values = []
            for i in range(array_length):
                start_pos = index + 2 + i * field_size
                end_pos = start_pos + field_size
                if field_size == 1:
                    setting_values.append(data[start_pos])
                else:
                    setting_values.append(int.from_bytes(data[start_pos:end_pos], "little"))

            settings.append(cls.SettingType(type=setting_type, values=setting_values))
            index += 2 + field_size * array_length

        return cls(
            measurement_type=measurement_type,
            error_code=error_code,
            more_frames=more_frames,
            settings=settings,
        )

    def to_bytes(self) -> bytearray:
        """Build a bytearray from current measurement settings (Request to device)."""
        data = bytearray()
        data.append(PmdControlOperationCode.START)
        data.append(self.measurement_type.value)

        for setting in self.settings:
            data.append(setting.type.value)
            data.append(setting.array_length)
            for value in setting.values:
                field_size = setting.type.field_size
                data.extend(value.to_bytes(field_size, "little"))

        return data
