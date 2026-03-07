from dataclasses import dataclass


@dataclass
class HRData:
    """Represents standard Bluetooth heart rate measurement data.

    Attributes:
        heartrate: The current heart rate in beats per minute (BPM).
        rr_intervals: A list of RR intervals in milliseconds (ms).
    """

    heartrate: int
    rr_intervals: list[float]
