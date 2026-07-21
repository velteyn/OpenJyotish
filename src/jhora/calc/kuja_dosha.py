"""Kuja Dosha (Mangal Dosha) — Mars affliction check.

Based on BPHS principles (matching JHora 8.0 behavior).

Checks Mars placement in houses 1, 2, 4, 7, 8, 12 from:
  - Lagna (Janma Lagna)
  - Moon (Chandra Lagna)
  - Venus (Shukra Lagna)

Cancellation rules:
  - Mars in own sign (Aries, Scorpio) → weakened
  - Mars conjoined with or aspected by Jupiter → cancelled
  - Ascendant-specific exemptions (Mars rules benefic houses for some lagnas)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


# Houses from lagna where Mars causes Kuja Dosha
_KUJA_HOUSES = {1, 2, 4, 7, 8, 12}

# Aspects: Graha aspects the 7th house from itself (full), plus special aspects
_FULL_ASPECT = 7
_MARS_ASPECTS = {4, 8}      # Mars also fully aspects 4th and 8th
_JUPITER_ASPECTS = {5, 9}   # Jupiter also fully aspects 5th and 9th
_SATURN_ASPECTS = {3, 10}   # Saturn also fully aspects 3rd and 10th


def _house_from(reference_lon: float, planet_lon: float) -> int:
    """House number of planet_lon measured from reference_lon (1-indexed)."""
    diff = (planet_lon - reference_lon) % 360.0
    return int(diff // 30) + 1


def _sign_from_lon(lon: float) -> int:
    return int(lon // 30) % 12


def _graha_aspects(g: Graha, from_lon: float, target_lon: float) -> bool:
    """Does graha g aspect target from its position?"""
    tgt_house = _house_from(from_lon, target_lon)
    if tgt_house == _FULL_ASPECT:
        return True
    if g == Graha.MARS and tgt_house in _MARS_ASPECTS:
        return True
    if g == Graha.JUPITER and tgt_house in _JUPITER_ASPECTS:
        return True
    if g == Graha.SATURN and tgt_house in _SATURN_ASPECTS:
        return True
    return False


def _mars_rules_bad_houses_for_lagna(lagna: Rasi) -> bool:
    """For certain ascendants, Mars rules good houses so dosha is weakened.

    If Mars rules trine (5,9) or quadrant (4,7,10) houses, it's less malefic.
    These are the Mars lordships:
      Aries(1)   → Mars rules 1+8  → BAD (8th is dusthana)
      Taurus(2)  → Mars rules 7+12 → mixed (7th is quadrant but maraka)
      Gemini(3)  → Mars rules 6+11 → BAD (6th is dusthana)
      Cancer(4)  → Mars rules 5+10 → GOOD (trine + quadrant)
      Leo(5)     → Mars rules 4+9  → GOOD (quadrant + trine)
      Virgo(6)   → Mars rules 3+8  → BAD (8th is dusthana)
      Libra(7)   → Mars rules 2+7  → mixed
      Scorpio(8) → Mars rules 1+6  → BAD (6th dusthana, but 1st is lagna lord)
      Sag(9)     → Mars rules 5+12 → mixed (5th trine, 12th dusthana)
      Cap(10)    → Mars rules 4+11 → GOOD (quadrant)
      Aquarius(11)→ Mars rules 3+10 → GOOD (quadrant)
      Pisces(12) → Mars rules 2+9  → GOOD (trine)
    """
    lordship = {
        Rasi.ARIES:     (1, 8),
        Rasi.TAURUS:    (7, 12),
        Rasi.GEMINI:    (6, 11),
        Rasi.CANCER:    (5, 10),
        Rasi.LEO:       (4, 9),
        Rasi.VIRGO:     (3, 8),
        Rasi.LIBRA:     (2, 7),
        Rasi.SCORPIO:   (1, 6),
        Rasi.SAGITTARIUS: (5, 12),
        Rasi.CAPRICORN: (4, 11),
        Rasi.AQUARIUS:  (3, 10),
        Rasi.PISCES:    (2, 9),
    }
    houses = lordship[lagna]
    # At least one trine (1,5,9) or quadrant (1,4,7,10) not counting 1st itself
    good = {5, 9, 4, 7, 10}
    return any(h in good for h in houses)


@dataclass
class KujaDosaResult:
    """Complete Kuja Dosha analysis."""
    has_dosha: bool = False
    from_lagna: bool = False
    from_moon: bool = False
    from_venus: bool = False

    mars_from_lagna_house: int = 0
    mars_from_moon_house: int = 0
    mars_from_venus_house: int = 0

    mars_sign: str = ""
    mars_own_sign: bool = False
    jupiter_cancels: bool = False
    lagna_cancels: bool = False
    lagna_name: str = ""

    messages: List[str] = field(default_factory=list)


def compute_kuja_dosha(cd: ChartData) -> KujaDosaResult:
    """Check Kuja Dosha for the given chart."""
    result = KujaDosaResult()

    mars = cd.planet(Graha.MARS)
    jupiter = cd.planet(Graha.JUPITER)
    venus = cd.planet(Graha.VENUS)
    moon = cd.planet(Graha.MOON)
    mars_lon = mars.longitude
    mars_rasi = mars.rasi
    lagna_lon = cd.ascendant
    lagna_rasi = Rasi.from_longitude(lagna_lon)
    jupiter_lon = jupiter.longitude
    venus_lon = venus.longitude
    moon_lon = moon.longitude

    result.lagna_name = lagna_rasi.full_name
    result.mars_sign = mars.rasi.full_name

    # House positions from each reference
    mars_lagna_house = _house_from(lagna_lon, mars_lon)
    mars_moon_house = _house_from(moon_lon, mars_lon)
    mars_venus_house = _house_from(venus_lon, mars_lon)

    result.mars_from_lagna_house = mars_lagna_house
    result.mars_from_moon_house = mars_moon_house
    result.mars_from_venus_house = mars_venus_house

    # Check presence from each reference
    result.from_lagna = mars_lagna_house in _KUJA_HOUSES
    result.from_moon = mars_moon_house in _KUJA_HOUSES
    result.from_venus = mars_venus_house in _KUJA_HOUSES

    # Cancellation: Mars in own sign
    result.mars_own_sign = mars_rasi.short_name in ("Ar", "Sc")
    if result.mars_own_sign:
        result.messages.append(f"Mars in own sign {mars_rasi.full_name} — weakened")

    # Cancellation: Jupiter aspects Mars
    if _graha_aspects(Graha.JUPITER, jupiter_lon, mars_lon):
        result.jupiter_cancels = True
        result.messages.append("Jupiter aspects Mars — dosha cancelled")

    # Cancellation: Mars conjunct Jupiter (within 5 degrees)
    if abs((mars_lon - jupiter_lon + 180) % 360 - 180) < 5:
        result.jupiter_cancels = True
        result.messages.append("Jupiter conjoined with Mars — dosha cancelled")

    # Cancellation: special ascendant rules
    result.lagna_cancels = _mars_rules_bad_houses_for_lagna(lagna_rasi)
    if result.lagna_cancels:
        result.messages.append(
            f"From {lagna_rasi.full_name} lagna, Mars rules beneficial houses — weakened"
        )

    # Final determination
    effective_dosha = (result.from_lagna or result.from_moon or result.from_venus)
    if result.jupiter_cancels:
        effective_dosha = False
    if result.mars_own_sign and not (result.from_moon and result.from_venus):
        effective_dosha = False

    result.has_dosha = effective_dosha

    if result.has_dosha:
        parts = []
        if result.from_lagna:
            parts.append(f"Lagna (H{mars_lagna_house})")
        if result.from_moon:
            parts.append(f"Moon (H{mars_moon_house})")
        if result.from_venus:
            parts.append(f"Venus (H{mars_venus_house})")
        result.messages.append(f"Kuja Dosha present from: {', '.join(parts)}")
    else:
        result.messages.insert(0, "No Kuja Dosha")

    return result
