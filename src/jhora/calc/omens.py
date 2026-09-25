"""Birth omens — Ganda Moola nakshatras and Vishti (Bhadra) birth.

Ganda Moola: the six nakshatras flanking the three gandanta junctions
(Ashlesha/Magha, Jyeshtha/Moola, Revati/Ashwini). Birth with the Moon
there calls for shanti in the most-used tradition. The lagna's
nakshatra is reported alongside, labelled as such.
Vishti (Bhadra) karana at birth is the second classic birth omen.
"""

from typing import Dict, Optional

from jhora.calc.muhurta import _karana
from jhora.types.nakshatra import Nakshatra

#: Nakshatra indices needing shanti at birth.
GANDA_MOOLA = frozenset({0, 8, 9, 17, 18, 26})


def ganda_moola(nak_idx: int) -> Optional[str]:
    """Nakshatra display name when ganda-moola, else None."""
    if nak_idx in GANDA_MOOLA:
        return Nakshatra(nak_idx).name.replace("_", " ").title()
    return None


def karana_at(sun_lon: float, moon_lon: float) -> str:
    """Karana name at the given longitudes."""
    return _karana(sun_lon, moon_lon)[1]


def birth_omens(moon_lon: float, lagna_lon: float,
                sun_lon: float) -> Dict[str, Optional[str]]:
    """{moon_nakshatra, moon_ganda_moola, lagna_nakshatra,
    lagna_ganda_moola, karana, vishti} (None where absent)."""
    moon_nak, _ = Nakshatra.from_longitude(moon_lon)
    lagna_nak, _ = Nakshatra.from_longitude(lagna_lon)
    karana = karana_at(sun_lon, moon_lon)
    return {
        "moon_nakshatra": Nakshatra(moon_nak).name.replace("_", " ").title(),
        "moon_ganda_moola": ganda_moola(int(moon_nak)),
        "lagna_nakshatra": Nakshatra(lagna_nak).name.replace("_", " ").title(),
        "lagna_ganda_moola": ganda_moola(int(lagna_nak)),
        "karana": karana,
        "vishti": karana if karana == "Vishti" else None,
    }
