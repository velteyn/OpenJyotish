"""Combustion (Asta/Moudhya) — planets burnt by proximity to the Sun.

A planet within its orb of the Sun loses the power to give its own
results (it acts through the Sun instead). The orb set below is the
standard most-used table (Lahiri/Raman tradition): Mercury and Venus
use tighter orbs when retrograde. The luminaries and nodes are never
"combust" (the Moon has its own waning doctrine; the nodes are shadows).
"""

from typing import Dict, Optional

from jhora.types.graha import Graha

#: Combustion orb (degrees of elongation from the Sun). Mercury and
#: Venus carry (direct, retrograde) pairs.
_ORBS = {
    Graha.MOON: 12.0,
    Graha.MARS: 17.0,
    Graha.MERCURY: (14.0, 12.0),
    Graha.JUPITER: 11.0,
    Graha.VENUS: (10.0, 8.0),
    Graha.SATURN: 15.0,
}


def elongation(lon: float, sun_lon: float) -> float:
    """Minimal angular distance of a longitude from the Sun (0-180)."""
    return abs((lon - sun_lon + 180.0) % 360.0 - 180.0)


def orb(graha: Graha, retrograde: bool = False) -> Optional[float]:
    """Combustion orb for a planet (None = never combust)."""
    o = _ORBS.get(graha)
    if o is None:
        return None
    if isinstance(o, tuple):
        return o[1] if retrograde else o[0]
    return o


def is_combust(graha: Graha, lon: float, sun_lon: float,
               retrograde: bool = False) -> bool:
    """True when the planet is burnt (strictly inside its orb)."""
    o = orb(graha, retrograde)
    return o is not None and elongation(lon, sun_lon) < o


def combust_planets(lons: Dict[Graha, float], sun_lon: float,
                    retro: Optional[Dict[Graha, bool]] = None
                    ) -> Dict[Graha, float]:
    """Elongation of each combust planet ({graha: elongation})."""
    retro = retro or {}
    return {g: elongation(lon, sun_lon) for g, lon in lons.items()
            if is_combust(g, lon, sun_lon, retro.get(g, False))}
