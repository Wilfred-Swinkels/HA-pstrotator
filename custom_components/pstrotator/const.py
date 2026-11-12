"""Constants for the PstRotator integration."""
from __future__ import annotations

DOMAIN = "pstrotator"
DEFAULT_NAME = "PstRotator"
DEFAULT_PORT = 4533

PLATFORMS = ["number"]

CONF_HOST = "host"
CONF_PORT = "port"
CONF_PROTOCOL = "protocol"
CONF_ELEVATION = "elevation"
CONF_CUSTOM_TEMPLATE = "custom_template"
CONF_CUSTOM_IS_UDP = "custom_is_udp"

PROTOCOL_ROTCTLD = "rotctld"
PROTOCOL_CUSTOM = "custom"

DEFAULT_CUSTOM_TEMPLATE = "{az:.1f}\n"

CARD_URL_BASE = "/pstrotator_files"
CARD_FILENAME = "pstrotator-card.js"
LAND_DATA_FILENAME = "land-110m.json"

INTEGRATION_VERSION = "1.0.0"
