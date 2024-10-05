import asyncio
import signal
import threading
import numpy
from typing import Union
from bleak import BleakScanner
from rich.console import Console
from rich import inspect

from polar_python import (
    PolarDevice,
    MeasurementSettings,
    SettingType,
    ECGData,
    ACCData,
    HRData,
)

console = Console()

exit_event = threading.Event()


def handle_exit(signum, frame):
    console.print("[bold red]Received exit signal[/bold red]")

    numpy.save("ecg_data.npy", ecg_data_list)
    exit_event.set()


ecg_data_list = []


def heartrate_callback(data: HRData):
    console.print(f"[bold green]Received Data:[/bold green] {data}")


def data_callback(data: Union[ECGData, ACCData]):
    console.print(f"[bold green]Received Data:[/bold green] {data}")
    if isinstance(data, ECGData):
        ecg_data_list.extend(data.data)


async def main():
    device = await BleakScanner.find_device_by_filter(
        lambda bd, ad: bd.name and "Polar H10" in bd.name, timeout=5
    )
    if device is None:
        console.print("[bold red]Device not found[/bold red]")
        return

    inspect(device)

    async with PolarDevice(device) as polar_device:
        available_features = await polar_device.available_features()
        inspect(available_features)

        for feature in available_features:
            settings = await polar_device.request_stream_settings(feature)
            console.print(f"[bold blue]Settings for {feature}:[/bold blue] {settings}")

        ecg_settings = MeasurementSettings(
            measurement_type="ECG",
            settings=[
                SettingType(type="SAMPLE_RATE", array_length=1, values=[130]),
                SettingType(type="RESOLUTION", array_length=1, values=[14]),
            ],
        )

        acc_settings = MeasurementSettings(
            measurement_type="ACC",
            settings=[
                SettingType(type="SAMPLE_RATE", array_length=1, values=[25]),
                SettingType(type="RESOLUTION", array_length=1, values=[16]),
                SettingType(type="RANGE", array_length=1, values=[2]),
            ],
        )

        polar_device.set_callback(data_callback, heartrate_callback)

        await polar_device.start_stream(ecg_settings)
        await polar_device.start_stream(acc_settings)

        await polar_device.start_heartrate_stream()

        while not exit_event.is_set():
            await asyncio.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        console.print("[bold red]Program exited gracefully[/bold red]")
