# Troubleshooting checklist

Lessons from a three-pack installation running since 2026. Evidence labels: see the [README](../README.md#evidence-labels).

## Values look normal but never change

**Symptom:** SOC, voltage and current identical for hours, whatever the load. **[measured]**
**Cause seen:** a loose RS485 cable in the daisy chain. Two packs dropped out in the same second, the pack nearest to the adapter kept answering (17 h unnoticed).
**Why it is silent:** many readers only update their cache on a successful read and keep serving the last value; "connected" flags and update counters keep running, because they count loop iterations, not successful Modbus answers.
**Check:**
1. Look at the raw values over time (`felicity_watch.py` reports unchanged measurements after 15 min).
2. Stop the normal reader, scan all addresses with `felicity_scan.py`. If only the first pack answers, the chain is broken behind it.
3. Re-seat every RJ45 plug, check COMM-GND (pin 4).

Two packs failing at the same moment points at one cable, not two BMS.

## C13 "Parallel failed"

See [dip-and-parallel.md](dip-and-parallel.md) for the mechanism. In practice:
1. **Scan** the bus; every pack must answer on its **own** address. Duplicate IDs → fix the DIP switches and **power-cycle** the packs.
2. Termination SW5 ON on the first and the last pack only.
3. Look at the time of the event: a restart or reset of any pack in the group can announce "undecided" for a moment.
4. A single transient C13 (seconds to minutes) with healthy cells is not a battery problem. A permanent one is a configuration or wiring problem.
5. Packs of different families in one group are outside the manufacturer's specification; they work, but expect the unexpected.

## A fault shows on the LCD but not in the register

C14 and the self-healing faults (C05, C06, C11, C12) can be gone before your next poll. Poll `0x1304` every 0.5–1 s ([`examples/felicity_watch.py`](../examples/felicity_watch.py)) and log changes. The event log `0x4300+` is **not** a substitute — it returns mirrored data ([registers.md](registers.md)).

## Fault name in the vendor tool does not match the manual

Codes 3–10 are shifted in the tool; the manual and the bits of `0x1304` are right ([fault-codes.md](fault-codes.md)).

## Limits change by themselves

FLA packs report **dynamic** charge/discharge current limits (temperature/SOC dependent). A fixed limit in your monitoring will raise false alarms; check against a plausibility ceiling instead. LPBF packs report a static limit. **[measured]**

## BMS voltage differs from the multimeter

The FLA read +0.11 V high against two meters. Compare packs with **one** meter across the open disconnector before paralleling; never BMS value against meter value.

## Energy counters show nonsense

`0x4406–0x440B` are not energy; `0x130E–0x131B` are garbage on LPBF and valid (word-swapped uint32, uncalibrated) on FLA. Use your own shunt or meter for kWh ([registers.md](registers.md)).

## Good bus hygiene

- **One** polling process per RS485 bus. Two readers corrupt each other's frames, which looks like random timeouts.
- ~1 s per transaction is normal at 9600 baud with several packs; retry a few times before declaring a pack dead.
- After **every** DIP change or power cycle, scan the addresses again — a pack keeps its old address until restarted.
- Read-only first. Never write EEPROM registers based on the public PDF ([errata.md](errata.md)).
