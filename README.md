# felicity-bms-notes

Field notes on reading and understanding **Felicity Solar LiFePO4 rack batteries** (LPBF48200-P / LPBA48200 and FLA48460TG2-EU) over their RS485 Modbus interface: register map, fault codes (C01–C14), the parallel-bus fault C13, EEPROM parameter names, and errata for the vendor protocol PDF.

Everything here comes from a real three-pack installation (2× LPBF48200-P + 1× FLA48460TG2-EU in parallel, read continuously since early 2026), from the vendor's own manuals and monitoring tool, and from static analysis of the firmware update files the vendor distributes with its tool. Nothing was flashed, and no firmware or vendor software is redistributed here.

> ⚠ **Unofficial and unaffiliated.** This is not vendor documentation. Statements are labelled with how well they are backed (see below). Writing to the BMS EEPROM can change protection thresholds of a battery that stores ~10 kWh; read first, write only if you know exactly what a register does.

## What is in here

| File | Content |
|---|---|
| [`docs/registers.md`](docs/registers.md) | Modbus register map with scaling, model differences (LPBF vs FLA) and what is *not* usable |
| [`docs/fault-codes.md`](docs/fault-codes.md) | `0x1303` / `0x1304` semantics, C01–C14 ↔ bit mapping, self-healing faults, the wrong enum in the vendor tool |
| [`docs/dip-and-parallel.md`](docs/dip-and-parallel.md) | DIP switches, pack IDs, termination, parallel rules, the C13 mechanism (role/address heartbeat on the parallel bus) |
| [`docs/eeprom-parameters.md`](docs/eeprom-parameters.md) | Names of all EEPROM registers `0x2040–0x207F` and `0x2320–0x237F` as named by the vendor's own tool |
| [`docs/errata.md`](docs/errata.md) | Where the public vendor PDF (`BMS Communication Protocol RS485 20210608`) and the vendor tool are wrong |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Checklist: frozen values, C13, missed faults, dynamic limits, bus hygiene |
| [`docs/methodology.md`](docs/methodology.md) | How the findings were obtained, and their limits |
| [`examples/felicity_read.py`](examples/felicity_read.py) | Minimal **read-only** Modbus RTU reader (stdlib + `pyserial`) |
| [`examples/felicity_scan.py`](examples/felicity_scan.py) | Finds the packs on the bus (address, model, serial, firmware) — run after DIP changes |
| [`examples/felicity_watch.py`](examples/felicity_watch.py) | Fast fault watcher + frozen-data detector for one pack |

All examples are read-only (FC03 only), need `pyserial`, and come with offline tests: `cd examples && python3 -m unittest`.

## Evidence labels

| Label | Meaning |
|---|---|
| **[measured]** | observed on real packs over the bus |
| **[firmware]** | read from the firmware of the pack (static analysis, not tested on a pack) |
| **[manual]** | stated in a vendor manual |
| **[tool]** | taken from the vendor's monitoring software (EDMS) |
| **[unverified]** | plausible, but not backed by any of the above |

## Headline findings

1. **Fault code = bit number + 1.** `0x1303` holds the code of the *first* active fault (1–15), `0x1304` is the bitfield of *all* active faults. `0x1001` means C01 *and* C13. The C01…C14 table in the vendor manuals is right.
2. **The vendor tool shows wrong names** for fault codes 3–10 (its `BmsFaultCode` enum is shifted); its flag-bit names are correct. Derive names from the bits of `0x1304`.
3. **C13 "Parallel failed" is not a voltage/current event.** It is raised when a pack sees *its own address* in other packs' role heartbeats for 10 s — duplicate pack ID, or its own frames coming back on the parallel bus.
4. **C05/C06/C11/C12 clear themselves** after a timer and are retried; that is why short faults are often missed by a slow poll.
5. **Section 3.11 of the public protocol PDF (EEPROM write block) is wrong** for these packs. Following it would overwrite a *cell voltage* threshold instead of a current limit. See [`docs/errata.md`](docs/errata.md).
6. The "fault event log" `0x4300+` and ring buffer `0x0000+` return mirrored/stale data on the tested firmware — do not treat them as history.

## Not covered / open

- FLA firmware V524 (master MCU of the FLA48460TG2) and the LCD firmware were not available; whatever applies only to them is marked.
- The parallel voltage condition (< 3 V difference, per manual) was not found in the analysed firmware.
- What triggered a single transient C01+C13 flag on one pack in October 2026 is unknown.

## Contributing

Corrections and measurements from other models are very welcome — open an issue or pull request with the model, firmware version (`0xF80B`), and how you observed it.

## License

Text: CC BY 4.0. Code in `examples/`: MIT. Code: [`LICENSE`](LICENSE) (MIT) · text: [`LICENSE-docs.md`](LICENSE-docs.md) (CC BY 4.0).
