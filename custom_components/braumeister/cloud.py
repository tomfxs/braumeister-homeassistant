"""Direkte Verbindung zu My-Speidel (Login, Token, MQTT über WebSocket) – ohne Dashboard."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from collections.abc import Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE = "https://www.myspeidel.com"
MQTT_HOST = "api.cloud.myspeidel.com"
MQTT_PATH = "/mqtt"
BACKOFF_MIN, BACKOFF_MAX = 2, 60
COMMAND_TIMEOUT = 12


class CloudError(Exception):
    """My-Speidel nicht erreichbar."""


class InvalidAuth(CloudError):
    """Benutzername oder Passwort falsch."""


async def async_get_token(session: aiohttp.ClientSession, user: str, password: str) -> str:
    """Anmelden und das Token aus der Cockpit-Seite lesen (dient als MQTT-Benutzername)."""
    try:
        async with session.post(
            f"{BASE}/auth/login",
            data={"identity": user, "password": password, "submit": ""},
            headers={"Origin": BASE, "Referer": f"{BASE}/auth/login"},
            allow_redirects=False,
            timeout=aiohttp.ClientTimeout(total=20),
        ):
            pass
        async with session.get(
            f"{BASE}/myspeidel/index",
            headers={"Referer": f"{BASE}/auth/login"},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as r:
            if r.status >= 400:
                raise CloudError(f"My-Speidel antwortet mit HTTP {r.status}")
            html = await r.text()
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CloudError(f"My-Speidel nicht erreichbar: {err}") from err
    m = re.search(r"var\s+sessionValue\s*=\s*'([0-9a-f]+)'", html, re.IGNORECASE)
    if not m:
        raise InvalidAuth("Anmeldung bei My-Speidel fehlgeschlagen")
    return m.group(1)


class SpeidelCloud:
    """Hält die MQTT-Verbindung, verbindet bei Abbruch mit frischem Token neu."""

    def __init__(
        self,
        hass: Any,
        session_factory: Callable[[], aiohttp.ClientSession],
        user: str,
        password: str,
        device: str,
        on_message: Callable[[str, bytes], None],
        on_connected: Callable[[], None],
        on_auth_failed: Callable[[], None],
    ) -> None:
        self.hass, self.user, self.password, self.device = hass, user, password, device
        self._session_factory = session_factory
        self._on_message, self._on_connected, self._on_auth_failed = on_message, on_connected, on_auth_failed
        self._loop = asyncio.get_running_loop()
        self._client: Any = None
        self._task: asyncio.Task | None = None
        self._stop = False
        self._connected = asyncio.Event()
        self._dropped = asyncio.Event()
        self._pending: dict[str, asyncio.Future] = {}
        self._ssl: Any = None

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    def start(self) -> None:
        self._task = self.hass.async_create_background_task(self._run(), "braumeister_cloud")

    async def stop(self) -> None:
        self._stop = True
        self._dropped.set()
        if self._task:
            self._task.cancel()
        await self.hass.async_add_executor_job(self._close)

    def _close(self) -> None:
        client, self._client = self._client, None
        if client:
            try:
                client.disconnect()
                client.loop_stop()
            except Exception:  # noqa: BLE001
                pass

    # -- Verbindungsschleife ------------------------------------------------
    async def _run(self) -> None:
        backoff = BACKOFF_MIN
        while not self._stop:
            try:
                session = self._session_factory()
                try:
                    token = await async_get_token(session, self.user, self.password)
                finally:
                    await session.close()
                await self._connect(token)
                await asyncio.wait_for(self._connected.wait(), 20)
                backoff = BACKOFF_MIN
                await self._dropped.wait()                       # läuft, bis die Verbindung abreißt
            except InvalidAuth:
                _LOGGER.error("My-Speidel lehnt die Anmeldung ab – Zugangsdaten prüfen")
                self._on_auth_failed()
                return
            except (CloudError, TimeoutError, OSError) as err:
                _LOGGER.warning("My-Speidel-Verbindung: %s – neuer Versuch in %s s", err, backoff)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unerwarteter Fehler in der My-Speidel-Verbindung")
            self._connected.clear()
            await self.hass.async_add_executor_job(self._close)
            if self._stop:
                return
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX)

    async def _connect(self, token: str) -> None:
        import paho.mqtt.client as mqtt  # noqa: PLC0415

        if self._ssl is None:
            from homeassistant.util.ssl import get_default_context  # noqa: PLC0415

            self._ssl = get_default_context()
        self._dropped.clear()
        self._connected.clear()
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="homeassistant_" + uuid.uuid4().hex[:8],
            protocol=mqtt.MQTTv311,
            transport="websockets",
            clean_session=True,
        )
        client.ws_set_options(path=MQTT_PATH)
        client.tls_set_context(self._ssl)
        client.username_pw_set(token)                           # Token als Benutzername, ohne Passwort
        client.reconnect_delay_set(min_delay=1, max_delay=1)
        client.on_connect = self._cb_connect
        client.on_disconnect = self._cb_disconnect
        client.on_message = self._cb_message
        self._client = client
        await self.hass.async_add_executor_job(self._start_client, client)

    @staticmethod
    def _start_client(client: Any) -> None:
        client.connect_async(MQTT_HOST, 443, keepalive=60)
        client.loop_start()

    # -- paho-Rückrufe (laufen im Netzwerk-Thread) -------------------------------
    def _cb_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        if getattr(reason_code, "is_failure", reason_code != 0):
            _LOGGER.warning("My-Speidel MQTT abgelehnt: %s", reason_code)
            self._loop.call_soon_threadsafe(self._dropped.set)
            return
        from .state import REQUEST_TOPICS, STAT_TOPICS, TELE_TOPICS  # noqa: PLC0415

        d = self.device
        for t in STAT_TOPICS:
            client.subscribe(f"stat/{d}/{t}", qos=0)
        for t in TELE_TOPICS:
            client.subscribe(f"tele/{d}/{t}", qos=0)
        for t in REQUEST_TOPICS:                                # Leseanfragen wie auf der My-Speidel-Seite
            client.publish(f"cmnd/{d}/{t}", "")
        self._loop.call_soon_threadsafe(self._connected.set)
        self._loop.call_soon_threadsafe(self._on_connected)

    def _cb_disconnect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        if client is self._client:
            self._loop.call_soon_threadsafe(self._dropped.set)

    def _cb_message(self, client: Any, userdata: Any, msg: Any) -> None:
        self._loop.call_soon_threadsafe(self._dispatch, msg.topic, bytes(msg.payload))

    def _dispatch(self, topic: str, payload: bytes) -> None:
        fut = self._pending.get(topic)
        if fut is not None:
            if not fut.done():
                try:
                    fut.set_result(json.loads(payload) if payload else None)
                except ValueError:
                    fut.set_result(payload.decode("utf-8", "replace"))
            return
        self._on_message(topic, payload)

    # -- Befehle ------------------------------------------------------------------
    async def send(self, command: str, payload: str, prefix: str = "manual") -> Any:
        """Befehl an cmnd/<gerät>/remoteCtrl/… senden und die Antwort abwarten."""
        if not self.connected or self._client is None:
            raise CloudError("Keine Verbindung zu My-Speidel")
        h = uuid.uuid4().hex
        rid = f"{prefix}-{h[:4]}-4{h[4:7]}-{'89ab'[int(h[7], 16) & 3]}{h[8:11]}-{h[12:24]}"       # Format wie die Weboberfläche
        stat_topic = f"stat/{self.device}/remoteCtrl/{rid}"
        cmnd_topic = f"cmnd/{self.device}/remoteCtrl/{rid}"
        fut: asyncio.Future = self._loop.create_future()
        self._pending[stat_topic] = fut
        client = self._client
        try:
            await self.hass.async_add_executor_job(
                lambda: (client.subscribe(stat_topic, qos=0), client.publish(
                    cmnd_topic, json.dumps({"topic": f"remoteControl/{command}", "payload": payload}, separators=(",", ":")))))
            return await asyncio.wait_for(fut, COMMAND_TIMEOUT)
        except TimeoutError as err:
            raise CloudError(f"Keine Antwort vom Braumeister auf {command} (Zeitüberschreitung)") from err
        finally:
            self._pending.pop(stat_topic, None)
            await self.hass.async_add_executor_job(client.unsubscribe, stat_topic)
