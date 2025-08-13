# test_permanent.py
#
# Angepasste Version, die zyklisch einen Bereich von IP-Adressen abfragt.

from pyModbusTCP.client import ModbusClient
import time

# --- Konfiguration ---
# Liste der abzufragenden IP-Adressen
INVERTER_IPS = [f'10.10.10.{i}' for i in range(120, 132)] # Erzeugt 10.10.10.120 bis 10.10.10.131

INVERTER_PORT = 5020
UNIT_ID = 1
QUERY_INTERVAL = 30 # Sekunden Pause zwischen den Abfragezyklen

def to_signed_int16(val):
    """Wandelt einen 16-Bit-Wert (unsigned) in einen signed-Integer um."""
    if val > 32767:
        return val - 65536
    return val

def query_device(ip, port, unit_id):
    """Fragt ein einzelnes Modbus-Gerät ab und gibt die Daten aus."""
    print(f"--- Abfrage für Gerät: {ip} ---")

    # Client für die Abfrage initialisieren
    client = ModbusClient(host=ip, port=port, unit_id=unit_id, auto_open=True, timeout=5)
    
    # RTU over TCP Modus aktivieren
    client.rtu_over_tcp = True

    # Register lesen (Adresse 0, Anzahl 3)
    response_regs = client.read_holding_registers(0, 3)
    
    # Verbindung wird durch die Bibliothek oder bei Zerstörung des Objekts geschlossen.
    # explizites client.close() ist in kurzen Skripten dennoch eine gute Praxis.
    client.close()

    # Auswertung
    if response_regs:
        print(f"Daten von {ip} erfolgreich empfangen!")

        # Werte auslesen und umrechnen
        raw_voltage = to_signed_int16(response_regs[0])
        raw_current = to_signed_int16(response_regs[1])
        power = to_signed_int16(response_regs[2])

        # Skalierungsfaktoren anwenden
        voltage = raw_voltage / 10.0
        current = raw_current / 10.0

        print(f"  Spannung: {voltage:.1f} V")
        print(f"  Strom:    {current:.1f} A")
        print(f"  Leistung: {power} W")
    else:
        print(f"Fehler: Konnte keine Daten vom Gerät {ip} lesen.")

# --- Hauptprogramm ---
if __name__ == "__main__":
    try:
        print("Starte kontinuierliche Modbus-Abfrage. Zum Beenden Strg+C drücken.")
        while True:
            print("\n" + "="*40)
            print(f"Starte neuen Abfragezyklus um {time.strftime('%H:%M:%S')}")
            print("="*40)

            for ip_address in INVERTER_IPS:
                query_device(ip_address, INVERTER_PORT, UNIT_ID)
                time.sleep(0.5) # Kurze Pause zwischen den Geräten, um sie nicht zu fluten

            print("\n" + "="*40)
            print(f"Alle Geräte abgefragt. Warte {QUERY_INTERVAL} Sekunden bis zum nächsten Zyklus.")
            print("="*40)
            time.sleep(QUERY_INTERVAL)

    except KeyboardInterrupt:
        print("\nSkript vom Benutzer beendet.")