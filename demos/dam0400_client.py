from src.modbus_rtu_client.base import ModBusRtuClient
from src.modbus_rtu_client.base import RtuMessage, RtuResponseError
from src.modbus_rtu_client.cmd import Cmd, RespAnalyzer
import serial
import math
from bitarray import bitarray


def time_per_frame(ser: serial.Serial):
    frame_len = math.ceil(
        1 + ser.bytesize + (0 if ser.parity == 'N' else 1) + ser.stopbits
    )
    t = float(frame_len / ser.baudrate)
    return t


class Dam0400Client(ModBusRtuClient):
    byteorder = "big"
    _slave_addr: int = 254
    _equip_id: int
    _dodi_num = 4
    _do_status: list  # 暂时无用
    _di_status: list

    def __init__(self, port, baudrate, **kwargs) -> None:
        ser = serial.Serial(
            port,
            baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=0.5
        )

        for k, v in kwargs.items():
            setattr(ser, k, v)

        if ser.closed:
            ser.open()

        frm_time = time_per_frame(ser)
        super().__init__(ser, frm_time)
        self._init_slave()

    def _init_slave(self):
        send = Cmd.read_ai_info(self._slave_addr, 1000, 20)
        raw_resp = self.query(send)  # 如果6不对 改成20
        resp = RespAnalyzer.read_ai_info(raw_resp)
        if len(resp) != 20:
            raise RtuResponseError(
                "Init slave",
                f"incorrect response data bytes, {raw_resp.data_bytes.hex()}")

        self._slave_addr = resp[0]
        self._equip_id = resp[1]

    def query(self, qry_msg: RtuMessage):
        self.send(qry_msg)
        res = self.recv(qry_msg)
        return res

    def conv_resp_data(self, data_bytes, keyname, byte_len=1):
        r_data = {}
        for i, n in enumerate(data_bytes):
            base = i * byte_len * 8
            d = n
            if isinstance(n, int):
                d = bitarray()
                d.frombytes(n.to_bytes(byte_len, self.byteorder))
            k = [base + j for j in range(len(d) - 1, -1, -1)]
            v = d.tolist()
            r_data.update(dict(zip(k, v)))
        return {
            f"{keyname}_{k}": r_data[k] 
            for k in r_data 
            if k < self._dodi_num
        }

    def open_do(self, io: int):
        if io > (self._dodi_num - 1) or io < 0:
            msg = (
                "Invalid do num, "
                f"{io} is not in valid range [{self._dodi_num - 1}, 0]")
            raise Exception(msg)
        send = Cmd.write_do(self._slave_addr, io, True)
        resp = RespAnalyzer.write_do(self.query(send))
        return True

    def close_do(self, io):
        if io > (self._dodi_num - 1) or io < 0:
            msg = (
                "Invalid do num, "
                f"{io} is not in valid range [{self._dodi_num - 1}, 0]")
            raise Exception(msg)
        send = Cmd.write_do(self._slave_addr, io, False)
        resp = RespAnalyzer.write_do(self.query(send))
        return True

    def open_all(self):
        send = Cmd.write_all_do(self._slave_addr, self._dodi_num, True)
        resp = RespAnalyzer.write_all_do(self.query(send))
        return True

    def close_all(self):
        send = Cmd.write_all_do(self._slave_addr, self._dodi_num, False)
        resp = RespAnalyzer.write_all_do(self.query(send))
        return True

    def read_do(self):
        send = Cmd.read_do(self._slave_addr, self._dodi_num)
        raw_resp = self.query(send)
        resp = RespAnalyzer.read_do(raw_resp)
        return self.conv_resp_data(resp, "do")

    def read_di(self):
        send = Cmd.read_di(self._slave_addr, self._dodi_num)
        raw_resp = self.query(send)
        resp = RespAnalyzer.read_di(raw_resp)
        return self.conv_resp_data(resp, "di")

    def read_ai_info(self, ai, quantity):
        send = Cmd.read_ai_info(self._slave_addr, ai, quantity)
        raw_resp = self.query(send)
        resp = RespAnalyzer.read_ai_info(raw_resp)
        return resp


if __name__ == "__main__":
    import sys
    port = sys.argv[1]
    baudrate = int(sys.argv[2])
    client = Dam0400Client(port, baudrate)
    print(client.read_do())
