### SolarBFE SoulPV3500 Installationsanleitung: Anbindung über Modbus TCP

Dieses Handbuch beschreibt die Einbindung eines SolarBFE SoulPV3500 Wechselrichters in ein IP-Symcon-System über das Modbus TCP Protokoll. Es richtet sich an Elektriker und Auszubildende.

#### Datenblatt: SolarBFE SoulPV3500 Wechselrichter

* **Modell:** SoulPV3500
* **Ausgangsleistung (max.):** 3500W
* **Schnittstelle:** Modbus TCP
* **Protokoll:** Modbus RTU über TCP
* **Register-Adressen:**
    * **0:** Spannung (Voltage)
    * **1:** Strom (Current)
    * **2:** Leistung (Power)
* **Datentypen:**
    * **Spannung:** Integer (Signed INT16)
    * **Strom:** Integer (Signed INT16)
    * **Leistung:** Integer (Signed INT16)
* **Skalierungsfaktor:**
    * **Spannung/Strom:** Der ausgelesene Wert muss durch 10.0 geteilt werden.
    * **Leistung:** Der Wert ist direkt in Watt und erfordert keine Skalierung.

#### Simulationslogik (zur Veranschaulichung)

Der Wechselrichter simuliert einen täglichen Betriebszyklus.
* **Spannung:** Stabil bei ca. 230V, mit geringen, zufälligen Schwankungen.
* **Strom:** Folgt einem sinusförmigen Tagesverlauf, der von 0A auf einen Spitzenwert von ca. 15A ansteigt und dann wieder auf 0A abfällt.
* **Leistung:** Wird als Produkt von Spannung und Strom (`P = U * I`) berechnet.

---

### Schritt 1: Modbus Gateway einrichten

1.  Wählen Sie im **Objektbaum** von IP-Symcon das **Plus-Symbol** (+) aus.
2.  Gehen Sie zu **Gateway** und fügen Sie ein **Modbus Gateway** hinzu.
3.  Wählen Sie unter **Verbindung** die Option **Modbus TCP** aus.
4.  Geben Sie die **IP-Adresse** und den **Port** des SoulPV3500 an.
    * **Host:** `192.168.178.201` (oder die IP-Adresse Ihres Wechselrichters)
    * **Port:** `502`
5.  Bestätigen Sie die Einstellungen mit **Übernehmen**.

### Schritt 2: Modbus Gerät hinzufügen

1.  Wählen Sie erneut das **Plus-Symbol** (+) im Objektbaum.
2.  Wählen Sie **Gerät** und fügen Sie ein **Modbus Device** hinzu.
3.  Stellen Sie sicher, dass das Modbus Gateway als Parent ausgewählt ist.
4.  Setzen Sie die **Geräte-ID** auf **1**.

### Schritt 3: Register zur Datenabfrage definieren

Öffnen Sie die **Adressenliste** und fügen Sie die folgenden Einträge hinzu:

* **Spannung (Voltage)**
    * **Name:** `Spannung`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `0`
    * **Faktor:** `0.1` (Teilt den Wert durch den Skalierungsfaktor 10.0)
* **Strom (Current)**
    * **Name:** `Strom`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `1`
    * **Faktor:** `0.1` (Teilt den Wert durch den Skalierungsfaktor 10.0)
* **Leistung (Power)**
    * **Name:** `Leistung`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `2`
    * **Faktor:** `1` (Keine Skalierung erforderlich)

### Schritt 4: Abschluss der Konfiguration

1.  Aktivieren Sie die Checkbox **Aktiv** für jeden Eintrag.
2.  Klicken Sie auf **Übernehmen**.

Sie sollten nun die Werte für Spannung, Strom und Leistung im Objektbaum sehen können. Überprüfen Sie zur Sicherheit die Konsole des Wechselrichters, um die Werte zu verifizieren (z.B. `U=230.1V, I=7.50A, P=1725W`).
