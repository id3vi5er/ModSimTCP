# PV Simulator with Modbus TCP

This script simulates multiple photovoltaic (PV) systems, each with its own Modbus TCP server instance. It's primarily designed as a data source for home automation systems like Symcon or for testing Modbus client implementations that need to interact with multiple devices.

## Purpose

The main goal is to provide a simple way to generate realistic-looking PV system data (voltage, current, and power) from multiple simulated sources. Each source runs as an independent Modbus TCP server on a unique IP address. The simulation includes a daily cycle for current generation, mimicking the sun's rise and fall, with slight variations for each instance.

## Configuration

The script has several configuration options at the beginning of `main.py`:

*   `HOST_IPS`: (Default: `['192.168.178.201', ..., '192.168.178.212']`) A list of IP addresses on which the Modbus TCP server instances will listen. Each IP in this list will host a separate Modbus server.
*   `TCP_PORT`: (Default: `5020`) The TCP port for all Modbus server instances. 5020 is used as port 502 (standard Modbus) might require root privileges.
*   `UPDATE_INTERVAL_SECONDS`: (Default: `2`) How frequently the simulated PV values are updated for each instance, in seconds.
*   `SCALING_FACTOR`: (Default: `10.0`) Modbus registers are 16-bit integers. To represent floating-point numbers like voltage and current, these values are multiplied by this factor before being sent. The client (e.g., Symcon) will need to divide the received values by this factor.

## Modbus Registers (per instance)

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
    The script will launch multiple Modbus TCP server instances, one for each IP address defined in `HOST_IPS`. You'll see log messages indicating value updates for each instance. Press Ctrl+C to shut down all servers.

## Simulation Logic (per instance)

Each server instance simulates PV data with slight variations:

*   **Voltage:** Simulated as a relatively stable AC voltage around 230V with minor random fluctuations, slightly varied per instance.
*   **Current:** Simulates a daily solar generation cycle using a sine wave. The current output gradually increases from 0A, peaks (peak value slightly varied per instance, around 15A), and then decreases back to 0A. The phase of this daily cycle is also slightly offset for each instance to provide more diverse data.
*   **Power:** Calculated simply as `Power = Voltage * Current`.

## Note for Symcon Users (and other clients)

When reading the values in your Modbus client (e.g., IP-Symcon) from any of the configured IP addresses:

*   **Voltage:** The value read from `VOLTAGE_REGISTER` must be divided by `SCALING_FACTOR` (default 10.0) to get the actual voltage in Volts.
*   **Current:** The value read from `CURRENT_REGISTER` must be divided by `SCALING_FACTOR` (default 10.0) to get the actual current in Amperes.
*   **Power:** The value read from `POWER_REGISTER` is the direct power in Watts and does not need to be divided by `SCALING_FACTOR`.

The script will print the simulated values to the console, which can be helpful for verification:
`Update: U=230.1V, I=7.50A, P=1725W`

## Network Configuration (Ubuntu with Netplan)

For the script to bind to the configured `HOST_IPS`, these IP addresses must be assigned to a network interface on the machine running the script. Here's an example of how to configure this using `netplan` on an Ubuntu system.

**Disclaimer:** The exact network interface name (e.g., `eth0`, `ens18`, `enp0s3`) will vary depending on your system. Use commands like `ip addr` or `ls /sys/class/net` to identify your interface name.

1.  **Create or edit a Netplan configuration file.**
    These files are typically located in `/etc/netplan/`. For example, you could create a file named `01-custom-ips.yaml`.

2.  **Add the IP addresses to your interface.**
    Below is an example configuration. **Replace `ens18` with your actual network interface name.** The example assumes your primary network configuration (e.g., DHCP or a static IP for the main address) is handled by another file (like `00-installer-config.yaml` or similar) or you can integrate this into your existing configuration.

    ```yaml
    # /etc/netplan/01-custom-ips.yaml
    network:
      version: 2
      renderer: networkd
      ethernets:
        ens18: # <-- IMPORTANT: Replace with your actual interface name
          # If your interface gets its main IP via DHCP, you might have:
          # dhcp4: true
          # If it has a primary static IP, that would be listed here too.
          # Add the simulator IPs as additional addresses:
          addresses:
            # Add your primary static IP here if you have one and it's not managed elsewhere
            # - 192.168.178.100/24
            - 192.168.178.201/24
            - 192.168.178.202/24
            - 192.168.178.203/24
            - 192.168.178.204/24
            - 192.168.178.205/24
            - 192.168.178.206/24
            - 192.168.178.207/24
            - 192.168.178.208/24
            - 192.168.178.209/24
            - 192.168.178.210/24
            - 192.168.178.211/24
            - 192.168.178.212/24
          # Gateway and DNS settings are typically part of your primary IP configuration
          # gateway4: 192.168.178.1
          # nameservers:
          #   addresses: [8.8.8.8, 1.1.1.1]
    ```

3.  **Apply the configuration:**
    After saving the file, apply the changes with:
    ```bash
    sudo netplan apply
    ```

4.  **Verify the IP addresses:**
    You can check if the IPs are assigned using:
    ```bash
    ip addr show dev ens18 # <-- Replace with your interface name
    ```
    You should see all the configured IP addresses listed for the interface.

Once these IP addresses are active on your network interface, the Python script should be able to bind its Modbus server instances to them.
