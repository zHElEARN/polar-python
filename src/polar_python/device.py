import asyncio
import struct
from typing import Callable, TypeAlias

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice

from . import exceptions, parsers
from .constants import PmdControlOperationCode, PmdMeasurementType, PmdSettingType, PolarCharacteristic
from .models import ACCData, ECGData, GyroData, HRData, MAGData, MeasurementSettings, PPGData, PPIData


class PolarDevice:
    ECGCallback: TypeAlias = Callable[[ECGData], None]
    ACCCallback: TypeAlias = Callable[[ACCData], None]
    PPICallback: TypeAlias = Callable[[PPIData], None]
    PPGCallback: TypeAlias = Callable[[PPGData], None]
    GyroCallback: TypeAlias = Callable[[GyroData], None]
    MAGCallback: TypeAlias = Callable[[MAGData], None]
    HRCallback: TypeAlias = Callable[[HRData], None]

    _client: BleakClient
    _queue_pmd_control: asyncio.Queue
    _factors: dict[PmdMeasurementType, float]

    _ecg_callback: ECGCallback | None = None
    _acc_callback: ACCCallback | None = None
    _ppi_callback: PPICallback | None = None
    _ppg_callback: PPGCallback | None = None
    _gyro_callback: GyroCallback | None = None
    _mag_callback: MAGCallback | None = None
    _hr_callback: HRCallback | None = None

    def __init__(self, address_or_ble_device: str | BLEDevice) -> None:
        """
        Initialize the PolarDevice with a BLE address or device.

        :param address_or_ble_device: The address or BLEDevice instance of the Polar device.
        """
        self._client = BleakClient(address_or_ble_device)
        self._queue_pmd_control = asyncio.Queue()
        self._factors = {}

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
        return MeasurementSettings.from_bytes(await self._queue_pmd_control.get())

    async def start_stream(self, settings: MeasurementSettings) -> None:
        """Generic method to start a PMD stream and extract factor if present."""
        await self._client.write_gatt_char(PolarCharacteristic.PMD_CONTROL_POINT.value, settings.to_bytes())
        response = MeasurementSettings.from_bytes(await self._queue_pmd_control.get())
        for setting in response.settings:
            if setting.type == PmdSettingType.FACTOR and setting.values:
                raw_int_factor = setting.values[0]
                real_factor = struct.unpack("<f", struct.pack("<I", raw_int_factor))[0]
                self._factors[settings.measurement_type] = real_factor
                break

    async def stop_stream(self, measurement_type: PmdMeasurementType) -> None:
        """Generic method to stop a PMD stream and clean up its factor."""
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.STOP, measurement_type.value]),
        )
        self._factors.pop(measurement_type, None)

    async def start_ecg_stream(self, ecg_callback: ECGCallback, sample_rate: int, resolution: int) -> None:
        """Start ECG data stream."""
        self._ecg_callback = ecg_callback
        settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ECG,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
            ],
        )
        await self.start_stream(settings)

    async def stop_ecg_stream(self) -> None:
        """Stop ECG data stream."""
        self._ecg_callback = None
        await self.stop_stream(PmdMeasurementType.ECG)

    async def start_acc_stream(self, acc_callback: ACCCallback, sample_rate: int, resolution: int, range: int, channels: int | None = None) -> None:
        """Start ACC data stream."""
        self._acc_callback = acc_callback

        setting_list = [
            MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
            MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
            MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[range]),
        ]
        if channels is not None:
            setting_list.append(MeasurementSettings.SettingType(type=PmdSettingType.CHANNELS, values=[channels]))

        settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.ACC,
            settings=setting_list,
        )
        await self.start_stream(settings)

    async def stop_acc_stream(self) -> None:
        """Stop ACC data stream."""
        self._acc_callback = None
        await self.stop_stream(PmdMeasurementType.ACC)

    async def start_ppi_stream(self, ppi_callback: PPICallback) -> None:
        """Start PPI data stream."""
        self._ppi_callback = ppi_callback
        settings = MeasurementSettings(measurement_type=PmdMeasurementType.PPI, settings=[])
        await self.start_stream(settings)

    async def stop_ppi_stream(self) -> None:
        """Stop PPI data stream."""
        self._ppi_callback = None
        await self.stop_stream(PmdMeasurementType.PPI)

    async def start_ppg_stream(self, ppg_callback: PPGCallback, sample_rate: int, resolution: int, channels: int) -> None:
        """Start PPG data stream."""
        self._ppg_callback = ppg_callback
        settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.PPG,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
                MeasurementSettings.SettingType(type=PmdSettingType.CHANNELS, values=[channels]),
            ],
        )
        await self.start_stream(settings)

    async def stop_ppg_stream(self) -> None:
        """Stop PPG data stream."""
        self._ppg_callback = None
        await self.stop_stream(PmdMeasurementType.PPG)

    async def start_gyro_stream(self, gyro_callback: GyroCallback, sample_rate: int, resolution: int, range: int, channels: int) -> None:
        """Start Gyro data stream."""
        self._gyro_callback = gyro_callback
        settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.GYRO,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
                MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[range]),
                MeasurementSettings.SettingType(type=PmdSettingType.CHANNELS, values=[channels]),
            ],
        )
        await self.start_stream(settings)

    async def stop_gyro_stream(self) -> None:
        """Stop Gyro data stream."""
        self._gyro_callback = None
        await self.stop_stream(PmdMeasurementType.GYRO)

    async def start_mag_stream(self, mag_callback: MAGCallback, sample_rate: int, resolution: int, range: int, channels: int) -> None:
        """Start MAG data stream."""
        self._mag_callback = mag_callback
        settings = MeasurementSettings(
            measurement_type=PmdMeasurementType.MAG,
            settings=[
                MeasurementSettings.SettingType(type=PmdSettingType.SAMPLE_RATE, values=[sample_rate]),
                MeasurementSettings.SettingType(type=PmdSettingType.RESOLUTION, values=[resolution]),
                MeasurementSettings.SettingType(type=PmdSettingType.RANGE, values=[range]),
                MeasurementSettings.SettingType(type=PmdSettingType.CHANNELS, values=[channels]),
            ],
        )
        await self.start_stream(settings)

    async def stop_mag_stream(self) -> None:
        """Stop MAG data stream."""
        self._mag_callback = None
        await self.stop_stream(PmdMeasurementType.MAG)

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
        parsed_data = parsers.parse_polar_data(data, self._factors.get)

        if parsed_data is None:
            return
        match parsed_data:
            case ECGData() if self._ecg_callback:
                self._ecg_callback(parsed_data)
            case ACCData() if self._acc_callback:
                self._acc_callback(parsed_data)
            case PPIData() if self._ppi_callback:
                self._ppi_callback(parsed_data)
            case PPGData() if self._ppg_callback:
                self._ppg_callback(parsed_data)
            case GyroData() if self._gyro_callback:
                self._gyro_callback(parsed_data)
            case MAGData() if self._mag_callback:
                self._mag_callback(parsed_data)
            case _:
                return

    def _handle_hr_measurement(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Handle heart rate measurement notifications."""
        parsed_data = parsers.parse_hr_data(data)
        if self._hr_callback:
            self._hr_callback(parsed_data)
