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


#: Mrityu-bhaga base degrees per rasi (rows Ar..Pi) for Sun, Moon, Mars,
#: Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Mandi, Lagna (standard
#: published Mrityu-bhaga tables).
_MRITYU_BHAGA_BASE = (
    (20, 26, 19, 15, 19, 28, 10, 14, 8, 23, 1),
    (9, 12, 28, 14, 29, 15, 4, 13, 18, 24, 9),
    (12, 13, 25, 13, 12, 11, 7, 12, 20, 11, 22),
    (6, 25, 23, 12, 27, 17, 9, 11, 10, 12, 22),
    (8, 24, 29, 8, 6, 10, 12, 24, 21, 13, 25),
    (24, 11, 28, 18, 4, 13, 16, 23, 22, 14, 2),
    (16, 26, 14, 20, 13, 4, 3, 22, 23, 8, 4),
    (17, 14, 21, 10, 10, 6, 18, 21, 24, 18, 23),
    (22, 13, 2, 21, 17, 27, 28, 10, 11, 20, 18),
    (2, 25, 15, 22, 11, 12, 14, 20, 12, 10, 20),
    (3, 5, 11, 7, 15, 29, 13, 18, 13, 21, 24),
    (23, 12, 6, 5, 28, 19, 15, 8, 14, 22, 10),
)

#: Mrityu-bhaga tolerances (degrees) in the same column order.
_MRITYU_BHAGA_TOL = (1 / 3, 2 / 3, 0.25, 2 / 3, 0.25, 0.25, 0.25,
                     0.25, 0.25, 0.25, 2 / 3)


def planets_in_mrityu_bhaga(lons: List[float]) -> List[int]:
    """Indices (into ``lons``) of bodies within Mrityu bhaga.

    ``lons`` holds longitudes for Sun, Moon, Mars, Mercury, Jupiter,
    Venus, Saturn, Rahu, Ketu, Mandi, Lagna in order; a body counts
    when it falls within its rasi's base degree ± tolerance.
    """
    out = []
    for i, lon in enumerate(lons):
        sign = int(lon // 30) % 12
        deg = lon % 30
        if abs(deg - _MRITYU_BHAGA_BASE[sign][i]) <= _MRITYU_BHAGA_TOL[i]:
            out.append(i)
    return out
