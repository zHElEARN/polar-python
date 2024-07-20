# polar-python

`polar-python` is a Python library designed for seamless integration with Polar devices using Bluetooth Low Energy (BLE) through the Bleak library. With `polar-python`, you can easily connect to Polar devices, query supported functionalities such as ECG, ACC, and PPG, explore configurable options and their possible values, and start data streaming to receive parsed binary data through callback functions.

## Features

-   **Connect to Polar Devices**: Use BLE to connect to Polar devices.
-   **Query Device Capabilities**: Discover supported functionalities like ECG, ACC, and PPG.
-   **Explore Configurable Options**: Query and set measurement settings for each feature.
-   **Stream Data**: Start data streaming and receive parsed binary data via callback functions.

## Installation

You can install `polar-python` from PyPI using pip:

```sh
pip install polar-python
```

## Usage

Below is an example of how to use `polar-python` to connect to a Polar device, query its features, set measurement settings, and start data streaming.

### Step 1: Import Libraries and Initialize Console

```python
import asyncio
from bleak import BleakScanner
from polar_python import PolarDevice, MeasurementSettings, SettingType, ECGData, ACCData
```

### Step 2: Define Data Callback Function

```python
def data_callback(data: Union[ECGData, ACCData]):
    """
    Callback function to handle incoming data from the Polar device.

    Args:
        data (Union[ECGData, ACCData]): The data received from the Polar device.
    """
```

### Step 3: Define Main Function to Connect to Polar Device

```python
async def main():
    """
    Main function to connect to a Polar device, query its features,
    set measurement settings, and start data streaming.
    """
    # Find the Polar H10 device
    device = await BleakScanner.find_device_by_filter(
        lambda bd, ad: bd.name and "Polar H10" in bd.name, timeout=5
    )
    if device is None:
        return
```

### Step 4: Connect to Polar Device and Query Features

```python
    # Establish connection to the Polar device
    async with PolarDevice(device, data_callback) as polar_device:
        # Query available features
        available_features = await polar_device.available_features()

        # Query and print stream settings for each feature
        for feature in available_features:
            settings = await polar_device.request_stream_settings(feature)
```

### Step 5: Define and Start Data Streams

```python
        # Define ECG measurement settings
        ecg_settings = MeasurementSettings(
            measurement_type="ECG",
            settings=[
                SettingType(type="SAMPLE_RATE", array_length=1, values=[130]),
                SettingType(type="RESOLUTION", array_length=1, values=[14]),
            ],
        )

        # Define ACC measurement settings
        acc_settings = MeasurementSettings(
            measurement_type="ACC",
            settings=[
                SettingType(type="SAMPLE_RATE", array_length=1, values=[25]),
                SettingType(type="RESOLUTION", array_length=1, values=[16]),
                SettingType(type="RANGE", array_length=1, values=[2]),
            ],
        )

        # Start data streams for ECG and ACC
        await polar_device.start_stream(ecg_settings)
        await polar_device.start_stream(acc_settings)

        # Keep the stream running for 120 seconds
        await asyncio.sleep(120)
```

### Step 6: Run the Main Function

```python
if __name__ == "__main__":
    asyncio.run(main())
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

-   [Bleak](https://github.com/hbldh/bleak) - BLE library for Python.
-   [Rich](https://github.com/Textualize/rich) - Python library for rich text and beautiful formatting in the terminal.
-   [bleakheart](https://github.com/fsmeraldi/bleakheart) - For providing inspiration and valuable insights.
-   [Polar BLE SDK](https://github.com/polarofficial/polar-ble-sdk) - For providing official BLE SDK and documentation for Polar devices.
