# EEPROM parameter names

Names and registers as used by the vendor's own tool (EDMS 2.1.1213, classes `BMSHighEEPROMData` / `BMSLowEEPROMData`), **[tool]**. The tool's descriptions are in Chinese; they are not reproduced. Units/ranges are from the tool where it gives them.

⚠ **Read first.** `0x2040–0x207F` is the only block writable with FC16 (protection thresholds, group configuration). A wrong write changes the protection of the pack. Do **not** use the table in section 3.11 of the public PDF — see [errata.md](errata.md). The "Low" block `0x2320–0x237F` is read-only in the tool.

Naming pattern for thresholds: *High / Low* = over / under limit; *Alarm* = warning stage; *Back* = recovery value; *2* = second (shutdown) stage. The order of Alarm and Back inside a group differs between groups; for the current groups of an LPBF the values read back as 70 / 80 / 85 / 120 A in `0x2051–0x2054` — check the semantics on your own pack before writing.

## Group / parallel configuration and fault behaviour (the interesting ones)

| Register | Name | Relevance |
|---|---|---|
| `0x2041` | Hacp Mode Host | host (master) mode |
| `0x2042` | Slave Num | number of modules (master), read-only |
| `0x2043` | Model Address | BMS address of a slave, 1–30 |
| `0x2044` | Model Resistance | CAN termination resistor of a slave |
| `0x2072` | wFaultRstCnt | number of automatic fault restarts (C05/C06/C11/C12) |
| `0x2073` | wFaultClrTime | wait time in s before a retry |
| `0x2076` | wBreakWireMode | break-wire (C14) detection mode |
| `0x2079` | wFaultRecordEn | fault recording on/off — may explain the unusable `0x4300` log |
| `0x2077`/`0x2078` | wBackLightEn / wMenuRtnEn | LCD, "unused" per tool |
| `0x2373` | ParallelDispMode | display mode in parallel operation (Low block) |

Live values of `0x2041–0x2044` were not read on our packs.

## Block `0x2040–0x207F` ("High EEPROM", writable)

| Register | Name (as in the tool) | Unit / range |
|---|---|---|
| `0x2040` | Length |  |
| `0x2041` | Hacp Mode Host Active Config Protocol |  |
| `0x2042` | Slave Num | Read Only |
| `0x2043` | Model Address | 1~30 |
| `0x2044` | Model Resistance |  |
| `0x2045` | Cell Soc Percentage 80 Volt | V 3.2~4.5V |
| `0x2046` | Cell Soc Percentage 20 Volt | V 1.8~3.7V |
| `0x2047` | Cell Volt High 2 | V 3.2~4.5V |
| `0x2048` | Cell Volt Low 2 | V 0.0~3.7V |
| `0x2049` | Cell Volt High Alarm | V 3.2~4.5V |
| `0x204A` | Cell Volt High Alarm Back | V 3.0~4.2V |
| `0x204B` | Cell Volt High | V 3.2~4.5V |
| `0x204C` | Cell Volt High Back | V 3.0~4.2V |
| `0x204D` | Cell Volt Low Alarm | V 2.0~3.7V |
| `0x204E` | Cell Volt Low Alarm Back | V 2.5~3.9V |
| `0x204F` | Cell Volt Low | V 2.0~3.7V |
| `0x2050` | Cell Volt Low Back | V 2.5~3.9V |
| `0x2051` | Battery Charge Current High Alarm Back | A 0~200A |
| `0x2052` | Battery Charge Current High Alarm | A 0~200A |
| `0x2053` | Battery Charge Current High | A 0~200A |
| `0x2054` | Battery Charge Current High 2 | A 0~400A |
| `0x2055` | Battery Discharge Current High Alarm Back | A 0~200A |
| `0x2056` | Battery Discharge Current High Alarm | A 0~200A |
| `0x2057` | Battery Discharge Current High | A 0~200A |
| `0x2058` | Battery Discharge Current High 2 | A 0~400A |
| `0x2059` | Cell Charge Temp High Alarm Back | ℃ 25~75℃ |
| `0x205A` | Cell Charge Temp High Alarm | ℃ 25~75℃ |
| `0x205B` | Cell Charge Temp High | ℃ 25~75℃ |
| `0x205C` | Cell Charge Temp High 2 | ℃ 25~75℃ |
| `0x205D` | Cell Charge Temp Low Alarm Back | ℃ -25~25℃ |
| `0x205E` | Cell Charge Temp Low Alarm | ℃ -25~25℃ |
| `0x205F` | Cell Charge Temp Low | ℃ -25~25℃ |
| `0x2060` | Cell Charge Temp Low 2 | ℃ -25~25℃ |
| `0x2061` | Cell Discharge Temp High Alarm Back | ℃ 25~75℃ |
| `0x2062` | Cell Discharge Temp High Alarm | ℃ 25~75℃ |
| `0x2063` | Cell Discharge Temp High | ℃ 25~75℃ |
| `0x2064` | Cell Discharge Temp High 2 | ℃ 25~75℃ |
| `0x2065` | Cell Discharge Temp Low Alarm Back | ℃ -25~25℃ |
| `0x2066` | Cell Discharge Temp Low Alarm | ℃ -25~25℃ |
| `0x2067` | Cell Discharge Temp Low | ℃ -25~25℃ |
| `0x2068` | Cell Discharge Temp Low 2 | ℃ -25~25℃ |
| `0x2069` | Heat Sink Temp High Alarm | ℃ 35~119℃ |
| `0x206A` | Heat Sink Temp High | ℃ 35~119℃ |
| `0x206B` | Equalization Enable |  |
| `0x206C` | Equalization Volt Difference | V 0~0.5V |
| `0x206D` | Equalization Volt Start | V 2.5~4V |
| `0x206E` | wBalanceTempEn | ℃ |
| `0x206F` | wCellDcgDepth | % |
| `0x2070` | wCellTempCoef |  |
| `0x2072` | wFaultRstCnt |  |
| `0x2073` | wFaultClrTime | sec |
| `0x2074` | wIdleExitTime | min |
| `0x2075` | wSleepExitTime | min |
| `0x2076` | wBreakWireMode |  |
| `0x2077` | wBackLightEn |  |
| `0x2078` | wMenuRtnEn |  |
| `0x2079` | wFaultRecordEn |  |
| `0x207E` | wRandomNum |  |
| `0x207F` | wCheckSum |  |

`0x2040` ("Length") read 64 on our packs — most likely the block length (64 registers) rather than a capacity **[inference]**.

## Block `0x2320–0x237F` ("Low EEPROM", read-only in the tool)

| Register | Name (as in the tool) | Unit / range |
|---|---|---|
| `0x2320` | EEEepromLength |  |
| `0x2321` | Battery Type |  |
| `0x2322` | BattCapRated | AH |
| `0x2323` | Battery Cell Num |  |
| `0x2324` | CellVoltRated | V |
| `0x2325` | CellChgVoltHiLimit | V |
| `0x2326` | CellChgVoltLoLimit | V |
| `0x2327` | CellChgCurrHiLimit | A |
| `0x2328` | CellDcgCurrHiLimit | A |
| `0x2329` | Cell Soc Full Volt | V |
| `0x232A` | Cell Soc 95 Percentage Volt | V |
| `0x232B` | Cell Soc 05 Percentage Volt | V |
| `0x232C` | Cell Soc Empty Volt | V |
| `0x232D` | BattFloatTime | s |
| `0x232E` | BattDcgDepth | % |
| `0x232F` | BattSocAdjPrd | day |
| `0x2330` | BattCycleLife |  |
| `0x2331` | FaultRstCnt |  |
| `0x2332` | FaultClrTime | s |
| `0x2333` | IdleExitTime | min |
| `0x2334` | SleepExitTime | min |
| `0x2335` | FanSelfChkEn |  |
| `0x2336` | CellLoMode |  |
| `0x2337` | BattPackMode |  |
| `0x2338` | BattVoltHiAlm | V |
| `0x2339` | BattVoltHiAlmBack | V |
| `0x233A` | BattVoltHi | V |
| `0x233B` | BattVoltHiBack | V |
| `0x233C` | BattVoltLoAlm | V |
| `0x233D` | BattVoltLoAlmBack | V |
| `0x233E` | BattVoltLo | V |
| `0x233F` | Battery Volt Low Back | V |
| `0x2340` | Cell Volt High Alarm | V |
| `0x2341` | Cell Volt High Alarm Back | V |
| `0x2342` | Cell Volt High | V |
| `0x2343` | Cell Volt High Back | V |
| `0x2344` | Cell Volt Low Alarm | V |
| `0x2345` | Cell Volt Low Alarm Back | V |
| `0x2346` | Cell Volt Low | V |
| `0x2347` | Cell Volt Low Back | V |
| `0x2348` | Battery Charge Current High Alarm | A |
| `0x2349` | Battery Charge Current High Alarm Back | A |
| `0x234A` | Battery Charge Current High | A |
| `0x234B` | Battery Discharge Current High Alarm | A |
| `0x234C` | Battery Discharge Current High Alarm Back | A |
| `0x234D` | Battery Discharge Current High | A |
| `0x234E` | Cell Charge Temp High Alarm | ℃ |
| `0x234F` | Cell Charge Temp High | ℃ |
| `0x2350` | Cell Charge Temp Low Alarm | ℃ |
| `0x2351` | Cell Charge Temp Low | ℃ |
| `0x2352` | Cell Discharge Temp High Alarm | ℃ |
| `0x2353` | Cell Discharge Temp High | ℃ |
| `0x2354` | Cell Discharge Temp Low Alarm | ℃ |
| `0x2355` | Cell Discharge Temp Low | ℃ |
| `0x2356` | BattTempHiAlm | ℃ |
| `0x2357` | BattTempHi | ℃ |
| `0x2358` | BattTempLoAlm | ℃ |
| `0x2359` | BattTempLo | ℃ |
| `0x235A` | FanLockChkEn |  |
| `0x235B` | CellOpenChkEn |  |
| `0x235C` | BattOpReverseEn |  |
| `0x235D` | BattOpShortEn |  |
| `0x235E` | Cell Equalization Enable |  |
| `0x235F` | Cell Equalization Volt Difference | V |
| `0x2360` | Cell Equalization Volt Start | V |
| `0x2361` | CellEqVoltStop | V |
| `0x2362` | CellEqTempStop | ℃ |
| `0x2363` | CellEqTempBack | ℃ |
| `0x2364` | CellTempCompCoef0 |  |
| `0x2365` | CellTempCompCoef1 |  |
| `0x2366` | CellTempCompCoef2 |  |
| `0x2367` | CellTempCompCoef3 |  |
| `0x2368` | CellTempCompCoef4 |  |
| `0x2369` | CellTempCompCoef5 |  |
| `0x236A` | CellTempCompCoef6 |  |
| `0x236B` | CellTempCompCoef7 |  |
| `0x236C` | CellTempCompCoef8 |  |
| `0x236D` | CellTempCompCoef9 |  |
| `0x236E` | CellTempCompCoef10 |  |
| `0x236F` | CellTempCompCoef11 |  |
| `0x2370` | CellTempCompCoef12 |  |
| `0x2371` | CellTempCompCoef13 |  |
| `0x2372` | CellTempCompCoef14 |  |
| `0x2373` | ParallelDispMode |  |
| `0x237F` | EECheckSum |  |
