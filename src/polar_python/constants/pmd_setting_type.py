from enum import IntEnum


class PmdSettingType(IntEnum):
    SAMPLE_RATE = 0
    RESOLUTION = 1
    RANGE = 2
    RANGE_MILLIUNIT = 3
    CHANNELS = 4
    FACTOR = 5
    SECURITY = 6
    UNKNOWN = 255

    @classmethod
    def _missing_(cls, _unused_value):
        return cls.UNKNOWN

    @property
    def field_size(self) -> int:
        """Get the field size in bytes for the setting type."""
        match self:
            case PmdSettingType.RANGE_MILLIUNIT | PmdSettingType.FACTOR:
                return 4
            case PmdSettingType.CHANNELS:
                return 1
            case PmdSettingType.SECURITY:
                return 16
            case PmdSettingType.SAMPLE_RATE | PmdSettingType.RESOLUTION | PmdSettingType.RANGE:
                return 2
            case _:
                return 2
