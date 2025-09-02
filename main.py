#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import math
import random
import datetime
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from flask import Flask, render_template, jsonify, request

# --- Globale Daten und Sperren ---
# Thread-sichere Datenablage für den UI-Status
server_data = {}
data_lock = threading.Lock()

# Globale Konfiguration für die Simulation
fault_flags = {}
day_cycle_increment = 0.2

# --- Konfiguration ---
HOST_IPS = [f"10.10.10.{120 + i}" for i in range(12)]
TCP_PORT = 5020
UPDATE_INTERVAL_SECONDS = 2

# --- Register-Adressen (Holding Registers, beginnend bei 0) ---
# Hinweis: Die Adressen sind um 1 verschoben gegenüber der üblichen Modbus-Dokumentation
VOLTAGE_REGISTER = 1          # AC Spannung (U)
CURRENT_REGISTER = 2          # AC Strom (I)
APPARENT_POWER_REGISTER = 3   # Scheinleistung (S = U*I), ehemals POWER_REGISTER

# NEUE REGISTER
# Leistungswerte
ACTIVE_POWER_REGISTER = 4     # Wirkleistung (P = S * cos(phi)), Einheit: W
POWER_FACTOR_REGISTER = 5     # Leistungsfaktor (cos(phi)), skaliert * 100
REACTIVE_POWER_REGISTER = 6   # Blindleistung (Q), Einheit: VAR

# Netzparameter
FREQUENCY_REGISTER = 7        # Netzfrequenz, skaliert * 100 (z.B. 5001 für 50.01 Hz)

# Energiezähler (32-Bit Werte, belegen je 2 Register)
DAILY_YIELD_REGISTER_H = 8    # Tagesertrag High Word, Einheit: Wh
DAILY_YIELD_REGISTER_L = 9    # Tagesertrag Low Word
TOTAL_YIELD_REGISTER_H = 10   # Gesamtertrag High Word, Einheit: kWh
TOTAL_YIELD_REGISTER_L = 11   # Gesamtertrag Low Word

# Status und Diagnose
OPERATING_STATE_REGISTER = 12 # Betriebszustand (0=Aus, 1=Standby, 2=Einspeisung, 3=Fehler)
DEVICE_TEMP_REGISTER = 13     # Gerätetemperatur, skaliert * 10 (°C)
FAULT_CODE_REGISTER = 14      # Fehlercode

# DC-Seite
DC_VOLTAGE_REGISTER = 15      # DC-Spannung, skaliert * 10 (V)
DC_CURRENT_REGISTER = 16      # DC-Strom, skaliert * 10 (A)
DC_POWER_REGISTER = 17        # DC-Leistung (P_DC), Einheit: W

# Skalierungsfaktoren
VOLTAGE_SCALING = 10.0
CURRENT_SCALING = 100.0
POWER_FACTOR_SCALING = 100.0
FREQUENCY_SCALING = 100.0
TEMP_SCALING = 10.0
DC_VOLTAGE_SCALING = 10.0
DC_CURRENT_SCALING = 100.0

def split_32bit_value(value):
    """Teilt einen 32-Bit-Wert in zwei 16-Bit-Werte (High und Low Word)."""
    value = int(value)
    high_word = (value >> 16) & 0xFFFF
    low_word = value & 0xFFFF
    return [high_word, low_word]

def simulate_pv_values(datablock, instance_id, host_ip):
    """
    Diese Funktion läuft in einem separaten Thread und aktualisiert
    kontinuierlich die Werte im Modbus Datastore für eine bestimmte Instanz.
    """
    global fault_flags, day_cycle_increment
    print(f"Starte Simulation der PV-Werte für Instanz {instance_id}...")
    
    day_cycle_counter = instance_id * 30
    total_yield_kwh = random.uniform(500, 2000)
    daily_yield_wh = 0.0
    last_reset_day = datetime.date.today().day
    fault_timer = 0

    while True:
        try:
            # Fehlerinjektion prüfen
            if fault_flags.get(instance_id):
                fault_timer = 15  # 15 Zyklen * 2s/Zyklus = 30s Fehler
                fault_flags[instance_id] = False
                print(f"Manueller Fehler für Instanz {instance_id} injiziert.")

            current_day = datetime.date.today().day
            if current_day != last_reset_day:
                daily_yield_wh = 0.0
                last_reset_day = current_day
                print(f"[{instance_id}] Tagesertrag zurückgesetzt.")

            # 1. DC-Seite simulieren
            sine_wave = (math.sin(math.radians(day_cycle_counter)) + 1) / 2
            dc_voltage = 350.0 + (random.random() - 0.5) * 20
            max_dc_current = 10.0 + (instance_id % 3 - 1)
            dc_current = sine_wave * max_dc_current + (random.random() * 0.05)
            if dc_current < 0.05: dc_current = 0.0
            dc_power = dc_voltage * dc_current

            # 2. AC-Werte berechnen
            inverter_efficiency = 0.97
            ac_power_potential = dc_power * inverter_efficiency
            ac_voltage = 230.0 + (random.random() - 0.5) * 2
            ac_current = ac_power_potential / ac_voltage if ac_power_potential > 1.0 else 0.0
            
            apparent_power = ac_voltage * ac_current
            power_factor = 0.98 + (random.random() * 0.02) if apparent_power > 100 else 0.90 + (random.random() * 0.05)
            active_power = apparent_power * power_factor
            reactive_power = math.sqrt(apparent_power**2 - active_power**2) if apparent_power > active_power else 0.0

            # 3. Netz- und Statusparameter
            frequency = 50.0 + (random.random() - 0.5) * 0.04
            device_temperature = 25.0 + (active_power / 150.0) + (random.random() - 0.5)

            if fault_timer > 0:
                operating_state, fault_code, fault_timer = 3, 101, fault_timer - 1
                active_power = 0 # Im Fehlerfall keine Leistung
            elif active_power > 10:
                operating_state, fault_code = 2, 0
            else:
                operating_state, fault_code = 1, 0

            # 4. Energiezähler
            energy_this_interval_wh = active_power * (UPDATE_INTERVAL_SECONDS / 3600.0)
            daily_yield_wh += energy_this_interval_wh
            total_yield_kwh += (energy_this_interval_wh / 1000.0)

            # 5. Werte in Register schreiben
            datablock.setValues(VOLTAGE_REGISTER, [int(ac_voltage * VOLTAGE_SCALING)])
            datablock.setValues(CURRENT_REGISTER, [int(ac_current * CURRENT_SCALING)])
            datablock.setValues(APPARENT_POWER_REGISTER, [int(apparent_power)])
            datablock.setValues(ACTIVE_POWER_REGISTER, [int(active_power)])
            datablock.setValues(POWER_FACTOR_REGISTER, [int(power_factor * POWER_FACTOR_SCALING)])
            datablock.setValues(REACTIVE_POWER_REGISTER, [int(reactive_power)])
            datablock.setValues(FREQUENCY_REGISTER, [int(frequency * FREQUENCY_SCALING)])
            datablock.setValues(DAILY_YIELD_REGISTER_H, split_32bit_value(daily_yield_wh))
            datablock.setValues(TOTAL_YIELD_REGISTER_H, split_32bit_value(total_yield_kwh))
            datablock.setValues(OPERATING_STATE_REGISTER, [operating_state])
            datablock.setValues(DEVICE_TEMP_REGISTER, [int(device_temperature * TEMP_SCALING)])
            datablock.setValues(FAULT_CODE_REGISTER, [fault_code])
            datablock.setValues(DC_VOLTAGE_REGISTER, [int(dc_voltage * DC_VOLTAGE_SCALING)])
            datablock.setValues(DC_CURRENT_REGISTER, [int(dc_current * DC_CURRENT_SCALING)])
            datablock.setValues(DC_POWER_REGISTER, [int(dc_power)])

            # 6. Daten für Web-UI aktualisieren
            with data_lock:
                status_text = "Running" if operating_state != 3 else "Fault"
                server_data[instance_id] = {
                    "host_ip": host_ip,
                    "status": status_text,
                    "ac_voltage": f"{ac_voltage:.1f} V",
                    "ac_current": f"{ac_current:.2f} A",
                    "active_power": f"{active_power:.0f} W",
                    "power_factor": f"{power_factor:.2f}",
                    "frequency": f"{frequency:.2f} Hz",
                    "daily_yield": f"{daily_yield_wh / 1000.0:.3f} kWh",
                    "op_state": operating_state,
                    "temp": f"{device_temperature:.1f} °C",
                    "fault_code": fault_code,
                    "dc_power": f"{dc_power:.0f} W"
                }
            
            day_cycle_counter = (day_cycle_counter + day_cycle_increment) % 360
            time.sleep(UPDATE_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Fehler im Update-Thread für Instanz {instance_id}: {e}")
            with data_lock:
                server_data[instance_id] = {"status": f"Error: {e}"}
            time.sleep(10)

# --- Web UI (Flask) ---
app = Flask(__name__, template_folder='.')
UI_HOST = "0.0.0.0"
UI_PORT = 5010

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    with data_lock:
        response_data = {
            "servers": sorted(server_data.items()),
            "day_cycle_increment": day_cycle_increment
        }
    return jsonify(response_data)

@app.route('/inject_fault/<int:instance_id>', methods=['POST'])
def inject_fault(instance_id):
    global fault_flags
    if instance_id in fault_flags:
        fault_flags[instance_id] = True
        print(f"Fehlerinjektion für Instanz {instance_id} angefordert.")
        return jsonify({"status": "success", "message": f"Fault injected for instance {instance_id}"})
    else:
        return jsonify({"status": "error", "message": "Invalid instance ID"}), 404

@app.route('/set_cycle_speed', methods=['POST'])
def set_cycle_speed():
    global day_cycle_increment
    data = request.get_json()
    if data and 'speed' in data:
        try:
            new_speed = float(data['speed'])
            if 0.1 <= new_speed <= 10.0:
                day_cycle_increment = new_speed
                print(f"Zyklusgeschwindigkeit auf {new_speed} gesetzt.")
                return jsonify({"status": "success", "message": f"Cycle speed set to {day_cycle_increment}"})
            else:
                return jsonify({"status": "error", "message": "Speed value out of range (0.1-10.0)"}), 400
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid speed value"}), 400
    return jsonify({"status": "error", "message": "Missing or invalid 'speed' parameter"}), 400

def run_flask_app():
    print(f"UI wird auf http://{UI_HOST}:{UI_PORT} gestartet...")
    app.run(host=UI_HOST, port=UI_PORT, debug=True, use_reloader=False)

def start_modbus_server_instance(host_ip, instance_id):
    """
    Initialisiert und startet eine einzelne Modbus TCP Server Instanz.
    Diese Funktion bleibt strukturell unverändert.
    """
    with data_lock:
        server_data[instance_id] = {"host_ip": host_ip, "status": "Initializing"}

    print(f"Initialisiere Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
    
    datablock = ModbusSequentialDataBlock(0, [0] * 100)
    
    # Der Geräte-Kontext wird hier erstellt, wie in Ihrer Version
    device_context = ModbusDeviceContext(hr=datablock)
    
    # Der Server-Kontext wird als Dictionary definiert, wie in Ihrer Version
    context = {
        1: device_context
    }

    update_thread = threading.Thread(target=simulate_pv_values, args=(datablock, instance_id, host_ip))
    update_thread.daemon = True
    update_thread.start()

    print(f"Modbus TCP Slave für Instanz {instance_id} wird auf {host_ip}:{TCP_PORT} gestartet...")
    # StartTcpServer wird hier ohne 'single=True' aufgerufen, wie in Ihrer Version
    StartTcpServer(context=context, address=(host_ip, TCP_PORT))


def main():
    """
    Hauptfunktion: Initialisiert und startet mehrere Modbus Server Instanzen und das Web-UI.
    """
    global fault_flags
    for i in range(len(HOST_IPS)):
        fault_flags[i + 1] = False

    ui_thread = threading.Thread(target=run_flask_app)
    ui_thread.daemon = True
    ui_thread.start()

    server_threads = []
    for i, host_ip in enumerate(HOST_IPS):
        server_thread = threading.Thread(target=start_modbus_server_instance, args=(host_ip, i + 1))
        server_thread.daemon = True
        server_threads.append(server_thread)
        server_thread.start()
        print(f"Server-Thread für {host_ip} gestartet.")
        time.sleep(0.1)

    print(f"{len(HOST_IPS)} Modbus TCP Server Instanzen gestartet.")
    print("Drücken Sie Strg+C zum Beenden.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server werden heruntergefahren...")


if __name__ == "__main__":
    main()
