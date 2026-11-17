from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BraumeisterCoordinator
from .direct import DirectCoordinator


def dig(data: Any, path: str) -> Any:
    """'device.status.temperature' -> Wert oder None."""
    for key in path.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


class BraumeisterEntity(CoordinatorEntity[BraumeisterCoordinator | DirectCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BraumeisterCoordinator | DirectCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.uid}_{key}"
        info = dig(coordinator.data, "device.info") or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.uid)},
            name="Braumeister",
            manufacturer="Speidel",
            model=info.get("machinetype", "Braumeister"),
            sw_version=info.get("firmware"),
            configuration_url=coordinator.url,
        )

    def value(self, path: str) -> Any:
        return dig(self.coordinator.data, path)
