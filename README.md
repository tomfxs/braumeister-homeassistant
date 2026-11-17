# Braumeister für Home Assistant

<img src="icon.svg" width="96" align="right" alt="Braumeister">

Behalte deinen Speidel Braumeister auch in Home Assistant im Blick: Temperatur, Zustand, Fortschritt, Restzeiten und
Warnungen wie „Deckel entfernen“ – und steuere ihn bei Bedarf direkt aus Home Assistant.

Damit lassen sich zum Beispiel Handy-Meldungen, Automationen (etwa Licht an, wenn der Sud fertig ist) oder ein
Dashboard mit dem aktuellen Brauverlauf bauen.

## Voraussetzungen

- Home Assistant 2025.1 oder neuer mit installiertem [HACS](https://hacs.xyz)
- Das **Braumeister-Dashboard** läuft in deinem Heimnetz (Standard: Port 8080). Du brauchst dessen IP-Adresse oder
  Rechnernamen, z. B. `192.168.0.189`.

## Installation

1. In Home Assistant **HACS** öffnen, oben rechts das Menü (⋮) › **Benutzerdefinierte Repositories**.
2. Als Repository `https://github.com/tomfxs/braumeister-homeassistant` eintragen, als Kategorie **Integration** wählen
   und **Hinzufügen** klicken.
3. In HACS nach **Braumeister** suchen und **Herunterladen**.
4. Home Assistant **neu starten**.
5. *Einstellungen › Geräte & Dienste › Integration hinzufügen › Braumeister*. Dort die Adresse des Dashboards und den
   Port eintragen.

Fertig – alle Entitäten erscheinen unter dem Gerät **Braumeister**.

## Aktualisieren

In HACS den Eintrag **Braumeister** öffnen und auf **Aktualisieren** klicken, danach Home Assistant neu starten.
Wird kein Update angezeigt: oben rechts im Menü (⋮) **Repository aktualisieren** wählen.

## Was du bekommst

| Typ | Entitäten |
|---|---|
| Sensoren | Zustand, Temperatur, Solltemperatur, Phase, Rezept, Gesamt- und Phasenfortschritt, Timer-Restzeit, Gesamt-Restzeit, Brausession, Checkliste erledigt, Warnung, letzter Hinweis, Firmware |
| Binärsensoren | Online, Sud läuft, Handbetrieb, Heizung, Pumpe, Timer läuft, Wasser eingefüllt, Warnung aktiv, Session läuft, Probelauf |
| Schalter | Handbetrieb: Pumpe, Temperaturregelung, Timer |
| Zahlen | Handbetrieb: Solltemperatur, Timer-Dauer (Minuten) |
| Buttons | Brauen starten, Abbruch anfordern / bestätigen / zurücknehmen, Handbetrieb starten (Brauen oder Gären) und beenden, Wasser bestätigen |
| Dienst | `braumeister.start_recipe` – startet ein Rezept auf dem Braumeister (Angabe: Rezept-UUID aus My-Speidel) |

Die Werte werden alle 5 Sekunden aktualisiert. Schalter, Zahlen und Buttons funktionieren nur, wenn der Braumeister
im passenden Zustand ist (z. B. Handbetrieb für die Pumpe). Sonst zeigt Home Assistant eine Fehlermeldung an.

## Hinweise

- Das Dashboard hat keine Anmeldung und ist nur aus dem Heimnetz erreichbar. Gib den Port nicht im Router frei.
- Der Braumeister muss eingeschaltet sein und sich beim Dashboard melden. Sonst steht **Online** auf „aus“.

## Probleme?

- *„Dashboard nicht erreichbar“* bei der Einrichtung: Adresse und Port prüfen und testen, ob das Dashboard im Browser
  unter `http://<Adresse>:8080` erreichbar ist.
- Werte bleiben leer: Prüfen, ob der Braumeister online ist.
- Fehler melden: [GitHub Issues](https://github.com/tomfxs/braumeister-homeassistant/issues).
