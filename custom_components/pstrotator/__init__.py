"""The PstRotator integration.

Provides a number entity that represents the target antenna azimuth and
forwards every change to PstRotator over the network, plus a bundled
Lovelace map card that lets you pick a bearing by clicking a world map.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CARD_FILENAME, CARD_URL_BASE, DOMAIN, INTEGRATION_VERSION, PLATFORMS
from .position_tracker import PositionTracker
from .rotator import PstRotatorClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class PstRotatorRuntimeData:
    """Per-config-entry runtime objects."""

    client: PstRotatorClient
    tracker: PositionTracker


async def _async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Add the card to the Lovelace *Resources* list (storage-mode dashboards).

    This is the same storage Settings -> Dashboards -> Resources edits, so a
    card added this way behaves exactly like one added by hand -- unlike
    `frontend.add_extra_js_url`, which only patches the server-rendered
    index.html and can be missed by an already-cached frontend shell.
    """
    url = f"{CARD_URL_BASE}/{CARD_FILENAME}"

    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            return False
        resources = getattr(lovelace_data, "resources", None)
        if resources is None and isinstance(lovelace_data, dict):
            resources = lovelace_data.get("resources")
        if resources is None:
            return False

        # Always (re)load from storage first. async_items() happily returns
        # an empty list -- rather than raising -- when the collection hasn't
        # read its storage file yet, which previously made every version
        # bump think no resource existed yet and create a brand new one
        # instead of finding and updating the existing entry.
        try:
            await resources.async_load()
        except Exception:  # noqa: BLE001 - already loaded, or load not needed
            pass
        items = resources.async_items()

        new_url = f"{url}?v={INTEGRATION_VERSION}"
        matches = [
            item for item in items if str(item.get("url", "")).split("?")[0] == url
        ]

        if not matches:
            await resources.async_create_item({"res_type": "module", "url": new_url})
            return True

        # Earlier releases created a new resource item on every version bump
        # instead of updating the existing one, leaving several duplicate
        # <script> modules registered at once -- each one calls
        # customElements.define() on load, so only the first succeeds and
        # the rest throw "has already been used with this registry". Keep a
        # single entry and point it at the current version; delete the rest.
        keep, *extra = matches
        if keep.get("url") != new_url:
            await resources.async_update_item(
                keep["id"], {"res_type": "module", "url": new_url}
            )
        for item in extra:
            await resources.async_delete_item(item["id"])
        return True
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Could not auto-register the Lovelace resource: %s", err)
        return False


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

    registered = await _async_register_lovelace_resource(hass)

    if not registered:
        # Fallback only: add_extra_js_url patches the server-rendered
        # index.html rather than the Resources list. Only used when the
        # Lovelace resource storage isn't available at all, so the card
        # never ends up loaded through both mechanisms at once (which
        # throws "pstrotator-card has already been used with this
        # registry" on the second customElements.define() call).
        try:
            from homeassistant.components.frontend import add_extra_js_url

            add_extra_js_url(
                hass, f"{CARD_URL_BASE}/{CARD_FILENAME}?v={INTEGRATION_VERSION}"
            )
        except ImportError:
            pass

        _LOGGER.warning(
            "Kon de PstRotator-kaart niet automatisch registreren als "
            "Lovelace resource; voeg %s/%s handmatig toe via Instellingen -> "
            "Dashboards -> Resources (type: JavaScript module).",
            CARD_URL_BASE,
            CARD_FILENAME,
        )

    hass.data.setdefault(DOMAIN, {})["_frontend_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PstRotator from a config entry."""
    await _async_register_frontend(hass)

    client = PstRotatorClient(hass, dict(entry.data), dict(entry.options))
    tracker = PositionTracker(hass, client)
    tracker.start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = PstRotatorRuntimeData(
        client=client, tracker=tracker
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    runtime: PstRotatorRuntimeData = hass.data[DOMAIN][entry.entry_id]
    runtime.client.update_options(dict(entry.options))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a PstRotator config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runtime: PstRotatorRuntimeData = hass.data[DOMAIN].pop(entry.entry_id)
        await runtime.tracker.async_stop()
        await runtime.client.async_close()
    return unload_ok
