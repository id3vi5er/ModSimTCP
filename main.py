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
VOLTAGE_REGISTER = 0   # Spannung (U)
CURRENT_REGISTER = 1   # Strom (I)
POWER_REGISTER = 2     # Leistung (P)

# Skalierungsfaktor: Modbus Register sind 16-Bit Integer.
# Um Fließkommazahlen zu senden, multiplizieren wir sie mit einem Faktor.
# Symcon muss den empfangenen Wert durch diesen Faktor teilen.
SCALING_FACTOR = 10.0

def simulate_pv_values(slave_context, instance_id, host_ip):
    """
    Diese Funktion läuft in einem separaten Thread und aktualisiert
    kontinuierlich die Werte im Modbus Datastore für eine bestimmte Instanz.
    """
    print(f"Starte Simulation der PV-Werte für Instanz {instance_id}...")
    
    # Ein Zähler, um einen Tagesverlauf zu simulieren
    # Add instance_id to day_cycle_counter to vary the simulation slightly per instance
    day_cycle_counter = instance_id * 30 # Offset based on instance_id for variety

    while True:
        try:
            # 1. Spannung (U) simulieren
            # Eine stabile Netzspannung mit leichten Schwankungen.
            # Add small variation based on instance_id
            voltage = 230.0 + (random.random() - 0.5) + (instance_id % 5 - 2) * 0.1
            
            # 2. Strom (I) simulieren
            # Simuliert einen Sinus-Verlauf über den Tag (Sonne geht auf und unter)
            # Der Wert schwankt zwischen 0 und ca. 15A
            # Der Zyklus wird hier beschleunigt, um die Änderungen schnell zu sehen
            sine_wave = (math.sin(math.radians(day_cycle_counter)) + 1) / 2
            # Vary max current slightly per instance
            max_current = 15.0 + (instance_id % 3 - 1)
            current = sine_wave * max_current + (random.random() * 0.1) # Max current + leichtes Rauschen
            if current < 0.1: # Nachts kein Strom
                current = 0.0

            # 3. Leistung (P) berechnen
            # P = U * I
            power = voltage * current

            # Skalierte Werte vorbereiten
            scaled_voltage = int(voltage * SCALING_FACTOR)
            scaled_current = int(current * SCALING_FACTOR)
            scaled_power = int(power) # Leistung oft als ganzer Watt-Wert

            # Werte in die Register schreiben
            # Der Funktionscode '3' wird hier entfernt
            slave_context.setValues(VOLTAGE_REGISTER, [scaled_voltage])
            slave_context.setValues(CURRENT_REGISTER, [scaled_current])
            slave_context.setValues(POWER_REGISTER, [scaled_power])

            # Update shared data for UI
            with data_lock:
                server_data[instance_id] = {
                    "host_ip": host_ip,
                    "status": "Running",
                    "client_ip": "N/A",
                    "voltage": f"{voltage:.1f}",
                    "current": f"{current:.2f}",
                    "power": f"{power:.0f}"
                }
            
            # Zähler für den Tageszyklus erhöhen
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
    # Initialize shared data for this instance
    with data_lock:
        server_data[instance_id] = {
            "host_ip": host_ip, "status": "Initializing", "client_ip": "N/A",
            "voltage": "0", "current": "0", "power": "0"
        }

    print(f"Initialisiere Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
    # Initialisiere die Registerblöcke. Wir nutzen nur Holding Registers.
    # Wir erstellen 100 Register, initialisiert mit 0.
    store = ModbusSequentialDataBlock(0, [0] * 100) # Holding Registers
    
    # Der Server-Kontext, der den Slave unter ID 1 verwaltet
    context = ModbusServerContext({1: store}, single=True)

    # Starte den Simulations-Thread im Hintergrund für diese Instanz
    # Wir übergeben jetzt direkt den 'store' an den Thread
    update_thread = threading.Thread(target=simulate_pv_values, args=(store, instance_id, host_ip))
    update_thread.daemon = True # Beendet den Thread, wenn das Hauptprogramm endet
    update_thread.start()

    # Starte den Modbus TCP Server für diese Instanz
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
