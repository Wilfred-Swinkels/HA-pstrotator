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
CONF_BEAMWIDTH = "beamwidth"
CONF_ANTENNA_GAIN = "antenna_gain"

# How long to keep actively polling PstRotator for its real position after
# the last detected change, before dropping back to idle. Idle polling still
# runs every second (not just on command) so a move made some other way --
# directly in PstRotator, from a different controller -- is picked up and
# reflected in HA quickly instead of only after the next commanded move.
POSITION_ACTIVE_POLL_INTERVAL = 0.5
POSITION_IDLE_POLL_INTERVAL = 1.0
POSITION_ACTIVE_TIMEOUT = 15.0

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

INTEGRATION_VERSION = "1.4.7"
