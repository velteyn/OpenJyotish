"""Graha Yuddha (planetary war) — most-used form.

Two of the five tara-grahas (Mars, Mercury, Jupiter, Venus, Saturn)
within one degree of each other are at war; the Sun (combustion),
Moon (samagama) and nodes never fight. Victory, in order:

1. Venus wins whenever Venus fights (brightest, north or south);
2. otherwise the more northern planet (ecliptic latitude) wins;
3. an exact latitude tie goes to the larger disc (classical bimba
   diameters) — a deterministic tiebreak for a case that never
   occurs in practice.

Sources: Surya Siddhanta latitude/brightness criteria, Brihat
Samhita ch. 17 (Venus ever-bright), Uttara Kalamrita (north wins).
"""

from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha

#: The five star-planets that can fight.
WARRIORS = (Graha.MARS, Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
            Graha.SATURN)

#: War must be strictly inside one degree.
ORB = 1.0

#: Classical disc diameters (arcsec) — tiebreak only.
_DISC = {
    Graha.JUPITER: 190.4,
    Graha.SATURN: 158.0,
    Graha.VENUS: 16.6,
    Graha.MARS: 9.4,
    Graha.MERCURY: 6.6,
}


def separation(a: float, b: float) -> float:
    """Minimal angular distance between two longitudes (0-180)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def victor(pair: Tuple[Graha, Graha],
           lats: Dict[Graha, float]) -> Tuple[Graha, str]:
    """(Winner, reason) for a warring pair."""
    g1, g2 = pair
    if Graha.VENUS in pair:
        return Graha.VENUS, "Venus wins north or south"
    n1, n2 = lats.get(g1, 0.0), lats.get(g2, 0.0)
    if n1 != n2:
        win = g1 if n1 > n2 else g2
        return win, "more northern latitude"
    win = g1 if _DISC[g1] >= _DISC[g2] else g2
    return win, "larger disc (latitude tie)"


def planetary_wars(lons: Dict[Graha, float],
                   lats: Optional[Dict[Graha, float]] = None
                   ) -> List[dict]:
    """All wars: [{pair, separation, winner, loser, reason}]."""
    lats = lats or {}
    present = [g for g in WARRIORS if g in lons]
    wars = []
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            g1, g2 = present[i], present[j]
            sep = separation(lons[g1], lons[g2])
            if sep < ORB:
                win, reason = victor((g1, g2), lats)
                lose = g2 if win == g1 else g1
                wars.append({
                    "pair": (g1, g2),
                    "separation": sep,
                    "winner": win,
                    "loser": lose,
                    "reason": reason,
                })
    return wars
