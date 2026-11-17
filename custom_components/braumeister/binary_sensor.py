from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BraumeisterEntity


@dataclass(frozen=True, kw_only=True)
class BmBinaryDescription(BinarySensorEntityDescription):
    fn: Callable[[Callable[[str], Any]], bool | None]


BINARY: tuple[BmBinaryDescription, ...] = (
    BmBinaryDescription(key="online", translation_key="online", device_class=BinarySensorDeviceClass.CONNECTIVITY,
                        fn=lambda v: bool(v("device.fresh"))),
    BmBinaryDescription(key="brewing", translation_key="brewing", device_class=BinarySensorDeviceClass.RUNNING,
                        fn=lambda v: v("device.group") == "brewing"),
    BmBinaryDescription(key="manual_mode", translation_key="manual_mode",
                        fn=lambda v: v("device.group") == "manual"),
    BmBinaryDescription(key="heating", translation_key="heating", device_class=BinarySensorDeviceClass.HEAT,
                        fn=lambda v: None if v("device.status.heating") is None else v("device.status.heating") == 2),
    BmBinaryDescription(key="pump", translation_key="pump", device_class=BinarySensorDeviceClass.RUNNING,
                        fn=lambda v: None if v("device.status.pump") is None else v("device.status.pump") == 2),
    BmBinaryDescription(key="timer_running", translation_key="timer_running", device_class=BinarySensorDeviceClass.RUNNING,
                        fn=lambda v: bool(v("device.timers.running"))),
    BmBinaryDescription(key="water_filled", translation_key="water_filled",
                        fn=lambda v: v("device.manual.waterFilledIn")),
    BmBinaryDescription(key="alert", translation_key="alert_active", device_class=BinarySensorDeviceClass.PROBLEM,
                        fn=lambda v: bool(v("alert.recent"))),
    BmBinaryDescription(key="session_running", translation_key="session_running",
                        fn=lambda v: v("session.id") is not None),
    BmBinaryDescription(key="dry_run", translation_key="dry_run", entity_category=EntityCategory.DIAGNOSTIC,
                        fn=lambda v: bool(v("device.dryRun"))),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(BraumeisterBinary(entry.runtime_data, d) for d in BINARY)


class BraumeisterBinary(BraumeisterEntity, BinarySensorEntity):
    entity_description: BmBinaryDescription

    def __init__(self, coordinator, description: BmBinaryDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.fn(self.value)
