"""Braumeister (Speidel) – mit lokalem Dashboard oder direkt über My-Speidel."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_DEVICE, CONF_MODE, DOMAIN, MODE_DIRECT, PLATFORMS
from .coordinator import BraumeisterCoordinator
from .direct import DirectCoordinator

type BraumeisterConfigEntry = ConfigEntry[BraumeisterCoordinator | DirectCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BraumeisterConfigEntry) -> bool:
    if entry.data.get(CONF_MODE) == MODE_DIRECT:
        coordinator = DirectCoordinator(
            hass, entry, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], entry.data[CONF_DEVICE]
        )
        await coordinator.async_start()
    else:                                   # Einträge ohne Betriebsart stammen von der Dashboard-Version
        coordinator = BraumeisterCoordinator(hass, entry.data[CONF_HOST], entry.data[CONF_PORT])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    async def start_recipe(call: ServiceCall) -> None:
        # bei mehreren Braumeistern: der erste eingerichtete Eintrag
        loaded = [e for e in hass.config_entries.async_loaded_entries(DOMAIN)]
        await loaded[0].runtime_data.command("startRecipe", uuid=call.data["uuid"])

    if not hass.services.has_service(DOMAIN, "start_recipe"):
        hass.services.async_register(
            DOMAIN, "start_recipe", start_recipe, schema=vol.Schema({vol.Required("uuid"): str})
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BraumeisterConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.async_shutdown()
        if not hass.config_entries.async_loaded_entries(DOMAIN):
            hass.services.async_remove(DOMAIN, "start_recipe")
    return ok
