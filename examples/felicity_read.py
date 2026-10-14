#!/usr/bin/env python3
"""Minimal READ-ONLY Modbus RTU reader for Felicity Solar LPBF/FLA rack batteries.

Only function code 0x03 (read holding registers) is ever sent. There is no
write path in this file on purpose.

Usage:
    python3 felicity_read.py /dev/ttyUSB0 2            # pack with Modbus address 2
    python3 felicity_read.py /dev/ttyUSB0 1 --baud 9600

Needs `pyserial` (pip install pyserial). Run only ONE reader per RS485 bus:
a second process on the same bus disturbs both.

See ../docs/registers.md and ../docs/fault-codes.md for what the registers mean.
"""
import argparse
import struct
import time

# C-code = bit number of 0x1304 + 1 (see docs/fault-codes.md). Names from the
# manufacturer's fault table, NOT from the (shifted) code enum of the vendor tool.
FAULT_BITS = [
    "C01 Battery overvoltage", "C02 Battery undervoltage",
    "C03 Cell overvoltage", "C04 Cell undervoltage",
    "C05 Charge overcurrent", "C06 Discharge overcurrent",
    "C07 MOS overtemperature", "C08 MOS undertemperature",
    "C09 Cell overtemperature", "C10 Cell undertemperature",
    "C11 Abnormal current sampling", "C12 Abnormal output impedance",
    "C13 Parallel failed", "C14 Output loss (break wire)",
    "(bit 14) pirated detection",
]
MODELS = {2409: "LPBF48200-P", 7500: "FLA48460TG2-EU"}


def crc16(data: bytes) -> int:
    """Modbus CRC-16 (poly 0xA001, init 0xFFFF)."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def build_read(addr: int, start: int, count: int) -> bytes:
    """Request frame for FC03, CRC appended low byte first."""
    body = struct.pack(">BBHH", addr, 0x03, start, count)
    return body + struct.pack("<H", crc16(body))


def parse_read(frame: bytes, addr: int, count: int) -> list:
    """Validate a FC03 response and return the registers as unsigned ints."""
    if len(frame) < 5:
        raise ValueError("short frame")
    if frame[0] != addr or frame[1] != 0x03:
        raise ValueError("unexpected header %02x %02x" % (frame[0], frame[1]))
    if frame[2] != count * 2 or len(frame) != 5 + count * 2:
        raise ValueError("unexpected length")
    if struct.unpack("<H", frame[-2:])[0] != crc16(frame[:-2]):
        raise ValueError("CRC mismatch")
    return list(struct.unpack(">%dH" % count, frame[3:-2]))


def signed(v: int) -> int:
    return v - 0x10000 if v & 0x8000 else v


def read_regs(port, addr: int, start: int, count: int, wait: float = 1.0) -> list:
    """One FC03 transaction on an open pyserial port."""
    port.reset_input_buffer()
    port.write(build_read(addr, start, count))
    time.sleep(wait)
    return parse_read(port.read(5 + count * 2), addr, count)


def decode_faults(flags: int) -> list:
    return [name for bit, name in enumerate(FAULT_BITS) if flags & (1 << bit)]


def decode_status(regs: list) -> dict:
    """regs = 10 registers read from 0x1302 (0x1302 .. 0x130B)."""
    flag, fault_code, fault_flags = regs[0], regs[1], regs[2]
    return {
        "charge_enabled": bool(flag & 0x01),
        "charge_immediately": bool(flag & 0x02),
        "discharge_enabled": bool(flag & 0x04),
        # first fault that occurred (bit + 1), 0 = none
        "fault_code": fault_code,
        # all active faults
        "fault_flags": fault_flags,
        "faults": decode_faults(fault_flags),
        "alarm_flags": regs[3],
        "voltage_v": regs[4] * 0.01,
        # negative = charging, positive = discharging
        "current_a": signed(regs[5]) * 0.1,
        "ambient_c": signed(regs[8]),
        "soc_pct": regs[9],
    }


def decode_info(regs: list) -> dict:
    """regs = 16 registers read from 0xF800."""
    sn_digits = "".join("%04d" % r for r in regs[4:9])[: regs[9]]
    return {
        "model_id": regs[1],
        "model": MODELS.get(regs[1], "unknown"),
        "protocol_version": regs[2],
        "serial": sn_digits,
        "mcu1_version": regs[11],
    }


def main():
    import serial  # imported late so the offline tests need no pyserial

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("device")
    ap.add_argument("address", type=int, help="Modbus address = pack ID (1-15)")
    ap.add_argument("--baud", type=int, default=9600)
    a = ap.parse_args()

    with serial.Serial(a.device, a.baud, timeout=3) as port:
        info = decode_info(read_regs(port, a.address, 0xF800, 16))
        status = decode_status(read_regs(port, a.address, 0x1302, 10))
        cells = read_regs(port, a.address, 0x0220, 16)
        limits = read_regs(port, a.address, 0x131C, 4)

    print("model       :", info["model"], "(ID %d), MCU1 %d" % (info["model_id"], info["mcu1_version"]))
    print("serial      :", info["serial"])
    print("pack        : %.2f V  %+.1f A  SOC %d %%" % (status["voltage_v"], status["current_a"], status["soc_pct"]))
    print("cells (mV)  :", cells, " spread:", max(cells) - min(cells), "mV")
    print("limits      : charge %.2f V / discharge %.2f V / charge %.1f A / discharge %.1f A" % (
        limits[0] * 0.01, limits[1] * 0.01, limits[2] * 0.1, limits[3] * 0.1))
    print("fault code  :", status["fault_code"], "(first fault, = bit + 1)")
    print("fault flags : 0x%04X" % status["fault_flags"], status["faults"] or "none")
    print("alarm flags : 0x%04X" % status["alarm_flags"])


if __name__ == "__main__":
    main()
