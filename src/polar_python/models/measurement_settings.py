from dataclasses import dataclass

from ..constants import PmdMeasurementType


@dataclass
class MeasurementSettings:
    """Represents measurement settings for a specific type."""

    @dataclass
    class SettingType:
        """Represents a setting type with its array length and possible values."""

        type: str
        values: list[int]

        @property
        def array_length(self) -> int:
            """Calculate array length from the values list."""
            return len(self.values)

    measurement_type: PmdMeasurementType
    settings: list[SettingType]
    error_code: str | None = None
    more_frames: bool | None = None
