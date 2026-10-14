# DIP switches, pack IDs, parallel operation and C13

## DIP switches **[manual]**

| Switch | Function |
|---|---|
| SW1–SW4 | Pack ID 0–15, binary, SW1 = 1 |
| SW5 | 120 Ω termination of the parallel bus |

- **ID 0 = stand-alone.** The parallel condition is not checked, communication address `0x00/0x10`. A pack with ID 0 cannot raise C13.
- **ID 1–15 = parallel operation.** The Modbus address equals the ID.
- **Termination:** the **last** pack must have SW5 ON, otherwise communication can be disturbed. The first pack carries SW5 as well.
- Codes by number of packs (manual): 1 pack `1,5` · 2 packs `1,5` / `2,5` · **3 packs `1,5` / `2` / `1,2,5`** · 4 packs `1,5` / `2` / `1,2` / `3,5` … (numbers = switches ON).
- **Parallel condition:** with ID 1–15 a pack checks that its voltage differs by **< 3 V** from all other packs, otherwise it waits. *Not found in the analysed firmware* **[manual only]**.
- **Group on/off:** switching one pack on turns all on; switching one off turns all off. **[manual]**
- The manuals forbid mixing model families (an FLA only pairs with FLA). A mixed LPBF + FLA bus works electrically and on RS485, but is outside the specification.

## Modbus addresses in a parallel group **[measured]**

The Modbus address follows the pack ID (master → 1, slave 1 → 2, slave 2 → 3). A freshly changed DIP setting only takes effect after a power cycle; before that a pack may answer on its old address. **Re-scan `0xF801` (model ID) per address after every DIP change or power cycle**: `2409` = LPBF48200-P, `7500` = FLA48460TG2-EU.

## What C13 is **[firmware]**

C13 is **not** a voltage or current event. It is a failure of the role/address protocol on the parallel (CAN) bus. Identical logic was found in four firmware versions (416, 417, 516, 518).

- Every pack broadcasts a **role heartbeat every 200 ms**. The data byte is `0x50` = master, `0x51` = slave, `0x52` = undecided.
- 29-bit CAN identifier: type in bits 27..24, sender address + `0x10` in bits 23..16, destination in bits 15..8, code in bits 7..0. The sender address is 0–15.
- Receivers keep three address masks (undecided / slave / master). Every received heartbeat sets the sender's bit; entries expire after **3 s**.
- **Role state machine:**
  - undecided → **slave** after 3 s without collision;
  - slave → **master** after 2 s with no master and no slave with a lower address;
  - master → undecided if a master with a lower address is heard for more than 5 s.
- **C13 fires when a pack's *own* address bit is set by other packs' heartbeats for 10 s** — state undecided: any mask; slave: slave or master mask; master: master mask.
- That means: **two packs with the same address**, or **the pack receives its own frames back** (loop, reflection, a second path). Result: fault code 13, flag `0x1000`, fault mode.

### Practical consequences

- Check for duplicate pack IDs first (read `0xF804…` serial numbers and address per pack).
- Check the parallel cables and termination (SW5 on first and last pack only).
- A transient C13 can come from a pack that restarts and briefly announces "undecided" — not necessarily from a wiring defect.
- Manufacturer's text for C13: check whether a single unit is installed in a parallel system; if the cabling is fine, complete the parallel installation first and then restart the device.

### Group configuration in EEPROM

`0x2041` host mode, `0x2042` slave count (read-only), `0x2043` BMS address (1–30), `0x2044` CAN termination resistor — see [eeprom-parameters.md](eeprom-parameters.md). Live values of these registers were **not** read on our packs, so their relation to the DIP-set address is **[unverified]**.
