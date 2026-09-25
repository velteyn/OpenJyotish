"""Gandanta — the water-fire junction zones (knots).

The last 3°20' of the water signs (Cancer, Scorpio, Pisces) and the
first 3°20' of the fire signs (Aries, Leo, Sagittarius) are gandanta:
planets (above all the Moon) and the lagna placed there are considered
tied in a knot, weak and in need of propitiation. The first-look check
in almost every reading.
"""

from typing import Dict, Optional

from jhora.types.graha import Graha

#: 3°20' in degrees.
_PADA = 10.0 / 3.0

#: Signs whose END is gandanta (water) and whose START is (fire).
_END_SIGNS = {3: "Cancer", 7: "Scorpio", 11: "Pisces"}
_START_SIGNS = {0: "Aries", 4: "Leo", 8: "Sagittarius"}


def gandanta_zone(lon: float) -> Optional[str]:
    """Zone name when a longitude is in gandanta, else None.

    End zones are closed at 26°40' (a planet exactly there counts);
    start zones run strictly below 3°20'.
    """
    sign = int(lon // 30) % 12
    deg = lon % 30
    if sign in _END_SIGNS and deg >= 30.0 - _PADA:
        return f"end-{_END_SIGNS[sign]}"
    if sign in _START_SIGNS and deg < _PADA:
        return f"start-{_START_SIGNS[sign]}"
    return None


def is_gandanta(lon: float) -> bool:
    """True when a longitude falls in a gandanta zone."""
    return gandanta_zone(lon) is not None


def gandanta_planets(lons: Dict[Graha, float]) -> Dict[Graha, str]:
    """{graha: zone} for planets in gandanta."""
    out = {}
    for g, lon in lons.items():
        zone = gandanta_zone(lon)
        if zone is not None:
            out[g] = zone
    return out
