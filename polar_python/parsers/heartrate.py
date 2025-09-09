"""Heart rate data parsing functions."""

from .. import constants


def parse_heartrate_data(data: bytearray) -> constants.HRData:
    """Parse heart rate data from a bytearray."""
    try:
        heartrate = int.from_bytes(data[1:2], byteorder="little", signed=False)
        rr_intervals = [
            int.from_bytes(data[i : i + 2], byteorder="little", signed=False)
            / 1024.0
            * 1000.0
            for i in range(2, len(data), 2)
        ]
        return constants.HRData(heartrate, rr_intervals)
    except IndexError as e:
        raise ValueError(
            "Failed to parse heart rate data: insufficient data length"
        ) from e
