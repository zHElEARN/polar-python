# polar-python

[![PyPI version](https://img.shields.io/pypi/v/polar-python.svg)](https://pypi.org/project/polar-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/polar-python.svg)](https://pypi.org/project/polar-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/zHElEARN/polar-python/actions/workflows/publish.yml/badge.svg)](https://github.com/zHElEARN/polar-python/actions)

`polar-python` is an asynchronous Python library designed for integration with Polar devices using Bluetooth Low Energy (BLE). Powered by the `bleak` library, `polar-python` abstracts the complexity of Polar's binary protocols, allowing developers to easily connect, configure, and stream real-time physiological and kinematic data directly into structured Python objects via callback functions. The codebase is fully type-hinted and passes strict static type checks. Additionally, all public functions and classes include comprehensive docstrings for better developer experience and IDE support.

> [!CAUTION]
> **Breaking Changes:** Current versions (1.x.x+) are **incompatible** with older `0.0.x` versions. The API has undergone significant architectural changes. New users can proceed normally; existing users should refer to the [examples](examples/) section to migrate their code.

## Supported Devices & Data Streams

Currently, `polar-python` has been tested and is guaranteed to work with **Polar H10** and **Polar Verity Sense**. Below are the supported data streams and their precise configuration limits for each device.

### Polar H10

The Polar H10 is a heart rate sensor that also provides electrocardiogram and kinematics data.

- Heart Rate (HR): Standard BLE heart rate stream with RR intervals.
- Electrocardiogram (ECG):
  - _Sample Rate_: 130 Hz
  - _Resolution_: 14 bit
- Accelerometer (ACC):
  - _Sample Rate_: 25, 50, 100, 200 Hz
  - _Resolution_: 16 bit
  - _Range_: 2, 4, 8 G

### Polar Verity Sense

The Polar Verity Sense is an optical heart rate sensor providing a wide array of optical and kinematic data.

- Heart Rate (HR): Standard BLE heart rate stream.
- Photoplethysmography (PPG):
  - _Sample Rate_: 55 Hz
  - _Resolution_: 22 bit
  - _Channels_: 4
- Peak-to-Peak Interval (PPI):
  - Requires no specific configuration. Streams raw PPI, error estimates, and calculated HR.
- Accelerometer (ACC):
  - _Sample Rate_: 52 Hz
  - _Resolution_: 16 bit
  - _Range_: 8 G
  - _Channels_: 3
- Gyroscope (Gyro):
  - _Sample Rate_: 52 Hz
  - _Resolution_: 16 bit
  - _Range_: 2000 dps (deg/s)
  - _Channels_: 3
- Magnetometer (MAG):
  - _Sample Rate_: 10, 20, 50, 100 Hz
  - _Resolution_: 16 bit
  - _Range_: 50 Gauss
  - _Channels_: 3

## Installation

You can install `polar-python` from PyPI using pip:

```sh
pip install polar-python
```

To use the interactive Command Line Interface (CLI) tool, install the extra dependencies:

```sh
pip install polar-python[cli]
```

## Usage

### Interactive CLI Tool

For a quick start or to test your hardware, use our built-in CLI tool. It will scan for nearby Polar devices, allow you to select one, inspect its supported measurement types, and configure/start data streams interactively.

```sh
python -m polar_python.cli
```

### Non-interactive CLI Tool

For scripting or automation, you can also use `python -m polar_python` directly:

```sh
python -m polar_python --help
```

The available subcommands are:

- `scan`: Scan nearby Polar devices.
- `inspect`: Inspect a device and list its available stream settings.
- `stream`: Start one or more streams. Repeat `--stream` to enable multiple streams, for example `--stream hr --stream ecg:sample_rate=130,resolution=14`.

All command-specific options can be viewed with `--help`, for example `python -m polar_python stream --help`.

Example:

```sh
python -m polar_python scan --json
{"name": "Polar H10 BA2B0B2D", "address": "24E7A9AB-A686-652D-A3C3-F3080DC4AA1E"}

python -m polar_python inspect --name "Polar H10 BA2B0B2D" --json
{"name": "Polar H10 BA2B0B2D", "address": "24E7A9AB-A686-652D-A3C3-F3080DC4AA1E", "features": [{"id": 0, "name": "ECG", "settings": {"sample_rate": [130], "resolution": [14]}}, {"id": 2, "name": "ACC", "settings": {"sample_rate": [25, 50, 100, 200], "resolution": [16], "range": [2, 4, 8]}}]}

python -m polar_python stream --name "Polar H10 BA2B0B2D" --stream hr --stream ecg:sample_rate=130,resolution=14 --json
{"event": "device_selected", "name": "Polar H10 BA2B0B2D", "address": "24E7A9AB-A686-652D-A3C3-F3080DC4AA1E"}
{"event": "stream_config", "streams": [{"type": "hr", "params": {}}, {"type": "ecg", "params": {"sample_rate": 130, "resolution": 14}}]}
{"type": "HR", "data": {"heartrate": 71, "rr_intervals": [877.9296875]}}
{"type": "ACC", "data": {"timestamp": 1546308138460820452, "data": [[-1004, -33, -226], [-1006, -29, -220], [-1007, -29, -215], [-1009, -26, -215], [-1010, -28, -214], [-1011, -24, -209], [-1011, -26, -214], [-1013, -25, -208], [-1013, -26, -207], [-1013, -28, -212], [-1012, -29, -210], [-1011, -36, -215], [-1009, -34, -219], [-1008, -42, -217], [-1007, -35, -218], [-1006, -35, -219], [-1005, -38, -221], [-1005, -36, -222], [-1005, -35, -221], [-1004, -29, -220], [-1004, -28, -221], [-1004, -28, -222], [-1003, -25, -220], [-1006, -24, -219], [-1007, -25, -219], [-1007, -23, -220], [-1008, -26, -220], [-1009, -22, -216], [-1010, -22, -220], [-1010, -27, -219], [-1010, -28, -213], [-1010, -30, -217], [-1011, -30, -213], [-1011, -32, -216], [-1011, -31, -215], [-1011, -32, -214]]}}
{"type": "ECG", "data": {"timestamp": 1546308139165379372, "data": [6769, 6722, 6680, 6633, 6579, 6524, 6480, 6440, 6378, 6306, 6264, 6227, 6165, 6100, 6058, 6011, 5969, 5924, 5865, 5806, 5761, 5711, 5659, 5615, 5568, 5523, 5476, 5409, 5345, 5290, 5243, 5211, 5169, 5117, 5075, 5047, 5013, 4961, 4901, 4842, 4792, 4752, 4708, 4658, 4609, 4562, 4517, 4472, 4420, 4371, 4353, 4420, 4641, 4973, 5146, 4730, 3875, 3615, 3999, 4004, 3781, 3848, 3885, 3774, 3746, 3761, 3714, 3672, 3657, 3632, 3603, 3580, 3558]}}
```

### Examples

Here is a minimal, self-contained example demonstrating the core workflow: scanning for a Polar H10 device, establishing a connection, and streaming real-time data using callbacks.

```python
import asyncio
from bleak import BleakScanner
from polar_python import PolarDevice
from polar_python.models import ACCData, ECGData, HRData

async def main():
    # 1. Find a Polar H10 device
    print("Scanning for Polar H10...")
    device = await BleakScanner.find_device_by_filter(lambda bd, ad: bd.name and "Polar H10" in bd.name, timeout=5)
    if not device:
        print("Device not found. Please ensure your Polar device is awake and nearby.")
        return
    print(f"Found {device.name}, connecting...")

    # 2. Connect and manage the device session
    async with PolarDevice(device) as polar_device:
        # 3. Define your callback functions
        def ecg_callback(data: ECGData):
            print(f"ECG Data: {data}")
        def acc_callback(data: ACCData):
            print(f"ACC Data: {data}")
        def hr_callback(data: HRData):
            print(f"HR Data: {data}")

        # 4. Start data streams with desired configurations
        await polar_device.start_ecg_stream(ecg_callback=ecg_callback, sample_rate=130, resolution=14)
        await polar_device.start_acc_stream(acc_callback=acc_callback, sample_rate=25, resolution=16, range=2)
        await polar_device.start_hr_stream(hr_callback=hr_callback)

        # 5. Keep the main loop running to receive data
        print("Streaming data for 10 seconds...")
        await asyncio.sleep(10)
if __name__ == "__main__":
    asyncio.run(main())
```

To understand how to integrate the library into your own scripts, please refer to the `examples/` directory in the repository. These files demonstrate the **complete usage** of the library, including connection management, custom configurations, and data handling:

- [`polar_h10.py`](examples/polar_h10.py): Detailed implementation for ECG, ACC, and HR streaming.
- [`polar_verity_sense.py`](examples/polar_verity_sense.py): Comprehensive usage of PPG, PPI, and IMU sensors.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome and highly encouraged! Whether you are fixing a bug, adding a new feature, or improving documentation, your help is appreciated.

- **Submit a Pull Request**: Feel free to fork the repository, make your changes, and submit a PR.
- **Report Issues**: If you encounter any bugs or have suggestions for improvements, please open an **Issue** to let us know.

We appreciate your support in making `polar-python` better!

## Acknowledgements

- [Bleak](https://github.com/hbldh/bleak) - BLE library for Python.
- [bleakheart](https://github.com/fsmeraldi/bleakheart) - For providing inspiration and valuable insights.
- [Polar BLE SDK](https://github.com/polarofficial/polar-ble-sdk) - For providing official BLE SDK and documentation for Polar devices.
