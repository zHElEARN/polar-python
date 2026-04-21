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
    """A client to interface with Polar BLE devices.

    This class provides methods to connect to a Polar device, discover its available
    measurement features, and start/stop various data streams (e.g., ECG, ACC, HR)
    using asynchronous callbacks.

    Note:
        Currently, this library has only been tested on and is guaranteed to work
        with the **Polar H10** and **Polar Verity Sense** devices.
    """

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
        """Initializes the PolarDevice with a BLE address or device.

        Args:
            address_or_ble_device: The Bluetooth MAC address (str) or a discovered
                BLEDevice instance of the Polar device.
        """
        self._client = BleakClient(address_or_ble_device)
        self._queue_pmd_control = asyncio.Queue()
        self._factors = {}

    async def connect(self) -> None:
        """Connects to the Polar BLE device and sets up initial notifications.

        Establishes the Bluetooth connection and starts listening to the PMD control
        point and PMD data characteristics.
        """
        await self._client.connect()
        await self._client.start_notify(PolarCharacteristic.PMD_CONTROL_POINT.value, self._handle_pmd_control)
        await self._client.start_notify(PolarCharacteristic.PMD_DATA.value, self._handle_pmd_data)

    async def disconnect(self) -> None:
        """Disconnects from the Polar BLE device."""
        await self._client.disconnect()

    async def __aenter__(self):
        """Asynchronous context manager entry point.

        Returns:
            PolarDevice: The connected device instance.
        """
        await self.connect()
        return self

    async def __aexit__(self, _unused_exc_type, _unused_exc_val, _unused_exc_tb):
        """Asynchronous context manager exit point."""
        await self.disconnect()

    async def get_available_features(self) -> list[PmdMeasurementType]:
        """Retrieves the available measurement features from the Polar device.

        Queries the PMD control point to determine which sensor streams (e.g., ECG,
        ACC, PPG) are supported by the currently connected device.

        Returns:
            A list of supported PmdMeasurementType enums.

        Raises:
            exceptions.ControlPointResponseError: If the device returns an unexpected
                response format.
        """
        data = await self._client.read_gatt_char(PolarCharacteristic.PMD_CONTROL_POINT.value)
        if data[0] != 0x0F:
            raise exceptions.ControlPointResponseError("Unexpected response from the control point")
        features = data[1]
        return [PmdMeasurementType(i) for i in range(8) if features & (1 << i)]

    async def request_stream_settings(self, measurement_type: PmdMeasurementType) -> MeasurementSettings:
        """Requests the available stream settings for a specific measurement type.

        Args:
            measurement_type: The type of measurement (e.g., ECG, ACC) to query.

        Returns:
            The available measurement settings for the requested type.
        """
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.GET, measurement_type.value]),
        )
        return MeasurementSettings.from_bytes(await self._queue_pmd_control.get())

    async def start_stream(self, settings: MeasurementSettings) -> None:
        """Starts a generic PMD stream based on the provided settings.

        Writes the configuration to the device and extracts necessary calculation factors
        from the response if they are provided.

        Args:
            settings: The measurement settings configuration to apply.
        """
        await self._client.write_gatt_char(PolarCharacteristic.PMD_CONTROL_POINT.value, settings.to_bytes())
        response = MeasurementSettings.from_bytes(await self._queue_pmd_control.get())
        for setting in response.settings:
            if setting.type == PmdSettingType.FACTOR and setting.values:
                raw_int_factor = setting.values[0]
                real_factor = struct.unpack("<f", struct.pack("<I", raw_int_factor))[0]
                self._factors[settings.measurement_type] = real_factor
                break

    async def stop_stream(self, measurement_type: PmdMeasurementType) -> None:
        """Stops a generic PMD stream and cleans up its stored factors.

        Args:
            measurement_type: The type of measurement stream to stop.
        """
        await self._client.write_gatt_char(
            PolarCharacteristic.PMD_CONTROL_POINT.value,
            bytearray([PmdControlOperationCode.STOP, measurement_type.value]),
        )
        self._factors.pop(measurement_type, None)

    async def start_ecg_stream(self, ecg_callback: ECGCallback, sample_rate: int, resolution: int) -> None:
        """Starts the Electrocardiogram (ECG) data stream.

        Device Support:
            - Polar H10:
                - Supported `sample_rate`: 130
                - Supported `resolution`: 14

        Args:
            ecg_callback: A function to be called whenever new ECG data arrives.
            sample_rate: The desired sampling rate for the ECG stream.
            resolution: The data resolution setting.
        """
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
        """Stops the Electrocardiogram (ECG) data stream."""
        self._ecg_callback = None
        await self.stop_stream(PmdMeasurementType.ECG)

    async def start_acc_stream(self, acc_callback: ACCCallback, sample_rate: int, resolution: int, range: int, channels: int | None = None) -> None:
        """Starts the Accelerometer (ACC) data stream.

        Device Support:
            - Polar H10:
                - Supported `sample_rate`: 25, 50, 100, 200
                - Supported `resolution`: 16
                - Supported `range`: 2, 4, 8
                - Supported `channels`: Leave as None
            - Polar Verity Sense:
                - Supported `sample_rate`: 52
                - Supported `resolution`: 16
                - Supported `range`: 8
                - Supported `channels`: 3

        Args:
            acc_callback: A function to be called whenever new ACC data arrives.
            sample_rate: The desired sampling rate for the ACC stream.
            resolution: The data resolution setting.
            range: The measurement range of the accelerometer.
            channels: The number of channels to use. Defaults to None.
        """
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
        """Stops the Accelerometer (ACC) data stream."""
        self._acc_callback = None
        await self.stop_stream(PmdMeasurementType.ACC)

    async def start_ppi_stream(self, ppi_callback: PPICallback) -> None:
        """Starts the Peak-to-Peak Interval (PPI) data stream.

        Device Support:
            - Polar Verity Sense: No specific configuration is needed for PPI streams.

        Args:
            ppi_callback: A function to be called whenever new PPI data arrives.
        """
        self._ppi_callback = ppi_callback
        settings = MeasurementSettings(measurement_type=PmdMeasurementType.PPI, settings=[])
        await self.start_stream(settings)

    async def stop_ppi_stream(self) -> None:
        """Stops the Peak-to-Peak Interval (PPI) data stream."""
        self._ppi_callback = None
        await self.stop_stream(PmdMeasurementType.PPI)

    async def start_ppg_stream(self, ppg_callback: PPGCallback, sample_rate: int, resolution: int, channels: int) -> None:
        """Starts the Photoplethysmography (PPG) data stream.

        Device Support:
            - Polar Verity Sense:
                - Supported `sample_rate`: 55
                - Supported `resolution`: 22
                - Supported `channels`: 4

        Args:
            ppg_callback: A function to be called whenever new PPG data arrives.
            sample_rate: The desired sampling rate for the PPG stream.
            resolution: The data resolution setting.
            channels: The number of optical channels to capture.
        """
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
        """Stops the Photoplethysmography (PPG) data stream."""
        self._ppg_callback = None
        await self.stop_stream(PmdMeasurementType.PPG)

    async def start_gyro_stream(self, gyro_callback: GyroCallback, sample_rate: int, resolution: int, range: int, channels: int) -> None:
        """Starts the Gyroscope (Gyro) data stream.

        Device Support:
            - Polar Verity Sense:
                - Supported `sample_rate`: 52
                - Supported `resolution`: 16
                - Supported `range`: 2
                - Supported `channels`: 3

        Args:
            gyro_callback: A function to be called whenever new Gyro data arrives.
            sample_rate: The desired sampling rate for the Gyro stream.
            resolution: The data resolution setting.
            range: The measurement range of the gyroscope.
            channels: The number of channels to use.
        """
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
        """Stops the Gyroscope (Gyro) data stream."""
        self._gyro_callback = None
        await self.stop_stream(PmdMeasurementType.GYRO)

    async def start_mag_stream(self, mag_callback: MAGCallback, sample_rate: int, resolution: int, range: int, channels: int) -> None:
        """Starts the Magnetometer (MAG) data stream.

        Device Support:
            - Polar Verity Sense:
                - Supported `sample_rate`: 10, 20, 50, 100
                - Supported `resolution`: 16
                - Supported `range`: 50
                - Supported `channels`: 3

        Args:
            mag_callback: A function to be called whenever new MAG data arrives.
            sample_rate: The desired sampling rate for the MAG stream.
            resolution: The data resolution setting.
            range: The measurement range of the magnetometer.
            channels: The number of channels to use.
        """
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
        """Stops the Magnetometer (MAG) data stream."""
        self._mag_callback = None
        await self.stop_stream(PmdMeasurementType.MAG)

    async def start_hr_stream(self, hr_callback: HRCallback) -> None:
        """Starts the Heart Rate (HR) measurement stream.

        Unlike PMD streams, this subscribes to the standard Bluetooth Heart Rate profile.

        Args:
            hr_callback: A function to be called whenever new HR data arrives.
        """
        self._hr_callback = hr_callback
        await self._client.start_notify(
            PolarCharacteristic.HEART_RATE.value,
            self._handle_hr_measurement,
        )

    async def stop_hr_stream(self) -> None:
        """Stops the Heart Rate (HR) measurement stream."""
        self._hr_callback = None
        await self._client.stop_notify(PolarCharacteristic.HEART_RATE.value)

    def _handle_pmd_control(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Queue only PMD control point responses.

        On BlueZ, reading the PMD control point while notifications are enabled can
        also surface the feature packet as a notification. Those packets start with
        ``0x0F`` and must not be mixed into the control point response queue.
        """
        if not data or data[0] != 0xF0:
            return

        self._queue_pmd_control.put_nowait(data)

    def _handle_pmd_data(self, _: BleakGATTCharacteristic | int, data: bytearray) -> None:
        """Parses raw PMD data and dispatches it to the appropriate registered callback."""
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
        """Parses raw heart rate data and dispatches it to the registered callback."""
        parsed_data = parsers.parse_hr_data(data)
        if self._hr_callback:
            self._hr_callback(parsed_data)
