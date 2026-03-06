import asyncio
import signal
import threading

from bleak import BleakScanner
from rich import inspect
from rich.console import Console

from polar_python import PolarDevice
from polar_python.models import ACCData, GyroData, HRData, MAGData, PPGData, PPIData

console = Console()
exit_event = threading.Event()


def handle_exit(*_):
    console.print("[bold red]Received exit signal[/bold red]")
    exit_event.set()


async def main():
    device = await BleakScanner.find_device_by_filter(lambda bd, ad: bd.name is not None and "Polar Sense" in bd.name, timeout=5)
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

        def acc_callback(data: ACCData):
            console.print(f"[bold green]Received ACC Data:[/bold green] {data}")

        def ppi_callback(data: PPIData):
            console.print(f"[bold green]Received PPI Data:[/bold green] {data}")

        def ppg_callback(data: PPGData):
            console.print(f"[bold green]Received PPG Data:[/bold green] {data}")

        def gyro_callback(data: GyroData):
            console.print(f"[bold green]Received Gyro Data:[/bold green] {data}")

        def mag_callback(data: MAGData):
            console.print(f"[bold green]Received MAG Data:[/bold green] {data}")

        def hr_callback(data: HRData):
            console.print(f"[bold green]Received HR Data:[/bold green] {data}")

        await polar_device.start_acc_stream(acc_callback=acc_callback, sample_rate=52, resolution=16, range=8, channels=3)
        await polar_device.start_ppi_stream(ppi_callback=ppi_callback)
        await polar_device.start_ppg_stream(ppg_callback=ppg_callback, sample_rate=55, resolution=22, channels=4)
        await polar_device.start_gyro_stream(gyro_callback=gyro_callback, sample_rate=52, resolution=16, range=2000, channels=3)
        await polar_device.start_mag_stream(mag_callback=mag_callback, sample_rate=20, resolution=16, range=50, channels=3)
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
