import asyncio
from bleak import BleakClient, BleakScanner

PMD_CONTROL_POINT = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_MEASUREMENT_TYPES = ["ECG",  "PPG",
                         "ACC",  "PPI",  "RFU", "GYRO", "MAG"]
PMD_CONTROL_POINT_ERROR_CODES = [
    'SUCCESS',
    'ERROR INVALID OP CODE',
    'ERROR INVALID MEASUREMENT TYPE',
    'ERROR NOT SUPPORTED',
    'ERROR INVALID LENGTH',
    'ERROR INVALID PARAMETER',
    'ERROR ALREADY IN STATE',
    'ERROR INVALID RESOLUTION',
    'ERROR INVALID SAMPLE RATE',
    'ERROR INVALID RANGE',
    'ERROR INVALID MTU',
    'ERROR INVALID NUMBER OF CHANNELS',
    'ERROR INVALID STATE',
    'ERROR DEVICE IN CHARGER'
]
PMD_CONTROL_OPERATION_CODE = {"GET": 0x01, "START": 0x02, "STOP": 0x03}
PMD_SETTING_TYPES = ['SAMPLE_RATE', 'RESOLUTION', 'RANGE', 'RFU', 'CHANNELS']


pmd_control_event = asyncio.Event()
pmd_control_response = None


def byte_to_bitmap(byte):
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]
    return reversed_binary_string


def print_data(data):
    print(f"hex: {' '.join(f'{byte:02x}' for byte in data)}")
    print(f"dec: {list(data)}")
    print()


def parse_pmd_data(data):
    measurement_type_index = data[2]
    error_code_index = data[3]
    more_frames = data[4] != 0

    measurement_type = PMD_MEASUREMENT_TYPES[measurement_type_index] if measurement_type_index < len(
        PMD_MEASUREMENT_TYPES) else "UNKNOWN"
    error_code = PMD_CONTROL_POINT_ERROR_CODES[error_code_index] if error_code_index < len(
        PMD_CONTROL_POINT_ERROR_CODES) else "UNKNOWN"

    settings = []
    index = 5
    while index < len(data):
        setting_type_index = data[index]
        setting_type = PMD_SETTING_TYPES[setting_type_index] if setting_type_index < len(
            PMD_SETTING_TYPES) else "UNKNOWN"
        array_length = data[index + 1]
        setting_values = []
        for i in range(array_length):
            value = int.from_bytes(
                data[index + 2 + 2 * i:index + 4 + 2 * i], 'little')
            setting_values.append(value)
        settings.append({
            'type': setting_type,
            'array_length': array_length,
            'values': setting_values
        })
        index += 2 + 2 * array_length

    return {
        'measurement_type': measurement_type,
        'error_code': error_code,
        'more_frames': more_frames,
        'settings': settings
    }


def decode_ecg_data(data):
    if data[9] != 0x00:
        raise ValueError("Invalid ECG frame type")
    if (len(data)-10) % 3 != 0:
        raise ValueError("Bad ECG data frame length")
    microvolt = []
    for offset in range(10, len(data), 3):
        muv = int.from_bytes(data[offset:offset+3],
                             'little',
                             signed=True)
        microvolt.append(muv)
    return microvolt


def handle_pmd_control(sender, data):
    global pmd_control_response

    pmd_control_response = data
    pmd_control_event.set()


def handle_pmd_data(sender, data):
    print(decode_ecg_data(data))
    print_data(data)


async def main():
    device = await BleakScanner.find_device_by_filter(lambda bleDevice, advertisementData: "Polar H10" in bleDevice.name, timeout=5)
    if device is None:
        print("device is none")
        return

    print(device)

    async with BleakClient(device) as client:
        print(f"mtu_size: {client.mtu_size}")
        print(f"is_connected: {client.is_connected}")
        print()

        # read features from device
        print("read features from device")
        data = await client.read_gatt_char(PMD_CONTROL_POINT)
        print_data(data)

        features = data[1]
        print(f"feature bitmap({data[1]}): {byte_to_bitmap(features)}")

        support_features = []
        for index, bit in enumerate(byte_to_bitmap(features)):
            if bit == "1":
                support_features.append(PMD_MEASUREMENT_TYPES[int(index)])

        print(f"supported features: {support_features}")
        print()
        
        print(f"mtu_size: {client.mtu_size}")

        # request stream settings
        print("request stream settings")
        await client.start_notify(PMD_CONTROL_POINT, handle_pmd_control)
        for feature in support_features:
            pmd_control_event.clear()
            await client.write_gatt_char(PMD_CONTROL_POINT, bytearray([PMD_CONTROL_OPERATION_CODE["GET"], PMD_MEASUREMENT_TYPES.index(feature)]))
            await pmd_control_event.wait()
            print(parse_pmd_data(pmd_control_response))
            print_data(pmd_control_response)
            print()

        # start stream
        print("start stream")
        # start ecg stream
        await client.start_notify(PMD_DATA, handle_pmd_data)
        await client.write_gatt_char(PMD_CONTROL_POINT, bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0e, 0x00]))

        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())
