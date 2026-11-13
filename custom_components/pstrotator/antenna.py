"""Antenna beamwidth resolution for the beam-pattern overlay."""
from __future__ import annotations

import math

from .const import CONF_ANTENNA_GAIN, CONF_BEAMWIDTH


def beamwidth_from_gain(gain_dbi: float) -> float:
    """Estimate the -3dB beamwidth (degrees) from antenna gain.

    Kraus' approximation for a symmetric pencil beam: G ~= 41253 / theta^2
    (theta in degrees, G linear). This is a well-known rule of thumb, not
    an exact figure for any specific antenna design.
    """
    gain_linear = 10 ** (gain_dbi / 10)
    return math.sqrt(41253 / gain_linear)


def resolve_beamwidth(data: dict, options: dict) -> float | None:
    """Return the configured/derived beamwidth in degrees, or None."""
    conf = {**data, **(options or {})}

    gain_raw = str(conf.get(CONF_ANTENNA_GAIN) or "").strip()
    if gain_raw:
        try:
            gain = float(gain_raw)
            if gain > 0:
                return round(beamwidth_from_gain(gain), 1)
        except ValueError:
            pass

    beamwidth_raw = str(conf.get(CONF_BEAMWIDTH) or "").strip()
    if beamwidth_raw:
        try:
            beamwidth = float(beamwidth_raw)
            if 0 < beamwidth <= 360:
                return beamwidth
        except ValueError:
            pass

    return None
