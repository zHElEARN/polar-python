import asyncio
import signal
import threading

import numpy
from bleak import BleakScanner
from rich import inspect
from rich.console import Console

from polar_python import PolarDevice
from polar_python.constants import PmdMeasurementType, PmdSettingType
from polar_python.models import ACCData, ECGData, HRData, MeasurementSettings, PPIData

console = Console()

exit_event = threading.Event()


def handle_exit(signum, frame):
    console.print("[bold red]Received exit signal[/bold red]")

    numpy.save("ecg_data.npy", ecg_data_list)
    exit_event.set()


ecg_data_list = []


def heartrate_callback(data: HRData):
    console.print(f"[bold green]Received Data:[/bold green] {data}")


def data_callback(data: ECGData | ACCData | PPIData):
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
        available_features = await polar_device.get_available_features()
        inspect(available_features)

        for feature in available_features:
            settings = await polar_device.request_stream_settings(feature)
            console.print(f"[bold blue]Settings for {feature}:[/bold blue] {settings}")

        ecg_settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ECG,
            settings=[
                MeasurementSettings.SettingType(
                    type=PmdSettingType.SAMPLE_RATE, values=[130]
                ),
                MeasurementSettings.SettingType(
                    type=PmdSettingType.RESOLUTION, values=[14]
                ),
            ],
        )

        acc_settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ACC,
            settings=[
                MeasurementSettings.SettingType(
                    type=PmdSettingType.SAMPLE_RATE, values=[25]
                ),
                MeasurementSettings.SettingType(
                    type=PmdSettingType.RESOLUTION, values=[16]
                ),
                MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[2]),
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
