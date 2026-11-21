"""Constants for the HAm-rotator integration."""
from __future__ import annotations

DOMAIN = "ham_rotator"
DEFAULT_NAME = "HAm-rotator"

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
CONF_WIND_DIRECTION_ENTITY = "wind_direction_entity"
CONF_WIND_DIRECTION_AVG_ENTITY = "wind_direction_avg_entity"
CONF_STORM_TURN_MODE = "storm_turn_mode"

STORM_TURN_MODE_WITH_WIND = "with_wind"
STORM_TURN_MODE_PERPENDICULAR = "perpendicular"
CONF_BEAMWIDTH = "beamwidth"
CONF_ANTENNA_GAIN = "antenna_gain"
CONF_PARK_AZIMUTH = "park_azimuth"
CONF_FRIEND1_LABEL = "friend1_label"
CONF_FRIEND1_AZIMUTH = "friend1_azimuth"
CONF_FRIEND2_LABEL = "friend2_label"
CONF_FRIEND2_AZIMUTH = "friend2_azimuth"
CONF_DIR1_LABEL = "dir1_label"
CONF_DIR1_AZIMUTH = "dir1_azimuth"
CONF_DIR2_LABEL = "dir2_label"
CONF_DIR2_AZIMUTH = "dir2_azimuth"
CONF_DIR3_LABEL = "dir3_label"
CONF_DIR3_AZIMUTH = "dir3_azimuth"
CONF_DIR4_LABEL = "dir4_label"
CONF_DIR4_AZIMUTH = "dir4_azimuth"

# Button presets always shown on the card: (config key prefix, attribute
# prefix). "storm" and "park" keep their fixed translated label and only
# toggle between that label and blank; the rest show whatever free-text
# label the user configured.
PRESET_BUTTONS = ["storm", "park", "friend1", "friend2", "dir1", "dir2", "dir3", "dir4"]

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
PROTOCOL_YAESU_GS232 = "yaesu_gs232"

# PstRotator's own UDP input, e.g. <PST><AZIMUTH>123</AZIMUTH></PST> on
# port 12000 -- this is PstRotator's native/default remote-control input
# and needs no extra configuration inside PstRotator itself.
DEFAULT_PSTROTATOR_UDP_PORT = 12000
ROTCTLD_PORT = 4533
# Common default for rotor controllers (e.g. Green Heron, many DIY
# ethernet-to-serial bridges) that speak Yaesu GS-232(B) directly over TCP.
DEFAULT_YAESU_GS232_PORT = 4533

DEFAULT_CUSTOM_TEMPLATE = "{az:.1f}\n"

CARD_URL_BASE = "/ham_rotator_files"
CARD_FILENAME = "ham-rotator-card.js"
LAND_DATA_FILENAME = "land-110m.json"

INTEGRATION_VERSION = "2.1.6"
