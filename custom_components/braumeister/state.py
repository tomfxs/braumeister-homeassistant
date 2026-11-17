"""Gerätezustand des Braumeisters aus den My-Speidel-MQTT-Nachrichten (ohne Home-Assistant-Abhängigkeit).

Entspricht server/device/telemetry.js, states.js, alerts.js und control.js des Dashboards und liefert denselben
Datensatz wie dessen /api/ha/state, damit die Entitäten in beiden Betriebsarten gleich funktionieren.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

IDLE = ["Finished", "Idle", "Completed"]
BREWING = [
    "AboutToStartBrewing", "PumpVentilation", "HeatingUpMashing", "HeatedUpMashing", "MaltInsertBreak",
    "HeatingUpRest", "HeatedUpRest", "Resting", "RestFinished", "TakeOutMalt", "HeatingUpHop", "HeatedUpHop",
    "HopCooking", "AddHop", "Cooling", "Mashing", "Lautering", "Boiling",
]
MANUAL = ["Manual", "Fermenting"]

LIVE_S = 150          # im Leerlauf meldet das Gerät etwa alle 40–60 s
STATUS_S = 180
ALERT_WINDOW_S = 600

# Muster für Warnungen („Deckel entfernen“ o. ä.), wie BM_ALERT_REGEX im Dashboard
ALERT_RE = re.compile(
    r"deckel\W*(?:\w+\W+){0,2}?(?:entfern|abnehm|öffn|abheb|runter)"
    r"|(?:entfern|abnehm|öffn|abheb)\w*\W+(?:\w+\W+){0,2}?deckel"
    r"|remove\W+(?:the\W+)?lid|lid\W+(?:off|remov|open)",
    re.IGNORECASE,
)

# Themen, die abonniert und beim Verbinden einmal angefragt werden (wie braumeister-client.js)
STAT_TOPICS = [
    "status", "machineinfo", "brewing/phase", "brewing/state", "brewing/timers",
    "brewing/startBrewing", "brewing/manual", "config", "tilt/color",
]
TELE_TOPICS = ["status", "brewing/phase", "brewing/state", "brewing/timers", "brewing/startBrewing", "brewing/manual"]
REQUEST_TOPICS = [
    "status", "brewing/phase", "brewing/state", "brewing/timers", "brewing/startBrewing", "brewing/manual",
    "config", "machineinfo", "tilt/color",
]


class CommandError(ValueError):
    """Ungültiger Befehl oder im aktuellen Gerätezustand nicht erlaubt."""


def _num_in(v: Any, lo: float, hi: float, name: str) -> float:
    try:
        n = float(v)
    except (TypeError, ValueError):
        n = float("nan")
    if n != n or n in (float("inf"), float("-inf")) or n < lo or n > hi:
        raise CommandError(f"{name}: Wert zwischen {lo:g} und {hi:g} erwartet")
    return int(n) if n == int(n) else n


def _bool(v: Any, name: str) -> bool:
    if not isinstance(v, bool):
        raise CommandError(f"{name}: true/false erwartet")
    return v


def _js(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _start_recipe(b: dict[str, Any]) -> str:
    if not re.fullmatch(r"[0-9a-f-]{36}", str(b.get("uuid", "")), re.IGNORECASE):
        raise CommandError("Ungültige Rezept-ID")
    return _js(b["uuid"])


def _start_manual(b: dict[str, Any]) -> str:
    if b.get("mode") not in ("brewing", "fermenting"):
        raise CommandError("Modus brewing oder fermenting erwartet")
    return b["mode"]


# Befehl -> (erlaubte Zustände, Payload) – exakt wie server/device/control.js
COMMANDS: dict[str, tuple[list[str], Any]] = {
    "startRecipe": (IDLE, _start_recipe),
    "startBrewing": (["AboutToBrewStart"], lambda b: ""),
    "requestAbort": ([*BREWING, "AboutToBrewStart"], lambda b: ""),
    "confirmAbort": (["AboutToAbort"], lambda b: ""),
    "cancelAbort": (["AboutToAbort"], lambda b: ""),
    "startManual": (IDLE, _start_manual),
    "stopManual": (MANUAL, lambda b: ""),
    "manual/waterConfirm": (MANUAL, lambda b: ""),
    "manual/temperature": (MANUAL, lambda b: _js({"value": _num_in(b.get("value"), 0, 100, "Temperatur")})),
    "manual/temperatureControl": (MANUAL, lambda b: _js({"on": _bool(b.get("on"), "on")})),
    "manual/pump": (MANUAL, lambda b: _js({"on": _bool(b.get("on"), "on")})),
    # Dauer in Minuten, das Gerät erwartet Sekunden
    "manual/timer": (MANUAL, lambda b: _js({"duration": _num_in(b.get("minutes"), 0, 600, "Timer") * 60})),
    "manual/timerEnable": (MANUAL, lambda b: _js({"enable": _bool(b.get("enable"), "enable")})),
}


def _iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _alert_text(value: Any) -> str | None:
    """Kürzester passender Text in der Nachricht (wie alertText in alerts.js)."""
    hits: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, str):
            if ALERT_RE.search(v):
                hits.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(value)
    return min(hits, key=len)[:200] if hits else None


class DeviceState:
    """Letzte Meldungen des Geräts und der daraus abgeleitete Zustand."""

    def __init__(self, device: str) -> None:
        self.device = device
        self.latest: dict[str, tuple[float, Any]] = {}      # Thema (ohne stat/tele) -> (Zeit, Inhalt)
        self.live_at: float | None = None
        self.alert: dict[str, Any] | None = None
        self._prefixes = (f"stat/{device}/", f"tele/{device}/")

    def feed(self, topic: str, payload: bytes | str, now: float) -> bool:
        """Nachricht aufnehmen; True, wenn sie den Zustand betrifft."""
        raw = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else payload
        if not raw or not topic.startswith(self._prefixes):
            return False
        try:
            msg = json.loads(raw)
        except ValueError:
            return False
        body = msg["body"] if isinstance(msg, dict) and "body" in msg else msg
        suffix = topic.split("/", 2)[2]
        if suffix.startswith("remoteCtrl/"):
            return False
        text = _alert_text(msg)
        if text:
            self.alert = {"text": text, "topic": topic, "at": now}
        if body is None:
            return False
        self.latest[suffix] = (now, body)
        if topic.startswith(f"tele/{self.device}/status"):
            self.live_at = now
        return True

    def body(self, suffix: str) -> Any:
        v = self.latest.get(suffix)
        return v[1] if v else None

    def snapshot(self, now: float) -> dict[str, Any]:
        status_entry = self.latest.get("status")
        status = status_entry[1] if status_entry else {}
        state = status.get("deviceState") if isinstance(status, dict) else None
        age = None if status_entry is None else now - status_entry[0]
        live_age = None if self.live_at is None else now - self.live_at
        fresh = age is not None and age < STATUS_S and live_age is not None and live_age < LIVE_S
        brewing_state = self.body("brewing/state") or {}
        alert = self.alert
        if alert and now - alert["at"] > ALERT_WINDOW_S:
            alert = None
        return {
            "device": {
                "state": state, "fresh": fresh, "powerOff": False, "dryRun": False,
                "ts": _iso(status_entry[0]) if status_entry else None, "liveTs": _iso(self.live_at),
                "group": None if not state else "brewing" if state in BREWING else "manual" if state in MANUAL
                         else "idle" if state in IDLE else "other",
                "status": status, "manual": self.body("brewing/manual"),
                "recipeName": brewing_state.get("recipeName") or None,
                "brewing": self.body("brewing/state"), "phase": self.body("brewing/phase"),
                "timers": self.body("brewing/timers"), "info": self.body("machineinfo"),
            },
            "session": None,
            "alert": None if alert is None else {"text": alert["text"], "topic": alert["topic"], "ts": _iso(alert["at"]), "recent": True},
            "notify": {"configured": False, "last": None},
        }

    def prepare_command(self, command: str, params: dict[str, Any], now: float) -> tuple[str, str]:
        """Prüft den Befehl gegen den Gerätezustand -> (Befehlsname, Payload)."""
        spec = COMMANDS.get(command)
        if not spec:
            raise CommandError(f"Unbekannter Befehl: {command}")
        snap = self.snapshot(now)["device"]
        if not snap["fresh"]:
            raise CommandError("Der aktuelle Gerätezustand ist unbekannt (keine Statusmeldung in den letzten 3 Minuten). Ist der Braumeister eingeschaltet?")
        if snap["state"] not in spec[0]:
            raise CommandError(f"„{command}“ ist im Zustand „{snap['state']}“ nicht möglich")
        return command, spec[1](params)
