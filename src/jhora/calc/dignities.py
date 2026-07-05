"""Planetary dignity calculator."""

from typing import Dict, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


# Exaltation degrees per planet (sign_index, degree)
EXALTATION: Dict[Graha, Tuple[int, float]] = {
    Graha.SUN:     (0, 10.0),     # Aries 10°
    Graha.MOON:    (1, 3.0),      # Taurus 3°
    Graha.MARS:    (9, 28.0),     # Capricorn 28°
    Graha.MERCURY: (5, 15.0),     # Virgo 15°
    Graha.JUPITER: (3, 5.0),      # Cancer 5°
    Graha.VENUS:   (11, 27.0),    # Pisces 27°
    Graha.SATURN:  (6, 20.0),     # Libra 20°
}

# Debilitation degrees (7th sign from exaltation)
DEBILITATION: Dict[Graha, Tuple[int, float]] = {
    Graha.SUN:     (6, 10.0),     # Libra 10°
    Graha.MOON:    (7, 3.0),      # Scorpio 3°
    Graha.MARS:    (3, 28.0),     # Cancer 28°
    Graha.MERCURY: (11, 15.0),    # Pisces 15°
    Graha.JUPITER: (9, 5.0),      # Capricorn 5°
    Graha.VENUS:   (5, 27.0),     # Virgo 27°
    Graha.SATURN:  (0, 20.0),     # Aries 20°
}

# Moolatrikona signs
MOOLATRIKONA: Dict[Graha, Tuple[int, float]] = {
    Graha.SUN:     (4, 0.0),      # Leo 0-20°
    Graha.MOON:    (1, 3.0),      # Taurus 3-30°
    Graha.MARS:    (0, 0.0),      # Aries 0-12°
    Graha.MERCURY: (5, 15.0),     # Virgo 15-30°
    Graha.JUPITER: (8, 0.0),      # Sagittarius 0-5°
    Graha.VENUS:   (6, 0.0),      # Libra 0-15°
    Graha.SATURN:  (10, 0.0),     # Aquarius 0-20°
}

# Own sign (full sign rulership)
OWN_SIGNS: Dict[Graha, Tuple[int, ...]] = {
    Graha.SUN:     (4,),
    Graha.MOON:    (3,),
    Graha.MARS:    (0, 7),
    Graha.MERCURY: (2, 5),
    Graha.JUPITER: (8, 11),
    Graha.VENUS:   (1, 6),
    Graha.SATURN:  (9, 10),
}


class DignityChecker:
    """Check planetary dignity (exalted, debilitated, moolatrikona, own, etc.)."""

    def __init__(self):
        self._exalt = EXALTATION
        self._debil = DEBILITATION
        self._moola = MOOLATRIKONA
        self._own = OWN_SIGNS

    def get_dignity(self, graha: Graha, rasi_index: int, deg_in_rasi: float) -> str:
        # Nodes don't have rasi-based dignity
        if graha in (Graha.RAHU, Graha.KETU):
            return "node"
        # Exalted
        if graha in self._exalt:
            r, d = self._exalt[graha]
            if r == rasi_index and abs(deg_in_rasi - d) < 5:
                return "exalted"
        # Debilitated
        if graha in self._debil:
            r, d = self._debil[graha]
            if r == rasi_index and abs(deg_in_rasi - d) < 5:
                return "debilitated"
        # Moolatrikona
        if graha in self._moola:
            r, start = self._moola[graha]
            if r == rasi_index:
                end = {
                    Graha.SUN: 20, Graha.MOON: 30, Graha.MARS: 12,
                    Graha.MERCURY: 30, Graha.JUPITER: 5, Graha.VENUS: 15,
                    Graha.SATURN: 20,
                }.get(graha, 30)
                if start <= deg_in_rasi < end:
                    return "moolatrikona"
        # Own sign
        if graha in self._own:
            if rasi_index in self._own[graha]:
                return "own"
        # Friend/neutral/enemy — depends on graha relationships
        return "neutral"
