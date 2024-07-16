import asyncio
from typing import Union
from bleak import BleakScanner
from rich.console import Console
from rich import inspect

from polar_python import PolarDevice, MeasurementSettings, SettingType, ECGData, ACCData

# Initialize Rich Console
console = Console()


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
        console.print("[bold red]Device not found[/bold red]")
        return

    # Inspect the device details
    inspect(device)

    def data_callback(data: Union[ECGData, ACCData]):
        """
        Callback function to handle incoming data from the Polar device.

        Args:
            data (Union[ECGData, ACCData]): The data received from the Polar device.
        """
        console.print(f"[bold green]Received Data:[/bold green] {data}")

    # Establish connection to the Polar device
    async with PolarDevice(device, data_callback) as polar_device:
        # Query available features
        available_features = await polar_device.available_features()
        inspect(available_features)

        # Query and print stream settings for each feature
        for feature in available_features:
            settings = await polar_device.request_stream_settings(feature)
            console.print(f"[bold blue]Settings for {feature}:[/bold blue] {settings}")

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

        # Keep the stream running for 60 seconds
        await asyncio.sleep(60)

        # Stop data stream for ECG
        await polar_device.stop_stream("ECG")

        # Keep the stream running for 60 seconds
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
