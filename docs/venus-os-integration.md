# Integrating the packs into Victron Venus OS (concept)

This page describes **how** we feed three Felicity packs into a Victron GX / Venus OS system and which traps we hit. It is a design note, **not** a ready-to-install package: no code is published here, and the details depend on your Venus version and your system. Evidence labels: see the [README](../README.md#evidence-labels).

Setup this is based on: Raspberry Pi running Venus OS Large (3.8x), three packs on one RS485 bus (2× LPBF48200-P, 1× FLA48460TG2-EU), Victron MPPT chargers, DVCC on. No CAN link between the packs and the GX; the packs talk Modbus RS485 only.

> ⚠ **Changing a battery service on a GX changes what DVCC, the system SOC and your chargers see.** Test on a bench or with the system in a safe state, and know how to switch the service off again.

## 1. Architecture: one reader, many consumers

```
RS485 ── ONE polling process ── cache ── local HTTP/JSON ──┬── per-pack D-Bus service (x3)
(Modbus FC03)                                              ├── combined "bank" D-Bus service
                                                           ├── dashboard / HA / alarms
                                                           └── (optional) DVCC current-limit bridge
```

- **Exactly one process owns the serial port.** Everything else reads the JSON it publishes. Two Modbus masters on one RS485 bus corrupt each other's frames ([troubleshooting.md](troubleshooting.md)). A manual one-off script on the live bus counts as a second master.
- A pack answers one request in roughly a second; with three packs and several blocks per pack, a full cycle takes a few seconds. Poll the fault word (`0x1304`) in a separate fast loop ([fault-codes.md](fault-codes.md)).
- The JSON should carry the raw registers plus decoded fields (voltage, current, SOC, limits, `FaultCode`, `FaultStatus`, `AlarmStatus`) and the serial/model block, so the D-Bus side stays dumb.

## 2. D-Bus services

| Service | Purpose |
|---|---|
| `com.victronenergy.battery.<name>` per pack | pack-level values for display, history, and per-pack alarms |
| one aggregated `…battery.<combined>` service with its own DeviceInstance | the **bank**: what Venus uses as the system battery (SOC, voltage, current, power) |

- Use **stable, self-chosen service names** (`felicity_battery1` …). Names derived from `ttyUSB` numbers drift when USB enumeration changes. **[measured]**
- Give the bank a DeviceInstance clearly above the per-pack ones (we use 512), so the instances never collide.
- Populate the standard paths (`/Dc/0/Voltage`, `/Dc/0/Current`, `/Dc/0/Power`, `/Soc`, `/Soh`, `/Dc/0/Temperature`, `/Alarms/*`, `/Info/*`, `/Connected`) the way the Victron BMS drivers do. Map the Felicity fault bits to the Victron alarm paths from the `0x1304` bits, **not** from the fault *code* names of the vendor tool ([fault-codes.md](fault-codes.md)).

## 3. Aggregating three packs into a bank

- **Voltage:** the packs are in parallel — use the mean (or the master's value), never the sum.
- **Current and power:** sum. Negative-is-charging in `0x1307` must be mapped to Victron's sign convention (positive = charging into the battery).
- **SOC:** a capacity-weighted mean is the honest figure for unequal packs (200 / 200 / 460 Ah). **Trap:** when a pack drops out for a few seconds, the weights change and the bank SOC jumps (with a 460 Ah pack by >15 percentage points). Keep a *last known good* value per pack with a time-to-live (we use 15 min), and gate values to `0 < SOC ≤ 100`. **[measured]**
- **Limits:** for the bank's charge-voltage limit the smallest pack value wins; the **sum** of the pack charge/discharge current limits is the sensible bank limit — remembering that the FLA reports *dynamic* limits (250 A → 10 A within hours) while the LPBF reports a static 80 A ([registers.md](registers.md)).
- **Cell statistics:** take the min/max across all packs, keep the pack and cell position.

## 4. The three traps that cost us real time

### 4.1 Never register a driver with default values **[measured]**
If the service appears on the D-Bus before the first valid data arrives, the system sees the initial values — `/Soc = 0` in our case. Everything downstream (MQTT, Home Assistant, history) records a 0 % SOC for 30–60 s after **every** restart of the service or reboot of the GX. Fix:
1. create the service **without registering it** (`register=False` in `VeDbusService`),
2. add the paths with `None` as value (shows as unknown), never `0`,
3. call `register()` only after the first valid read,
4. add a **timeout fallback** (we use 90 s): without it two dead packs would keep the service invisible forever, and an automation that reacts to "battery unavailable" could end up power-cycling the host in a loop.

### 4.2 "Service up" and "connected" prove nothing **[measured]**
A service that keeps serving its last cached value looks perfectly healthy. In one incident two packs stopped answering (a loose RS485 cable) and the integration kept reporting 99 % and the old voltage for 17 hours, with `/Connected = 1` and its update counter still counting. The counter counts loop iterations, not successful Modbus answers.
- Make a failed read **visible**: age out the cache, set `/Connected = 0` or drop the value, and log the age of the data.
- Add an **independent staleness check**: identical readings for ≥ 30 min are suspicious *only if something else in the system is moving* (chargers, inverters). In a genuinely quiet system a pack can be bit-identical for 15 min. Comparing packs against each other does **not** work as a freshness test, because they share the bus and fail together. **[measured]**

### 4.3 A syntax-correct edit can silently kill the data **[measured]**
The aggregated service built a dictionary of values once per cycle. Removing a variable's definition but not its use raised a `NameError` inside the loop; the process stayed up (`svstat: up`) while the bank reported SOC = 0, V = 0, I = 0. After every change: read the **D-Bus values**, not the process state.

## 5. DVCC: do not make the bank a "BMS" by accident

The Venus `dbus-systemcalc-py` treats a battery service as a **BMS** as soon as `/Info/MaxChargeVoltage` is set on it; DVCC then takes over the **charge voltage** from that service too. **[source reading, dbus-systemcalc-py]** If you want the chargers to keep their own absorption/float settings and only want the BMS to *limit current*:
- do **not** publish `/Info/MaxChargeVoltage` on the bank service;
- instead write the sum of the packs' charge-current limits to the system's user-set maximum charge current (`/Settings/SystemSetup/MaxChargeCurrent`) from a small separate bridge. DVCC combines it with other limits by taking the minimum.
- Sanity check after any DVCC work: `/Control/SolarChargeVoltage` must still read `0` if you want the chargers to keep their own voltage. If it flips to `1`, something has registered a BMS service. When you stop such a bridge, reset the user-set maximum charge current to "no limit" (`-1`), otherwise the last value stays in force.

Why bother: with a large charger (here a 285 A-class MPPT) and a pack whose own limit can drop from 250 A to 10 A, nothing between the charger and the bank would otherwise limit the current except the BMS cut-off itself.

## 6. Other notes

- **Venus updates:** a Venus firmware update replaces the root file system; custom services, hooks and `/data` additions need a boot-time mechanism that re-creates them (`/data/rc.local`-style hooks). Check the services after every update.
- **Fault visibility:** surface `FaultCode` ("LCD code") and the raw `0x1304` word in your JSON/dashboard. A C13 or C14 is gone from the register before you open the page, so keep a log with timestamps ([`examples/felicity_watch.py`](../examples/felicity_watch.py) shows the idea).
- **Energy counters:** do not publish `0x4406–0x440B` as `/History/ChargedEnergy` — they are not energy ([registers.md](registers.md)). We removed them from the dashboard, D-Bus and Home Assistant.
- **Don't poll faster than the bus can answer.** If packs seem to drop out at random, check the cabling first ([troubleshooting.md](troubleshooting.md)).

## What is not published and why

The integration scripts themselves are tied to one installation (pack/address mapping, instance numbers, local hooks) and need a configuration layer before anyone else could run them safely. If there is interest, that is the next step; until then this page is the design record.
