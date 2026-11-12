"""Maidenhead (QRA) grid locator <-> latitude/longitude conversion.

Standard amateur-radio grid locator, e.g. "JO32wd". Supports 2/4/6/8
character locators; the returned coordinate is the center of the
smallest cell the locator resolves to.
"""
from __future__ import annotations

import re

_LOCATOR_RE = re.compile(
    r"^([A-Ra-r]{2})(?:([0-9]{2})(?:([A-Xa-x]{2})(?:([0-9]{2}))?)?)?$"
)


class InvalidLocatorError(ValueError):
    """Raised when a string is not a valid Maidenhead locator."""


def locator_to_latlon(locator: str) -> tuple[float, float]:
    """Convert a Maidenhead grid locator to the (lat, lon) of its center."""
    match = _LOCATOR_RE.match(locator.strip())
    if not match:
        raise InvalidLocatorError(f"'{locator}' is geen geldige QTH-locator")

    field, square, subsquare, extsquare = match.groups()

    lon = (ord(field[0].upper()) - ord("A")) * 20 - 180
    lat = (ord(field[1].upper()) - ord("A")) * 10 - 90
    lon_size, lat_size = 20.0, 10.0

    if square:
        lon += int(square[0]) * 2
        lat += int(square[1]) * 1
        lon_size, lat_size = 2.0, 1.0

    if subsquare:
        lon += (ord(subsquare[0].lower()) - ord("a")) * (2.0 / 24)
        lat += (ord(subsquare[1].lower()) - ord("a")) * (1.0 / 24)
        lon_size, lat_size = 2.0 / 24, 1.0 / 24

    if extsquare:
        lon += int(extsquare[0]) * (lon_size / 10)
        lat += int(extsquare[1]) * (lat_size / 10)
        lon_size, lat_size = lon_size / 10, lat_size / 10

    # Center the result within the smallest resolved cell.
    lon += lon_size / 2
    lat += lat_size / 2
    return lat, lon
