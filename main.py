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
wallbox_data = {} # NEU für Wallboxen
data_lock = threading.Lock()

# Globale Konfiguration für die Simulation
fault_flags = {}
wallbox_controls = {} # NEU für Wallboxen
day_cycle_increment = 0.2

# --- Konfiguration ---
PV_HOST_IPS = [f"10.10.10.{120 + i}" for i in range(12)]
WALLBOX_HOST_IPS = [f"10.10.10.{140 + i}" for i in range(12)] # NEU für Wallboxen
TCP_PORT = 5020
UPDATE_INTERVAL_SECONDS = 2

# --- PV-Register-Adressen (Holding Registers, beginnend bei 0) ---
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

# --- Wallbox-Register-Adressen ---
WALLBOX_STATE_REGISTER = 20      # 1:Bereit, 2:Ladevorgang, 3:Fehler
CHARGING_POWER_REGISTER = 21     # Ladeleistung in W
STATE_OF_CHARGE_REGISTER = 22    # SoC in %
CHARGED_ENERGY_REGISTER = 23     # Geladene Energie (UINT32), Wh
WALLBOX_FAULT_CODE_REGISTER = 25 # Fehlercode (0=OK, 201=Ladefehler)


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


def simulate_wallbox_values(datablock, instance_id, host_ip):
    """
    Diese Funktion läuft in einem separaten Thread und simuliert die Werte
    einer Wallbox. Die Ladeleistung ist konstant, aber die Ladegeschwindigkeit
    wird durch die globale Simulationsgeschwindigkeit skaliert.
    """
    global wallbox_controls, day_cycle_increment
    print(f"Starte Simulation der Wallbox-Werte für Instanz {instance_id}...")

    # Zustandvariablen
    state = 1  # 1:Bereit, 2:Ladevorgang, 3:Fehler
    soc = 0
    charged_energy = 0.0
    fault_code = 0
    fault_timer = 0

    while True:
        try:
            # 1. Steuerbefehle aus der UI verarbeiten
            control_action = wallbox_controls.get(instance_id, {}).pop('action', None)

            if control_action == 'set_soc' and state == 1:
                try:
                    new_soc = int(wallbox_controls.get(instance_id, {}).pop('value', soc))
                    if 0 <= new_soc <= 100:
                        soc = new_soc
                        print(f"[Wallbox {instance_id}] SoC auf {soc}% gesetzt.")
                except (ValueError, TypeError):
                    pass

            elif control_action == 'start_charging' and state != 3:
                state = 2
                if soc < 20: soc = 20
                charged_energy = 0.0
                print(f"[Wallbox {instance_id}] Ladevorgang gestartet.")
            elif control_action == 'stop_charging':
                state = 1
                print(f"[Wallbox {instance_id}] Ladevorgang gestoppt.")
            elif control_action == 'inject_fault':
                state = 3
                fault_code = 201
                fault_timer = 30
                print(f"[Wallbox {instance_id}] Fehler injiziert.")

            # 2. Simulationslogik basierend auf dem Zustand
            if state == 2:  # Ladevorgang
                # Ladeleistung ist konstant bei ca. 11 kW
                charging_power = 11000 + (random.random() - 0.5) * 100

                # Berechne die Energie für ein reales Zeitintervall
                energy_this_interval_wh = charging_power * (UPDATE_INTERVAL_SECONDS / 3600.0)

                # Skaliere die Energie basierend auf der Simulationsgeschwindigkeit
                base_speed_increment = 0.2  # Basis-Geschwindigkeit der Simulation
                speed_scaling_factor = day_cycle_increment / base_speed_increment
                scaled_energy_this_interval_wh = energy_this_interval_wh * speed_scaling_factor

                # Aktualisiere Zähler und SoC mit der skalierten Energie
                charged_energy += scaled_energy_this_interval_wh

                # Annahme Batteriekapazität 60kWh für SoC-Berechnung
                soc_increase = (scaled_energy_this_interval_wh / 60000.0) * 100
                soc += soc_increase

                if soc >= 100:
                    soc = 100
                    state = 1
                    print(f"[Wallbox {instance_id}] Ladevorgang abgeschlossen (SoC 100%).")

            elif state == 1:  # Bereit
                charging_power = 0

            elif state == 3:  # Fehler
                charging_power = 0
                fault_timer -= 1
                if fault_timer <= 0:
                    state = 1
                    fault_code = 0
                    print(f"[Wallbox {instance_id}] Fehlerzustand beendet.")

            # 3. Werte in Register schreiben
            datablock.setValues(WALLBOX_STATE_REGISTER, [state])
            datablock.setValues(CHARGING_POWER_REGISTER, [int(charging_power)])
            datablock.setValues(STATE_OF_CHARGE_REGISTER, [int(soc)])
            datablock.setValues(CHARGED_ENERGY_REGISTER, split_32bit_value(charged_energy))
            datablock.setValues(WALLBOX_FAULT_CODE_REGISTER, [fault_code])

            # 4. Daten für Web-UI aktualisieren
            with data_lock:
                status_map = {1: "Bereit", 2: "Ladevorgang", 3: "Fehler"}
                wallbox_data[instance_id] = {
                    "host_ip": host_ip,
                    "status": status_map.get(state, "Unbekannt"),
                    "charging_power": f"{charging_power:.0f} W",
                    "soc": f"{soc:.1f} %",
                    "charged_energy": f"{charged_energy / 1000.0:.3f} kWh",
                    "fault_code": fault_code,
                    "state": state
                }

            time.sleep(UPDATE_INTERVAL_SECONDS)

        except Exception as e:
            print(f"Fehler im Wallbox-Update-Thread für Instanz {instance_id}: {e}")
            with data_lock:
                wallbox_data[instance_id] = {"status": f"Error: {e}"}
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
            "wallboxes": sorted(wallbox_data.items()), # NEU
            "day_cycle_increment": day_cycle_increment
        }
    return jsonify(response_data)

@app.route('/start_charging/<int:instance_id>', methods=['POST'])
def start_charging(instance_id):
    if instance_id in wallbox_controls:
        wallbox_controls[instance_id]['action'] = 'start_charging'
        return jsonify({"status": "success", "message": f"Start charging command sent to wallbox {instance_id}"})
    return jsonify({"status": "error", "message": "Invalid wallbox ID"}), 404

@app.route('/stop_charging/<int:instance_id>', methods=['POST'])
def stop_charging(instance_id):
    if instance_id in wallbox_controls:
        wallbox_controls[instance_id]['action'] = 'stop_charging'
        return jsonify({"status": "success", "message": f"Stop charging command sent to wallbox {instance_id}"})
    return jsonify({"status": "error", "message": "Invalid wallbox ID"}), 404

@app.route('/inject_wallbox_fault/<int:instance_id>', methods=['POST'])
def inject_wallbox_fault(instance_id):
    if instance_id in wallbox_controls:
        wallbox_controls[instance_id]['action'] = 'inject_fault'
        return jsonify({"status": "success", "message": f"Fault injection command sent to wallbox {instance_id}"})
    return jsonify({"status": "error", "message": "Invalid wallbox ID"}), 404

@app.route('/set_soc/<int:instance_id>', methods=['POST'])
def set_soc(instance_id):
    data = request.get_json()
    if not data or 'soc' not in data:
        return jsonify({"status": "error", "message": "Missing 'soc' parameter"}), 400
    try:
        soc_value = int(data['soc'])
        if not (0 <= soc_value <= 100):
             return jsonify({"status": "error", "message": "SoC value out of range (0-100)"}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid SoC value"}), 400

    if instance_id in wallbox_controls:
        wallbox_controls[instance_id]['action'] = 'set_soc'
        wallbox_controls[instance_id]['value'] = soc_value
        return jsonify({"status": "success", "message": f"Set SoC command sent to wallbox {instance_id}"})
    return jsonify({"status": "error", "message": "Invalid wallbox ID"}), 404

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

def start_modbus_server_instance(host_ip, instance_id, sim_type='pv'):
    """
    Initialisiert und startet eine einzelne Modbus TCP Server Instanz
    für einen PV-Wechselrichter oder eine Wallbox.
    """
    datablock = ModbusSequentialDataBlock(0, [0] * 100)
    device_context = ModbusDeviceContext(hr=datablock)
    context = {1: device_context}

    if sim_type == 'pv':
        with data_lock:
            server_data[instance_id] = {"host_ip": host_ip, "status": "Initializing"}
        print(f"Initialisiere PV Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
        target_func = simulate_pv_values
    elif sim_type == 'wallbox':
        with data_lock:
            wallbox_data[instance_id] = {"host_ip": host_ip, "status": "Initializing"}
        print(f"Initialisiere Wallbox Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
        target_func = simulate_wallbox_values
    else:
        return

    update_thread = threading.Thread(target=target_func, args=(datablock, instance_id, host_ip))
    update_thread.daemon = True
    update_thread.start()

    print(f"Modbus TCP Slave ({sim_type}) für Instanz {instance_id} wird auf {host_ip}:{TCP_PORT} gestartet...")
    StartTcpServer(context=context, address=(host_ip, TCP_PORT))


def main():
    """
    Hauptfunktion: Initialisiert und startet mehrere Modbus Server Instanzen und das Web-UI.
    """
    global fault_flags, wallbox_controls
    # Initialisierung für PV-Wechselrichter
    for i in range(len(PV_HOST_IPS)):
        fault_flags[i + 1] = False
    # Initialisierung für Wallboxen
    for i in range(len(WALLBOX_HOST_IPS)):
        wallbox_controls[i + 1] = {}

    ui_thread = threading.Thread(target=run_flask_app)
    ui_thread.daemon = True
    ui_thread.start()

    server_threads = []
    # PV-Simulatoren starten
    for i, host_ip in enumerate(PV_HOST_IPS):
        server_thread = threading.Thread(target=start_modbus_server_instance, args=(host_ip, i + 1, 'pv'))
        server_thread.daemon = True
        server_threads.append(server_thread)
        server_thread.start()
        print(f"PV-Server-Thread für {host_ip} gestartet.")
        time.sleep(0.1)

    # Wallbox-Simulatoren starten
    for i, host_ip in enumerate(WALLBOX_HOST_IPS):
        server_thread = threading.Thread(target=start_modbus_server_instance, args=(host_ip, i + 1, 'wallbox'))
        server_thread.daemon = True
        server_threads.append(server_thread)
        server_thread.start()
        print(f"Wallbox-Server-Thread für {host_ip} gestartet.")
        time.sleep(0.1)

    total_instances = len(PV_HOST_IPS) + len(WALLBOX_HOST_IPS)
    print(f"{total_instances} Modbus TCP Server Instanzen gestartet.")
    print("Drücken Sie Strg+C zum Beenden.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server werden heruntergefahren...")


if __name__ == "__main__":
    main()
