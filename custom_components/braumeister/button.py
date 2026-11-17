"""Befehle an den Braumeister."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BraumeisterEntity


@dataclass(frozen=True, kw_only=True)
class BmButtonDescription(ButtonEntityDescription):
    command: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


def _b(key: str, **kw: Any) -> BmButtonDescription:
    return BmButtonDescription(key=key, translation_key=key, **kw)


BUTTONS = (
    _b("start_brewing", command="startBrewing"),
    _b("request_abort", command="requestAbort"),
    _b("confirm_abort", command="confirmAbort"),
    _b("cancel_abort", command="cancelAbort"),
    _b("start_manual_brewing", command="startManual", params={"mode": "brewing"}),
    _b("start_manual_fermenting", command="startManual", params={"mode": "fermenting"}),
    _b("stop_manual", command="stopManual"),
    _b("water_confirm", command="manual/waterConfirm"),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(BraumeisterButton(c, d) for d in BUTTONS)


class BraumeisterButton(BraumeisterEntity, ButtonEntity):
    entity_description: BmButtonDescription

    def __init__(self, coordinator, description: BmButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        d = self.entity_description
        # Der Server prüft, ob der Befehl im aktuellen Gerätezustand erlaubt ist, und meldet sonst einen Fehler.
        await self.coordinator.command(d.command, **d.params)
