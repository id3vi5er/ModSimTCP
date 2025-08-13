# Technisches Handbuch für Dozenten: PV-Simulator

Dieses Dokument bietet eine detaillierte technische Referenz für den PV-Simulator. Es richtet sich an Dozenten und Entwickler, die ein tiefes Verständnis der simulierten Werte und des Systemverhaltens benötigen.

---

## Modbus Register-Referenz

Die folgende Tabelle listet alle Holding-Register auf, die von jeder Simulator-Instanz bereitgestellt werden.

| Adresse | Register-Name (Code) | Beschreibung | Datentyp | Client Faktor | Einheit | Min. Wert (ca.) | Max. Wert (ca.) |
|---|---|---|---|---|---|---|---|
| 1 | `VOLTAGE_REGISTER` | AC Netzspannung | `INT16` | `0.1` | V | 229.0 | 231.0 |
| 2 | `CURRENT_REGISTER` | AC Netzstrom | `INT16` | `0.01` | A | 0.0 | ~16.5 |
| 3 | `APPARENT_POWER_REGISTER` | AC Scheinleistung | `INT16` | `1` | VA | 0 | ~3800 |
| 4 | `ACTIVE_POWER_REGISTER` | AC Wirkleistung | `INT16` | `1` | W | 0 | ~3750 |
| 5 | `POWER_FACTOR_REGISTER` | Leistungsfaktor | `INT16` | `0.01` | - | 0.90 | 1.00 |
| 6 | `REACTIVE_POWER_REGISTER` | AC Blindleistung | `INT16` | `1` | VAR | 0 | ~850 |
| 7 | `FREQUENCY_REGISTER` | Netzfrequenz | `INT16` | `0.01` | Hz | 49.98 | 50.02 |
| 8-9 | `DAILY_YIELD_REGISTER` | Tagesertrag (Energie) | `UINT32` | `1` | Wh | 0 | Kumulativ |
| 10-11 | `TOTAL_YIELD_REGISTER` | Gesamtertrag (Energie) | `UINT32` | `1` | kWh | 500 | Kumulativ |
| 12 | `OPERATING_STATE_REGISTER` | Betriebszustand | `INT16` | `1` | - | 1 | 3 |
| 13 | `DEVICE_TEMP_REGISTER` | Gerätetemperatur | `INT16` | `0.1` | °C | 24.5 | ~51.0 |
| 14 | `FAULT_CODE_REGISTER` | Fehlercode | `INT16` | `1` | - | 0 | 101 |
| 15 | `DC_VOLTAGE_REGISTER` | DC Eingangsspannung | `INT16` | `0.1` | V | 340.0 | 360.0 |
| 16 | `DC_CURRENT_REGISTER` | DC Eingangsstrom | `INT16` | `0.01` | A | 0.0 | ~11.0 |
| 17 | `DC_POWER_REGISTER` | DC Eingangsleistung | `INT16` | `1` | W | 0 | ~4000 |

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
| `101` | **Simulierter Fehler** | Ein zufällig ausgelöster, temporärer Fehler. Das System setzt sich nach kurzer Zeit (einige Update-Zyklen) automatisch zurück. Dient zum Testen der Fehlererkennung im Client. |

---

## Hinweise zur Simulation

*   **Tageszyklus:** Die DC-Leistung folgt einer Sinus-Kurve, um einen Tag-Nacht-Wechsel zu simulieren.
*   **Zufälligkeit:** Alle Werte enthalten eine leichte zufällige Schwankung, um realistische Messdaten nachzubilden.
*   **Instanz-Varianz:** Die maximale DC-Stromstärke variiert leicht zwischen den 12 Instanzen, was zu geringfügig unterschiedlichen maximalen Leistungen führt.
*   **Tagesertrag-Reset:** Der Tagesertrag (`DAILY_YIELD_REGISTER`) wird automatisch um Mitternacht zurückgesetzt.
