import asyncio
import rich
from bleak import BleakScanner

from polar_python import PolarDevice, MeasurementSettings, SettingType


async def main():
    device = await BleakScanner.find_device_by_filter(lambda bd, _: "Polar H10" in bd.name, timeout=5)
    if device is None:
        rich.print("Device not found")
        return

    rich.inspect(device)

    async with PolarDevice(device) as polar_device:
        available_features = await polar_device.available_features()
        rich.inspect(available_features)

        for feature in available_features:
            rich.print(await polar_device.request_stream_settings(feature))

        ecg_settings = MeasurementSettings(
            measurement_type="ECG",
            settings=[SettingType(type="SAMPLE_RATE", array_length=1, values=[
                                  130]), SettingType(type="RESOLUTION", array_length=1, values=[14])]
        )
        
        await polar_device.start_stream(ecg_settings)

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
