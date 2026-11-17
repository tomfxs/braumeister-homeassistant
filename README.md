# Braumeister – Home-Assistant-Integration

<img src="icon.svg" width="96" align="right" alt="Braumeister">

Bringt den Speidel Braumeister mit allen wichtigen Daten in Home Assistant. Die Integration spricht mit dem
lokalen Braumeister-Dashboard (`node dashboard.js`, Port 8080), das `braumeister-client.js` füttert –
sie verbindet sich also nicht selbst mit My-Speidel.

Der Dashboard-Server liefert dafür einen gebündelten Zustand unter `GET /api/ha/state` (`server/api/homeassistant.js`).
Befehle laufen über das vorhandene `POST /api/device/command` (mit den gleichen Zustandsprüfungen wie im Dashboard).

## Installation mit HACS

Voraussetzung: [HACS](https://hacs.xyz) ist in Home Assistant installiert (Version 2025.1 oder neuer).

1. In HACS oben rechts das Menü (⋮) › **Benutzerdefinierte Repositories**.
2. Repository: `https://github.com/tomfxs/braumeister-homeassistant`, Kategorie: **Integration** › Hinzufügen.
   (Das Repo muss öffentlich sein, oder in HACS ist ein GitHub-Token hinterlegt.)
3. In HACS nach **Braumeister** suchen › Herunterladen (die neueste Version wählen).
4. Home Assistant **neu starten**.
5. Einstellungen › Geräte & Dienste › Integration hinzufügen › **Braumeister** – Host/IP des Rechners mit `dashboard.js` und Port (8080).

Das Dashboard hat keine Anmeldung – nur im Heimnetz erreichbar machen.

## Entitäten

| Typ | Entitäten |
|---|---|
| Sensor | Zustand, Temperatur, Solltemperatur, Phase, Rezept, Gesamt-/Phasenfortschritt, Timer-/Gesamt-Restzeit, Brausession, Checkliste erledigt, Warnung („Deckel entfernen“), letzter Hinweis, Firmware |
| Binärsensor | Online, Sud läuft, Handbetrieb, Heizung, Pumpe, Timer läuft, Wasser eingefüllt, Warnung aktiv, Session läuft, Probelauf |
| Schalter | Handbetrieb: Pumpe, Temperaturregelung, Timer |
| Zahl | Handbetrieb: Solltemperatur, Timer-Dauer (Minuten) |
| Button | Brauen starten, Abbruch anfordern/bestätigen/zurücknehmen, Handbetrieb starten (Brauen/Gären)/beenden, Wasser bestätigen |
| Dienst | `braumeister.start_recipe` (`uuid`) – Rezept auf dem Gerät starten |

Schalter, Zahlen und Befehle sind nur im passenden Gerätezustand möglich; sonst meldet Home Assistant die Fehlermeldung des Servers.
Aktualisierung alle 5 Sekunden.

> Hinweis: Die Zuordnung `heating`/`pump` (2 = an) und die Feldnamen der Statusmeldung (`temperature`, `targetTemperature`)
> stammen aus dem Code des Projekts; ob sie bei laufendem Gerät exakt so ankommen, sollte beim nächsten Sud geprüft werden.

## Updates

Änderungen im Repo committen, pushen und ein neues Release anlegen (Tag z. B. `v1.0.1`, `version` in
`custom_components/braumeister/manifest.json` passend erhöhen). HACS zeigt dann ein Update an; danach Home Assistant neu starten.
Ohne Release nutzt HACS den neuesten Commit des Standardzweigs.

## Hinweis zum Dashboard

Die Integration braucht den Endpunkt `/api/ha/state` im Braumeister-Dashboard (`server/api/homeassistant.js`
im Projekt-Repo). Dashboard und Integration müssen zusammenpassen.
