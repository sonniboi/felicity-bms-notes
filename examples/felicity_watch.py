#!/usr/bin/env python3
"""Fast, read-only fault watcher for ONE pack: catches short faults and frozen data.

    python3 felicity_watch.py /dev/ttyUSB0 2              # pack at address 2
    python3 felicity_watch.py /dev/ttyUSB0 2 --interval 0.5

Prints a timestamped line whenever
  * the fault flags (0x1304) or the first-fault code (0x1303) change, or
  * the measurements have not changed at all for --freeze-seconds (default 900).

Why this exists (docs/fault-codes.md, docs/troubleshooting.md):
  * C05/C06/C11/C12 clear themselves and C14 is intermittent - a poll every
    few seconds can miss them. Poll fast (0.5-1 s) and log every change.
  * A pack that stops answering (loose RS485 cable) is silent: many readers keep
    the last value and look healthy for hours. Identical values for a long time
    on a pack that carries any load are not a measurement.

Run only ONE reader per bus. Needs pyserial.
"""
import argparse
import time

import felicity_read as f


class FaultTracker:
    """Reports every change of the fault flags or of the first-fault code."""

    def __init__(self):
        self.last = (0, 0)

    def update(self, fault_code, fault_flags):
        """Return a list of event strings (empty if nothing changed)."""
        events = []
        if (fault_code, fault_flags) != self.last:
            events.append("fault code %d  flags 0x%04X  %s" % (
                fault_code, fault_flags, ", ".join(f.decode_faults(fault_flags)) or "none"))
            self.last = (fault_code, fault_flags)
        return events


class FreezeDetector:
    """Flags identical measurement tuples that persist for `seconds`."""

    def __init__(self, seconds=900.0):
        self.seconds = seconds
        self.value = None
        self.since = None
        self.reported = False

    def update(self, value, now):
        if value != self.value:
            self.value, self.since, self.reported = value, now, False
            return None
        if not self.reported and now - self.since >= self.seconds:
            self.reported = True
            return "measurements unchanged for %d s - pack silent or bus problem?" % (now - self.since)
        return None


def main():
    import serial

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("device")
    ap.add_argument("address", type=int)
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between polls")
    ap.add_argument("--freeze-seconds", type=float, default=900.0)
    a = ap.parse_args()

    tracker, freeze = FaultTracker(), FreezeDetector(a.freeze_seconds)
    with serial.Serial(a.device, a.baud, timeout=2) as port:
        while True:
            t0 = time.time()
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                s = f.decode_status(f.read_regs(port, a.address, 0x1302, 10, wait=0.4))
            except ValueError as e:
                print(stamp, "read failed:", e, flush=True)
            else:
                for ev in tracker.update(s["fault_code"], s["fault_flags"]):
                    print(stamp, ev, flush=True)
                msg = freeze.update((s["voltage_v"], s["current_a"], s["soc_pct"]), t0)
                if msg:
                    print(stamp, msg, flush=True)
            time.sleep(max(0.0, a.interval - (time.time() - t0)))


if __name__ == "__main__":
    main()
