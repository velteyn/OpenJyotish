"""Avasthas (Balaadi set) — planetary age-states within a sign.

In odd signs the planet runs Bala → Kumara → Yuva → Vriddha → Mrita
across the five 6° bands; in even signs the order reverses. The
result-grade runs one-fourth, half, full, negligible, nil (BPHS
Avastha doctrine, most-used form). Nodes carry no avastha.
"""

from typing import Dict, Optional, Tuple

from jhora.types.graha import Graha

_BANDS = ("Bala", "Kumara", "Yuva", "Vriddha", "Mrita")

_GRADES = {
    "Bala": "1/4",
    "Kumara": "1/2",
    "Yuva": "full",
    "Vriddha": "negligible",
    "Mrita": "nil",
}

#: Planets carrying avasthas (the seven visible grahas).
_AVASTHA_GRAHAS = frozenset({
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN,
})


def balaadi_avastha(lon: float) -> Tuple[str, str]:
    """(Avastha name, result grade) for a longitude."""
    sign = int(lon // 30) % 12
    band = min(int((lon % 30) // 6), 4)
    name = _BANDS[band] if sign % 2 == 0 else _BANDS[4 - band]
    return name, _GRADES[name]


def avastha_of(graha: Graha, lon: float) -> Optional[Tuple[str, str]]:
    """Avastha of a planet (None for nodes)."""
    if graha not in _AVASTHA_GRAHAS:
        return None
    return balaadi_avastha(lon)


def avasthas(lons: Dict[Graha, float]) -> Dict[Graha, str]:
    """{graha: avastha name} for the seven planets."""
    return {g: balaadi_avastha(lon)[0] for g, lon in lons.items()
            if g in _AVASTHA_GRAHAS}
