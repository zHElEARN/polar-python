import asyncio

from bleak import BleakScanner
from rich import inspect
from rich.console import Console

from polar_python import PolarDevice
from polar_python.models import ACCData, ECGData, HRData

console = Console()


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

        await polar_device.start_ecg_stream(ecg_callback=ecg_callback, sample_rate=130, resolution=14)
        await polar_device.start_acc_stream(acc_callback=acc_callback, sample_rate=25, resolution=16, range=2)
        await polar_device.start_hr_stream(hr_callback=hr_callback)

        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]Received Ctrl+C[/bold red]")
    finally:
        console.print("[bold red]Program exited gracefully[/bold red]")
