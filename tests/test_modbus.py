import unittest
from modbus_rtu_client.cmd import Cmd

class TestCmd(unittest.TestCase):
    def test_write_do(self):
        cmd = Cmd.write_do(254, 0, True)
        self.assertEqual(cmd.encode(False), b'\xfe\x05\x00\x00\xff\x00')

    def test_read_do(self):
        cmd = Cmd.read_do(254, 4)
        self.assertEqual(cmd.encode(False), b'\xfe\x01\x00\x00\x00\x04')

    def test_write_all_do(self):
        cmd = Cmd.write_all_do(254, 4, True)
        self.assertEqual(cmd.encode(False), b'\xfe\x0f\x00\x00\x00\x04\x01\xff')

if __name__ == '__main__':
    unittest.main()