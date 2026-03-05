import asyncio
from typing import Callable, TypeAlias

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice

from . import exceptions, parsers
from .constants import PmdControlOperationCode, PmdMeasurementType, PolarCharacteristic
from .models import HRData, MeasurementSettings, SensorData


class PolarDevice:
    DataCallback: TypeAlias = Callable[[SensorData], None]
    HRCallback: TypeAlias = Callable[[HRData], None]

    _client: BleakClient
    _queue_pmd_control: asyncio.Queue
    _data_callback: DataCallback | None = None
    _hr_callback: HRCallback | None = None

    def __init__(self, address_or_ble_device: str | BLEDevice) -> None:
        """
        Initialize the PolarDevice with a BLE address or device.

        :param address_or_ble_device: The address or BLEDevice instance of the Polar device.
        """
        self._client = BleakClient(address_or_ble_device)
        self._queue_pmd_control = asyncio.Queue()

    async def connect(self) -> None:
        """Connect to the Polar device."""
        await self._client.connect()
        await self._client.start_notify(PolarCharacteristic.PMD_CONTROL_POINT.value, self._handle_pmd_control)
        await self._client.start_notify(PolarCharacteristic.PMD_DATA.value, self._handle_pmd_data)

    async def disconnect(self) -> None:
        """Disconnect from the Polar device."""
        await self._client.disconnect()

    async def __aenter__(self):
        """Support for async context management."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context management."""
        await self.disconnect()

    async def get_available_features(self) -> list[PmdMeasurementType]:
        """Retrieve available features from the Polar device."""
        data = await self._client.read_gatt_char(PolarCharacteristic.PMD_CONTROL_POINT.value)
        if data[0] != 0x0F:
            raise exceptions.ControlPointResponseError("Unexpected response from the control point")
        features = data[1]
        return [PmdMeasurementType(i) for i in range(8) if features & (1 << i)]

    async def request_stream_settings(self, measurement_type: PmdMeasurementType) -> MeasurementSettings:
        """Request stream settings for a specific measurement type."""
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.GET, measurement_type.value]),
        )
        return parsers.parse_pmd_data(await self._queue_pmd_control.get())

    async def start_stream(self, settings: MeasurementSettings) -> None:
        """Start data stream with specified settings."""
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            parsers.build_measurement_settings(settings),
        )

    async def stop_stream(self, measurement_type: PmdMeasurementType) -> None:
        """Stop data stream for a specific measurement type."""
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.STOP, measurement_type.value]),
        )

    async def start_heartrate_stream(self) -> None:
        """Start heart rate data stream."""
        await self._client.start_notify(
            PolarCharacteristic.HEART_RATE.value,
            self._handle_heartrate_measurement,
        )

    async def stop_heartrate_stream(self) -> None:
        """Stop heart rate data stream."""
        await self._client.stop_notify(PolarCharacteristic.HEART_RATE.value)

    def set_callback(
        self,
        data_callback: DataCallback | None = None,
        heartrate_callback: HRCallback | None = None,
    ) -> None:
        self._data_callback = data_callback
        self._hr_callback = heartrate_callback

    def _handle_pmd_control(self, sender: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle PMD control notifications."""
        self._queue_pmd_control.put_nowait(data)

    def _handle_pmd_data(self, sender: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle PMD data notifications."""
        parsed_data = parsers.parse_bluetooth_data(data)
        if self._data_callback and parsed_data:
            self._data_callback(parsed_data)

    def _handle_heartrate_measurement(self, sender: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle heart rate measurement notifications."""
        parsed_data = parsers.parse_heartrate_data(data)
        if self._hr_callback:
            self._hr_callback(parsed_data)
