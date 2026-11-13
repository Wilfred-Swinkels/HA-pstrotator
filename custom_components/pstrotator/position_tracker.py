"""Adaptive real-position polling for PstRotator (rotctld only).

Polls every POSITION_ACTIVE_POLL_INTERVAL while the rotator has moved
recently, continuing for POSITION_ACTIVE_TIMEOUT seconds after the last
detected change ("settling time") before dropping back to a slow idle
poll. notify_command_sent() re-arms active polling immediately whenever
a new azimuth is commanded.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from .const import (
    POSITION_ACTIVE_POLL_INTERVAL,
    POSITION_ACTIVE_TIMEOUT,
    POSITION_IDLE_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PositionListener = Callable[[float | None, bool, bool], None]


def _angle_diff(a: float, b: float) -> float:
    return abs(((a - b + 180) % 360) - 180)


class PositionTracker:
    """Tracks PstRotator's real-world azimuth via periodic rotctld polls."""

    def __init__(self, hass, client) -> None:
        self.hass = hass
        self._client = client
        self._listeners: list[PositionListener] = []
        self._task: asyncio.Task | None = None
        self._last_azimuth: float | None = None
        self._last_change = time.monotonic()
        self._active = True  # poll actively right after startup too
        self._external_change = False
        self._wake = asyncio.Event()

    def add_listener(self, listener: PositionListener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: PositionListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify_command_sent(self) -> None:
        """Call after sending a new azimuth to re-arm active polling."""
        self._active = True
        self._external_change = False
        self._last_change = time.monotonic()
        self._wake.set()

    def start(self) -> None:
        if self._task is None:
            self._task = self.hass.loop.create_task(self._run())

    async def async_stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def _notify(self, azimuth: float | None, active: bool) -> None:
        for listener in list(self._listeners):
            try:
                listener(azimuth, active, self._external_change)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error notifying position listener")

    async def _run(self) -> None:
        while True:
            try:
                if self._active:
                    azimuth = await self._client.async_get_azimuth()
                    now = time.monotonic()
                    if azimuth is not None:
                        if (
                            self._last_azimuth is None
                            or _angle_diff(azimuth, self._last_azimuth) > 0.2
                        ):
                            self._last_change = now
                        self._last_azimuth = azimuth
                        self._notify(azimuth, True)

                    if now - self._last_change > POSITION_ACTIVE_TIMEOUT:
                        self._active = False
                        self._notify(self._last_azimuth, False)
                        continue

                    await asyncio.sleep(POSITION_ACTIVE_POLL_INTERVAL)
                else:
                    self._wake.clear()
                    try:
                        await asyncio.wait_for(
                            self._wake.wait(), timeout=POSITION_IDLE_POLL_INTERVAL
                        )
                    except asyncio.TimeoutError:
                        azimuth = await self._client.async_get_azimuth()
                        if azimuth is not None and (
                            self._last_azimuth is None
                            or _angle_diff(azimuth, self._last_azimuth) > 0.2
                        ):
                            self._last_azimuth = azimuth
                            self._last_change = time.monotonic()
                            self._active = True
                            # Nobody told us to expect this -- the antenna
                            # was moved some other way (PstRotator itself,
                            # a physical control box). Mark it so listeners
                            # can treat the new reading as the new target,
                            # not just a real-position-catching-up update.
                            self._external_change = True
                            self._notify(azimuth, True)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error in PstRotator position tracker")
                await asyncio.sleep(POSITION_IDLE_POLL_INTERVAL)
