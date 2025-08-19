import time
from io import BytesIO
from enum import Enum

FC_DIAGNOSTICS = 0x08
FC_GET_COMM_EVT_COUNTER = 0x0B
FC_READ_DEV_ID = 0x0E

MIN_MSG_BYTES = 2
MAX_MSG_BYTES = 256

MIN_FRAME_INTERVAL = 0.00175
MIN_FRAME_TIMEOUT = 0.00075

CRC_TABLE = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
]

DATA_BYTE_COUNT_TABLE = {
    0x01: "byte_count",
    0x02: "byte_count",
    0x03: "byte_count",
    0x04: "byte_count",
    0x05: 4,
    0x06: 4,
    0x07: 1,
    0x0B: 4,
    0x0F: 4,
    0x10: 4,
    0x11: "byte_count",
    0x16: 6
}


def cal_crc(data):

    crc = 0xffff
    for b in bytearray(data):
        temp = b ^ crc & 0xff  # 只取8bit
        crc = (crc >> 8) ^ CRC_TABLE[temp]
    return crc


class FUNCTION_CODE(Enum):
    READ_COIL_STATUS = 0x01
    READ_INPUT_STATUS = 0x02
    WRITE_INPUT_REGS = 0x04
    FORCE_SINGLE_COIL = 0x05
    PRESET_SINGLE_REG = 0x06
    WRITE_MULTI_COILS = 0x0F
    PRESET_MULTI_REGS = 0x10


class RtuMessage:
    _addr: int
    _func: int
    _data_bytes: bytes
    _crc_bytes: bytes

    BYTE_LEN_PER_ADDR = 1
    BYTE_LEN_PER_FUNC = 1
    BYTE_LEN_PER_CRC = 2

    ADDR_IDX = 0
    FUNC_IDX = 1
    DATA_START_IDX = 2
    CRC_START_IDX = -2

    byteorder = "big"

    def __init__(
            self,
            addr: int = None,
            func: int = None,
            data_bytes: bytes = b'',
    ):
        self._addr = addr
        self._func = func.value if isinstance(func, FUNCTION_CODE) else func
        self._data_bytes = data_bytes
        self._crc_bytes = b''
        pass

    def __str__(self):
        return (
            f"addr: {self.addr}, "
            f"func: {self.func}, "
            f"data_bytes: {self.data_bytes}, "
            f"crc_bytes: {self._crc_bytes}"
        )

    def encode(self, crc_enable: bool = True):
        if crc_enable:
            self._crc_bytes = self.calculated_crc_bytes
        return self.raw + self._crc_bytes

    def decode(self, raw_message: bytes, crc_enable: bool = True):
        self.addr = raw_message[self.ADDR_IDX]
        self.func = raw_message[self.FUNC_IDX]
        if crc_enable:
            self.data_bytes = (
                raw_message[self.DATA_START_IDX:self.CRC_START_IDX]
            )
            self._crc_bytes = raw_message[self.CRC_START_IDX:]
        else:
            self.data_bytes = raw_message[self.DATA_START_IDX:]

    def check_crc(self):
        return self.calculated_crc_bytes == self._crc_bytes

    @property
    def addr(self):
        return self._addr.to_bytes(self.BYTE_LEN_PER_ADDR, self.byteorder)

    @addr.setter
    def addr(self, val):
        if isinstance(val, bytes):
            self._addr = int.from_bytes(val, self.byteorder)
        else:
            self._addr = val

    @property
    def func(self):
        return self._func.to_bytes(self.BYTE_LEN_PER_FUNC, self.byteorder)

    @func.setter
    def func(self, val):
        if isinstance(val, bytes):
            self._func = int.from_bytes(val, self.byteorder)
        else:
            self._func = val

    @property
    def data_bytes(self):
        return self._data_bytes

    @data_bytes.setter
    def data_bytes(self, val):
        self._data_bytes = val

    @property
    def raw(self):
        return self.addr + self.func + self.data_bytes

    @property
    def calculated_crc_bytes(self):
        return cal_crc(self.raw).to_bytes(self.BYTE_LEN_PER_CRC, "little")

    @property
    def length(self):
        return (
            len(self.addr) +
            len(self.func) +
            len(self.data_bytes) +
            len(self._crc_bytes)
        )


class RtuReceiveAbort(Exception):
    def __init__(self, state, message):
        if isinstance(state, str):
            state_name = state
        else:
            state_name = state.__class__.__name__
        self.msg = "[{}]{}".format(state_name, message)
        super().__init__(self.msg)

    def __str__(self):
        return self.msg


class RtuReceiveComplete(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class RtuResponseError(Exception):
    def __init__(self, cmd_name, message):
        self.msg = "[{}]{}".format(cmd_name, message)
        super().__init__(self.msg)

    def __str__(self):
        return self.msg


class State:
    def handle(self, input, *args):
        raise NotImplementedError()


class AddrState(State):
    """
    addr received
    waiting for func code
    """
    def handle(self, input: bytes, sent: RtuMessage, recv: BytesIO):
        if len(input) == 0:
            return self
        if input == sent.addr:
            recv.write(input)
            return FuncState()
        return self


class FuncState(State):
    """
    func code received
    waiting for byte count or data
    """
    def handle(self, input: bytes, sent: RtuMessage, recv: BytesIO):
        if len(input) == 0:
            raise RtuReceiveAbort(self, "Receiving function code timeout")

        if input != sent.func:
            msg = (
                f"Unmatch function code: sent is {sent.func.hex()}, "
                f"received is {input.hex()}"
            )
            raise RtuReceiveAbort(self, msg)

        recv.write(input)
        byte_count = DATA_BYTE_COUNT_TABLE[sent._func]
        if byte_count == "byte_count":
            return ByteCountState()
        else:
            return DataRecvState(byte_count)


class ByteCountState(State):
    def handle(self, input: bytes, sent: RtuMessage, recv: BytesIO):
        if len(input) == 0:
            raise RtuReceiveAbort(self, "Receiving function code timeout")

        recv.write(input)
        return DataRecvState(int.from_bytes(input, sent.byteorder))


class DataRecvState(State):
    def __init__(self, count, **kwargs):
        self._count = count
        for k in kwargs:
            self.__setattr__(k, kwargs[k])
        super().__init__()

    def handle(self, input: bytes, sent: RtuMessage, recv: BytesIO):
        if len(input) == 0:
            raise RtuReceiveAbort(self, "Receiving function code timeout")

        recv.write(input)
        self._count -= 1
        if self._count > 0:
            return self

        return CrcState()


class CrcState(State):
    _count = 2

    def handle(self, input: bytes, sent: RtuMessage, recv: BytesIO):
        if len(input) == 0:
            raise RtuReceiveAbort(self, "Receiving function code timeout")

        recv.write(input)
        self._count -= 1
        if self._count > 0:
            return self

        raise RtuReceiveComplete()


class ModBusRtuClient:
    def __init__(self, conn, frm_time: float = None, crc_enable=True) -> None:
        self._conn = conn
        if frm_time is None:
            self._frm_interval = MIN_FRAME_INTERVAL
            self._frm_timeout = MIN_FRAME_TIMEOUT
        else:
            self._frm_interval = 3.5 * frm_time
            self._frm_timeout = 1.5 * frm_time
        self._crc_enable = crc_enable
        pass

    def send(self, message: RtuMessage):
        msg = message.encode(self._crc_enable)
        time.sleep(self._frm_interval)
        return self._conn.write(msg)

    def recv(self, sent: RtuMessage):
        state = AddrState()
        recv_raw = BytesIO()
        while True:
            try:
                out = self._conn.read()
                state = state.handle(out, sent, recv_raw)
                # 暂时未增加1.5 frame time
            except RtuReceiveComplete:
                recv_msg = RtuMessage()
                recv_msg.decode(recv_raw.getvalue())
                if not recv_msg.check_crc():
                    raise RtuReceiveAbort(
                        "CrcCheck",
                        "Checking Crc failed, incorrect crc code"
                    )
                return recv_msg
