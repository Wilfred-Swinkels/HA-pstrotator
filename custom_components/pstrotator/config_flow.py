"""Config flow for the PstRotator integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CUSTOM_IS_UDP,
    CONF_CUSTOM_TEMPLATE,
    CONF_ELEVATION,
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_QTH_LOCATOR,
    CONF_STORM_AZIMUTH,
    CONF_WIND_SPEED_ENTITY,
    CONF_WIND_SPEED_THRESHOLD,
    DEFAULT_CUSTOM_TEMPLATE,
    DEFAULT_NAME,
    DEFAULT_PSTROTATOR_UDP_PORT,
    DOMAIN,
    PROTOCOL_CUSTOM,
    PROTOCOL_PSTROTATOR_UDP,
    PROTOCOL_ROTCTLD,
)
from .maidenhead import InvalidLocatorError, locator_to_latlon

PROTOCOL_OPTIONS = {
    PROTOCOL_PSTROTATOR_UDP: "PstRotator native UDP (standaard, poort 12000)",
    PROTOCOL_ROTCTLD: "Hamlib rotctld-compatible",
    PROTOCOL_CUSTOM: "Custom text command (UDP/TCP)",
}


def _validate_qth_locator(user_input: dict[str, Any], errors: dict[str, str]) -> None:
    """Validate the optional QTH locator field in place."""
    locator = (user_input.get(CONF_QTH_LOCATOR) or "").strip()
    if not locator:
        return
    try:
        locator_to_latlon(locator)
    except InvalidLocatorError:
        errors[CONF_QTH_LOCATOR] = "invalid_qth_locator"


class PstRotatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PstRotator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            _validate_qth_locator(user_input, errors)

            if not errors:
                host = user_input[CONF_HOST]
                port = user_input[CONF_PORT]
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                name = user_input.pop("name", DEFAULT_NAME)
                return self.async_create_entry(title=name, data=user_input)

        schema = vol.Schema(
            {
                vol.Optional("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(
                    CONF_PORT, default=DEFAULT_PSTROTATOR_UDP_PORT
                ): vol.Coerce(int),
                vol.Required(
                    CONF_PROTOCOL, default=PROTOCOL_PSTROTATOR_UDP
                ): vol.In(PROTOCOL_OPTIONS),
                vol.Optional(CONF_QTH_LOCATOR, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PstRotatorOptionsFlow:
        return PstRotatorOptionsFlow(config_entry)


class PstRotatorOptionsFlow(config_entries.OptionsFlow):
    """Handle PstRotator options, presented as a menu."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    def _current(self) -> dict[str, Any]:
        return {**self._config_entry.data, **self._config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["connection", "storm"],
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        current = self._current()

        if user_input is not None:
            _validate_qth_locator(user_input, errors)
            if not errors:
                return self.async_create_entry(
                    title="", data={**current, **user_input}
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): str,
                vol.Required(
                    CONF_PORT,
                    default=current.get(CONF_PORT, DEFAULT_PSTROTATOR_UDP_PORT),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_PROTOCOL,
                    default=current.get(CONF_PROTOCOL, PROTOCOL_PSTROTATOR_UDP),
                ): vol.In(PROTOCOL_OPTIONS),
                vol.Optional(
                    CONF_ELEVATION, default=current.get(CONF_ELEVATION, 0)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CUSTOM_TEMPLATE,
                    default=current.get(CONF_CUSTOM_TEMPLATE, DEFAULT_CUSTOM_TEMPLATE),
                ): str,
                vol.Optional(
                    CONF_CUSTOM_IS_UDP, default=current.get(CONF_CUSTOM_IS_UDP, True)
                ): bool,
                vol.Optional(
                    CONF_QTH_LOCATOR, default=current.get(CONF_QTH_LOCATOR, "")
                ): str,
                vol.Optional(
                    CONF_HOME_LATITUDE, default=current.get(CONF_HOME_LATITUDE, "")
                ): str,
                vol.Optional(
                    CONF_HOME_LONGITUDE, default=current.get(CONF_HOME_LONGITUDE, "")
                ): str,
            }
        )
        return self.async_show_form(
            step_id="connection", data_schema=schema, errors=errors
        )

    async def async_step_storm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        current = self._current()

        if user_input is not None:
            return self.async_create_entry(title="", data={**current, **user_input})

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_STORM_AZIMUTH, default=current.get(CONF_STORM_AZIMUTH, "")
                ): str,
                vol.Optional(
                    CONF_WIND_SPEED_ENTITY,
                    default=current.get(CONF_WIND_SPEED_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_WIND_SPEED_THRESHOLD,
                    default=current.get(CONF_WIND_SPEED_THRESHOLD, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="storm", data_schema=schema)
