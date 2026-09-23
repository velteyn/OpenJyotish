"""Special sensitive points — Baadhaka, Pushkara, Khara navamsa, 22nd drekkana.

Small classical points used across readings (Jaimini, longevity, strength):
all are pure functions of longitudes, following the standard doctrine
(BPHS; Jataka Parijata for the Pushkara tables).

- **Baadhaka sthana**: 11th from movable, 9th from fixed, 7th from dual
  lagna; its lord is the Baadhakesha.
- **Pushkara navamsa**: navamsa degrees that nourish a planet — per-sign
  windows ([start, start+3°20) and [start+6°40, start+10)).
- **Pushkara bhaga**: the nourishing degree per sign (±1° window).
- **64th navamsa (Khara)**: 4th navamsa from the Moon's navamsa.
- **22nd drekkana**: 8th drekkana from the Moon's drekkana.
"""

from typing import Dict, List

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

#: Pushkara navamsa window starts per sign (fire/earth/air/water cycle).
_PUSHKARA_NAVAMSA_START = (
    20.0, 6 + 40 / 60, 16 + 40 / 60, 0.0,
    20.0, 6 + 40 / 60, 16 + 40 / 60, 0.0,
    20.0, 6 + 40 / 60, 16 + 40 / 60, 0.0,
)

_NAVAMSA_SPAN = 30.0 / 9

#: Pushkara bhaga (nourishing degree) per sign.
_PUSHKARA_BHAGA = (21.0, 14.0, 24.0, 7.0,
                   21.0, 14.0, 24.0, 7.0,
                   21.0, 14.0, 24.0, 7.0)


def baadhaka_sthana(lagna_rasi: int) -> int:
    """Baadhaka sthana rasi index from the lagna rasi (0-based).

    Movable → 11th, fixed → 9th, dual → 7th.
    """
    rasi = Rasi(lagna_rasi % 12)
    if rasi.is_movable:
        return (lagna_rasi + 10) % 12
    if rasi.is_fixed:
        return (lagna_rasi + 8) % 12
    return (lagna_rasi + 6) % 12


def baadhaka_lord(lagna_rasi: int) -> Graha:
    """Lord of the Baadhaka sthana (Baadhakesha)."""
    return Graha[Rasi(baadhaka_sthana(lagna_rasi)).lord.upper()]


def planets_in_pushkara_navamsa(planets: Dict[Graha, float]) -> List[Graha]:
    """Planets occupying a Pushkara navamsa (by longitude)."""
    out = []
    for g, lon in planets.items():
        sign = int(lon // 30) % 12
        deg = lon % 30
        start = _PUSHKARA_NAVAMSA_START[sign]
        if (start <= deg < start + _NAVAMSA_SPAN or
                start + 2 * _NAVAMSA_SPAN <= deg < start + 3 * _NAVAMSA_SPAN):
            out.append(g)
    return out


def planets_in_pushkara_bhaga(planets: Dict[Graha, float]) -> List[Graha]:
    """Planets within ±1° of their sign's Pushkara bhaga degree."""
    out = []
    for g, lon in planets.items():
        sign = int(lon // 30) % 12
        deg = lon % 30
        bhaga = _PUSHKARA_BHAGA[sign]
        if bhaga - 1.0 <= deg < bhaga:
            out.append(g)
    return out


def _navamsa_sign(longitude: float) -> int:
    """Classical navamsa sign: movable from sign, fixed from 9th, dual from 5th."""
    sign = int(longitude // 30) % 12
    index = int((longitude % 30) // _NAVAMSA_SPAN) % 9
    rasi = Rasi(sign)
    offset = 0 if rasi.is_movable else (8 if rasi.is_fixed else 4)
    return (sign + offset + index) % 12


def khara_navamsa_64(moon_longitude: float) -> int:
    """64th navamsa from the Moon (Khara): 4th from the Moon's navamsa."""
    return (_navamsa_sign(moon_longitude) + 3) % 12


def drekkana_22(moon_longitude: float) -> int:
    """22nd drekkana from the Moon: 8th from the Moon's drekkana."""
    moon_sign = int(moon_longitude // 30) % 12
    moon_drekkana = int((moon_longitude % 30) // 10) % 3
    return (moon_sign + 4 * moon_drekkana + 7) % 12
