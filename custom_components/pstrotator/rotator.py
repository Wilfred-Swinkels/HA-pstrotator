"""Network client that talks to PstRotator.

PstRotator (YO3DMU) exposes a Hamlib ``rotctld``-compatible TCP server
(enable it in PstRotator under Settings -> "Hamlib Net rotctl" / external
program control). That is the default, documented way this integration
talks to the rotator. For setups that expose a different network
interface, a "custom text command" mode is also available so the exact
string PstRotator expects can be configured without touching code.
"""
from __future__ import annotations

import asyncio
import logging

from .const import (
    CONF_CUSTOM_IS_UDP,
    CONF_CUSTOM_TEMPLATE,
    CONF_ELEVATION,
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    DEFAULT_CUSTOM_TEMPLATE,
    DEFAULT_PORT,
    PROTOCOL_CUSTOM,
    PROTOCOL_ROTCTLD,
)

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 3.0


class PstRotatorConnectionError(Exception):
    """Raised when PstRotator cannot be reached or rejects a command."""


class PstRotatorClient:
    """Sends azimuth commands to a running PstRotator instance."""

    def __init__(self, hass, data: dict, options: dict | None = None) -> None:
        self.hass = hass
        self._data = data
        self._options = options or {}
        self._lock = asyncio.Lock()

    def update_options(self, options: dict | None) -> None:
        self._options = options or {}

    def _conf(self, key, default=None):
        if key in self._options:
            return self._options[key]
        return self._data.get(key, default)

    async def async_set_azimuth(self, azimuth: float) -> None:
        """Send a new target azimuth to PstRotator."""
        protocol = self._conf(CONF_PROTOCOL, PROTOCOL_ROTCTLD)
        if protocol == PROTOCOL_CUSTOM:
            await self._async_send_custom(azimuth)
        else:
            await self._async_send_rotctld(azimuth)

    async def _async_send_rotctld(self, azimuth: float) -> None:
        host = self._conf(CONF_HOST)
        port = int(self._conf(CONF_PORT, DEFAULT_PORT))
        elevation = float(self._conf(CONF_ELEVATION, 0))
        command = f"P {azimuth:.1f} {elevation:.1f}\n"

        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), TIMEOUT
                )
            except (OSError, asyncio.TimeoutError) as err:
                raise PstRotatorConnectionError(
                    f"Kan geen verbinding maken met PstRotator op {host}:{port}: {err}"
                ) from err

            try:
                writer.write(command.encode("ascii"))
                await writer.drain()
                try:
                    reply = await asyncio.wait_for(reader.readline(), TIMEOUT)
                except asyncio.TimeoutError:
                    reply = b""
                if reply and not reply.decode(errors="ignore").strip().startswith("RPRT"):
                    _LOGGER.debug("Onverwacht antwoord van PstRotator: %s", reply)
            finally:
                writer.close()

    async def async_get_azimuth(self) -> float | None:
        """Read the current azimuth back from PstRotator (rotctld mode only)."""
        if self._conf(CONF_PROTOCOL, PROTOCOL_ROTCTLD) != PROTOCOL_ROTCTLD:
            return None

        host = self._conf(CONF_HOST)
        port = int(self._conf(CONF_PORT, DEFAULT_PORT))

        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), TIMEOUT
                )
            except (OSError, asyncio.TimeoutError):
                return None

            try:
                writer.write(b"p\n")
                await writer.drain()
                line = await asyncio.wait_for(reader.readline(), TIMEOUT)
                return float(line.decode(errors="ignore").strip())
            except (ValueError, asyncio.TimeoutError, OSError):
                return None
            finally:
                writer.close()

    async def _async_send_custom(self, azimuth: float) -> None:
        host = self._conf(CONF_HOST)
        port = int(self._conf(CONF_PORT, DEFAULT_PORT))
        template = self._conf(CONF_CUSTOM_TEMPLATE, DEFAULT_CUSTOM_TEMPLATE)
        is_udp = self._conf(CONF_CUSTOM_IS_UDP, True)

        try:
            message = template.format(az=azimuth, azimuth=azimuth).encode("ascii")
        except (KeyError, ValueError) as err:
            raise PstRotatorConnectionError(
                f"Ongeldige custom command template: {err}"
            ) from err

        if is_udp:
            loop = asyncio.get_running_loop()
            try:
                transport, _ = await loop.create_datagram_endpoint(
                    asyncio.DatagramProtocol, remote_addr=(host, port)
                )
            except OSError as err:
                raise PstRotatorConnectionError(
                    f"Kan geen UDP-pakket sturen naar {host}:{port}: {err}"
                ) from err
            try:
                transport.sendto(message)
            finally:
                transport.close()
        else:
            async with self._lock:
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port), TIMEOUT
                    )
                except (OSError, asyncio.TimeoutError) as err:
                    raise PstRotatorConnectionError(
                        f"Kan geen verbinding maken met {host}:{port}: {err}"
                    ) from err
                try:
                    writer.write(message)
                    await writer.drain()
                finally:
                    writer.close()

    async def async_close(self) -> None:
        """No persistent connection is kept open; nothing to close."""
        return
