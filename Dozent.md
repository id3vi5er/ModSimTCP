# Technisches Handbuch für Dozenten: PV-Simulator

Dieses Dokument bietet eine detaillierte technische Referenz für den PV-Simulator. Es richtet sich an Dozenten und Entwickler, die ein tiefes Verständnis der simulierten Werte und des Systemverhaltens benötigen.

---

## Modbus Register-Referenz (PV-Anlage, 3-phasig, 25 kWp)

Die folgende Tabelle listet alle Holding-Register auf, die von jeder PV-Simulator-Instanz bereitgestellt werden.

| Adresse | Register-Name (Code) | Beschreibung | Datentyp | Client Faktor | Einheit | Min. Wert (ca.) | Max. Wert (ca.) |
|---|---|---|---|---|---|---|---|
| 1 | `VOLTAGE_L1_REGISTER` | AC Spannung L1 | `INT16` | `0.1` | V | 229.0 | 231.0 |
| 2 | `VOLTAGE_L2_REGISTER` | AC Spannung L2 | `INT16` | `0.1` | V | 229.0 | 231.0 |
| 3 | `VOLTAGE_L3_REGISTER` | AC Spannung L3 | `INT16` | `0.1` | V | 229.0 | 231.0 |
| 4 | `CURRENT_L1_REGISTER` | AC Strom L1 | `INT16` | `0.01` | A | 0.0 | ~36.2 |
| 5 | `CURRENT_L2_REGISTER` | AC Strom L2 | `INT16` | `0.01` | A | 0.0 | ~36.2 |
| 6 | `CURRENT_L3_REGISTER` | AC Strom L3 | `INT16` | `0.01` | A | 0.0 | ~36.2 |
| 7 | `ACTIVE_POWER_REGISTER` | AC Wirkleistung (Gesamt) | `INT16` | `1` | W | 0 | ~25000 |
| 8 | `REACTIVE_POWER_REGISTER` | AC Blindleistung (Gesamt) | `INT16` | `1` | VAR | 0 | ~5000 |
| 9 | `APPARENT_POWER_REGISTER` | AC Scheinleistung (Gesamt) | `INT16` | `1` | VA | 0 | ~25500 |
| 10 | `POWER_FACTOR_REGISTER` | Leistungsfaktor | `INT16` | `0.01` | - | 0.95 | 1.00 |
| 11 | `FREQUENCY_REGISTER` | Netzfrequenz | `INT16` | `0.01` | Hz | 49.98 | 50.02 |
| 12-13 | `DAILY_YIELD_REGISTER` | Tagesertrag (Energie) | `UINT32` | `1` | Wh | 0 | Kumulativ |
| 14-15 | `TOTAL_YIELD_REGISTER` | Gesamtertrag (Energie) | `UINT32` | `1` | kWh | 500 | Kumulativ |
| 16 | `DC_VOLTAGE_REGISTER` | DC Eingangsspannung | `INT16` | `0.1` | V | 800.0 | 900.0 |
| 17 | `DC_CURRENT_REGISTER` | DC Eingangsstrom | `INT16` | `0.01` | A | 0.0 | ~29.4 |
| 18 | `DC_POWER_REGISTER` | DC Eingangsleistung | `INT16` | `1` | W | 0 | ~25000 |
| 19 | `OPERATING_STATE_REGISTER` | Betriebszustand | `INT16` | `1` | - | 1 | 3 |
| 20 | `DEVICE_TEMP_REGISTER` | Gerätetemperatur | `INT16` | `0.1` | °C | 24.5 | ~65.0 |
| 21 | `FAULT_CODE_REGISTER` | Fehlercode | `INT16` | `1` | - | 0 | 101 |
| 22 | `RESET_REGISTER` | Fehler zurücksetzen | `INT16` | `1` | - | *Write-Only* | *Write-Only* |

---

## Betriebszustände (`OPERATING_STATE_REGISTER`, Adresse 12)

Der Betriebszustand gibt den aktuellen Status des Wechselrichters an.

| Wert | Zustand | Beschreibung |
|---|---|---|
| `1` | **Standby** | Der Wechselrichter ist betriebsbereit, aber die DC-Leistung ist zu gering, um mit der Einspeisung zu beginnen (z.B. bei Nacht). |
| `2` | **Einspeisung** | Der Wechselrichter wandelt aktiv DC-Energie in AC-Energie um und speist sie ins Netz ein. |
| `3` | **Fehler** | Ein interner Fehler ist aufgetreten. Der Wechselrichter stoppt die Einspeisung. Details siehe Fehlercode. |

---

## Fehlercodes (`FAULT_CODE_REGISTER`, Adresse 14)

Wenn der Betriebszustand `3` (Fehler) ist, gibt dieses Register die Ursache an.

| Wert | Fehler | Beschreibung |
|---|---|---|
| `0` | **Kein Fehler** | Normalbetrieb. |
| `101` | **Simulierter Fehler** | Ein manuell ausgelöster Fehler. Der Zustand ist **persistent** und muss durch Schreiben einer `1` auf `RESET_REGISTER` (22) oder über die UI zurückgesetzt werden. |

---

## Hinweise zur Simulation

*   **Tageszyklus:** Die DC-Leistung folgt einer Sinus-Kurve, um einen Tag-Nacht-Wechsel zu simulieren.
*   **Zufälligkeit:** Alle Werte enthalten eine leichte zufällige Schwankung, um realistische Messdaten nachzubilden.
*   **Instanz-Varianz:** Die maximale DC-Stromstärke variiert leicht zwischen den 12 Instanzen, was zu geringfügig unterschiedlichen maximalen Leistungen führt.
*   **Tagesertrag-Reset:** Der Tagesertrag (`DAILY_YIELD_REGISTER`) wird automatisch um Mitternacht zurückgesetzt.

---
---

## Wallbox-Simulation: Technische Details

Die Wallbox-Simulation wurde hinzugefügt, um das Laden von Elektrofahrzeugen abzubilden, inklusive Fahrzeugerkennung und persistenter Fehler.

### Wallbox Modbus Register-Referenz

| Adresse | Register-Name (Code) | Beschreibung | Datentyp | Client Faktor | Einheit | Min. Wert (ca.) | Max. Wert (ca.) |
|---|---|---|---|---|---|---|---|
| 20 | `WALLBOX_STATE_REGISTER` | Betriebszustand der Wallbox | `INT16` | `1` | - | 1 | 3 |
| 21 | `CHARGING_POWER_REGISTER` | Aktuelle Ladeleistung | `INT16` | `1` | W | 0 | ~11050 |
| 22 | `STATE_OF_CHARGE_REGISTER`| Ladezustand des Fahrzeugs (SoC)| `INT16` | `1` | % | 0 | 100 |
| 23-24| `CHARGED_ENERGY_REGISTER`| Geladene Energie (Session) | `UINT32`| `1` | Wh | 0 | Kumulativ |
| 25 | `WALLBOX_FAULT_CODE_REGISTER`| Fehlercode der Wallbox | `INT16` | `1` | - | 0 | 404 |
| 26 | `REMOTE_CONTROL_REGISTER`| Start/Stop-Befehl schreiben | `INT16` | `1` | - | *Write-Only* | *Write-Only* |
| 27 | `CAR_CONNECTED_REGISTER` | Fahrzeug verbunden? | `INT16` | `1` | - | 0 | 1 |
| 28 | `WALLBOX_RESET_REGISTER` | Fehler zurücksetzen | `INT16` | `1` | - | *Write-Only* | *Write-Only* |

### Wallbox Betriebszustände (`WALLBOX_STATE_REGISTER`, Adresse 20)

| Wert | Zustand | Beschreibung |
|---|---|---|
| `1` | **Bereit** | Die Wallbox ist bereit zum Laden oder hat den Ladevorgang abgeschlossen. Der Start-SoC kann in diesem Zustand über die UI gesetzt werden. |
| `2` | **Ladevorgang** | Die Wallbox lädt aktiv das Fahrzeug. Dies ist nur möglich, wenn `CAR_CONNECTED_REGISTER` auf 1 steht. |
| `3` | **Fehler** | Ein simulierter Fehler ist aufgetreten. Dieser Zustand ist **persistent** und muss zurückgesetzt werden. |

### Fehlercodes (`WALLBOX_FAULT_CODE_REGISTER`, Adresse 25)

| Wert | Fehler | Beschreibung |
|---|---|---|
| `0` | **Kein Fehler** | Normalbetrieb. |
| `201`| **Ladefehler** | Allgemeiner, persistenter Fehler, der durch die UI ausgelöst wurde. |
| `404`| **Kein Fahrzeug** | Temporärer Fehler, der signalisiert, dass ein Lade-Startbefehl empfangen wurde, aber `CAR_CONNECTED_REGISTER` auf `0` stand. |

### Hinweise zur Wallbox-Simulation

*   **Fahrzeugverbindung:** Ein Ladevorgang kann nur gestartet werden (via UI oder Modbus), wenn ein Fahrzeug verbunden ist (`CAR_CONNECTED_REGISTER` = 1). Der Verbindungsstatus kann über die UI umgeschaltet werden.
*   **Fernsteuerung via Modbus:** Das `REMOTE_CONTROL_REGISTER` (26) wird wie folgt verwendet:
    *   Client schreibt `1` um den Ladevorgang zu **starten**.
    *   Client schreibt `0` um den Ladevorgang zu **stoppen**.
    *   Der Server bestätigt die Verarbeitung des Befehls, indem er eine `2` in das Register zurückschreibt.
*   **Persistente Fehler:** Der Fehlerzustand (`state`=3, `fault_code`=201) bleibt bestehen, bis er aktiv über `WALLBOX_RESET_REGISTER` (28) oder die UI zurückgesetzt wird.
*   **Konstante Ladeleistung:** Wenn ein Ladevorgang aktiv ist, zeigt das Register `CHARGING_POWER_REGISTER` immer einen Wert von ca. 11 kW an.
*   **Skalierte Ladegeschwindigkeit:** Die tatsächliche Ladegeschwindigkeit (wie schnell der SoC steigt) ist an die globale **Simulationsgeschwindigkeit** gekoppelt. Dies dient dazu, lange Ladevorgänge in kurzer Zeit zu demonstrieren.
