"""Handbetrieb: Pumpe, Temperaturregelung, Timer (nur im Zustand Manual/Fermenting möglich)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BraumeisterEntity

# key -> (Feld in brewing/manual, Befehl, Parametername)
SWITCHES = {
    "manual_pump": ("pump", "manual/pump", "on"),
    "manual_temperature_control": ("tempControl", "manual/temperatureControl", "on"),
    "manual_timer": ("timerEnable", "manual/timerEnable", "enable"),
}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(BraumeisterSwitch(entry.runtime_data, k, *v) for k, v in SWITCHES.items())


class BraumeisterSwitch(BraumeisterEntity, SwitchEntity):
    def __init__(self, coordinator, key: str, field: str, command: str, param: str) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._field, self._command, self._param = field, command, param

    @property
    def available(self) -> bool:
        return super().available and self.value("device.group") == "manual" and bool(self.value("device.fresh"))

    @property
    def is_on(self) -> bool | None:
        v = self.value(f"device.manual.{self._field}")
        return None if v is None else bool(v)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.command(self._command, **{self._param: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.command(self._command, **{self._param: False})
