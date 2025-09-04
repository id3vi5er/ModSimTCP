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

Öffnen Sie die Konfiguration des Modbus-Geräts und fügen Sie unter **Adressen** die folgenden Einträge hinzu. Die Adressen sind die Register-Nummern aus der Simulation.

**Wichtig:** 32-Bit-Werte wie die Energiezähler belegen zwei 16-Bit-Register. In IP-Symcon können Sie hierfür den Datentyp `UINT32` oder `INT32` mit der Option `High Word First` (oder ähnlich) verwenden, um die beiden Register automatisch zu einem Wert zusammenzufassen.

---

**Spannungen und Ströme**

*   **Spannung L1**
    *   Adresse: `1`, Datentyp: `INT16`, Faktor: `0.1`
*   **Spannung L2**
    *   Adresse: `2`, Datentyp: `INT16`, Faktor: `0.1`
*   **Spannung L3**
    *   Adresse: `3`, Datentyp: `INT16`, Faktor: `0.1`
*   **Strom L1**
    *   Adresse: `4`, Datentyp: `INT16`, Faktor: `0.01`
*   **Strom L2**
    *   Adresse: `5`, Datentyp: `INT16`, Faktor: `0.01`
*   **Strom L3**
    *   Adresse: `6`, Datentyp: `INT16`, Faktor: `0.01`

---

**Leistungswerte (Gesamt)**

*   **Wirkleistung**
    *   Adresse: `7`, Datentyp: `INT16`, Faktor: `1`
*   **Blindleistung**
    *   Adresse: `8`, Datentyp: `INT16`, Faktor: `1`
*   **Scheinleistung**
    *   Adresse: `9`, Datentyp: `INT16`, Faktor: `1`
*   **Leistungsfaktor**
    *   Adresse: `10`, Datentyp: `INT16`, Faktor: `0.01`

---

**Netz- & Energiezähler**

*   **Netzfrequenz**
    *   Adresse: `11`, Datentyp: `INT16`, Faktor: `0.01`
*   **Tagesertrag (Wh, 32-Bit)**
    *   Adresse: `12`, Datentyp: `UINT32 (High Word First)`
*   **Gesamtertrag (kWh, 32-Bit)**
    *   Adresse: `14`, Datentyp: `UINT32 (High Word First)`

---

**DC-Seite (Gleichstrom)**

*   **DC Spannung**
    *   Adresse: `16`, Datentyp: `INT16`, Faktor: `0.1`
*   **DC Strom**
    *   Adresse: `17`, Datentyp: `INT16`, Faktor: `0.01`
*   **DC Leistung**
    *   Adresse: `18`, Datentyp: `INT16`, Faktor: `1`

---

**Status und Steuerung**

*   **Betriebszustand**
    *   Adresse: `19`
    *   (Werte: 1=Standby, 2=Einspeisung, 3=Fehler)
*   **Gerätetemperatur**
    *   Adresse: `20`, Datentyp: `INT16`, Faktor: `0.1`
*   **Fehlercode**
    *   Adresse: `21`, Datentyp: `INT16`
*   **Fehler zurücksetzen (Schreiben)**
    *   Adresse: `22`, Datentyp: `INT16`
    *   **Beschreibung:** Um einen Fehler zu quittieren, schreiben Sie eine `1`.

---

#### D. Abschluss der Konfiguration

1.  Aktivieren Sie für jeden Eintrag die Checkbox **Aktiv**, damit eine Variable in IP-Symcon erstellt wird.
2.  Klicken Sie auf **Übernehmen**.

Sie sollten nun die Live-Werte für alle konfigurierten Register im Objektbaum von IP-Symcon sehen können.

---
---

### Schritt 4: Wallbox-Simulation

Zusätzlich zu den PV-Wechselrichtern simuliert das Skript auch **12 Wallboxen** zum Laden von Elektroautos.

*   **IP-Adressen:** `10.10.10.140` bis `10.10.10.151`
*   **Modbus Port:** `5020` (derselbe wie für die PV-Wechselrichter)

Die Wallboxen erscheinen in einer separaten Tabelle auf der Web-Monitoring-Oberfläche.

#### A. Steuerung über die Weboberfläche

In der Wallbox-Tabelle auf der Weboberfläche finden Sie für jede Wallbox die folgenden Steuerelemente:

*   **Verbinden / Trennen:** Simuliert das An- und Abstecken eines Elektroautos.
*   **Laden starten / stoppen:** Startet oder beendet einen Ladevorgang. Ein Ladevorgang kann nur gestartet werden, wenn ein Fahrzeug verbunden ist.
*   **Fehler erzeugen:** Simuliert einen Fehler der Wallbox. Dieser Fehler ist **persistent** und muss über den "Reset"-Button zurückgesetzt werden.
*   **SoC setzen:** Hier können Sie einen Start-Ladezustand (in %) für das simulierte Fahrzeug eintragen. Dies funktioniert nur, wenn die Wallbox gerade nicht lädt.

#### B. Anbindung an IP-Symcon

Die Anbindung einer Wallbox an IP-Symcon erfolgt analog zu den PV-Wechselrichtern (siehe Schritt 3), nur dass Sie die IP-Adresse einer Wallbox verwenden (z.B. `10.10.10.140`).

#### C. Wallbox-Register zur Datenabfrage

Hier sind die Modbus-Register, die jede Wallbox zur Verfügung stellt:

*   **Betriebszustand**
    *   Name: `Wallbox Zustand`
    *   Adresse: `20`
    *   Datentyp: `INT16`
    *   (Werte: 1=Bereit, 2=Ladevorgang, 3=Fehler)
*   **Ladeleistung**
    *   Name: `Ladeleistung`
    *   Adresse: `21`
    *   Datentyp: `INT16`
    *   Einheit: `W`
*   **Ladezustand (SoC)**
    *   Name: `Ladezustand`
    *   Adresse: `22`
    *   Datentyp: `INT16`
    *   Einheit: `%`
*   **Geladene Energie (32-Bit)**
    *   Name: `Geladene Energie`
    *   Adresse: `23`
    *   Datentyp: `UINT32 (High Word First)`
    *   Einheit: `Wh`
*   **Fehlercode**
    *   Name: `Wallbox Fehlercode`
    *   Adresse: `25`
    *   Datentyp: `INT16`
    *   (Werte: 0=OK, 201=Ladefehler, 404=Kein Auto verbunden)
*   **Fahrzeug verbunden (Lesen)**
    *   Name: `Fahrzeug verbunden`
    *   Adresse: `27`
    *   Datentyp: `INT16`
    *   (Werte: 0=Nein, 1=Ja)

---

**Steuerung (Schreiben)**

*   **Fernsteuerung**
    *   Name: `Fernsteuerung`
    *   Adresse: `26`
    *   Datentyp: `INT16`
    *   **Beschreibung:** Schreiben Sie eine `1` zum Starten oder `0` zum Stoppen des Ladevorgangs. Der Start funktioniert nur, wenn ein Fahrzeug verbunden ist. Der Simulator quittiert den Befehl, indem er eine `2` zurückschreibt.
*   **Fehler zurücksetzen**
    *   Name: `Fehler Reset`
    *   Adresse: `28`
    *   Datentyp: `INT16`
    *   **Beschreibung:** Um einen Fehler (Zustand 3) zu quittieren, schreiben Sie eine `1` in dieses Register.
