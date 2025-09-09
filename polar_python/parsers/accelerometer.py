"""Accelerometer (ACC) data parsing functions."""

from typing import List
from .compression import parse_delta_frames_all


def parse_acc_data(
    data: List[int], timestamp: int, frame_type: int, factor: float = 1.0
) -> dict:
    """Parse accelerometer data from a list of integers based on frame type."""
    is_compressed = (frame_type & 0x80) != 0
    actual_frame_type = frame_type & 0x7F

    # print(f"Frame type: {frame_type}, Is compressed: {is_compressed}, Actual frame type: {actual_frame_type}")

    if is_compressed:
        return parse_compressed_acc_data(data, timestamp, actual_frame_type, factor)
    else:
        return parse_raw_acc_data(data, timestamp, actual_frame_type)


def parse_raw_acc_data(data: List[int], timestamp: int, frame_type: int) -> dict:
    """Parse raw (non-compressed) accelerometer data.

    For raw data, the device sends values in the correct units (milliG),
    so no factor conversion is needed.
    """
    acc_data = []

    if frame_type == 0x00:  # TYPE_0: 1 byte per axis
        step = 1
        channels = 3
        for i in range(10, len(data), step * channels):
            if i + step * channels <= len(data):
                x = int.from_bytes(data[i : i + step], byteorder="little", signed=True)
                y = int.from_bytes(
                    data[i + step : i + 2 * step], byteorder="little", signed=True
                )
                z = int.from_bytes(
                    data[i + 2 * step : i + 3 * step], byteorder="little", signed=True
                )
                acc_data.append((x, y, z))
    elif frame_type == 0x01:  # TYPE_1: 2 bytes per axis
        step = 2
        channels = 3
        for i in range(10, len(data), step * channels):
            if i + step * channels <= len(data):
                x = int.from_bytes(data[i : i + step], byteorder="little", signed=True)
                y = int.from_bytes(
                    data[i + step : i + 2 * step], byteorder="little", signed=True
                )
                z = int.from_bytes(
                    data[i + 2 * step : i + 3 * step], byteorder="little", signed=True
                )
                acc_data.append((x, y, z))
    elif frame_type == 0x02:  # TYPE_2: 3 bytes per axis
        step = 3
        channels = 3
        for i in range(10, len(data), step * channels):
            if i + step * channels <= len(data):
                x = int.from_bytes(data[i : i + step], byteorder="little", signed=True)
                y = int.from_bytes(
                    data[i + step : i + 2 * step], byteorder="little", signed=True
                )
                z = int.from_bytes(
                    data[i + 2 * step : i + 3 * step], byteorder="little", signed=True
                )
                acc_data.append((x, y, z))

    return {"timestamp": timestamp, "data": acc_data}


def parse_compressed_acc_data(
    data: List[int], timestamp: int, frame_type: int, factor: float
) -> dict:
    """Parse compressed accelerometer data."""
    if frame_type == 0x00:  # Compressed TYPE_0
        # type 0 data arrives in G units, convert to milliG
        acc_factor = factor * 1000
        samples = parse_delta_frames_all(data[10:], 3, 16, "signed_int")
        acc_data = [
            (
                int(sample[0] * acc_factor),
                int(sample[1] * acc_factor),
                int(sample[2] * acc_factor),
            )
            for sample in samples
        ]
    elif frame_type == 0x01:  # Compressed TYPE_1
        samples = parse_delta_frames_all(data[10:], 3, 16, "signed_int")
        acc_data = [
            (
                int(sample[0] * factor) if factor != 1.0 else sample[0],
                int(sample[1] * factor) if factor != 1.0 else sample[1],
                int(sample[2] * factor) if factor != 1.0 else sample[2],
            )
            for sample in samples
        ]
    else:
        raise ValueError(f"Unsupported compressed frame type: {frame_type}")

    return {"timestamp": timestamp, "data": acc_data}
