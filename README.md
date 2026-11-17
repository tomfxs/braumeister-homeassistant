<p align="center">
  <img src="https://raw.githubusercontent.com/tomfxs/braumeister-homeassistant/main/images/icon.png" width="128" alt="Braumeister">
</p>

<h1 align="center">Braumeister für Home Assistant</h1>

<p align="center"><b>Dein Speidel Braumeister – live in Home Assistant.</b><br>
Temperatur, Zustand, Fortschritt und Warnungen im Blick, Steuerung per Knopfdruck.</p>

---

## ✨ Was kann die Integration?

- 🌡️ **Live-Werte:** Temperatur, Solltemperatur, Phase, Rezept, Fortschritt und Restzeiten
- 🔔 **Warnungen:** zum Beispiel „Deckel entfernen“ – ideal für Handy-Meldungen und Automationen
- 🎛️ **Steuerung:** Brauen starten, Abbruch, Handbetrieb mit Pumpe, Temperatur und Timer
- 🏠 **Automationen:** zum Beispiel Licht an, wenn der Sud fertig ist, oder eine Meldung bei erreichter Temperatur
- 📋 **Brausession:** laufende Session und Fortschritt deiner Checkliste

## 📸 So sieht es aus

**Steuerung** – alle Befehle und Handbetrieb-Einstellungen auf einen Blick:

<img src="https://raw.githubusercontent.com/tomfxs/braumeister-homeassistant/main/images/steuerung.png" width="640" alt="Steuerung des Braumeisters">

**Sensoren** – Zustand, Temperatur, Fortschritt und mehr:

<img src="https://raw.githubusercontent.com/tomfxs/braumeister-homeassistant/main/images/sensoren.png" width="320" alt="Sensoren des Braumeisters">

## 📦 Voraussetzungen

- Home Assistant **2025.1** oder neuer mit installiertem [HACS](https://hacs.xyz)
- Das **Braumeister-Dashboard** läuft in deinem Heimnetz (Standard-Port 8080). Du brauchst dessen IP-Adresse oder den Rechnernamen, z. B. `192.168.0.189`.

## 🚀 Installation

1. In Home Assistant **HACS** öffnen, oben rechts das Menü (⋮) › **Benutzerdefinierte Repositories**.
2. Als Repository `https://github.com/tomfxs/braumeister-homeassistant` eintragen, als Kategorie **Integration** wählen und **Hinzufügen** klicken.
3. In HACS nach **Braumeister** suchen und **Herunterladen**.
4. Home Assistant **neu starten**.
5. *Einstellungen › Geräte & Dienste › Integration hinzufügen › Braumeister* – Adresse des Dashboards und Port eintragen.

Fertig! Alle Entitäten erscheinen unter dem Gerät **Braumeister**.

## 🔄 Aktualisieren

In HACS den Eintrag **Braumeister** öffnen, auf **Aktualisieren** klicken und danach Home Assistant neu starten.
Wird kein Update angezeigt: oben rechts im Menü (⋮) **Repository aktualisieren** wählen.

## 🧾 Entitäten im Überblick

**Sensoren**
- Zustand, Phase, Rezept
- Temperatur, Solltemperatur
- Gesamtfortschritt, Phasenfortschritt
- Timer-Restzeit, Gesamt-Restzeit
- Brausession, Checkliste erledigt
- Warnung, letzter Hinweis, Firmware

**Binärsensoren**
- Online, Sud läuft, Handbetrieb
- Heizung, Pumpe, Timer läuft
- Wasser eingefüllt, Warnung aktiv, Session läuft, Probelauf

**Schalter** (Handbetrieb)
- Pumpe, Temperaturregelung, Timer

**Zahlen** (Handbetrieb)
- Solltemperatur, Timer-Dauer in Minuten

**Buttons**
- Brauen starten
- Abbruch anfordern, bestätigen oder zurücknehmen
- Handbetrieb starten (Brauen oder Gären) und beenden
- Wasser bestätigen

**Dienst**
- `braumeister.start_recipe` – startet ein Rezept auf dem Braumeister (Angabe: Rezept-UUID aus My-Speidel)

Die Werte werden alle 5 Sekunden aktualisiert. Schalter, Zahlen und Buttons funktionieren nur, wenn der Braumeister im passenden Zustand ist (z. B. Handbetrieb für die Pumpe). Sonst zeigt Home Assistant eine Fehlermeldung an.

## ⚠️ Hinweise

- Das Dashboard hat keine Anmeldung und ist nur aus dem Heimnetz erreichbar. Gib den Port nicht im Router frei.
- Der Braumeister muss eingeschaltet sein und sich beim Dashboard melden, sonst steht **Online** auf „aus“.

## 🛠️ Probleme?

- **„Dashboard nicht erreichbar“** bei der Einrichtung: Adresse und Port prüfen und testen, ob das Dashboard im Browser unter `http://<Adresse>:8080` erreichbar ist.
- **Werte bleiben leer:** Prüfen, ob der Braumeister online ist.
- **Fehler melden:** [GitHub Issues](https://github.com/tomfxs/braumeister-homeassistant/issues)
