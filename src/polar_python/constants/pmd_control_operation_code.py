from enum import IntEnum


class PmdControlOperationCode(IntEnum):
    GET = 0x01
    START = 0x02
    STOP = 0x03
