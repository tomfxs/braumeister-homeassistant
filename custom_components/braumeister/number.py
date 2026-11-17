"""Handbetrieb: Solltemperatur und Timer-Dauer."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BraumeisterEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([BraumeisterTemperature(c), BraumeisterTimer(c)])


class _ManualNumber(BraumeisterEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    @property
    def available(self) -> bool:
        return super().available and self.value("device.group") == "manual" and bool(self.value("device.fresh"))


class BraumeisterTemperature(_ManualNumber):
    _attr_translation_key = "manual_temperature"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value, _attr_native_max_value, _attr_native_step = 0, 100, 0.5

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "manual_temperature")

    @property
    def native_value(self) -> float | None:
        return self.value("device.manual.temperature")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.command("manual/temperature", value=value)


class BraumeisterTimer(_ManualNumber):
    _attr_translation_key = "manual_timer_duration"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value, _attr_native_max_value, _attr_native_step = 0, 600, 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "manual_timer_duration")

    @property
    def native_value(self) -> float | None:
        s = self.value("device.manual.timer")          # Gerät liefert Sekunden
        return None if s is None else round(s / 60)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.command("manual/timer", minutes=value)
