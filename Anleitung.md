### PV-Simulator für Modbus TCP: Installationsanleitung

Dieses Handbuch beschreibt die Inbetriebnahme des PV-Simulators und die Anbindung der simulierten Wechselrichter an ein IP-Symcon-System über Modbus TCP. Es richtet sich an Elektriker und Auszubildende.

Der Simulator erstellt 12 virtuelle PV-Wechselrichter, die jeweils unter einer eigenen IP-Adresse erreichbar sind.

---

### Schritt 1: Installation und Start des Simulators

1.  **Voraussetzungen installieren:**
    Das Skript benötigt Python 3 und die Bibliotheken `pymodbus` und `flask`. Installieren Sie diese mit pip:
    ```bash
    pip install pymodbus flask
    ```

2.  **Netzwerk konfigurieren:**
    Der Server, auf dem das Skript läuft, muss die IP-Adressen `10.10.10.120` bis `10.10.10.131` besitzen. Eine detaillierte Anleitung zur Netzwerkkonfiguration unter Linux finden Sie in der [README.md](README.md).

3.  **Simulator starten:**
    Führen Sie das Skript in Ihrem Terminal aus:
    ```bash
    python3 main.py
    ```
    Das Skript startet nun 12 Modbus-Server und ein Web-Interface.

---

### Schritt 2: Web-Monitoring-Oberfläche

Zur Überwachung der simulierten Wechselrichter können Sie die mitgelieferte Weboberfläche nutzen.

*   **URL:** `http://<IP-des-Servers>:5010`
    (Ersetzen Sie `<IP-des-Servers>` mit der primären IP-Adresse des Rechners, auf dem das Skript läuft, z.B. `http://10.10.10.115:5010`)

Die Oberfläche zeigt den Status, die aktuelle Leistung und weitere Daten für alle 12 simulierten Geräte in Echtzeit an.

---

### Schritt 3: Anbindung an IP-Symcon (Beispiel)

Hier wird die Anbindung eines der 12 simulierten Wechselrichter beschrieben.

#### A. Modbus Gateway einrichten

1.  Wählen Sie im **Objektbaum** von IP-Symcon das **Plus-Symbol** (+) aus.
2.  Gehen Sie zu **Gateway** und fügen Sie ein **Modbus Gateway** hinzu.
3.  Wählen Sie unter **Verbindung** die Option **Modbus TCP** aus.
4.  Geben Sie die **IP-Adresse** und den **Port** eines simulierten Geräts an.
    * **Host:** `10.10.10.120` (oder eine andere IP von `.121` bis `.131`)
    * **Port:** `5020`
5.  Bestätigen Sie die Einstellungen mit **Übernehmen**.

#### B. Modbus Gerät hinzufügen

1.  Wählen Sie erneut das **Plus-Symbol** (+) im Objektbaum.
2.  Wählen Sie **Gerät** und fügen Sie ein **Modbus Device** hinzu.
3.  Stellen Sie sicher, dass das zuvor erstellte Modbus Gateway als Parent ausgewählt ist.
4.  Setzen Sie die **Geräte-ID** auf **1**.

#### C. Register zur Datenabfrage definieren

Öffnen Sie die Konfiguration des Modbus-Geräts und fügen Sie unter **Adressen** die folgenden Einträge hinzu:

* **Spannung (Voltage)**
    * **Name:** `Spannung`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `1`
    * **Faktor:** `0.1` (Teilt den gelesenen Wert durch 10.0)
* **Strom (Current)**
    * **Name:** `Strom`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `2`
    * **Faktor:** `0.1` (Teilt den gelesenen Wert durch 10.0)
* **Leistung (Power)**
    * **Name:** `Leistung`
    * **Datentyp:** `INT16`
    * **Funktion (Lesen):** `Read Holding Registers (3)`
    * **Adresse (Lesen):** `3`
    * **Faktor:** `1` (Keine Skalierung)

#### D. Abschluss der Konfiguration

1.  Aktivieren Sie die Checkbox **Aktiv** für jeden Eintrag, damit eine Variable in IP-Symcon erstellt wird.
2.  Klicken Sie auf **Übernehmen**.

Sie sollten nun die Live-Werte für Spannung, Strom und Leistung im Objektbaum von IP-Symcon sehen können.
