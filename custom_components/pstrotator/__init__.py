"""The PstRotator integration.

Provides a number entity that represents the target antenna azimuth and
forwards every change to PstRotator over the network, plus a bundled
Lovelace map card that lets you pick a bearing by clicking a world map.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CARD_FILENAME, CARD_URL_BASE, DOMAIN, INTEGRATION_VERSION, PLATFORMS
from .rotator import PstRotatorClient

_LOGGER = logging.getLogger(__name__)


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled card + map data and register it as a Lovelace resource."""
    if hass.data.get(DOMAIN, {}).get("_frontend_registered"):
        return

    www_dir = Path(__file__).parent / "www"

    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL_BASE, str(www_dir), False)]
        )
    except ImportError:
        # Older Home Assistant core without StaticPathConfig.
        hass.http.register_static_path(CARD_URL_BASE, str(www_dir), False)

    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(
            hass, f"{CARD_URL_BASE}/{CARD_FILENAME}?v={INTEGRATION_VERSION}"
        )
    except ImportError:
        _LOGGER.warning(
            "Kon de PstRotator-kaart niet automatisch registreren; voeg "
            "%s/%s handmatig toe als Lovelace resource (JS module).",
            CARD_URL_BASE,
            CARD_FILENAME,
        )

    hass.data.setdefault(DOMAIN, {})["_frontend_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PstRotator from a config entry."""
    await _async_register_frontend(hass)

    client = PstRotatorClient(hass, dict(entry.data), dict(entry.options))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    client: PstRotatorClient = hass.data[DOMAIN][entry.entry_id]
    client.update_options(dict(entry.options))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a PstRotator config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        client: PstRotatorClient = hass.data[DOMAIN].pop(entry.entry_id)
        await client.async_close()
    return unload_ok
