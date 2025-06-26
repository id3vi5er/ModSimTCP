#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import math
import random
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# --- Konfiguration ---
# List of IP addresses for the Modbus servers
HOST_IPS = [f"192.168.178.{201 + i}" for i in range(12)]
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

def simulate_pv_values(context, instance_id):
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

            # In Modbus-Register schreiben (skalierte Integer-Werte)
            # context[0] ist die Referenz auf unseren Slave (unit=1)
            # setValues(Funktionscode, Start-Adresse, [Werte])
            # Funktionscode 3 = Holding Register
            
            # Skalierte Werte vorbereiten
            scaled_voltage = int(voltage * SCALING_FACTOR)
            scaled_current = int(current * SCALING_FACTOR)
            scaled_power = int(power) # Leistung oft als ganzer Watt-Wert

            print(f"Instanz {instance_id}: Update: U={voltage:.1f}V, I={current:.2f}A, P={power:.0f}W")

            # Werte in die Register schreiben
            # context[0] refers to the slave context for this server instance
            context[0].setValues(3, VOLTAGE_REGISTER, [scaled_voltage])
            context[0].setValues(3, CURRENT_REGISTER, [scaled_current])
            context[0].setValues(3, POWER_REGISTER, [scaled_power])
            
            # Zähler für den Tageszyklus erhöhen
            day_cycle_counter = (day_cycle_counter + 1) % 360

            time.sleep(UPDATE_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Fehler im Update-Thread für Instanz {instance_id}: {e}")
            time.sleep(10)

def start_modbus_server_instance(host_ip, instance_id):
    """
    Initialisiert und startet eine einzelne Modbus TCP Server Instanz.
    """
    print(f"Initialisiere Modbus Datastore für Instanz {instance_id} auf {host_ip}:{TCP_PORT}...")
    # Initialisiere die Registerblöcke. Wir nutzen nur Holding Registers.
    # Wir erstellen 100 Register, initialisiert mit 0.
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0] * 100) # Holding Registers
    )
    context = ModbusServerContext(slaves=store, single=True)

    # Starte den Simulations-Thread im Hintergrund für diese Instanz
    update_thread = threading.Thread(target=simulate_pv_values, args=(context, instance_id))
    update_thread.daemon = True # Beendet den Thread, wenn das Hauptprogramm endet
    update_thread.start()

    # Starte den Modbus TCP Server für diese Instanz
    print(f"Modbus TCP Slave für Instanz {instance_id} wird auf {host_ip}:{TCP_PORT} gestartet...")
    StartTcpServer(context=context, address=(host_ip, TCP_PORT))


def main():
    """
    Hauptfunktion: Initialisiert und startet mehrere Modbus Server Instanzen.
    """
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
