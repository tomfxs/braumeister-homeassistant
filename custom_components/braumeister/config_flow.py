"""Einrichtung: mit lokalem Dashboard oder direkt über My-Speidel."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession, async_get_clientsession

from .cloud import CloudError, InvalidAuth, async_get_token
from .const import CONF_DEVICE, CONF_MODE, DEFAULT_PORT, DOMAIN, MODE_DASHBOARD, MODE_DIRECT


class BraumeisterConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="user", menu_options=[MODE_DASHBOARD, MODE_DIRECT])

    # -- Mit Dashboard -------------------------------------------------------
    async def async_step_dashboard(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host, port = user_input[CONF_HOST].strip(), user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                async with async_get_clientsession(self.hass).get(
                    f"http://{host}:{port}/api/ha/state", timeout=aiohttp.ClientTimeout(total=8)
                ) as r:
                    r.raise_for_status()
                    await r.json()
            except (aiohttp.ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Braumeister ({host})", data={CONF_MODE: MODE_DASHBOARD, CONF_HOST: host, CONF_PORT: port}
                )
        return self.async_show_form(
            step_id="dashboard",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str, vol.Required(CONF_PORT, default=DEFAULT_PORT): int}),
            errors=errors,
        )

    # -- Direkt über My-Speidel --------------------------------------------------
    async def _check_login(self, user: str, password: str) -> str | None:
        session = async_create_clientsession(self.hass)
        try:
            await async_get_token(session, user, password)
        except InvalidAuth:
            return "invalid_auth"
        except CloudError:
            return "cannot_connect"
        finally:
            await session.close()
        return None

    async def async_step_direct(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device = str(user_input[CONF_DEVICE]).strip()
            await self.async_set_unique_id(f"direct_{device}")
            self._abort_if_unique_id_configured()
            if not device.isdigit():
                errors[CONF_DEVICE] = "invalid_device"
            elif err := await self._check_login(user_input[CONF_USERNAME].strip(), user_input[CONF_PASSWORD]):
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title=f"Braumeister {device}",
                    data={
                        CONF_MODE: MODE_DIRECT, CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                        CONF_PASSWORD: user_input[CONF_PASSWORD], CONF_DEVICE: device,
                    },
                )
        return self.async_show_form(
            step_id="direct",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str, vol.Required(CONF_DEVICE): str,
            }),
            errors=errors,
        )

    # -- Neu anmelden, wenn My-Speidel die Zugangsdaten ablehnt ---------------------
    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            user = user_input[CONF_USERNAME].strip()
            if err := await self._check_login(user, user_input[CONF_PASSWORD]):
                errors["base"] = err
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_USERNAME: user, CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME, default=entry.data.get(CONF_USERNAME, "")): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )
