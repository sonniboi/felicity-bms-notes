# Errata for the public protocol PDF and the vendor tool

Reference: *BMS Communication Protocol RS485 20210608* (the public vendor PDF) and the vendor Windows tool EDMS (1.71 and 2.1).

## 1. ⛔ The EEPROM write table (section 3.11) is wrong for these packs

The PDF lists the block `0x2040–0x2068` as **pairs** (protection + recovery, 11 pairs). The real packs implement **groups of four** (alarm / alarm-recovery / protection / stage 2) — the vendor's own tool 2.1 names them that way. The offset between PDF and reality is therefore not constant.

| Register | PDF says | Pack actually holds (read back) |
|---|---|---|
| `0x204A` | Discharge OC protection (× 0.1 A) | cell-overvoltage alarm **recovery**: **3500 mV** |
| `0x204C` | Charge OT protection (× 0.1 °C) | cell-overvoltage protection **recovery**: 3500 mV |
| `0x2051–0x2054` | discharge OT recovery … MOS OT protection | charge-current group: 70 / 80 / 85 / 120 A |
| `0x2055–0x2058` | MOS OT recovery + undocumented | discharge-current group: 70 / 80 / 85 / 120 A |

Plausibility check: under the PDF mapping `0x204A = 3500` would be a 350 A discharge protection in a 200 Ah pack with an 80 A limit — impossible; as 3500 mV it fits (alarm 3600, protection 3650, shutdown 3750 mV).

🔴 **Writing according to the PDF overwrites a cell-voltage threshold.** Before any FC16 write, read the target registers and check that unit and magnitude of the value make sense. Use the names in [eeprom-parameters.md](eeprom-parameters.md); the order of "alarm" and "back" within a group follows the tool's naming and was not verified for every group.

Also: `0x2040` reads 64 on our packs (not the 200 Ah the old mapping suggests). The tool names it "Length" (block length) — **[inference]**, consistent with 64 registers in `0x2040–0x207F`.

## 2. Fault code names in EDMS (codes 3–10)

The tool's code enum is shifted; the bit enum is right. Details: [fault-codes.md](fault-codes.md).

## 3. C14 is not `0x440C`

`0x440C` stays `0xFF`/`0x00` whether or not C14 is active. C14 is bit 13 of `0x1304`.

## 4. Event log / ring buffer

Described as a fault log in the PDF; on the tested firmware it returns mirrored/stale data. See [registers.md](registers.md).

## 5. Energy counters

`0x4406–0x440B` are not energy; `0x130E–0x131B` are garbage on LPBF and valid word-swapped uint32 on FLA. See [registers.md](registers.md). The PDF's `÷10` scaling for `0x4406/0x4408` gives implausible values.

## 6. Small items

| Item | Old claim | Correct |
|---|---|---|
| `0x130A` | "BMS/heatsink temperature" | ambient temperature |
| `0x130C` | "rated capacity" | SOH in % |
| `0x130D` | — | cycle count |
| C01, C02, C08 | "suspected" | confirmed by the manual's fault table |
| SN registers | not documented | `0xF804–0xF808`, 4-digit decimal groups, `SNLen` in `0xF809` |
