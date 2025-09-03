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
The simulator provides a comprehensive set of registers for a detailed PV inverter simulation.

| Address | Name | Data Type | Client Factor | Unit | Description |
|---|---|---|---|---|---|
| 1 | AC Voltage | `INT16` | `0.1` | V | AC Line-to-Neutral Voltage |
| 2 | AC Current | `INT16` | `0.01` | A | AC Output Current |
| 3 | Apparent Power | `INT16` | `1` | VA | Apparent Power (S = U * I) |
| 4 | Active Power | `INT16` | `1` | W | Real Power (P) |
| 5 | Power Factor | `INT16` | `0.01` | - | Power Factor (cos φ) |
| 6 | Reactive Power | `INT16` | `1` | VAR | Reactive Power (Q) |
| 7 | Frequency | `INT16` | `0.01` | Hz | Grid Frequency |
| 8-9 | Daily Yield | `UINT32` | `1` | Wh | Accumulated energy for the day |
| 10-11 | Total Yield | `UINT32` | `1` | kWh | Total accumulated energy |
| 12 | Operating State | `INT16` | `1` | - | `1`:Standby, `2`:Feeding, `3`:Fault |
| 13 | Device Temperature | `INT16` | `0.1` | °C | Internal inverter temperature |
| 14 | Fault Code | `INT16` | `1` | - | Active fault code (0 = OK) |
| 15 | DC Voltage | `INT16` | `0.1` | V | DC Input Voltage |
| 16 | DC Current | `INT16` | `0.01` | A | DC Input Current |
| 17 | DC Power | `INT16` | `1` | W | DC Input Power (P_DC) |

**Note on 32-bit Registers:** `Daily Yield` and `Total Yield` are 32-bit unsigned integers (`UINT32`) that span two 16-bit Modbus registers. When reading, you must query both registers (e.g., starting at address 8 for a length of 2). The server stores values in **High Word First** order.

### Wallbox Registers (per instance)

| Address | Name | Data Type | Client Factor | Unit | Description |
|---|---|---|---|---|---|
| 20 | Wallbox State | `INT16` | `1` | - | `1`:Ready, `2`:Charging, `3`:Fault |
| 21 | Charging Power | `INT16` | `1` | W | Current charging power |
| 22 | State of Charge | `INT16` | `1` | % | SoC of the connected vehicle |
| 23-24 | Charged Energy | `UINT32` | `1` | Wh | Energy transferred in this session |
| 25 | Wallbox Fault Code | `INT16` | `1` | - | Active fault code (0=OK, 201=...) |
| 26 | Remote Control | `INT16` | `1` | - | Write `1` to start, `2` to stop |
