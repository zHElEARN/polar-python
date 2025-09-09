import math
from typing import List, Union
from . import constants


def byte_to_bitmap(byte: int) -> List[bool]:
    """Convert a byte to a bitmap (list of booleans)."""
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]
    return [bit == "1" for bit in reversed_binary_string]


def parse_pmd_data(data: bytearray) -> constants.MeasurementSettings:
    """Parse PMD data from a bytearray."""
    try:
        measurement_type_index = data[2]
        error_code_index = data[3]
        more_frames = data[4] != 0

        measurement_type = (
            constants.PMD_MEASUREMENT_TYPES[measurement_type_index]
            if measurement_type_index < len(constants.PMD_MEASUREMENT_TYPES)
            else "UNKNOWN"
        )
        error_code = (
            constants.PMD_CONTROL_POINT_ERROR_CODES[error_code_index]
            if error_code_index < len(constants.PMD_CONTROL_POINT_ERROR_CODES)
            else "UNKNOWN"
        )

        settings = []
        index = 5
        while index < len(data):
            setting_type_index = data[index]
            setting_type = (
                constants.PMD_SETTING_TYPES[setting_type_index]
                if setting_type_index < len(constants.PMD_SETTING_TYPES)
                else "UNKNOWN"
            )
            array_length = data[index + 1]
            field_size = constants.PMD_SETTING_TYPES_TO_FIELD_SIZES.get(setting_type, 2)
            setting_values = []
            for i in range(array_length):
                start_pos = index + 2 + i * field_size
                end_pos = start_pos + field_size
                if end_pos <= len(data):
                    if field_size == 1:
                        setting_values.append(data[start_pos])
                    else:
                        setting_values.append(
                            int.from_bytes(data[start_pos:end_pos], "little")
                        )
            settings.append(
                constants.SettingType(type=setting_type, values=setting_values)
            )
            index += 2 + field_size * array_length

        return constants.MeasurementSettings(
            measurement_type=measurement_type,
            error_code=error_code,
            more_frames=more_frames,
            settings=settings,
        )
    except IndexError as e:
        raise ValueError("Failed to parse PMD data: insufficient data length") from e


def build_measurement_settings(
    measurement_settings: constants.MeasurementSettings,
) -> bytearray:
    """Build a bytearray from measurement settings."""
    data = bytearray()
    data.append(constants.PMD_CONTROL_OPERATION_CODE["START"])

    measurement_type_index = constants.PMD_MEASUREMENT_TYPES.index(
        measurement_settings.measurement_type
    )
    data.append(measurement_type_index)

    for setting in measurement_settings.settings:
        setting_type_index = constants.PMD_SETTING_TYPES.index(setting.type)
        data.append(setting_type_index)
        data.append(setting.array_length)
        for value in setting.values:
            field_size = constants.PMD_SETTING_TYPES_TO_FIELD_SIZES.get(setting.type, 2)
            data.extend(value.to_bytes(field_size, "little"))

    return data


def parse_ecg_data(data: List[int], timestamp: int) -> constants.ECGData:
    """Parse ECG data from a list of integers."""
    ecg_data = [
        int.from_bytes(data[i : i + 3], byteorder="little", signed=True)
        for i in range(10, len(data), 3)
    ]
    return constants.ECGData(timestamp=timestamp, data=ecg_data)


import math
from typing import List


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


def parse_bluetooth_data(
    data: List[int],
) -> Union[constants.ECGData, constants.ACCData]:
    """Parse Bluetooth data and return the appropriate data type."""
    try:
        data_type_index = data[0]
        data_type = constants.PMD_MEASUREMENT_TYPES[data_type_index]
        timestamp = (
            int.from_bytes(data[1:9], byteorder="little") + constants.TIMESTAMP_OFFSET
        )
        frame_type = data[9]

        if data_type == "ECG":
            return parse_ecg_data(data, timestamp)
        elif data_type == "ACC":
            return parse_acc_data(data, timestamp, frame_type)
        elif data_type == "PPI":
            return parse_ppi_data(data, timestamp)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
    except IndexError as e:
        raise ValueError(
            "Failed to parse Bluetooth data: insufficient data length"
        ) from e


def parse_ppi_data(data: List[int], timestamp: int) -> constants.PPIData:
    """Parse PPI data from a list of integers."""
    ppi_samples = []
    offset = 10

    while offset + 6 <= len(data):
        sample = data[offset : offset + 6]

        hr = sample[0] & 0xFF
        ppi = int.from_bytes(sample[1:3], byteorder="little", signed=False)
        error_estimate = int.from_bytes(sample[3:5], byteorder="little", signed=False)
        status_byte = sample[5] & 0xFF

        invalid_ppi = (status_byte & 0x01) != 0
        skin_contact_status = (status_byte & 0x02) != 0
        skin_contact_supported = (status_byte & 0x04) != 0

        ppi_samples.append(
            {
                "ppi": ppi,
                "error_estimate": error_estimate,
                "hr": hr,
                "invalid_ppi": invalid_ppi,
                "skin_contact_status": skin_contact_status,
                "skin_contact_supported": skin_contact_supported,
            }
        )

        offset += 6

    samples = []
    if timestamp != 0:
        current_timestamp = timestamp

        for sample in reversed(ppi_samples):
            samples.append(
                constants.PPISample(
                    ppi=sample["ppi"],
                    error_estimate=sample["error_estimate"],
                    hr=sample["hr"],
                    invalid_ppi=sample["invalid_ppi"],
                    skin_contact_status=sample["skin_contact_status"],
                    skin_contact_supported=sample["skin_contact_supported"],
                    timestamp=current_timestamp,
                )
            )
            current_timestamp -= sample["ppi"] * 1_000_000

        samples.reverse()
    else:
        for sample in ppi_samples:
            samples.append(
                constants.PPISample(
                    ppi=sample["ppi"],
                    error_estimate=sample["error_estimate"],
                    hr=sample["hr"],
                    blocker_bit=sample["blocker_bit"],
                    skin_contact_status=sample["skin_contact_status"],
                    skin_contact_supported=sample["skin_contact_supported"],
                    timestamp=0,
                )
            )

    return constants.PPIData(samples=samples)


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
