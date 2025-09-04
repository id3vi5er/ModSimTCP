# Handout: Workplace IP Addresses and Modbus Registers

This document lists the IP addresses for each workplace's PV Inverter and Wallbox simulator. It also provides the Modbus register maps for both device types.

## Workplace IP Assignments

| Workplace | PV Inverter IP | Wallbox IP |
|---|---|---|
| 1 | `10.10.10.120` | `10.10.10.140` |
| 2 | `10.10.10.121` | `10.10.10.141` |
| 3 | `10.10.10.122` | `10.10.10.142` |
| 4 | `10.10.10.123` | `10.10.10.143` |
| 5 | `10.10.10.124` | `10.10.10.144` |
| 6 | `10.10.10.125` | `10.10.10.145` |
| 7 | `10.10.10.126` | `10.10.10.146` |
| 8 | `10.10.10.127` | `10.10.10.147` |
| 9 | `10.10.10.128` | `10.10.10.148` |
| 10 | `10.10.10.129` | `10.10.10.149` |
| 11 | `10.10.10.130` | `10.10.10.150` |
| 12 | `10.10.10.131` | `10.10.10.151` |

---

## Modbus Registers

The simulator provides two types of devices: PV Inverters and Wallboxes. It uses Modbus Holding Registers (read with Function Code 3), and all addresses are 1-indexed.

### PV Inverter Registers (per instance)
The simulator provides a comprehensive set of registers for a **3-phase, 25 kW peak** PV inverter.

| Address | Name | Data Type | Client Factor | Unit | Description |
|---|---|---|---|---|---|
| 1 | AC Voltage L1 | `INT16` | `0.1` | V | AC Voltage Phase 1 |
| 2 | AC Voltage L2 | `INT16` | `0.1` | V | AC Voltage Phase 2 |
| 3 | AC Voltage L3 | `INT16` | `0.1` | V | AC Voltage Phase 3 |
| 4 | AC Current L1 | `INT16` | `0.01` | A | AC Current Phase 1 |
| 5 | AC Current L2 | `INT16` | `0.01` | A | AC Current Phase 2 |
| 6 | AC Current L3 | `INT16` | `0.01` | A | AC Current Phase 3 |
| 7 | Active Power | `INT16` | `1` | W | **Total** Active Power (P) |
| 8 | Reactive Power | `INT16` | `1` | VAR | **Total** Reactive Power (Q) |
| 9 | Apparent Power | `INT16` | `1` | VA | **Total** Apparent Power (S) |
| 10 | Power Factor | `INT16` | `0.01` | - | Average Power Factor (cos φ) |
| 11 | Frequency | `INT16` | `0.01` | Hz | Grid Frequency |
| 12-13 | Daily Yield | `UINT32` | `1` | Wh | Accumulated energy for the day |
| 14-15 | Total Yield | `UINT32` | `1` | kWh | Total accumulated energy |
| 16 | DC Voltage | `INT16` | `0.1` | V | DC Input Voltage (String) |
| 17 | DC Current | `INT16` | `0.01` | A | DC Input Current (String) |
| 18 | DC Power | `INT16` | `1` | W | DC Input Power (P_DC) |
| 19 | Operating State | `INT16` | `1` | - | `1`:Standby, `2`:Feeding, `3`:Fault |
| 20 | Device Temperature | `INT16` | `0.1` | °C | Internal inverter temperature |
| 21 | Fault Code | `INT16` | `1` | - | Active fault code (0 = OK) |
| 22 | Reset Fault | `INT16` | `1` | - | **Write `1` to reset a fault** |

**Note on 32-bit Registers:** `Daily Yield` and `Total Yield` are 32-bit unsigned integers (`UINT32`) that span two 16-bit Modbus registers. When reading, you must query both registers (e.g., starting at address 12 for a length of 2). The server stores values in **High Word First** order.

**Note on Faults:** A fault state (`Operating State` = 3) is now **persistent**. It must be cleared by writing a `1` to the `Reset Fault` register (22).

### Wallbox Registers (per instance)

| Address | Name | Data Type | Client Factor | Unit | Description |
|---|---|---|---|---|---|
| 20 | Wallbox State | `INT16` | `1` | - | `1`:Ready, `2`:Charging, `3`:Fault |
| 21 | Charging Power | `INT16` | `1` | W | Current charging power |
| 22 | State of Charge | `INT16` | `1` | % | SoC of the connected vehicle |
| 23-24 | Charged Energy | `UINT32` | `1` | Wh | Energy transferred in this session |
| 25 | Wallbox Fault Code | `INT16` | `1` | - | `0`:OK, `201`:Charge Fault, `404`:No Car |
| 26 | Remote Control | `INT16` | `1` | - | Write `1`=Start, `0`=Stop. Reads `2`=OK. |
| 27 | Car Connected | `INT16` | `1` | - | `0`:No, `1`:Yes (Read-Only via Modbus) |
| 28 | Reset Fault | `INT16` | `1` | - | **Write `1` to reset a fault** |
