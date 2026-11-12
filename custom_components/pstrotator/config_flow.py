"""Config flow for the PstRotator integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_CUSTOM_IS_UDP,
    CONF_CUSTOM_TEMPLATE,
    CONF_ELEVATION,
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    DEFAULT_CUSTOM_TEMPLATE,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    PROTOCOL_CUSTOM,
    PROTOCOL_ROTCTLD,
)

PROTOCOL_OPTIONS = {
    PROTOCOL_ROTCTLD: "Hamlib rotctld-compatible (standaard)",
    PROTOCOL_CUSTOM: "Custom text command (UDP/TCP)",
}


class PstRotatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PstRotator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
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
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                vol.Required(
                    CONF_PROTOCOL, default=PROTOCOL_ROTCTLD
                ): vol.In(PROTOCOL_OPTIONS),
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
    """Handle PstRotator options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): str,
                vol.Required(
                    CONF_PORT, default=current.get(CONF_PORT, DEFAULT_PORT)
                ): vol.Coerce(int),
                vol.Required(
                    CONF_PROTOCOL, default=current.get(CONF_PROTOCOL, PROTOCOL_ROTCTLD)
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
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
