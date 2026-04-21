import argparse
import asyncio
import json
from typing import Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import PolarDevice
from .constants import PmdMeasurementType
from .models import MeasurementSettings

console = Console()


async def scan(timeout: float, name_contains: str, as_json: bool) -> int:
    if as_json:
        devices: list[BLEDevice] = await BleakScanner.discover(timeout=timeout)
    else:
        with console.status("[bold yellow]Searching for Polar devices...[/bold yellow]", spinner="dots"):
            devices = await BleakScanner.discover(timeout=timeout)

    name_filter = name_contains.lower()
    polar_devices: list[BLEDevice] = [device for device in devices if device.name and name_filter in device.name.lower()]

    if not polar_devices:
        if not as_json:
            console.print(f"[bold red]No devices found matching '{name_contains}'.[/bold red]")
        return 0

    if as_json:
        for device in polar_devices:
            print(json.dumps({"name": device.name, "address": device.address}, ensure_ascii=False))
        return 0

    table = Table(title="Discovered Polar Devices", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="bold")
    table.add_column("Address", style="cyan")

    for device in polar_devices:
        table.add_row(device.name, device.address)

    console.print(f"[bold green]Found {len(polar_devices)} Polar device(s).[/bold green]\n")
    console.print(table)
    return 0


def _match_device(
    devices: list[BLEDevice],
    address: str | None,
    name: str | None,
    name_contains: str | None,
) -> BLEDevice | None:
    if address:
        return next((device for device in devices if device.address == address), None)

    if name:
        return next((device for device in devices if device.name == name), None)

    if name_contains:
        name_filter = name_contains.lower()
        return next((device for device in devices if device.name and name_filter in device.name.lower()), None)

    return None


async def inspect_device(
    address: str | None,
    name: str | None,
    name_contains: str | None,
    timeout: float,
    as_json: bool,
) -> int:
    if not any([address, name, name_contains]):
        console.print("[bold red]One of --address, --name, or --name-contains is required.[/bold red]")
        return 1

    if as_json:
        devices: list[BLEDevice] = await BleakScanner.discover(timeout=timeout)
    else:
        with console.status("[bold yellow]Searching for Polar devices...[/bold yellow]", spinner="dots"):
            devices = await BleakScanner.discover(timeout=timeout)

    selected_device = _match_device(devices, address=address, name=name, name_contains=name_contains)

    if not selected_device:
        if as_json:
            print(json.dumps({"error": "No matching device found."}, ensure_ascii=False))
        else:
            console.print("[bold red]No matching device found.[/bold red]")
        return 1

    polar_device = PolarDevice(selected_device)

    if as_json:
        await polar_device.connect()
    else:
        console.print()
        console.print(
            Panel(
                f"[bold green]Selected:[/bold green] [bold white]{selected_device.name}[/bold white]\n[bold cyan]Address:[/bold cyan] {selected_device.address}",
                title="Inspecting",
                border_style="green",
                expand=False,
            )
        )
        with console.status(f"[bold yellow]Connecting to [bold white]{selected_device.name}[/bold white]...[/bold yellow]", spinner="dots"):
            await polar_device.connect()

    try:
        if not as_json:
            console.print(f"[bold green]Successfully connected to {selected_device.name}.[/bold green]\n")
            with console.status("[bold yellow]Fetching device features and settings...[/bold yellow]", spinner="dots"):
                available_features: list[PmdMeasurementType] = await polar_device.get_available_features()
                settings_by_feature: list[tuple[PmdMeasurementType, MeasurementSettings]] = []
                for feature in available_features:
                    settings_by_feature.append((feature, await polar_device.request_stream_settings(feature)))
        else:
            available_features = await polar_device.get_available_features()
            settings_by_feature = []
            for feature in available_features:
                settings_by_feature.append((feature, await polar_device.request_stream_settings(feature)))

        if as_json:
            result: dict[str, Any] = {
                "name": selected_device.name,
                "address": selected_device.address,
                "features": [
                    {
                        "id": feature.value,
                        "name": feature.name,
                        "settings": {setting.type.name.lower(): setting.values for setting in settings.settings},
                    }
                    for feature, settings in settings_by_feature
                ],
            }
            print(json.dumps(result, ensure_ascii=False))
            return 0

        table = Table(title="Available Stream Settings", show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Feature ID", justify="center", style="dim")
        table.add_column("Measurement Type", justify="center", style="bold")
        table.add_column("Supported Parameters", style="green")

        for feature, settings in settings_by_feature:
            params_str_list: list[str] = []
            for setting in settings.settings:
                setting_values = ", ".join(map(str, setting.values))
                params_str_list.append(f"{setting.type.name}: [{setting_values}]")

            params_display = " | ".join(params_str_list) if params_str_list else "[dim]No configurable parameters[/dim]"
            table.add_row(str(feature.value), feature.name, params_display)

        console.print(table)
        return 0
    finally:
        if as_json:
            await polar_device.disconnect()
        else:
            with console.status(f"[bold yellow]Disconnecting from [bold white]{selected_device.name}[/bold white]...[/bold yellow]", spinner="dots"):
                await polar_device.disconnect()
            console.print(f"[bold green]Disconnected from {selected_device.name}.[/bold green]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m polar_python")
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Scan nearby Polar devices")
    scan_parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Scan timeout in seconds (default: 5.0)",
    )
    scan_parser.add_argument(
        "--name-contains",
        default="polar",
        help="Case-insensitive device name filter (default: polar)",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Output newline-delimited JSON instead of rich text",
    )

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a Polar device and list its stream settings")
    inspect_parser.add_argument("--address", help="Exact device address to inspect")
    inspect_parser.add_argument("--name", help="Exact device name to inspect")
    inspect_parser.add_argument("--name-contains", help="Case-insensitive device name filter; uses the first match")
    inspect_parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Scan timeout in seconds (default: 5.0)",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of rich text",
    )

    return parser


def run() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return asyncio.run(scan(timeout=args.timeout, name_contains=args.name_contains, as_json=args.json))
    if args.command == "inspect":
        return asyncio.run(
            inspect_device(
                address=args.address,
                name=args.name,
                name_contains=args.name_contains,
                timeout=args.timeout,
                as_json=args.json,
            )
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
