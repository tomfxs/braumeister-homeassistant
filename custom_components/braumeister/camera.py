"""Kamera am Braumeister (Tapo, MJPEG über das Dashboard-Streaming mit ffmpeg)."""
from __future__ import annotations

import asyncio

import aiohttp
from aiohttp import web
from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_aiohttp_proxy_web
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BraumeisterEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    if c.data.get("camera", {}).get("configured"):
        async_add_entities([BraumeisterCamera(c)])


class BraumeisterCamera(BraumeisterEntity, Camera):
    _attr_translation_key = "camera"

    def __init__(self, coordinator) -> None:
        BraumeisterEntity.__init__(self, coordinator, "camera")
        Camera.__init__(self)
        self._url = f"{coordinator.base}/api/camera/stream?q=sd"

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Ein Einzelbild: aus dem MJPEG-Strom das erste vollständige JPEG lesen."""
        session = self.coordinator.session
        try:
            async with asyncio.timeout(15):
                async with session.get(self._url) as r:
                    if r.status != 200:
                        return None
                    buf = b""
                    async for chunk in r.content.iter_chunked(8192):
                        buf += chunk
                        start = buf.find(b"\xff\xd8")
                        end = buf.find(b"\xff\xd9", start + 2) if start >= 0 else -1
                        if end >= 0:
                            return buf[start : end + 2]
                        if len(buf) > 4_000_000:
                            return None
        except (aiohttp.ClientError, TimeoutError):
            return None
        return None

    async def handle_async_mjpeg_stream(self, request: web.Request) -> web.StreamResponse | None:
        # Das Dashboard erlaubt höchstens 3 gleichzeitige Ansichten (je Ansicht ein ffmpeg).
        resp = self.coordinator.session.get(
            self._url, timeout=aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=30)
        )
        return await async_aiohttp_proxy_web(self.hass, request, resp)
