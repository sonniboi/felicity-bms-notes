# How the findings were obtained — and their limits

## Sources

| Source | Used for |
|---|---|
| Live Modbus reads on three packs (2× LPBF48200-P, 1× FLA48460TG2-EU), partly continuous since early 2026 | everything labelled **[measured]** |
| Vendor manuals (LPBA48300 fault table, FLA48460-EU user guide, FLA48314-EU, LPBA48200 variants) | **[manual]**: DIP switches, fault table, parallel rules |
| Vendor monitoring tool EDMS 1.71 and 2.1 (.NET) — decompiled with ILSpy | **[tool]**: register lists, enums, EEPROM parameter names |
| Firmware update files distributed by the vendor with its tool (GD303 V416/V417, GD305 V516/V518, ComBox V102) — static analysis in Ghidra | **[firmware]**: fault logic, C13 mechanism |

## Limits

- **Static analysis only.** Function behaviour was read from decompiler output, not observed on a pack or with a bus capture. The decompiler occasionally drops arguments; one early mistake (the `0x1000` bit in the *alarm* word was mistaken for the fault word) was caught and corrected by cross-checking.
- **Not available:** FLA master firmware V524 and the LCD firmware. Statements about the FLA rest on the sibling GD305 firmware and on measurements. The LCD mapping (code = bit + 1) is supported by the manual and by the firmware, but the LCD firmware itself was not seen.
- **Nothing was flashed**, no vendor tool was run against a pack, and nothing from the vendor's download was executed on the machine used for analysis.
- Network search for the missing firmware found nothing public; it is distributed through the vendor and dealers only.

## What is deliberately not published here

Vendor firmware, vendor software, manuals, PDFs, decompiled code and function listings. Only findings, register numbers and names (for interoperability) and our own measurements.

## Reproducing the key checks yourself

- **Fault mapping:** read `0x1303` and `0x1304` together while a fault is active; for a single fault `0x1303` must equal (bit number in `0x1304`) + 1, with several faults it shows the one that occurred *first*. Use [`examples/felicity_read.py`](../examples/felicity_read.py).
- **Duplicate address / C13:** with two packs deliberately set to the same ID (stand-alone bench, no load), C13 should appear within ~10 s. We did **not** test this; it is the prediction of the firmware analysis.
- **Errata 3.11:** read `0x2049–0x2058` on a healthy pack and compare units and magnitudes with the PDF table. Read only.
