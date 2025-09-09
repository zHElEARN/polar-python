"""Data compression and decompression utilities."""

import math
from typing import List


def parse_delta_frames_all(
    data: List[int], channels: int, resolution: int, data_type: str
) -> List[List[int]]:
    """Parse delta frames similar to Java's parseDeltaFramesAll method."""
    if len(data) == 0:
        return []

    offset = 0
    ref_samples = parse_delta_frame_ref_samples(data, channels, resolution, data_type)
    offset += int(channels * math.ceil(resolution / 8.0))

    samples = [ref_samples]

    while offset < len(data):
        if offset + 2 > len(data):
            break

        delta_size = data[offset] & 0xFF
        offset += 1
        sample_count = data[offset] & 0xFF
        offset += 1

        bit_length = sample_count * delta_size * channels
        length = int(math.ceil(bit_length / 8.0))

        if offset + length > len(data):
            break

        delta_frame = data[offset : offset + length]
        delta_samples = parse_delta_frame(delta_frame, channels, delta_size)

        for delta in delta_samples:
            if len(delta) != channels:
                continue

            last_sample = samples[-1]
            next_samples = []
            for i in range(channels):
                sample = last_sample[i] + delta[i]
                next_samples.append(sample)
            samples.append(next_samples)

        offset += length

    return samples


def parse_delta_frame_ref_samples(
    data: List[int], channels: int, resolution: int, data_type: str
) -> List[int]:
    """Parse reference samples from delta frame data."""
    samples = []
    offset = 0
    resolution_in_bytes = int(math.ceil(resolution / 8.0))

    for _ in range(channels):
        if offset + resolution_in_bytes > len(data):
            break

        if data_type == "signed_int":
            sample = int.from_bytes(
                data[offset : offset + resolution_in_bytes],
                byteorder="little",
                signed=True,
            )
        else:
            sample = int.from_bytes(
                data[offset : offset + resolution_in_bytes],
                byteorder="little",
                signed=False,
            )

        offset += resolution_in_bytes
        samples.append(sample)

    return samples


def parse_delta_frame(
    data: List[int], channels: int, bit_width: int
) -> List[List[int]]:
    """Parse delta frame data into samples."""
    if len(data) == 0 or bit_width <= 0 or channels <= 0:
        return []

    bit_set = []
    for byte_val in data:
        for i in range(8):
            bit_set.append((byte_val >> i) & 1)

    samples = []
    offset = 0

    while offset + bit_width * channels <= len(bit_set):
        channel_samples = []
        for _ in range(channels):
            if offset + bit_width > len(bit_set):
                break

            value = 0
            for i in range(bit_width):
                if offset + i < len(bit_set):
                    value |= bit_set[offset + i] << i

            if bit_width > 1 and (value & (1 << (bit_width - 1))):
                value |= -1 << bit_width

            channel_samples.append(value)
            offset += bit_width

        if len(channel_samples) == channels:
            samples.append(channel_samples)

    return samples
