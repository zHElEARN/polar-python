import argparse
import asyncio
import importlib.util
import json
import sys
from dataclasses import asdict
from typing import Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from . import PolarDevice
from .constants import PmdMeasurementType
from .models import ACCData, ECGData, GyroData, HRData, MAGData, MeasurementSettings, PPGData, PPIData


def check_dependencies() -> None:
    if importlib.util.find_spec("rich") is not None:
        return

    print("Error: Missing optional dependency: rich")
    print("To use the CLI tool, please install the library with 'cli' extras:")
    print('pip install "polar-python[cli]"')
    sys.exit(1)


check_dependencies()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


STREAM_TYPES: set[str] = {"ecg", "acc", "ppi", "ppg", "gyro", "mag", "hr"}
STREAM_OUTPUT_JSON: bool = False


def print_stream_json(stream_type: str, data: ECGData | ACCData | PPIData | PPGData | GyroData | MAGData | HRData) -> None:
    print(json.dumps({"type": stream_type, "data": asdict(data)}, ensure_ascii=False))


def ecg_callback(data: ECGData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("ECG", data)
    else:
        console.print(f"[bold green]ECG:[/bold green] {data}")


def acc_callback(data: ACCData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("ACC", data)
    else:
        console.print(f"[bold green]ACC:[/bold green] {data}")


def ppi_callback(data: PPIData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("PPI", data)
    else:
        console.print(f"[bold green]PPI:[/bold green] {data}")


def ppg_callback(data: PPGData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("PPG", data)
    else:
        console.print(f"[bold green]PPG:[/bold green] {data}")


def gyro_callback(data: GyroData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("GYRO", data)
    else:
        console.print(f"[bold green]GYRO:[/bold green] {data}")


def mag_callback(data: MAGData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("MAG", data)
    else:
        console.print(f"[bold green]MAG:[/bold green] {data}")


def hr_callback(data: HRData) -> None:
    if STREAM_OUTPUT_JSON:
        print_stream_json("HR", data)
    else:
        console.print(f"[bold green]HR:[/bold green] {data}")


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
        if as_json:
            print(json.dumps({"error": "One of --address, --name, or --name-contains is required."}, ensure_ascii=False))
        else:
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


def parse_stream_spec(spec: str) -> dict[str, Any]:
    stream_type_part, separator, params_part = spec.partition(":")
    stream_type = stream_type_part.strip().lower()

    if not stream_type:
        raise ValueError("Stream type cannot be empty.")
    if stream_type not in STREAM_TYPES:
        raise ValueError(f"Unsupported stream type: {stream_type}")

    params: dict[str, int] = {}
    if separator:
        if not params_part.strip():
            raise ValueError(f"Stream '{stream_type}' has an empty parameter list.")

        for raw_param in params_part.split(","):
            param = raw_param.strip()
            if not param:
                raise ValueError(f"Stream '{stream_type}' contains an empty parameter entry.")

            key, has_value, value = param.partition("=")
            param_name = key.strip().lower()
            raw_value = value.strip()

            if not has_value:
                raise ValueError(f"Stream '{stream_type}' parameter '{param}' must use key=value format.")
            if not param_name:
                raise ValueError(f"Stream '{stream_type}' contains a parameter with an empty name.")
            if param_name in params:
                raise ValueError(f"Stream '{stream_type}' contains duplicate parameter '{param_name}'.")

            try:
                params[param_name] = int(raw_value)
            except ValueError as exc:
                raise ValueError(f"Stream '{stream_type}' parameter '{param_name}' must be an integer.") from exc

    return {"type": stream_type, "params": params}


async def start_stream(polar_device: PolarDevice, stream_config: dict[str, Any]) -> None:
    stream_type = stream_config["type"]
    params: dict[str, int] = stream_config["params"]

    if stream_type == "ecg":
        await polar_device.start_ecg_stream(ecg_callback=ecg_callback, **params)
    elif stream_type == "acc":
        await polar_device.start_acc_stream(acc_callback=acc_callback, **params)
    elif stream_type == "ppi":
        await polar_device.start_ppi_stream(ppi_callback=ppi_callback)
    elif stream_type == "ppg":
        await polar_device.start_ppg_stream(ppg_callback=ppg_callback, **params)
    elif stream_type == "gyro":
        await polar_device.start_gyro_stream(gyro_callback=gyro_callback, **params)
    elif stream_type == "mag":
        await polar_device.start_mag_stream(mag_callback=mag_callback, **params)
    elif stream_type == "hr":
        await polar_device.start_hr_stream(hr_callback=hr_callback)


async def stream_device(
    address: str | None,
    name: str | None,
    name_contains: str | None,
    timeout: float,
    duration: int,
    stream_specs: list[str] | None,
    as_json: bool,
) -> int:
    global STREAM_OUTPUT_JSON
    STREAM_OUTPUT_JSON = as_json

    if not any([address, name, name_contains]):
        if as_json:
            print(json.dumps({"error": "One of --address, --name, or --name-contains is required."}, ensure_ascii=False))
        else:
            console.print("[bold red]One of --address, --name, or --name-contains is required.[/bold red]")
        return 1
    if not stream_specs:
        if as_json:
            print(json.dumps({"error": "At least one --stream option is required."}, ensure_ascii=False))
        else:
            console.print("[bold red]At least one --stream option is required.[/bold red]")
        return 1

    try:
        stream_configs = [parse_stream_spec(spec) for spec in stream_specs]
    except ValueError as exc:
        if as_json:
            print(json.dumps({"error": f"Invalid --stream: {exc}"}, ensure_ascii=False))
        else:
            console.print(f"[bold red]Invalid --stream:[/bold red] {exc}")
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

    if not as_json:
        console.print()
        console.print(
            Panel(
                f"[bold green]Selected:[/bold green] [bold white]{selected_device.name}[/bold white]\n[bold cyan]Address:[/bold cyan] {selected_device.address}",
                title="Streaming",
                border_style="green",
                expand=False,
            )
        )
    else:
        print(json.dumps({"event": "device_selected", "name": selected_device.name, "address": selected_device.address}, ensure_ascii=False))

    polar_device = PolarDevice(selected_device)
    if as_json:
        await polar_device.connect()
    else:
        with console.status(f"[bold yellow]Connecting to [bold white]{selected_device.name}[/bold white]...[/bold yellow]", spinner="dots"):
            await polar_device.connect()

    try:
        if as_json:
            print(json.dumps({"event": "connected", "name": selected_device.name, "address": selected_device.address}, ensure_ascii=False))
            print(json.dumps({"event": "stream_config", "streams": stream_configs}, ensure_ascii=False))
        else:
            console.print(f"[bold green]Successfully connected to {selected_device.name}.[/bold green]\n")

            summary_table = Table(title="Final Configuration Summary", border_style="green", show_lines=True)
            summary_table.add_column("Measurement Type", justify="center", style="bold")
            summary_table.add_column("Selected Settings", style="cyan")

            for config in stream_configs:
                params: dict[str, int] = config["params"]
                params_display = " | ".join([f"{name}: {value}" for name, value in params.items()]) or "[dim]No parameters[/dim]"
                summary_table.add_row(config["type"].upper(), params_display)

            console.print(summary_table)

        for config in stream_configs:
            await start_stream(polar_device, config)

        if duration == -1:
            if as_json:
                print(json.dumps({"event": "streaming_started", "duration": -1}, ensure_ascii=False))
            else:
                console.print("\n[bold cyan]Streaming started. Press Ctrl+C to stop.[/bold cyan]\n")
            await asyncio.Future()
        else:
            if as_json:
                print(json.dumps({"event": "streaming_started", "duration": duration}, ensure_ascii=False))
            else:
                console.print(f"\n[bold cyan]Streaming started. Running for {duration} second(s).[/bold cyan]\n")
            await asyncio.sleep(duration)

        if as_json:
            print(json.dumps({"event": "streaming_completed"}, ensure_ascii=False))
        else:
            console.print("\n[bold green]Streaming completed successfully.[/bold green]")
        return 0
    finally:
        STREAM_OUTPUT_JSON = False
        if as_json:
            await polar_device.disconnect()
            print(json.dumps({"event": "disconnected", "name": selected_device.name, "address": selected_device.address}, ensure_ascii=False))
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

    stream_parser = subparsers.add_parser("stream", help="Start one or more streams on a Polar device")
    stream_parser.add_argument("--address", help="Exact device address to stream from")
    stream_parser.add_argument("--name", help="Exact device name to stream from")
    stream_parser.add_argument("--name-contains", help="Case-insensitive device name filter; uses the first match")
    stream_parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Scan timeout in seconds (default: 5.0)",
    )
    stream_parser.add_argument(
        "--duration",
        type=int,
        default=-1,
        help="Stream duration in seconds; -1 means run until interrupted (default: -1)",
    )
    stream_parser.add_argument(
        "--stream",
        action="append",
        help="Stream spec like 'hr' or 'ecg:sample_rate=130,resolution=14'; repeat to start multiple streams",
    )
    stream_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON lines instead of rich text",
    )

    return parser


def run() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
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
        if args.command == "stream":
            return asyncio.run(
                stream_device(
                    address=args.address,
                    name=args.name,
                    name_contains=args.name_contains,
                    timeout=args.timeout,
                    duration=args.duration,
                    stream_specs=args.stream,
                    as_json=args.json,
                )
            )
    except KeyboardInterrupt:
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
