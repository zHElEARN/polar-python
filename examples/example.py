import asyncio
import rich
from bleak import BleakScanner
from typing import Union
from rich.console import Console

from polar_python import PolarDevice, MeasurementSettings, SettingType, ECGData, ACCData


async def main():
    device = await BleakScanner.find_device_by_filter(lambda bd, _: "Polar H10" in bd.name, timeout=5)
    if device is None:
        rich.print("Device not found")
        return

    rich.inspect(device)

    def data_callback(data: Union[ECGData, ACCData]):
        rich.print(f"{data}")

    async with PolarDevice(device, data_callback) as polar_device:
        available_features = await polar_device.available_features()
        rich.inspect(available_features)

        for feature in available_features:
            rich.print(await polar_device.request_stream_settings(feature))

        ecg_settings = MeasurementSettings(
            measurement_type="ECG",
            settings=[SettingType(type="SAMPLE_RATE", array_length=1, values=[
                                  130]), SettingType(type="RESOLUTION", array_length=1, values=[14])]
        )

        acc_settings = MeasurementSettings(
            measurement_type="ACC",
            settings=[SettingType(type="SAMPLE_RATE", array_length=1, values=[25]), SettingType(
                type="RESOLUTION", array_length=1, values=[16]), SettingType(type="RANGE", array_length=1, values=[2])]
        )

        await polar_device.start_stream(ecg_settings)
        await polar_device.start_stream(acc_settings)

        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
