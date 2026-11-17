"""Betriebsart „Direkt“: Verbindung zu My-Speidel ohne laufendes Dashboard."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .cloud import BASE, CloudError, InvalidAuth, SpeidelCloud, async_get_token
from .const import DOMAIN
from .state import CommandError, DeviceState

_LOGGER = logging.getLogger(__name__)
REFRESH_SECONDS = 15        # nur, damit „Online“ auch ohne neue Meldungen ausläuft


class DirectCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Gleiche Schnittstelle wie BraumeisterCoordinator, Daten kommen per MQTT direkt von My-Speidel."""

    is_direct = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, user: str, password: str, device: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=timedelta(seconds=REFRESH_SECONDS))
        self.device = device
        self.uid = f"direct_{device}"
        self.url = BASE
        self.state = DeviceState(device)
        self.cloud = SpeidelCloud(
            hass, lambda: async_create_clientsession(hass), user, password, device,
            on_message=self._on_message, on_connected=self._push, on_auth_failed=self._auth_failed,
        )
        self._user, self._password = user, password

    async def async_start(self) -> None:
        """Zugangsdaten prüfen, dann die Verbindung im Hintergrund aufbauen."""
        session = async_create_clientsession(self.hass)
        try:
            await async_get_token(session, self._user, self._password)
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CloudError as err:
            raise ConfigEntryNotReady(str(err)) from err
        finally:
            await session.close()
        self.cloud.start()

    async def async_shutdown(self) -> None:
        await self.cloud.stop()
        await super().async_shutdown()

    # -- Daten --------------------------------------------------------------------
    def _snapshot(self) -> dict[str, Any]:
        return self.state.snapshot(time.time())

    async def _async_update_data(self) -> dict[str, Any]:
        return self._snapshot()

    def _push(self) -> None:
        self.async_set_updated_data(self._snapshot())

    def _on_message(self, topic: str, payload: bytes) -> None:
        if self.state.feed(topic, payload, time.time()):
            self._push()

    def _auth_failed(self) -> None:
        if self.config_entry:
            self.config_entry.async_start_reauth(self.hass)

    # -- Befehle -----------------------------------------------------------------------
    async def command(self, command: str, **params: Any) -> None:
        try:
            name, payload = self.state.prepare_command(command, params, time.time())
            response = await self.cloud.send(name, payload)
        except (CommandError, CloudError) as err:
            raise HomeAssistantError(str(err)) from err
        if isinstance(response, dict) and "error" in response:
            raise HomeAssistantError(f"Der Braumeister hat den Befehl abgelehnt (error {response['error']})")
