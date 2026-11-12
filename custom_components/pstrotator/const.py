"""Constants for the PstRotator integration."""
from __future__ import annotations

DOMAIN = "pstrotator"
DEFAULT_NAME = "PstRotator"

PLATFORMS = ["number"]

CONF_HOST = "host"
CONF_PORT = "port"
CONF_PROTOCOL = "protocol"
CONF_ELEVATION = "elevation"
CONF_CUSTOM_TEMPLATE = "custom_template"
CONF_CUSTOM_IS_UDP = "custom_is_udp"
CONF_QTH_LOCATOR = "qth_locator"
CONF_HOME_LATITUDE = "home_latitude"
CONF_HOME_LONGITUDE = "home_longitude"
CONF_STORM_AZIMUTH = "storm_azimuth"
CONF_WIND_SPEED_ENTITY = "wind_speed_entity"
CONF_WIND_SPEED_THRESHOLD = "wind_speed_threshold"

PROTOCOL_PSTROTATOR_UDP = "pstrotator_udp"
PROTOCOL_ROTCTLD = "rotctld"
PROTOCOL_CUSTOM = "custom"

# PstRotator's own UDP input, e.g. <PST><AZIMUTH>123</AZIMUTH></PST> on
# port 12000 -- this is PstRotator's native/default remote-control input
# and needs no extra configuration inside PstRotator itself.
DEFAULT_PSTROTATOR_UDP_PORT = 12000
ROTCTLD_PORT = 4533

DEFAULT_CUSTOM_TEMPLATE = "{az:.1f}\n"

CARD_URL_BASE = "/pstrotator_files"
CARD_FILENAME = "pstrotator-card.js"
LAND_DATA_FILENAME = "land-110m.json"

INTEGRATION_VERSION = "1.2.2"
