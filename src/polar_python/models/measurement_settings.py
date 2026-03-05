from dataclasses import dataclass

from ..constants import PmdControlPointErrorCode, PmdMeasurementType, PmdSettingType


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
