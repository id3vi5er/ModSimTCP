#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import math
import random
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext

# --- Globale Daten und Sperren ---
# Thread-sichere Datenablage für den UI-Status
server_data = {}
data_lock = threading.Lock()


# --- Konfiguration ---
# List of IP addresses for the Modbus servers
# HOST_IPS = [f"192.168.{51 + i}.100" for i in range(12)]
HOST_IPS = [f"10.10.10.{120 + i}" for i in range(12)]
TCP_PORT = 5020      # Standard Modbus TCP Port (using 5020 as 502 might require root)
UPDATE_INTERVAL_SECONDS = 2  # Wie oft die Werte aktualisiert werden (in Sekunden)

# Register-Adressen (beginnend bei 0)
# Wir verwenden Holding Registers (Funktionscode 3)
VOLTAGE_REGISTER = 1   # Spannung (U)
CURRENT_REGISTER = 2   # Strom (I)
POWER_REGISTER = 3     # Leistung (P)

# Skalierungsfaktor: Modbus Register sind 16-Bit Integer.
# Um Fließkommazahlen zu senden, multiplizieren wir sie mit einem Faktor.
# Symcon muss den empfangenen Wert durch diesen Faktor teilen.
SCALING_FACTOR = 10.0

def simulate_pv_values(datablock, instance_id, host_ip):
    """
    Diese Funktion läuft in einem separaten Thread und aktualisiert
    kontinuierlich die Werte im Modbus Datastore für eine bestimmte Instanz.
    """
    print(f"Starte Simulation der PV-Werte für Instanz {instance_id}...")
    
    # Ein Zähler, um einen Tagesverlauf zu simulieren
    day_cycle_counter = instance_id * 30 # Offset based on instance_id for variety

    while True:
        try:
            # ... (Rest der Funktion bleibt unverändert)
            voltage = 230.0 + (random.random() - 0.5) + (instance_id % 5 - 2) * 0.1
            sine_wave = (math.sin(math.radians(day_cycle_counter)) + 1) / 2
            max_current = 15.0 + (instance_id % 3 - 1)
            current = sine_wave * max_current + (random.random() * 0.1)
            if current < 0.1:
                current = 0.0
            power = voltage * current
            scaled_voltage = int(voltage * SCALING_FACTOR)
            scaled_current = int(current * SCALING_FACTOR)
            scaled_power = int(power)

            datablock.setValues(VOLTAGE_REGISTER, [scaled_voltage])
            datablock.setValues(CURRENT_REGISTER, [scaled_current])
            datablock.setValues(POWER_REGISTER, [scaled_power])

            with data_lock:
                server_data[instance_id] = {
                    "host_ip": host_ip,
                    "status": "Running",
                    "client_ip": "N/A",
                    "voltage": f"{voltage:.1f}",
                    "current": f"{current:.2f}",
                    "power": f"{power:.0f}"
                }
            
            day_cycle_counter = (day_cycle_counter + 1) % 360
            time.sleep(UPDATE_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Fehler im Update-Thread für Instanz {instance_id}: {e}")
            with data_lock:
                server_data[instance_id] = {
                    "host_ip": host_ip,
                    "status": f"Error: {e}",
                    "client_ip": "N/A",
                    "voltage": "0", "current": "0", "power": "0"
                }
            time.sleep(10)

from flask import Flask, render_template, jsonify

# --- Web UI (Flask) ---
app = Flask(__name__)
UI_HOST = "0.0.0.0" # Listen on all interfaces for the UI
UI_PORT = 5010

@app.route('/')
def index():
    """Zeigt das Haupt-Dashboard an."""
    return render_template('index.html')

@app.route('/data')
def data():
    """Liefert die Server-Daten als JSON."""
    with data_lock:
        # Sort data by instance_id
        sorted_data = sorted(server_data.items())
    return jsonify(sorted_data)

def run_flask_app():
    """Startet die Flask-Webanwendung."""
    print(f"UI wird auf http://{UI_HOST}:{UI_PORT} gestartet...")
    # 'use_reloader=False' is important to prevent Flask from starting twice in debug mode
    app.run(host=UI_HOST, port=UI_PORT, debug=True, use_reloader=False)


def start_modbus_server_instance(host_ip, instance_id):
    """
    Initialisiert und startet eine einzelne Modbus TCP Server Instanz.
    """
    with data_lock:
        server_data[instance_id] = {
            "host_ip": host_ip, "status": "Initializing", "client_ip": "N/A",
            "voltage": "0", "current": "0", "power": "0"
        }

    print(f"Initialisiere Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
    
    # 1. Erstelle den Datenblock (den Speicher)
    datablock = ModbusSequentialDataBlock(0, [0] * 100)

    # 2. Erstelle den Geräte-Kontext für den Slave
    device_context = ModbusDeviceContext(hr=datablock)

    # 3. Definiere den Kontext als einfaches Dictionary.
    #    Der Server kann die Geräte-ID (1) nachschlagen und findet dann den device_context.
    context = {
        1: device_context
    }

    # 4. Starte den Simulations-Thread und übergib ihm direkt den Datenblock
    update_thread = threading.Thread(target=simulate_pv_values, args=(datablock, instance_id, host_ip))
    update_thread.daemon = True
    update_thread.start()

    # 5. Starte den Modbus-Server. Das 'single=True' Argument wird entfernt.
    print(f"Modbus TCP Slave für Instanz {instance_id} wird auf {host_ip}:{TCP_PORT} gestartet...")
    StartTcpServer(context=context, address=(host_ip, TCP_PORT))


def main():
    """
    Hauptfunktion: Initialisiert und startet mehrere Modbus Server Instanzen und das Web-UI.
    """
    # Start UI thread
    ui_thread = threading.Thread(target=run_flask_app)
    ui_thread.daemon = True
    ui_thread.start()

    server_threads = []
    for i, host_ip in enumerate(HOST_IPS):
        # Start each server in its own thread because StartTcpServer is blocking
        server_thread = threading.Thread(target=start_modbus_server_instance, args=(host_ip, i + 1))
        server_thread.daemon = True # Ensure threads exit when main program exits
        server_threads.append(server_thread)
        server_thread.start()
        print(f"Server-Thread für {host_ip} gestartet.")
        time.sleep(0.1) # Small delay to allow threads to initialize without overwhelming system

    print(f"{len(HOST_IPS)} Modbus TCP Server Instanzen gestartet.")
    print("Drücken Sie Strg+C zum Beenden.")

    # Keep the main thread alive, otherwise daemon threads will be terminated
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server werden heruntergefahren...")


if __name__ == "__main__":
    main()
