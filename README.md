# PV Simulator with Modbus TCP

This script simulates multiple photovoltaic (PV) inverters, each with its own Modbus TCP server instance. It's designed as a data source for home automation systems like IP-Symcon or for testing Modbus client implementations that need to interact with multiple devices.

A specific German-language guide for setup is available here: [Anleitung.md](Anleitung.md)

## Features

*   **Multiple Modbus Servers**: Simulates 12 independent PV inverters, each on its own IP address.
*   **Realistic Data**: Generates dynamic data for voltage, current, and power, simulating a daily solar cycle.
*   **Web Monitoring UI**: A built-in Flask web server provides a dashboard to monitor all simulated inverters in real-time.
*   **Configurable**: Easily change IP addresses, port, and update speed in the `main.py` script.

## Configuration

Key options at the top of `main.py`:

*   `HOST_IPS`: (Default: `10.10.10.120` to `10.10.10.131`) A list of IP addresses where the Modbus TCP servers will listen.
*   `TCP_PORT`: (Default: `5020`) The TCP port for all Modbus server instances.
*   `UI_HOST`: (Default: `0.0.0.0`) The host address for the web monitoring UI.
*   `UI_PORT`: (Default: `5010`) The port for the web monitoring UI.
*   `SCALING_FACTOR`: (Default: `10.0`) A multiplier for voltage and current values to allow for decimals over Modbus.

## Modbus Registers (per instance)

The simulator uses Modbus Holding Registers (read with Function Code 3). The register addresses are 1-indexed:

*   **Register 1 (`VOLTAGE_REGISTER`):** Simulated AC voltage (U).
    *   Value is scaled by `SCALING_FACTOR`.
*   **Register 2 (`CURRENT_REGISTER`):** Simulated AC current (I).
    *   Value is scaled by `SCALING_FACTOR`.
*   **Register 3 (`POWER_REGISTER`):** Calculated AC power (P = U * I).
    *   Value is sent as a whole number (Watts), not scaled.

## Running the Simulator

### 1. Network Configuration (Required)

For the script to work, the host machine must be assigned the IP addresses used by the simulators. Both the machine running the script and the client (e.g., IP-Symcon) must be in the same subnet to communicate.

Here is an example configuration for **Ubuntu/Debian using `netplan`**.

1.  **Identify your network interface name** (e.g., `eth0`, `ens18`) using `ip addr`.

2.  **Create or edit a netplan config file** in `/etc/netplan/`, for example `01-custom-ips.yaml`.

3.  **Add the required IP addresses.** The following configuration sets a static primary IP (`10.10.10.115`) and adds all the simulator IPs. **Replace `ens18` with your interface name.**

    ```yaml
    # /etc/netplan/01-custom-ips.yaml
    network:
      version: 2
      renderer: networkd
      ethernets:
        ens18: # <-- IMPORTANT: Replace with your network interface name
          dhcp4: no
          addresses:
            - 10.10.10.115/24   # Primary IP for the server
            - 10.10.10.120/24   # First simulator IP
            - 10.10.10.121/24
            - 10.10.10.122/24
            - 10.10.10.123/24
            - 10.10.10.124/24
            - 10.10.10.125/24
            - 10.10.10.126/24
            - 10.10.10.127/24
            - 10.10.10.128/24
            - 10.10.10.129/24
            - 10.10.10.130/24
            - 10.10.10.131/24
          routes:
            - to: default
              via: 10.10.10.1
          nameservers:
            addresses: [10.10.10.1]
    ```

4.  **Apply the new network configuration:**
    ```bash
    sudo netplan apply
    ```
    Verify the IPs are assigned with `ip addr show dev ens18`.

### 2. Install Dependencies

The script requires `pymodbus` for the Modbus servers and `flask` for the web UI.
```bash
pip install pymodbus flask
```

### 3. Launch the Script

Run the script from your terminal:
```bash
python3 main.py
```
The script will confirm the launch of all 12 Modbus servers and the web UI. Press `Ctrl+C` to stop.

## Web Monitoring UI

Once running, you can view the status of all simulators via the web dashboard.
*   **URL**: `http://<your-server-ip>:5010`
*   Example: `http://10.10.10.115:5010`

The dashboard shows each inverter's IP, status, and real-time voltage, current, and power data.

## Adding a Simulator to IP-Symcon (Example)

This guide explains how to add one of the simulated inverters to IP-Symcon.

### Step 1: Create Modbus Gateway

1.  In the IP-Symcon Object Tree, add a **Modbus Gateway**.
2.  Set the **Connection** to **Modbus TCP**.
3.  Enter the IP and Port for one of the simulated devices.
    *   **Host**: `10.10.10.120` (or another IP from the `HOST_IPS` list)
    *   **Port**: `5020`
4.  Apply the settings.

### Step 2: Create Modbus Device

1.  Add a **Modbus Device** and select the gateway you just created as its parent.
2.  Set the **Device ID** to `1`.

### Step 3: Configure Addresses (Variables)

In the device's **Addresses** list, add an entry for each value you want to read.

*   **Voltage**
    *   **Address**: `1` (`VOLTAGE_REGISTER`)
    *   **Function**: `Read Holding Registers (3)`
    *   **Data Type**: `INT16`
    *   **Factor**: `0.1` (to divide by the `SCALING_FACTOR` of 10.0)

*   **Current**
    *   **Address**: `2` (`CURRENT_REGISTER`)
    *   **Function**: `Read Holding Registers (3)`
    *   **Data Type**: `INT16`
    *   **Factor**: `0.1`

*   **Power**
    *   **Address**: `3` (`POWER_REGISTER`)
    *   **Function**: `Read Holding Registers (3)`
    *   **Data Type**: `INT16`
    *   **Factor**: `1` (no scaling)

### Step 4: Finalize

1.  Check the **Active** box for each address to create the variables.
2.  Click **Apply**.

The live data from the simulator should now appear in your IP-Symcon Object Tree.
