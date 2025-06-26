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
HOST_IP = '192.168.178.13'  # Auf allen Interfaces lauschen
TCP_PORT = 5020      # Standard Modbus TCP Port
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

def simulate_pv_values(context):
    """
    Diese Funktion läuft in einem separaten Thread und aktualisiert
    kontinuierlich die Werte im Modbus Datastore.
    """
    print("Starte Simulation der PV-Werte...")
    
    # Ein Zähler, um einen Tagesverlauf zu simulieren
    day_cycle_counter = 0

    while True:
        try:
            # 1. Spannung (U) simulieren
            # Eine stabile Netzspannung mit leichten Schwankungen.
            voltage = 230.0 + (random.random() - 0.5) # z.B. 229.5V - 230.5V
            
            # 2. Strom (I) simulieren
            # Simuliert einen Sinus-Verlauf über den Tag (Sonne geht auf und unter)
            # Der Wert schwankt zwischen 0 und ca. 15A
            # Der Zyklus wird hier beschleunigt, um die Änderungen schnell zu sehen
            sine_wave = (math.sin(math.radians(day_cycle_counter)) + 1) / 2
            current = sine_wave * 15.0 + (random.random() * 0.1) # Max 15A + leichtes Rauschen
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

            print(f"Update: U={voltage:.1f}V, I={current:.2f}A, P={power:.0f}W")

            # Werte in die Register schreiben
            context[0].setValues(3, VOLTAGE_REGISTER, [scaled_voltage])
            context[0].setValues(3, CURRENT_REGISTER, [scaled_current])
            context[0].setValues(3, POWER_REGISTER, [scaled_power])
            
            # Zähler für den Tageszyklus erhöhen
            day_cycle_counter = (day_cycle_counter + 1) % 360

            time.sleep(UPDATE_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Fehler im Update-Thread: {e}")
            time.sleep(10)


def main():
    """
    Hauptfunktion: Initialisiert den Modbus Server.
    """
    print("Initialisiere Modbus Datastore...")
    # Initialisiere die Registerblöcke. Wir nutzen nur Holding Registers.
    # Wir erstellen 100 Register, initialisiert mit 0.
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0] * 100) # Holding Registers
    )
    context = ModbusServerContext(slaves=store, single=True)

    # Starte den Simulations-Thread im Hintergrund
    update_thread = threading.Thread(target=simulate_pv_values, args=(context,))
    update_thread.daemon = True # Beendet den Thread, wenn das Hauptprogramm endet
    update_thread.start()

    # Starte den Modbus TCP Server
    print(f"Modbus TCP Slave wird auf {HOST_IP}:{TCP_PORT} gestartet...")
    StartTcpServer(context=context, address=(HOST_IP, TCP_PORT))


if __name__ == "__main__":
    main()
