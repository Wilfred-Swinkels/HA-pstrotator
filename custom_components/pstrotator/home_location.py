"""Resolve the home location used to center the PstRotator map.

Priority: an explicit QTH locator, then explicit lat/lon, then Home
Assistant's own configured home location (zone.home).
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import CONF_HOME_LATITUDE, CONF_HOME_LONGITUDE, CONF_QTH_LOCATOR
from .maidenhead import InvalidLocatorError, locator_to_latlon


def resolve_home_location(
    hass: HomeAssistant, data: dict, options: dict
) -> tuple[float, float, str | None]:
    """Return (latitude, longitude, qth_locator_or_None)."""
    conf = {**data, **(options or {})}

    locator = (conf.get(CONF_QTH_LOCATOR) or "").strip()
    if locator:
        try:
            lat, lon = locator_to_latlon(locator)
            return lat, lon, locator.upper()
        except InvalidLocatorError:
            pass

    lat = conf.get(CONF_HOME_LATITUDE)
    lon = conf.get(CONF_HOME_LONGITUDE)
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon), None
        except (TypeError, ValueError):
            pass

    return hass.config.latitude, hass.config.longitude, None
