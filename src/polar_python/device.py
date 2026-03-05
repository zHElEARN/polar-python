import asyncio
from typing import Callable, TypeAlias

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice

from . import exceptions, parsers
from .constants import PmdControlOperationCode, PmdMeasurementType, PmdSettingType, PolarCharacteristic
from .models import ACCData, ECGData, HRData, MeasurementSettings


class PolarDevice:
    ECGCallback: TypeAlias = Callable[[ECGData], None]
    ACCCallback: TypeAlias = Callable[[ACCData], None]
    HRCallback: TypeAlias = Callable[[HRData], None]

    _client: BleakClient
    _queue_pmd_control: asyncio.Queue
    _ecg_callback: ECGCallback | None = None
    _acc_callback: ACCCallback | None = None
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

    async def start_ecg_stream(self, sample_rate: int, resolution: int, ecg_callback: ECGCallback) -> None:
        """Start ECG data stream."""
        ecg_settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ECG,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
            ],
        )
        self._ecg_callback = ecg_callback
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            parsers.build_measurement_settings(ecg_settings),
        )

    async def stop_ecg_stream(self) -> None:
        """Stop ECG data stream."""
        self._ecg_callback = None
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.STOP, PmdMeasurementType.ECG.value]),
        )

    async def start_acc_stream(self, sample_rate: int, resolution: int, range: int, acc_callback: ACCCallback) -> None:
        """Start ACC data stream."""
        acc_settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ACC,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
                MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[range]),
            ],
        )
        self._acc_callback = acc_callback
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            parsers.build_measurement_settings(acc_settings),
        )

    async def stop_acc_stream(self) -> None:
        """Stop ACC data stream."""
        self._acc_callback = None
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.STOP, PmdMeasurementType.ACC.value]),
        )

    async def start_hr_stream(self, hr_callback: HRCallback) -> None:
        """Start heart rate data stream."""
        self._hr_callback = hr_callback
        await self._client.start_notify(
            PolarCharacteristic.HEART_RATE.value,
            self._handle_hr_measurement,
        )

    async def stop_hr_stream(self) -> None:
        """Stop heart rate data stream."""
        self._hr_callback = None
        await self._client.stop_notify(PolarCharacteristic.HEART_RATE.value)

    def _handle_pmd_control(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle PMD control notifications."""
        self._queue_pmd_control.put_nowait(data)

    def _handle_pmd_data(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle PMD data notifications."""
        parsed_data = parsers.parse_bluetooth_data(data)

        if parsed_data is None:
            return
        match parsed_data:
            case ECGData() if self._ecg_callback:
                self._ecg_callback(parsed_data)
            case ACCData() if self._acc_callback:
                self._acc_callback(parsed_data)
            case _:
                return

    def _handle_hr_measurement(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle heart rate measurement notifications."""
        parsed_data = parsers.parse_hr_data(data)
        if self._hr_callback:
            self._hr_callback(parsed_data)
