"""Braumeister (Speidel) – Integration für das lokale Braumeister-Dashboard."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS
from .coordinator import BraumeisterCoordinator

type BraumeisterConfigEntry = ConfigEntry[BraumeisterCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BraumeisterConfigEntry) -> bool:
    coordinator = BraumeisterCoordinator(hass, entry.data[CONF_HOST], entry.data[CONF_PORT])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    async def start_recipe(call: ServiceCall) -> None:
        await coordinator.command("startRecipe", uuid=call.data["uuid"])

    if not hass.services.has_service(DOMAIN, "start_recipe"):
        hass.services.async_register(
            DOMAIN, "start_recipe", start_recipe, schema=vol.Schema({vol.Required("uuid"): str})
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BraumeisterConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok and not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, "start_recipe")
    return ok
