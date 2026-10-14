# Register map (Modbus RTU, FC03/FC16)

**Link:** RS485, 9600 baud, FC03 (read) and FC16 (write) only. FC01, FC17 and FC43 are silently ignored. PIN 4 (COMM-GND) of the RJ45 port must be connected. The slave address is the pack ID (see [dip-and-parallel.md](dip-and-parallel.md)). Allow ~1 s per request on a shared bus; several readers on one bus disturb each other, so use **one** polling process.

Models checked: **LPBF48200-P** (model ID 2409, 200 Ah, firmware 417) and **FLA48460TG2-EU** (model ID 7500, 460 Ah, master firmware 524). Same layout; differences are marked.

Evidence labels: see the [README](../README.md#evidence-labels).

## Status block `0x1300…`

| Register | Field | Scaling / notes |
|---|---|---|
| `0x1300` | SettingDataSn | settings sequence number **[tool]** |
| `0x1301` | BmsMode | 2 = normal **[measured]** |
| `0x1302` | BmsFlag (bitfield) | bit 0 charge enabled, bit 1 charge immediately, bit 2 discharge enabled **[measured]**. FLA: idle `0x15`, charging `0x95` (bit 7 extra, probably a charge indicator) |
| `0x1303` | BmsFaultCode | first active fault = bit + 1, see [fault-codes.md](fault-codes.md) |
| `0x1304` | BmsFaultFlag | all active faults, bit *n* = C(*n*+1) |
| `0x1305` | BmsAlarmFlag | warnings |
| `0x1306` | battery voltage | × 0.01 V |
| `0x1307` | battery current | × 0.1 A, signed; **negative = charging, positive = discharging** **[measured]** |
| `0x130A` | ambient temperature | 1 °C (the old PDF mislabels it "BMS/heatsink") |
| `0x130B` | SOC | % |
| `0x130C` | SOH | % (100 = 100 %, **not** "rated capacity") |
| `0x130D` | cycle count | also in `0x2085` |
| `0x131C–0x131F` | limits | charge V, discharge V (× 0.01 V), charge A, discharge A (× 0.1 A) |
| `0x1320–0x1327` | cell statistics | max/min voltage, delta, max/min temperature + sensor IDs |

A single read of `0x1302` with count 10 covers `0x1302…0x130B`.

⚠ **FLA reports dynamic current limits** in `0x131C–0x131F` (e.g. charge limit 250 A → 10 A → 10 A, discharge 250 A → 41 A → 250 A within hours); the LPBF reports a static 80/80 A. A fixed expectation on the FLA produces false alarms. **[measured]**

## Live block `0x0200…` (preferred over `0x132A`)

| Register | Field | Scaling |
|---|---|---|
| `0x0200–0x0203` | charge V limit, discharge V limit, charge I limit, discharge I limit | × 0.1 V / × 0.1 A (e.g. 57.6 V, 48.0 V, 80.0 A) |
| `0x0204` | current | × 0.1 A signed |
| `0x020D` | voltage | × 0.01 V |
| `0x0210` / `0x0211` | SOC / SOH | × 0.1 % |
| `0x0212` | chemistry | 3 = LFP |
| `0x0213` | max cell design voltage | mV |
| `0x0218–0x021B` | max/min cell ID (0-based) and voltage | mV |
| `0x021D`, `0x021F` | max/min cell temperature | × 0.1 °C |
| `0x0220–0x022F` | cell 1–16 voltages | mV |
| `0x0230–0x0237` | temperature sensors 1–8 | × 0.1 °C; `0x7FFF` = no sensor |
| `0x0238` | MOS temperature | × 0.1 °C |

The sum of the cell voltages equals the pack voltage in `0x1306` (FLA: both read 52.670 V in our test). **[measured]**

## Group aggregate `0x0100–0x011F`

Cross-pack values: system limits (the sum of the packs: 250 + 80 + 80 = 410 A), pack count (`0x0114`), max/min cell voltage and temperature with pack/cell position (high byte pack, low byte cell, 0-based). ⚠ `0x0110` "system SOC" mirrors the **master's** SOC — do not use it as an SOC source. **[measured]**

## Info block `0xF800–0xF80F` (16 registers)

| Register | Field |
|---|---|
| `0xF800` | type (112) |
| `0xF801` | **sub-type / model ID**: 2409 = LPBF48200-P, 7500 = FLA48460TG2-EU |
| `0xF802` | communication protocol version (3) |
| `0xF804–0xF808` | serial number: each register is a 4-digit decimal group; take the first `SNLen` characters of the concatenation |
| `0xF809` | SNLen (18) |
| `0xF80B` | MCU1 version (417 on LPBF, 524 on FLA) |
| `0xF80C` | MCU2 version (4 on LPBF, 8 on FLA) |
| `0xF80D–0xF80F` | display HW, control HW, power HW version (`0xFFFF` = n/a) |

## Energy / run-time counters

- **`0x130E–0x131B`** (ChgAh, ChgWh, ChgTime, DcgAh, DcgWh, DcgTime, RunTime) are **not implemented on LPBF48200-P** (garbage; the PDF says so too). On the **FLA they are implemented**, as **word-swapped uint32** (low word first: `regs[i] | regs[i+1] << 16`); `RunTime` counts up live. **[measured]** *Units/scaling are not calibrated.*
- **`0x4406–0x440B`** shown as "energy throughput" are **not energy**: converted to kWh the high words run 63/64/65 with the pack number, and charged and discharged differ by only 0.0014 kWh. Treat them as two unrelated 16-bit values. **[measured]** Use the cycle count (`0x130D`) and your own shunt/meter for energy.
- `0x440E–0x440F`: run time as uint32, ÷ 3600 = hours; survives power cycles. **[measured]**

## Unusable / unclear

- ⛔ **`0x4300–0x431F` "fault event log" and `0x0000–0x00FF` "ring buffer"**: mirrored or stale data (e.g. `0x0000–0x0007` returns the limit block twice; the same register reads `0 0 0 0` once and a plausible limit block the next time). Typical for unmapped addresses. **Do not use as history.** **[measured]**
- `0x440C`: not C14; fixed `0xFF`/`0x00`. `0x4400` = 124 on all packs, unknown. `0x2081` (firmware build) is not reliably readable while other readers are active. `0x2086–0x208F` are uint32 counter pairs with unknown scaling.

## Voltage offset on the FLA

The FLA BMS read +0.11 V high versus two multimeters (52.67 V vs 52.56 V) while being internally consistent. For ΔV before paralleling, **measure across the open disconnector with one meter**; never compare BMS value with meter value. **[measured]**

## EEPROM (`0x2040…`)

`0x2040–0x207F` is the only block writable with FC16. See [eeprom-parameters.md](eeprom-parameters.md) for the names and [errata.md](errata.md) for why the public PDF's table must not be used for writes.
