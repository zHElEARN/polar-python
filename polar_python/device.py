from bleak import BleakClient
from bleak.backends.device import BLEDevice
from typing import Union

from . import constants, exceptions, utils


class PolarDevice:
    def __init__(self, address_or_ble_device: Union[str, BLEDevice]) -> None:
        self.client = BleakClient(address_or_ble_device)

    async def connect(self) -> bool:
        return await self.client.connect()

    async def disconnect(self) -> bool:
        return await self.client.disconnect()

    def is_connected(self):
        return self.client.is_connected

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
        
