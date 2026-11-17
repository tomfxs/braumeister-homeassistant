from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_STATES
from .entity import BraumeisterEntity, dig


def _seconds(text: Any) -> float | None:
    """'00:12:30.000' -> Sekunden."""
    try:
        h, m, s = str(text).split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class BmSensorDescription(SensorEntityDescription):
    path: str
    convert: Callable[[Any], Any] | None = None


SENSORS: tuple[BmSensorDescription, ...] = (
    BmSensorDescription(key="state", translation_key="state", path="device.state",
                        device_class=SensorDeviceClass.ENUM, options=DEVICE_STATES),
    BmSensorDescription(key="temperature", translation_key="temperature", path="device.status.temperature",
                        device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        state_class=SensorStateClass.MEASUREMENT),
    BmSensorDescription(key="target_temperature", translation_key="target_temperature", path="device.status.targetTemperature",
                        device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        state_class=SensorStateClass.MEASUREMENT),
    BmSensorDescription(key="phase", translation_key="phase", path="device.phase.state.name"),
    BmSensorDescription(key="recipe", translation_key="recipe", path="device.recipeName"),
    BmSensorDescription(key="total_progress", translation_key="total_progress", path="device.brewing.totalProgress",
                        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    BmSensorDescription(key="phase_progress", translation_key="phase_progress", path="device.brewing.currentProgress",
                        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    BmSensorDescription(key="timer_remaining", translation_key="timer_remaining", path="device.timers.remainingTime",
                        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS,
                        convert=_seconds),
    BmSensorDescription(key="total_remaining", translation_key="total_remaining", path="device.timers.totalRemainingTime",
                        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS,
                        convert=_seconds),
    # Brausession
    BmSensorDescription(key="session", translation_key="session", path="session.name"),
    BmSensorDescription(key="checklist_done", translation_key="checklist_done", path="session.checklist.done"),
    BmSensorDescription(key="alert", translation_key="alert", path="alert.text"),
    BmSensorDescription(key="last_notification", translation_key="last_notification", path="notify.last.message",
                        entity_category=EntityCategory.DIAGNOSTIC),
    BmSensorDescription(key="firmware", translation_key="firmware", path="device.info.firmware",
                        entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(BraumeisterSensor(entry.runtime_data, d) for d in SENSORS)


class BraumeisterSensor(BraumeisterEntity, SensorEntity):
    entity_description: BmSensorDescription

    def __init__(self, coordinator, description: BmSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        v = self.value(self.entity_description.path)
        if self.entity_description.convert:
            v = self.entity_description.convert(v)
        if self.entity_description.device_class == SensorDeviceClass.ENUM and v not in DEVICE_STATES:
            return None
        return v

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        d = self.coordinator.data
        k = self.entity_description.key
        if k == "checklist_done":
            return {"total": dig(d, "session.checklist.total"), "session_id": dig(d, "session.id")}
        if k == "alert":
            return {"time": dig(d, "alert.ts"), "topic": dig(d, "alert.topic")}
        if k == "last_notification":
            return {"time": dig(d, "notify.last.ts"), "ok": dig(d, "notify.last.ok"), "error": dig(d, "notify.last.error")}
        return None
