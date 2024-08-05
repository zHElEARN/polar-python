import asyncio
import signal
import threading
from typing import Union
from bleak import BleakScanner
from rich.console import Console
from rich import inspect

from polar_python import PolarDevice, MeasurementSettings, SettingType, ECGData, ACCData, HRData

# Initialize Rich Console
console = Console()

# Event to signal exit
exit_event = threading.Event()

def handle_exit(signum, frame):
    """
    Handle the exit signal to set the exit event.
    """
    console.print("[bold red]Received exit signal[/bold red]")
    exit_event.set()

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

    # Establish connection to the Polar device
    async with PolarDevice(device) as polar_device:
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

        def heartrate_callback(data: HRData):
            console.print(f"[bold green]Received Data:[/bold green] {data}")

        def data_callback(data: Union[ECGData, ACCData]):
            """
            Callback function to handle incoming data from the Polar device.

            Args:
                data (Union[ECGData, ACCData]): The data received from the Polar device.
            """
            console.print(f"[bold green]Received Data:[/bold green] {data}")

        polar_device.set_callback(data_callback, heartrate_callback)

        # Start data streams for ECG and ACC
        await polar_device.start_stream(ecg_settings)
        await polar_device.start_stream(acc_settings)

        # Start data stream for HeartRate
        await polar_device.start_heartrate_stream()

        # Keep the stream running indefinitely until exit_event is set
        while not exit_event.is_set():
            await asyncio.sleep(1)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Run the main function
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        console.print("[bold red]Program exited gracefully[/bold red]")
