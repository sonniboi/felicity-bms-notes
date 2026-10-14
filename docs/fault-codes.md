# Fault codes (C01–C14) and the registers behind them

Applies to LPBF48200-P (firmware 416/417) and, by firmware of the same family (GD305 V516/V518) and by observation, to the FLA48460TG2-EU. The FLA's own master firmware (V524) was not analysed.

## The two registers

| Register | Name | Meaning |
|---|---|---|
| `0x1304` | BmsFaultFlag | Bitfield of **all** active faults. Bit *n* ↔ code C(*n*+1). |
| `0x1303` | BmsFaultCode | Code of the **first** active fault = (bit number) + 1. Stays until **all** flags are 0. **[firmware]** |
| `0x1305` | BmsAlarmFlag | Warnings (no shutdown); a separate bitfield, not the fault word. |

Example: `0x1304 = 0x1001` → bits 0 and 12 → **C01 + C13**. `0x1303` shows 1 or 13 depending on which came first. The LCD shows `voltage / "Cxx" / SOC`. **[manual]**

## C-code ↔ bit table

| Code | Bit | Meaning | Source |
|---|---|---|---|
| C01 | 0 | Battery overvoltage | [manual] [tool] |
| C02 | 1 | Battery undervoltage | [manual] [tool] |
| C03 | 2 | Cell overvoltage | [firmware] |
| C04 | 3 | Cell undervoltage | [firmware] |
| C05 | 4 | Charge overcurrent | [firmware] [manual] |
| C06 | 5 | Discharge overcurrent | [firmware] [manual] |
| C07 | 6 | MOS overtemperature | [firmware] |
| C08 | 7 | MOS undertemperature | [manual] [tool] |
| C09 | 8 | Cell overtemperature | [firmware] |
| C10 | 9 | Cell undertemperature | [firmware] |
| C11 | 10 | Abnormal current sampling | [manual] [tool] |
| C12 | 11 | Abnormal output impedance | [manual] [tool] |
| C13 | 12 | Parallel failed | [manual] [firmware] — see [dip-and-parallel.md](dip-and-parallel.md) |
| C14 | 13 | Output loss (break wire) | [manual] [tool] |
| — | 14 | "Pirated" detection (not in the manual's C-code list; by the bit + 1 rule it would be code 15) | [tool], code [unverified] |

Further fault flags exist in the tool without a C code (battery open, boot fault, overload). **[tool]**

⚠ **C14 is bit 13 of `0x1304`**, *not* register `0x440C` (which stays `0xFF`/`0x00` regardless of C14). **[measured]** C14 is intermittent: the LCD latches it, the register may already be 0 at the next poll — poll `0x1304` fast (we use ~500 ms) and OR the bits until consumed.

## Wrong names in the vendor tool

The vendor's Windows tool (EDMS) has two enums. Its **bit enum** (`BmsFaultFlagEnum`, used to decode `0x1304`) is correct. Its **code enum** (`BmsFaultCode`, used to name `0x1303`) is shifted for IDs 3–10:

| Code | EDMS shows | Firmware sends / manual says |
|---|---|---|
| 3 | charge current high | cell overvoltage |
| 4 | discharge current high | cell undervoltage |
| 5 | cell overvoltage | charge overcurrent |
| 6 | cell undervoltage | discharge overcurrent |
| 7 / 8 | cell temperature | MOS over-/undertemperature |
| 9 / 10 | MOS temperature | cell over-/undertemperature |

**Rule: derive names from the bits of `0x1304`, or use the table above — not from EDMS's status line.** **[firmware] [tool]**

## Self-healing faults

C05, C06, C11, C12 (mask `0xC30`) are cleared by a timer and retried, controlled by EEPROM `0x2072` (number of retries) and `0x2073` (wait time, s). The manual says: current limit exceeded for 15 s → both directions off; fault clears after 1 minute; after 10 events a manual restart is required. **[firmware] [manual]**

The other faults clear when their condition has gone (with hysteresis and a debounce counter). This explains why a fault can be gone between two polls.

## C13 has no clear path of its own

No dedicated clear for bit 12 was found. The fault flags are zeroed completely when the protection parameters are re-initialised; that is probably how C13 disappears. Observed: C13 on a LPBF pack disappeared after ~20 polls (≈ tens of seconds). **[firmware, partly unverified]**

## Warning bits `0x1305`

15 bits, names from the tool: Bat V High, Bat V Low, Cell V High, Cell V Low, Charge I High, Discharge I High, MOS Temp High, MOS Temp Low, Cell Temp High, Cell Temp Low, Fan Locked, EEPROM RW, ADC Timing, Float Timeout, Cell V Error High. Bits 2–6, 8, 9 are confirmed in the firmware as the alarm level of the fault of the same name; the other names are **[unverified]**.
