"""PPG (Photoplethysmogram) data parsing functions."""

from typing import Sequence

from ..models import PPGData
from .compression import parse_delta_frames_all


def parse_ppg_data(data: bytearray, timestamp: int, frame_type: int, factor: float = 1.0) -> PPGData:
    """Parse PPG data from a list of integers based on frame type."""
    is_compressed = (frame_type & 0x80) != 0
    actual_frame_type = frame_type & 0x7F

    if is_compressed:
        return parse_compressed_ppg_data(data, timestamp, actual_frame_type, factor)
    else:
        return parse_raw_ppg_data(data, timestamp, actual_frame_type)


def parse_raw_ppg_data(data: bytearray, timestamp: int, frame_type: int) -> PPGData:
    """Parse raw (non-compressed) PPG data."""
    ppg_samples = []
    ppg_type = PPGData.PPGType.UNKNOWN

    if frame_type == 0:  # TYPE_0: 4 channels (3 PPG + 1 Ambient), 3 bytes each
        ppg_type = PPGData.PPGType.PPG3_AMBIENT1
        step = 3
        channels = 4
        for i in range(10, len(data), step * channels):
            if i + step * channels <= len(data):
                samples = []
                for c in range(channels):
                    val = int.from_bytes(data[i + c * step : i + (c + 1) * step], byteorder="little", signed=True)
                    samples.append(val)
                ppg_samples.append(samples)
    else:
        raise ValueError(f"Unsupported raw PPG frame type: {frame_type}")

    return PPGData(timestamp=timestamp, samples=ppg_samples, type=ppg_type)


def parse_compressed_ppg_data(data: Sequence[int], timestamp: int, frame_type: int, factor: float) -> PPGData:
    """Parse compressed PPG data."""
    ppg_samples = []
    ppg_type = PPGData.PPGType.UNKNOWN

    if frame_type == 0:
        ppg_type = PPGData.PPGType.PPG3_AMBIENT1
        channels = 4
        resolution_bits = 24
        samples = parse_delta_frames_all(data[10:], channels, resolution_bits, "signed_int")
        ppg_samples = samples
    else:
        raise ValueError(f"Unsupported compressed PPG frame type: {frame_type}")

    return PPGData(timestamp=timestamp, samples=ppg_samples, type=ppg_type)


def apply_factor(samples: list[list[int]], factor: float) -> list[list[int]]:
    if factor == 1.0:
        return samples
    return [[int(val * factor) for val in sample] for sample in samples]
