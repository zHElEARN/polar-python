import asyncio
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from typing import Union, Callable, List

from . import constants, exceptions, utils


class PolarDevice:
    def __init__(
        self,
        address_or_ble_device: Union[str, BLEDevice],
        data_callback: Callable[
            [Union[constants.ECGData, constants.ACCData]], None
        ] = None,
        heartrate_callback: Callable[[constants.HRData], None] = None,
    ) -> None:
        """
        Initialize the PolarDevice with a BLE address or device.

        :param address_or_ble_device: The address or BLEDevice instance of the Polar device.
        :param data_callback: Callback function to handle data streams.
        :param heartrate_callback: Callback function to handle heart rate data.
        """
        self.client = BleakClient(address_or_ble_device)
        self._queue_pmd_control = asyncio.Queue()
        self._data_callback = data_callback
        self._heartrate_callback = heartrate_callback

    async def connect(self) -> None:
        """Connect to the Polar device."""
        try:
            await self.client.connect()
            await self.client.start_notify(
                constants.PMD_CONTROL_POINT_UUID, self._handle_pmd_control
            )
            await self.client.start_notify(
                constants.PMD_DATA_UUID, self._handle_pmd_data
            )
        except Exception as e:
            raise exceptions.ConnectionError(
                f"Failed to connect to the Polar device: {str(e)}"
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from the Polar device."""
        try:
            await self.client.disconnect()
        except Exception as e:
            raise exceptions.DisconnectionError(
                f"Failed to disconnect from the Polar device: {str(e)}"
            ) from e

    async def __aenter__(self):
        """Support for async context management."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context management."""
        await self.disconnect()

    async def available_features(self) -> List[str]:
        """Retrieve available features from the Polar device."""
        try:
            data = await self.client.read_gatt_char(constants.PMD_CONTROL_POINT_UUID)
            if data[0] != 0x0F:
                raise exceptions.ControlPointResponseError(
                    "Unexpected response from the control point"
                )
            features = data[1]
            bitmap = utils.byte_to_bitmap(features)
            return [
                constants.PMD_MEASUREMENT_TYPES[int(index)]
                for index, bit in enumerate(bitmap)
                if bit
            ]
        except Exception as e:
            raise exceptions.ReadCharacteristicError(
                f"Failed to read available features: {str(e)}"
            ) from e

    async def request_stream_settings(
        self, measurement_type: str
    ) -> constants.MeasurementSettings:
        """Request stream settings for a specific measurement type."""
        try:
            await self.client.write_gatt_char(
                constants.PMD_CONTROL_POINT_UUID,
                bytearray(
                    [
                        constants.PMD_CONTROL_OPERATION_CODE["GET"],
                        constants.PMD_MEASUREMENT_TYPES.index(measurement_type),
                    ]
                ),
            )
            return utils.parse_pmd_data(await self._queue_pmd_control.get())
        except Exception as e:
            raise exceptions.StreamSettingsError(
                f"Failed to request stream settings for {measurement_type}: {str(e)}"
            ) from e

    async def start_stream(self, settings: constants.MeasurementSettings) -> None:
        """Start data stream with specified settings."""
        try:
            data = utils.build_measurement_settings(settings)
            await self.client.write_gatt_char(constants.PMD_CONTROL_POINT_UUID, data)
        except Exception as e:
            raise exceptions.WriteCharacteristicError(
                f"Failed to start stream with settings {settings}: {str(e)}"
            ) from e

    async def stop_stream(self, measurement_type: str) -> None:
        """Stop data stream for a specific measurement type."""
        try:
            await self.client.write_gatt_char(
                constants.PMD_CONTROL_POINT_UUID,
                bytearray(
                    [
                        constants.PMD_CONTROL_OPERATION_CODE["STOP"],
                        constants.PMD_MEASUREMENT_TYPES.index(measurement_type),
                    ]
                ),
            )
        except Exception as e:
            raise exceptions.WriteCharacteristicError(
                f"Failed to stop stream for {measurement_type}: {str(e)}"
            ) from e

    async def start_heartrate_stream(self) -> None:
        """Start heart rate data stream."""
        try:
            await self.client.start_notify(
                constants.HEART_RATE_CHAR_UUID, self._handle_heartrate_measurement
            )
        except Exception as e:
            raise exceptions.NotificationError(
                f"Failed to start heart rate stream: {str(e)}"
            ) from e

    async def stop_heartrate_stream(self) -> None:
        """Stop heart rate data stream."""
        try:
            await self.client.stop_notify(constants.HEART_RATE_CHAR_UUID)
        except Exception as e:
            raise exceptions.NotificationError(
                f"Failed to stop heart rate stream: {str(e)}"
            ) from e

    def set_callback(
        self,
        data_callback: Callable[
            [Union[constants.ECGData, constants.ACCData]], None
        ] = None,
        heartrate_callback: Callable[[constants.HRData], None] = None,
    ) -> None:
        self._data_callback = data_callback
        self._heartrate_callback = heartrate_callback

    def _handle_pmd_control(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle PMD control notifications."""
        self._queue_pmd_control.put_nowait(data)

    def _handle_pmd_data(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle PMD data notifications."""
        parsed_data = utils.parse_bluetooth_data(data)
        if self._data_callback:
            self._data_callback(parsed_data)

    def _handle_heartrate_measurement(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle heart rate measurement notifications."""
        parsed_data = utils.parse_heartrate_data(data)
        if self._heartrate_callback:
            self._heartrate_callback(parsed_data)
