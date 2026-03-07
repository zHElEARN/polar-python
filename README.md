# polar-python

[![PyPI version](https://img.shields.io/pypi/v/polar-python.svg)](https://pypi.org/project/polar-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/polar-python.svg)](https://pypi.org/project/polar-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`polar-python` is an asynchronous Python library designed for integration with Polar devices using Bluetooth Low Energy (BLE). Powered by the `bleak` library, `polar-python` abstracts the complexity of Polar's binary protocols, allowing developers to easily connect, configure, and stream real-time physiological and kinematic data directly into structured Python objects via callback functions.

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

### Examples

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
