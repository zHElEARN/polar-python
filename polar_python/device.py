import asyncio
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from typing import Union, Callable

from . import constants, exceptions, utils


class PolarDevice:
    def __init__(self, address_or_ble_device: Union[str, BLEDevice], data_callback: Callable[[Union[constants.ECGData, constants.ACCData]], None] = None) -> None:
        self.client = BleakClient(address_or_ble_device)
        self._queue_pmd_control = asyncio.Queue()
        self._data_callback = data_callback

    async def connect(self) -> None:
        await self.client.connect()
        await self.client.start_notify(constants.PMD_CONTROL_POINT_UUID, self._handle_pmd_control)
        await self.client.start_notify(constants.PMD_DATA_UUID, self._handle_pmd_data)

    async def disconnect(self) -> None:
        await self.client.disconnect()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def available_features(self) -> list[str]:
        data = await self.client.read_gatt_char(constants.PMD_CONTROL_POINT_UUID)
        if data[0] != 0x0f:
            raise exceptions.ControlPointResponseError
        features= data[1]
        bitmap = utils.byte_to_bitmap(features)

        return [constants.PMD_MEASUREMENT_TYPES[int(index)] for index, bit in enumerate(bitmap) if bit]
    
    async def request_stream_settings(self, measurement_type: str) -> constants.MeasurementSettings:
        await self.client.write_gatt_char(constants.PMD_CONTROL_POINT_UUID, bytearray([constants.PMD_CONTROL_OPERATION_CODE["GET"], constants.PMD_MEASUREMENT_TYPES.index(measurement_type)]))

        return utils.parse_pmd_data(await self._queue_pmd_control.get())
        

    async def start_stream(self, settings: constants.MeasurementSettings) -> None:
        data = utils.build_measurement_settings(settings)

        await self.client.write_gatt_char(constants.PMD_CONTROL_POINT_UUID, data)

    def _handle_pmd_control(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        self._queue_pmd_control.put_nowait(data)

    def _handle_pmd_data(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        parsed_data = utils.parse_bluetooth_data(data)
        if self._data_callback:
            self._data_callback(parsed_data)

