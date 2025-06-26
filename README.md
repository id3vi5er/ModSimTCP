# PV Simulator with Modbus TCP

This script simulates a photovoltaic (PV) system and makes its data available via a Modbus TCP server. It's primarily designed as a data source for home automation systems like Symcon or for testing Modbus client implementations.

## Purpose

The main goal is to provide a simple way to generate realistic-looking PV system data (voltage, current, and power) that can be read by any Modbus TCP client. The simulation includes a daily cycle for current generation, mimicking the sun's rise and fall.

## Configuration

The script has several configuration options at the beginning of `main.py`:

*   `HOST_IP`: (Default: `'192.168.178.13'`) The IP address the Modbus TCP server will listen on. Change this to `'0.0.0.0'` to listen on all available network interfaces.
*   `TCP_PORT`: (Default: `5020`) The TCP port for the Modbus server. 502 is the standard Modbus TCP port.
*   `UPDATE_INTERVAL_SECONDS`: (Default: `2`) How frequently the simulated PV values are updated, in seconds.
*   `SCALING_FACTOR`: (Default: `10.0`) Modbus registers are 16-bit integers. To represent floating-point numbers like voltage and current, these values are multiplied by this factor before being sent. The client (e.g., Symcon) will need to divide the received values by this factor.

## Modbus Registers

The simulator uses Modbus Holding Registers (read with Function Code 3). The register addresses are 0-indexed:

*   **Register 0 (`VOLTAGE_REGISTER`):** Simulated AC voltage (U).
    *   Value is scaled by `SCALING_FACTOR`.
*   **Register 1 (`CURRENT_REGISTER`):** Simulated AC current (I).
    *   Value is scaled by `SCALING_FACTOR`.
*   **Register 2 (`POWER_REGISTER`):** Calculated AC power (P = U * I).
    *   Value is sent as a whole number (Watts), not scaled by `SCALING_FACTOR`.

## Running the Script

1.  **Dependencies:**
    The script requires the `pymodbus` library. You can install it using pip:
    ```bash
    pip install pymodbus
    ```

2.  **Execution:**
    Run the script from your terminal:
    ```bash
    python3 main.py
    ```
    The server will start, and you'll see log messages indicating value updates.

## Simulation Logic

*   **Voltage:** Simulated as a relatively stable AC voltage around 230V with minor random fluctuations.
*   **Current:** Simulates a daily solar generation cycle using a sine wave. The current output gradually increases from 0A, peaks around 15A (simulating midday sun), and then decreases back to 0A (simulating night). This cycle is sped up for demonstration purposes.
*   **Power:** Calculated simply as `Power = Voltage * Current`.

## Note for Symcon Users (and other clients)

When reading the values in your Modbus client (e.g., IP-Symcon):

*   **Voltage:** The value read from `VOLTAGE_REGISTER` must be divided by `SCALING_FACTOR` (default 10.0) to get the actual voltage in Volts.
*   **Current:** The value read from `CURRENT_REGISTER` must be divided by `SCALING_FACTOR` (default 10.0) to get the actual current in Amperes.
*   **Power:** The value read from `POWER_REGISTER` is the direct power in Watts and does not need to be divided by `SCALING_FACTOR`.

The script will print the simulated values to the console, which can be helpful for verification:
`Update: U=230.1V, I=7.50A, P=1725W`
