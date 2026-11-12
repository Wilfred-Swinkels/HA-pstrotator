"""Number entity for the PstRotator target azimuth."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .home_location import resolve_home_location
from .rotator import PstRotatorClient, PstRotatorConnectionError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PstRotator azimuth number entity."""
    client: PstRotatorClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PstRotatorAzimuthNumber(entry, client)])


class PstRotatorAzimuthNumber(NumberEntity, RestoreEntity):
    """Represents the commanded antenna azimuth."""

    _attr_has_entity_name = True
    _attr_name = "Azimuth"
    _attr_icon = "mdi:compass-rose"
    _attr_native_min_value = 0
    _attr_native_max_value = 359.9
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = DEGREE
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, client: PstRotatorClient) -> None:
        self._entry = entry
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_azimuth"
        self._attr_native_value = 0.0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="YO3DMU",
            model="PstRotator",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the resolved home location so the map card can use it."""
        lat, lon, locator = resolve_home_location(
            self.hass, self._entry.data, self._entry.options
        )
        attrs = {"home_latitude": lat, "home_longitude": lon}
        if locator:
            attrs["qth_locator"] = locator
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Send the new azimuth to PstRotator and update state."""
        value = round(value % 360, 1)
        try:
            await self._client.async_set_azimuth(value)
        except PstRotatorConnectionError as err:
            raise HomeAssistantError(str(err)) from err

        self._attr_native_value = value
        self.async_write_ha_state()
