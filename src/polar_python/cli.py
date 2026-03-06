import asyncio
import importlib.util
import sys
from contextlib import asynccontextmanager

from bleak import BleakScanner

from . import PolarDevice
from .models import ACCData, ECGData, GyroData, HRData, MAGData, PPGData, PPIData


def check_dependencies():
    missing = []
    for dep in ["questionary", "rich"]:
        if importlib.util.find_spec(dep) is None:
            missing.append(dep)

    if missing:
        print(f"Error: Missing optional dependencies: {', '.join(missing)}")
        print("To use the CLI tool, please install the library with 'cli' extras:")
        print('pip install "polar-python[cli]"')
        sys.exit(1)


check_dependencies()

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
exit_event = asyncio.Event()


def ecg_callback(data: ECGData):
    console.print(f"[bold green]ECG:[/bold green] {data}")


def acc_callback(data: ACCData):
    console.print(f"[bold green]ACC:[/bold green] {data}")


def ppi_callback(data: PPIData):
    console.print(f"[bold green]PPI:[/bold green] {data}")


def ppg_callback(data: PPGData):
    console.print(f"[bold green]PPG:[/bold green] {data}")


def gyro_callback(data: GyroData):
    console.print(f"[bold green]GYRO:[/bold green] {data}")


def mag_callback(data: MAGData):
    console.print(f"[bold green]MAG:[/bold green] {data}")


def hr_callback(data: HRData):
    console.print(f"[bold green]HR:[/bold green] {data}")


@asynccontextmanager
async def get_connected_device(device):
    pd = PolarDevice(device)
    with console.status(f"[bold yellow]Connecting to [bold white]{device.name}[/bold white]...[/bold yellow]", spinner="dots"):
        await pd.connect()
    try:
        console.print(f"[bold green]Successfully connected to {device.name}.[/bold green]\n")
        yield pd
    finally:
        with console.status(f"[bold yellow]Disconnecting from [bold white]{device.name}[/bold white]...[/bold yellow]", spinner="dots"):
            await pd.disconnect()
        console.print(f"[bold green]Disconnected from {device.name}.[/bold green]")


async def main():
    with console.status("[bold yellow]Searching for Polar devices...[/bold yellow]", spinner="dots"):
        devices = await BleakScanner.discover()

    polar_devices = [d for d in devices if d.name and "polar" in d.name.lower()]

    if not polar_devices:
        console.print("[bold red]No Polar devices found.[/bold red]")
        return

    choices = [f"{d.name} ({d.address})" for d in polar_devices]
    console.print(f"[bold green]Found {len(polar_devices)} Polar device(s).[/bold green]\n")

    selected_choice = await questionary.select(
        "Please select the Polar device you want to connect to:",
        choices=choices,
    ).ask_async()

    if not selected_choice:
        console.print("\n[bold yellow]Selection cancelled by user.[/bold yellow]")
        return

    selected_device = next(d for d in polar_devices if f"{d.name} ({d.address})" == selected_choice)
    console.print()
    console.print(Panel(f"[bold green]Selected:[/bold green] [bold white]{selected_device.name}[/bold white]\n[bold cyan]Address:[/bold cyan] {selected_device.address}", title="Connecting", border_style="green", expand=False))

    async with get_connected_device(selected_device) as polar_device:
        with console.status("[bold yellow]Fetching device features and settings...[/bold yellow]", spinner="dots"):
            available_features = await polar_device.get_available_features()

            table = Table(title="Available Stream Settings", show_header=True, header_style="bold magenta", show_lines=True)
            table.add_column("Feature ID", justify="center", style="dim")
            table.add_column("Measurement Type", justify="center", style="bold")
            table.add_column("Supported Parameters", style="green")

            for feature in available_features:
                settings = await polar_device.request_stream_settings(feature)

                params_str_list = []
                for s in settings.settings:
                    s_values = ", ".join(map(str, s.values))
                    params_str_list.append(f"{s.type.name}: [{s_values}]")

                params_display = " | ".join(params_str_list) if params_str_list else "[dim]No configurable parameters[/dim]"
                table.add_row(str(feature.value), feature.name, params_display)

        console.print(table)

        selected_features = await questionary.checkbox("Select Measurement Types to configure:", choices=[f.name for f in available_features]).ask_async()

        if not selected_features:
            console.print("\n[bold yellow]No features selected for configuration.[/bold yellow]")
            return

        user_configs = []
        for feature_name in selected_features:
            feature = next(f for f in available_features if f.name == feature_name)
            current_settings = await polar_device.request_stream_settings(feature)

            selected_params = []
            if current_settings.settings:
                console.print(f"\n[bold yellow]Configuring {feature_name}:[/bold yellow]")
                for s in current_settings.settings:
                    param_choices = [str(v) for v in s.values]
                    if len(param_choices) > 1:
                        val = await questionary.select(f"  Select {s.type.name} for {feature_name}:", choices=param_choices).ask_async()
                    else:
                        val = param_choices[0]
                        console.print(f"  [dim]{s.type.name} automatically set to {val}[/dim]")

                    selected_params.append({"name": s.type.name, "value": val})

            user_configs.append({"type": feature_name, "params": selected_params})

        summary_table = Table(title="Final Configuration Summary", border_style="green", show_lines=True)
        summary_table.add_column("Measurement Type", justify="center", style="bold")
        summary_table.add_column("Selected Settings", style="cyan")

        for config in user_configs:
            type_name = str(config["type"])
            params_display = " | ".join([f"{p['name']}: {p['value']}" for p in config["params"]]) or "[dim]No parameters[/dim]"
            summary_table.add_row(type_name, params_display)

        console.print("\n")
        console.print(summary_table)

        for config in user_configs:
            f_type = str(config["type"])
            params = {str(p["name"]).lower(): int(p["value"]) for p in config["params"]}

            if f_type == "ECG":
                await polar_device.start_ecg_stream(ecg_callback=ecg_callback, **params)
            elif f_type == "ACC":
                await polar_device.start_acc_stream(acc_callback=acc_callback, **params)
            elif f_type == "PPI":
                await polar_device.start_ppi_stream(ppi_callback=ppi_callback, **params)
            elif f_type == "PPG":
                await polar_device.start_ppg_stream(ppg_callback=ppg_callback, **params)
            elif f_type == "GYRO":
                await polar_device.start_gyro_stream(gyro_callback=gyro_callback, **params)
            elif f_type == "MAG":
                await polar_device.start_mag_stream(mag_callback=mag_callback, **params)
            elif f_type == "HR":
                await polar_device.start_hr_stream(hr_callback=hr_callback, **params)

        console.print("\n[bold cyan]Streaming started. Press Ctrl+C to stop.[/bold cyan]\n")

        await exit_event.wait()

        console.print("\n[bold green]Scan and configuration test completed successfully.[/bold green]")


def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Process interrupted.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    run()
