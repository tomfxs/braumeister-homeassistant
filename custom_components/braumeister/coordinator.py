"""Holt den gebündelten Zustand vom Braumeister-Dashboard (GET /api/ha/state)."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class BraumeisterCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS))
        self.host, self.port = host, port
        self.base = f"http://{host}:{port}"
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with self.session.get(f"{self.base}/api/ha/state", timeout=aiohttp.ClientTimeout(total=10)) as r:
                r.raise_for_status()
                return await r.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Dashboard {self.base} nicht erreichbar: {err}") from err

    async def _post(self, path: str, body: dict[str, Any]) -> Any:
        try:
            async with self.session.post(f"{self.base}{path}", json=body, timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status >= 400:
                    raise HomeAssistantError(await r.text())
                return await r.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Dashboard {self.base} nicht erreichbar: {err}") from err

    async def command(self, command: str, **params: Any) -> None:
        """Befehl an den Braumeister (POST /api/device/command), danach Zustand neu lesen."""
        await self._post("/api/device/command", {"command": command, **params})
        await self.async_request_refresh()
