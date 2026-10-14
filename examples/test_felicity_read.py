"""Offline tests: no serial port or battery needed.  Run: python3 -m unittest -v"""
import struct
import unittest

import felicity_read as f


def fake_response(addr, regs):
    body = bytes([addr, 0x03, len(regs) * 2]) + struct.pack(">%dH" % len(regs), *regs)
    return body + struct.pack("<H", f.crc16(body))


class Tests(unittest.TestCase):
    def test_crc_known_vector(self):
        # classic Modbus example: 01 03 00 00 00 0A -> CRC C5 CD (low byte first)
        self.assertEqual(f.build_read(1, 0x0000, 10), bytes.fromhex("01 03 00 00 00 0A C5 CD"))

    def test_roundtrip_and_crc_error(self):
        frame = fake_response(2, [1, 2, 3])
        self.assertEqual(f.parse_read(frame, 2, 3), [1, 2, 3])
        bad = frame[:-1] + bytes([frame[-1] ^ 0xFF])
        with self.assertRaises(ValueError):
            f.parse_read(bad, 2, 3)

    def test_fault_bits_c01_c13(self):
        # 0x1001 = bit 0 + bit 12 = C01 + C13 (see docs/fault-codes.md)
        self.assertEqual(f.decode_faults(0x1001), ["C01 Battery overvoltage", "C13 Parallel failed"])
        self.assertEqual(f.decode_faults(0), [])

    def test_status_decode(self):
        regs = [0x0015, 13, 0x1000, 0, 5314, 0xFFF6, 0, 0, 22, 83]
        s = f.decode_status(regs)
        self.assertAlmostEqual(s["voltage_v"], 53.14)
        self.assertAlmostEqual(s["current_a"], -1.0)  # 0xFFF6 = -10 -> -1.0 A (charging)
        self.assertEqual(s["fault_code"], 13)
        self.assertEqual(s["faults"], ["C13 Parallel failed"])
        self.assertTrue(s["charge_enabled"] and s["discharge_enabled"] and not s["charge_immediately"])

    def test_info_decode(self):
        regs = [112, 7500, 3, 0, 123, 456, 7890, 12, 3400, 18, 0xFFFF, 524, 8, 0, 0, 0]
        i = f.decode_info(regs)
        self.assertEqual(i["model"], "FLA48460TG2-EU")
        self.assertEqual(i["serial"], "01230456789000123400"[:18])
        self.assertEqual(i["mcu1_version"], 524)


if __name__ == "__main__":
    unittest.main()
