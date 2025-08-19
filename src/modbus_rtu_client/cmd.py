from .base import RtuMessage, FUNCTION_CODE, RtuResponseError
from io import BytesIO
# from bitarray import bitarray

BYTE_ORDER = "big"


class Cmd:
    @staticmethod
    def write_do(addr: int, io: int, on_off: bool):
        """
        Field Name                Example(Hex)

        Slave Address             01  <- addr
        Function                  05
        Coil Address Hi           00
        Coil Address Lo           01  <- io
        Force Data Hi             00  <- on_off
        Force Data Lo             00
        Error Check (LRC or CRC)  --
        """

        data_bytes = BytesIO()
        data_bytes.write(io.to_bytes(2, BYTE_ORDER))
        data_bytes.write(b"\xff\x00" if on_off else b"\x00\x00")
        return RtuMessage(
            addr,
            FUNCTION_CODE.FORCE_SINGLE_COIL,
            data_bytes.getvalue()
        )

    @staticmethod
    def write_all_do(addr: int, io_num: int, on_off: bool):
        """
        Field Name                 Example(Hex)

        Slave Address              01  <- addr
        Function                   0F
        Coil Address Hi            00
        Coil Address Lo            00  # force coils starting at coil 1
        Quantity of Coils Hi       00  # force io_num coils
        Quantity of Coils Lo       04  <- io_num
        Byte Count                 01  <- on_off
        Force Data Hi (Coils 8-1)  0F  # coil 8 [ 0 0 0 0 1 1 1 1 ] coil 1
        Error Check (LRC or CRC)   --
        """
        data_bytes = BytesIO()
        data_bytes.write(b"\x00\x00")
        data_bytes.write(io_num.to_bytes(2, BYTE_ORDER))
        byte_count = (io_num + 7) // 8
        data_bytes.write(byte_count.to_bytes(byteorder=BYTE_ORDER))
        for i in range(byte_count):
            data_bytes.write(b'\xff' if on_off else b'\x00')
        return RtuMessage(
            addr,
            FUNCTION_CODE.WRITE_MULTI_COILS,
            data_bytes.getvalue()
        )

    @staticmethod
    def read_do(addr: int, do_num: int):
        """
        Field Name                 Example(Hex)

        Slave Address              01  <- addr
        Function                   01
        Starting Address Hi        00
        Starting Address Lo        00
        No. of Points Hi           00
        No. of Points Lo           04  <- do_num
        Error Check (LRC or CRC)   --
        """
        data_bytes = BytesIO()
        data_bytes.write(b"\x00\x00")
        data_bytes.write(do_num.to_bytes(2, BYTE_ORDER))
        return RtuMessage(
            addr,
            FUNCTION_CODE.READ_COIL_STATUS,
            data_bytes.getvalue()
        )

    @staticmethod
    def read_di(addr: int, di_num: int):
        """
        Field Name                 Example(Hex)

        Slave Address              01  <- addr
        Function                   02
        Starting Address Hi        00
        Starting Address Lo        00
        No. of Points Hi           00
        No. of Points Lo           04  <- do_num
        Error Check (LRC or CRC)   --
        """
        data_bytes = BytesIO()
        data_bytes.write(b"\x00\x00")
        data_bytes.write(di_num.to_bytes(2, BYTE_ORDER))
        return RtuMessage(
            addr,
            FUNCTION_CODE.READ_INPUT_STATUS,
            data_bytes.getvalue()
        )

    @staticmethod
    def read_ai_info(addr: int, reg_start: int, reg_num: int):
        """
        Field Name                 Example(Hex)

        Slave Address              01  <- addr
        Function                   04
        Starting Address Hi        00  <- reg_start 高8位
        Starting Address Lo        00  <- reg_start 低8位
        No. of Points Hi           00  <- reg_num 高8位
        No. of Points Lo           04  <- reg_num 低8位
        Error Check (LRC or CRC)   --
        """
        data_bytes = BytesIO()
        data_bytes.write((reg_start >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_start & 0xff).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_num >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_num & 0xff).to_bytes(byteorder=BYTE_ORDER))
        return RtuMessage(
            addr,
            FUNCTION_CODE.WRITE_INPUT_REGS,
            data_bytes.getvalue()
        )

    @staticmethod
    def write_single_ao_info(addr: int, reg_start: int, ao: int):
        """
        Field Name                            Example(Hex)

        Slave Address                         01  <- addr
        Function                              06
        Register Address Hi                   00  <- reg_start 高8位
        Register Address Lo                   00  <- reg_start 低8位
        Preset Data Hi                        00  <- ao 高8位
        Preset Data Lo                        04  <- ao 低8位
        Error Check (LRC or CRC)              --
        """
        data_bytes = BytesIO()
        data_bytes.write((reg_start >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_start & 0xff).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((ao >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((ao & 0xff).to_bytes(byteorder=BYTE_ORDER))
        return RtuMessage(
            addr,
            FUNCTION_CODE.PRESET_SINGLE_REG,
            data_bytes.getvalue()
        )

    @staticmethod
    def write_multi_ao_info(addr: int, reg_start: int, reg_num: int, ao: list):
        """
        Field Name                            Example(Hex)

        Slave Address                         01  <- addr
        Function                              06
        Starting Address Hi                   00  <- reg_start 高8位
        Starting Address Lo                   00  <- reg_start 低8位
        No. of Registers Hi                   00
        No. of Registers Lo                   02
        Byte Count                            04
        Data Hi                               00  <- ao[0] 高8位
        Data Lo                               04  <- ao[0] 低8位
        Data Hi                               00  <- ao[1] 高8位
        Data Lo                               04  <- ao[1] 低8位
        Error Check (LRC or CRC)              --
        """
        data_bytes = BytesIO()
        data_bytes.write((reg_start >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_start & 0xff).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_num >> 8).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((reg_num & 0xff).to_bytes(byteorder=BYTE_ORDER))
        data_bytes.write((len(ao)*2).to_bytes(byteorder=BYTE_ORDER))
        for i in ao:
            data_bytes.write((i >> 8).to_bytes(byteorder=BYTE_ORDER))
            data_bytes.write((i & 0xff).to_bytes(byteorder=BYTE_ORDER))
        return RtuMessage(
            addr,
            FUNCTION_CODE.PRESET_MULTI_REGS,
            data_bytes.getvalue()
        )


class RespAnalyzer:
    @staticmethod
    def write_do(response: RtuMessage):
        """
        The normal response is an echo of the query,
        returned after the coil state has been forced.

        Field Name					    Example(Hex)
        Slave Address				    01
        Function					    05
        Coil Address Hi				    00
        Coil Address Lo				    01
        Force Data Hi				    00
        Force Data Lo				    00
        Error Check (LRC or CRC)	    ±±
        """
        if response.data_bytes == b'':
            raise RtuResponseError("write_do", "data_bytes is None")

    @staticmethod
    def write_all_do(response: RtuMessage):
        """
        Field Name					    Example(Hex)
        Slave Address				    01
        Function					    0F
        Coil Address Hi				    00
        Coil Address Lo				    00
        Quantity of Coils Hi		    00
        Quantity of Coils Lo		    04
        Error Check (LRC or CRC)	    ±±
        """
        if response.data_bytes == b'':
            raise RtuResponseError("write_all_do", "data_bytes is None")

    # @staticmethod
    # def proc_read_dido(data_bytes):
    #     val = []
    #     for d in data_bytes:
    #         d_bit = bitarray()
    #         d_bit.frombytes(d)
    #         val.append(d_bit)
    #     return val

    @staticmethod
    def read_do(response: RtuMessage):
        """
        Field Name			            Example(Hex)
        Slave Address					01
        Function					    01
        Byte Count					 	01
        Data (Coils 1±8)				0F  # Coil 8 [ 0 0 0 0 1 1 1 1] Coil 1
        Error Check (LRC or CRC)		±±
        """
        byte_cnt = response.data_bytes[0]
        return response.data_bytes[1: 1 + byte_cnt]

    @staticmethod
    def read_di(response: RtuMessage):
        """
        Field Name					    Example(Hex)
        Slave Address				    01
        Function					    02
        Byte Count					    01
        Data (Inputs 1±8)	            0F  # Coil 8 [ 0 0 0 0 1 1 1 1] Coil 1
        Error Check (LRC or CRC)  	    --
        """
        byte_cnt = response.data_bytes[0]
        return response.data_bytes[1: 1 + byte_cnt]

    # @staticmethod
    # def proc_data_pair(hi, lo):
    #     return hi << 8 | lo

    @staticmethod
    def read_ai_info(response: RtuMessage):
        """
        Field Name					    Example(Hex)
        Slave Address				    01
        Function					    04
        Byte Count					    08
        Data Hi (Register 30009)	    00
        Data Lo (Register 30009)	    0A
        Data Hi (Register 30010)	    00
        Data Lo (Register 30010)	    0A
        Data Hi (Register 30011)	    00
        Data Lo (Register 30011)	    0A
        Data Hi (Register 30012)	    00
        Data Lo (Register 30012)	    0A
        Error Check (LRC or CRC)  	    --
        """
        byte_cnt = response.data_bytes[0]
        data_bytes = response.data_bytes[1:1 + byte_cnt]
        val = [hi << 8 | lo for hi, lo in zip(*[iter(data_bytes)]*2)]
        return val

    @staticmethod
    def write_single_ao_info(response: RtuMessage, *args):
        """
        Field Name					    Example(Hex)
        Slave Address				    11
        Function					    06
        Register Address Hi			    00
        Register Address Lo	            01
        Preset Data Hi	                00
        Preset Data Lo				    03
        Error Check (LRC or CRC)  	    --
        """
        if response.data_bytes == b'':
            raise RtuResponseError("write_all_do", "data_bytes is None")

    @staticmethod
    def write_multi_ao_info(response: RtuMessage):
        """
        Field Name					    Example(Hex)
        Slave Address				    11
        Function					    10
        Starting Address Hi			    00
        Starting Address Lo	            01
        No. of Register Hi	            00
        No. of Register Lo				03
        Error Check (LRC or CRC)  	    --
        """
        start = response.data_bytes[:2].hex()
        quantity = int.from_bytes(response.data_bytes[2:], response.byteorder)
        return {
            "starting addr": start,
            "number of regs preset": quantity
        }
