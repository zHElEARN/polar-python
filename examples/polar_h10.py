import asyncio
import signal
import threading

from bleak import BleakScanner
from rich import inspect
from rich.console import Console

from polar_python import PolarDevice
from polar_python.models import ACCData, ECGData, HRData

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

        def ecg_callback(data: ECGData):
            console.print(f"[bold green]Received ECG Data:[/bold green] {data}")

        def acc_callback(data: ACCData):
            console.print(f"[bold green]Received ACC Data:[/bold green] {data}")

        def hr_callback(data: HRData):
            console.print(f"[bold green]Received HR Data:[/bold green] {data}")

        await polar_device.start_ecg_stream(sample_rate=130, resolution=14, ecg_callback=ecg_callback)
        await polar_device.start_acc_stream(sample_rate=25, resolution=16, range=2, acc_callback=acc_callback)
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
