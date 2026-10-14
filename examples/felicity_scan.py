#!/usr/bin/env python3
"""Find the Felicity packs on an RS485 bus: asks every address for the info block.

READ-ONLY (FC03 only). Stop every other reader on the bus first - two
processes talking at once corrupt each other's frames.

    python3 felicity_scan.py /dev/ttyUSB0            # addresses 1..15
    python3 felicity_scan.py /dev/ttyUSB0 --first 0 --last 16

Run it after every DIP-switch change and after every power cycle of the packs:
the address only follows the DIP setting after a restart (docs/dip-and-parallel.md).
Two packs answering on the same address, or a pack missing from the list,
is the first thing to check for C13 (docs/fault-codes.md).
"""
import argparse

import felicity_read as f


def scan(port, first=1, last=15, wait=1.0):
    """Return {address: info dict} for every address that answers."""
    found = {}
    for addr in range(first, last + 1):
        try:
            found[addr] = f.decode_info(f.read_regs(port, addr, 0xF800, 16, wait=wait))
        except ValueError:
            continue  # no/short/corrupt answer: nobody there (or bus problem)
    return found


def main():
    import serial

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("device")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=15)
    a = ap.parse_args()

    with serial.Serial(a.device, a.baud, timeout=1.5) as port:
        found = scan(port, a.first, a.last)

    if not found:
        print("no pack answered - check wiring (incl. COMM-GND, pin 4), baud rate, and that no other reader is running")
        return
    for addr, i in sorted(found.items()):
        print("address %2d: %-16s ID %4d  MCU1 %-4d  serial %s" % (
            addr, i["model"], i["model_id"], i["mcu1_version"], i["serial"]))
    print("%d pack(s) found" % len(found))


if __name__ == "__main__":
    main()
