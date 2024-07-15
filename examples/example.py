import asyncio
import rich
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from polar_python import PolarDevice


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


if __name__ == "__main__":
    asyncio.run(main())
