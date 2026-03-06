from dataclasses import dataclass

from ..constants import (
    PmdControlOperationCode,
    PmdControlPointErrorCode,
    PmdMeasurementType,
    PmdSettingType,
)


@dataclass
class MeasurementSettings:
    """Represents measurement settings for a specific type."""

    @dataclass
    class SettingType:
        """Represents a setting type with its array length and possible values."""

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
