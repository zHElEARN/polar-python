import asyncio
import signal
import threading

from bleak import BleakScanner
from rich import inspect
from rich.console import Console

from polar_python import PolarDevice
from polar_python.models import ACCData, HRData

console = Console()
exit_event = threading.Event()


def handle_exit(*_):
    console.print("[bold red]Received exit signal[/bold red]")
    exit_event.set()


async def main():
    device = await BleakScanner.find_device_by_filter(lambda bd, ad: bd.name is not None and "Polar H10" in bd.name, timeout=5)
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

        # acc_settings = MeasurementSettings(
        #     measurement_type=PmdMeasurementType.ACC,
        #     settings=[
        #         MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[52]),
        #         MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[16]),
        #         MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[8]),
        #         MeasurementSettings.SettingType(type=PmdSettingType.CHANNELS, values=[3]),
        #     ],
        # )

        # ppi_settings = MeasurementSettings(measurement_type=PmdMeasurementType.PPI, settings=[])

        # ppg_settings = MeasurementSettings(
        #     measurement_type="PPG",
        #     settings=[
        #         SettingType(type="SAMPLE_RATE", values=[55]),
        #         SettingType(type="RESOLUTION", values=[22]),
        #         SettingType(type="CHANNELS", values=[4]),
        #     ],
        # )

        def acc_callback(data: ACCData):
            console.print(f"[bold green]Received ACC Data:[/bold green] {data}")

        def hr_callback(data: HRData):
            console.print(f"[bold green]Received HR Data:[/bold green] {data}")

        # await polar_device.start_stream(acc_settings)
        # await polar_device.start_stream(ppi_settings)
        # await polar_device.start_stream(ppg_settings)
        await polar_device.start_acc_stream(
            sample_rate=52,
            resolution=16,
            range=8,
            # channels=4,
            acc_callback=acc_callback,
        )
        await polar_device.start_hr_stream(hr_callback=hr_callback)

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
