"""Number entity for the HAm-rotator target azimuth."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .antenna import resolve_beamwidth
from .const import (
    CONF_STORM_TURN_MODE,
    CONF_WIND_DIRECTION_AVG_ENTITY,
    CONF_WIND_DIRECTION_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    CONF_WIND_SPEED_THRESHOLD,
    DOMAIN,
    PRESET_BUTTONS,
    STORM_TURN_MODE_PERPENDICULAR,
    STORM_TURN_MODE_WITH_WIND,
)
from .home_location import resolve_home_location
from .position_tracker import PositionTracker
from .rotator import RotatorClient, RotatorConnectionError

_LOGGER = logging.getLogger(__name__)

# storm and park keep a fixed, translated button label (set client-side in
# the card); the rest show whatever free-text label the user configured.
_FIXED_LABEL_PRESETS = {"storm", "park"}


def _wrap360(value: float) -> float:
    return value % 360


def _angle_diff(a: float, b: float) -> float:
    return abs(((a - b + 180) % 360) - 180)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HAm-rotator azimuth number entity."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [HamRotatorAzimuthNumber(entry, runtime.client, runtime.tracker)]
    )


class HamRotatorAzimuthNumber(NumberEntity, RestoreEntity):
    """Represents the commanded antenna azimuth."""

    _attr_has_entity_name = True
    _attr_name = "Azimuth"
    _attr_icon = "mdi:compass-rose"
    _attr_native_min_value = 0
    _attr_native_max_value = 359.9
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = DEGREE
    _attr_mode = NumberMode.BOX

    def __init__(
        self, entry: ConfigEntry, client: RotatorClient, tracker: PositionTracker
    ) -> None:
        self._entry = entry
        self._client = client
        self._tracker = tracker
        self._attr_unique_id = f"{entry.entry_id}_azimuth"
        self._attr_native_value = 0.0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )
        self._storm_active = False
        self._real_azimuth: float | None = None
        self._tracking = False
        self._wind_speed: float | None = None
        self._wind_direction: float | None = None
        self._wind_direction_avg: float | None = None

    def _preset_azimuth(self, preset: str) -> float | None:
        raw = self._client.get_option(f"{preset}_azimuth")
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose home location, preset buttons, beamwidth and live position."""
        lat, lon, locator = resolve_home_location(
            self.hass, self._entry.data, self._entry.options
        )
        attrs = {"home_latitude": lat, "home_longitude": lon}
        if locator:
            attrs["qth_locator"] = locator
        for preset in PRESET_BUTTONS:
            azimuth = self._preset_azimuth(preset)
            if azimuth is not None:
                attrs[f"{preset}_azimuth"] = azimuth
            if preset not in _FIXED_LABEL_PRESETS:
                label = self._client.get_option(f"{preset}_label")
                if label:
                    attrs[f"{preset}_label"] = label
        beamwidth = resolve_beamwidth(self._entry.data, self._entry.options)
        if beamwidth is not None:
            attrs["beamwidth"] = beamwidth
        if self._real_azimuth is not None:
            attrs["real_azimuth"] = self._real_azimuth
        attrs["tracking"] = self._tracking
        if self._wind_direction is not None:
            attrs["wind_direction"] = self._wind_direction
        threshold = self._client.get_option(CONF_WIND_SPEED_THRESHOLD)
        if self._wind_speed is not None and threshold not in (None, ""):
            try:
                attrs["wind_alert"] = self._wind_speed > float(threshold)
            except (TypeError, ValueError):
                pass
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass

        wind_entity_id = self._client.get_option(CONF_WIND_SPEED_ENTITY)
        if wind_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [wind_entity_id], self._async_wind_speed_changed
                )
            )

        # Realtime wind direction, for the arrow shown on the card.
        wind_direction_entity_id = self._client.get_option(CONF_WIND_DIRECTION_ENTITY)
        if wind_direction_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    [wind_direction_entity_id],
                    self._async_wind_direction_changed,
                )
            )
            direction_state = self.hass.states.get(wind_direction_entity_id)
            if direction_state is not None:
                try:
                    self._wind_direction = float(direction_state.state)
                except (TypeError, ValueError):
                    pass

        # 10-minute-average wind direction, used to pick the storm azimuth --
        # smoother than the realtime reading, so a single gust doesn't send
        # the antenna chasing it.
        wind_direction_avg_entity_id = self._client.get_option(
            CONF_WIND_DIRECTION_AVG_ENTITY
        )
        if wind_direction_avg_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    [wind_direction_avg_entity_id],
                    self._async_wind_direction_avg_changed,
                )
            )
            avg_state = self.hass.states.get(wind_direction_avg_entity_id)
            if avg_state is not None:
                try:
                    self._wind_direction_avg = float(avg_state.state)
                except (TypeError, ValueError):
                    pass

        self._tracker.add_listener(self._on_position_update)
        self.async_on_remove(
            lambda: self._tracker.remove_listener(self._on_position_update)
        )

    def _on_position_update(
        self, azimuth: float | None, tracking: bool, external: bool
    ) -> None:
        self._real_azimuth = azimuth
        self._tracking = tracking
        if external and azimuth is not None:
            # The antenna moved without us commanding it (the rotor software
            # itself, a physical control box, ...) -- treat the new reading as the
            # new target so the card's needle follows reality instead of
            # staying pinned to a now-stale HA-side command.
            self._attr_native_value = azimuth
        self.async_write_ha_state()

    async def _async_wind_direction_changed(self, event: Event) -> None:
        """Track the realtime wind direction, shown as an arrow on the card."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        try:
            self._wind_direction = float(new_state.state)
        except (TypeError, ValueError):
            return
        self.async_write_ha_state()

    async def _async_wind_direction_avg_changed(self, event: Event) -> None:
        """Track the 10-minute-average wind direction, used for storm turns."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        try:
            self._wind_direction_avg = float(new_state.state)
        except (TypeError, ValueError):
            return

    def _storm_target_azimuth(self) -> float | None:
        """Pick where to turn for storm protection.

        Prefers the averaged wind direction (turned into or perpendicular to
        the wind, per the configured mode) over the fixed storm azimuth, so
        the antenna tracks the actual wind instead of a single static value.
        """
        if self._wind_direction_avg is not None:
            mode = self._client.get_option(
                CONF_STORM_TURN_MODE, STORM_TURN_MODE_WITH_WIND
            )
            if mode == STORM_TURN_MODE_PERPENDICULAR:
                current = self._attr_native_value or 0.0
                option_a = _wrap360(self._wind_direction_avg + 90)
                option_b = _wrap360(self._wind_direction_avg - 90)
                if _angle_diff(current, option_a) <= _angle_diff(current, option_b):
                    return option_a
                return option_b
            return _wrap360(self._wind_direction_avg)
        return self._preset_azimuth("storm")

    async def _async_wind_speed_changed(self, event: Event) -> None:
        """Move to the storm azimuth once wind speed crosses the threshold."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        threshold_raw = self._client.get_option(CONF_WIND_SPEED_THRESHOLD)
        if threshold_raw is None:
            return

        try:
            wind_speed = float(new_state.state)
            threshold = float(threshold_raw)
        except (TypeError, ValueError):
            return

        self._wind_speed = wind_speed

        target_azimuth = self._storm_target_azimuth()

        if wind_speed > threshold:
            if not self._storm_active:
                self._storm_active = True
                if target_azimuth is not None:
                    _LOGGER.warning(
                        "Windsnelheid (%s) boven drempel (%s) - antenne naar "
                        "%.1f°",
                        new_state.state,
                        threshold_raw,
                        target_azimuth,
                    )
                    try:
                        await self.async_set_native_value(target_azimuth)
                    except HomeAssistantError as err:
                        _LOGGER.error("Kon niet naar stormstand draaien: %s", err)
        else:
            self._storm_active = False
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Send the new azimuth to the rotor controller and update state."""
        value = round(value % 360, 1)
        try:
            await self._client.async_set_azimuth(value)
        except RotatorConnectionError as err:
            raise HomeAssistantError(str(err)) from err

        self._tracker.notify_command_sent()
        self._attr_native_value = value
        self.async_write_ha_state()
