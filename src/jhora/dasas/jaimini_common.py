"""Shared machinery for Jaimini rasi dasas (Karaka, Moola, Shoola, ...).

Classical rules implemented here (Jaimini Sutras, Upadesa Khanda, in the
standard Parasara/SJC reading):

- Sign lords: Mars, Venus, Mercury, Moon, Sun, Mercury, Venus, Mars,
  Jupiter, Saturn, Saturn, Jupiter; dual ownership Scorpio [Mars, Ketu]
  and Aquarius [Saturn, Rahu], resolved by strength.
- Strength for dual-lord resolution: occupant count dominates, then
  exaltation (+2) / debilitation (-2), then dispositor occupancy, then
  higher absolute longitude wins ties.
- Sign duration (Chara rule): distance in signs from the sign to its
  (resolved) lord — forward for odd-footed signs (Aries, Cancer, Libra,
  Capricorn, i.e. 0-based even indices), backward for even-footed ones;
  lord in own sign gives 12 years; a full 12-count reduces to 11;
  clamped to 1..12.
- Antardasas: the 12 signs in cycle order from the MD sign (forward, or
  parity direction for Karaka dasa: odd MD forward, even MD backward),
  durations proportional to each sign's own MD-year value.

Karaka ranks come from ``jhora.calc.karaka`` (degrees-in-sign order).
"""

from typing import Dict, List, Optional, Tuple

from jhora.dasas.base import _subdivide
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

DUAL_LORDS: Dict[int, Tuple[Graha, Graha]] = {
    7: (Graha.MARS, Graha.KETU),      # Scorpio
    10: (Graha.SATURN, Graha.RAHU),   # Aquarius
}

EXALT_SIGNS: Dict[Graha, int] = {
    Graha.SUN: 0, Graha.MOON: 1, Graha.MARS: 9, Graha.MERCURY: 5,
    Graha.JUPITER: 3, Graha.VENUS: 11, Graha.SATURN: 6,
}

_ALL_GRAHAS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN,
               Graha.RAHU, Graha.KETU]


def normalize_planets(planets: Dict) -> Dict[Graha, float]:
    """Accept Graha-, int- or name-keyed {planet: {longitude}} or bare floats."""
    out: Dict[Graha, float] = {}
    for key, val in (planets or {}).items():
        lon = val["longitude"] if isinstance(val, dict) else float(val)
        if isinstance(key, Graha):
            out[key] = float(lon)
        elif isinstance(key, int):
            try:
                out[Graha(key)] = float(lon)
            except ValueError:
                continue
        elif isinstance(key, str):
            try:
                out[Graha[key.strip().upper()]] = float(lon)
            except KeyError:
                continue
    return out


def planet_signs(planets: Dict[Graha, float]) -> Dict[Graha, int]:
    """0-based rasi index per planet."""
    return {g: int(lon // 30) % 12 for g, lon in planets.items()}


def sign_occupants(planet_sigs: Dict[Graha, int]) -> Dict[int, List[Graha]]:
    """Planets per sign (all nine grahas count, nodes included)."""
    occ: Dict[int, List[Graha]] = {i: [] for i in range(12)}
    for g, s in planet_sigs.items():
        occ[s].append(g)
    return occ


def _exalt_score(planet: Graha, sign: int) -> int:
    if planet not in EXALT_SIGNS:
        return 0
    if sign == EXALT_SIGNS[planet]:
        return 2
    if sign == (EXALT_SIGNS[planet] + 6) % 12:
        return -2
    return 0


def _single_lord(sign: int) -> Graha:
    name = Rasi(sign).lord
    return {"Mars": Graha.MARS, "Venus": Graha.VENUS,
            "Mercury": Graha.MERCURY, "Moon": Graha.MOON,
            "Sun": Graha.SUN, "Jupiter": Graha.JUPITER,
            "Saturn": Graha.SATURN}[name]


def _strength_score(planet: Graha, planet_sigs: Dict[Graha, int],
                    exalt_weight: int = 10) -> Tuple[int, int, int, float]:
    """Composite (count, exalt, dispositor-count, longitude) for comparisons."""
    occ = sign_occupants(planet_sigs)
    si = planet_sigs[planet]
    cnt = len(occ[si])
    ex = _exalt_score(planet, si)
    disp = _single_lord(si)
    disp_si = planet_sigs.get(disp, si)
    disp_score = len(occ.get(disp_si, []))
    return (cnt, ex * (exalt_weight // 10), disp_score,
            planet_sigs[planet])


def stronger_lord(sign: int, planet_sigs: Dict[Graha, int]) -> Graha:
    """Resolve a sign's lord (dual ownership by strength, longitude tiebreak)."""
    if sign not in DUAL_LORDS:
        return _single_lord(sign)
    l1, l2 = DUAL_LORDS[sign]
    s1 = _strength_score(l1, planet_sigs)
    s2 = _strength_score(l2, planet_sigs)
    if s1 == s2:
        return l1 if planet_sigs[l1] >= planet_sigs[l2] else l2
    return l1 if s1 > s2 else l2


def _count_years(sign: int, lord_si: int, own_years: int = 12) -> int:
    """Sign-to-lord count for one sign (1..12 years)."""
    if lord_si == sign:
        return own_years
    direction = 1 if sign % 2 == 0 else -1  # odd-footed forward
    count, s = 1, sign
    while s != lord_si:
        s = (s + direction) % 12
        count += 1
        if count > 12:
            break
    if count == 12:
        count = 11  # full-circle traverses 11 years, not 12
    return max(1, min(12, count))


def sign_years(sign: int, planet_sigs: Dict[Graha, int],
               own_years: int = 12) -> int:
    """Chara duration rule for one sign (1..12 years)."""
    lord = stronger_lord(sign, planet_sigs)
    return _count_years(sign, planet_sigs.get(lord, sign), own_years)


def cycle_years(planet_sigs: Dict[Graha, int],
                own_years: int = 12) -> List[int]:
    """Chara durations for all 12 signs in zodiacal order."""
    return [sign_years(s, planet_sigs, own_years) for s in range(12)]


def rao_dual_lord(sign: int, planet_sigs: Dict[Graha, int]) -> Graha:
    """Scorpio/Aquarius lord with the mainstream Rao own-sign exception.

    A planet sitting in its own dual-ruled sign alone loses to its
    co-lord (Mars in Scorpio with Ketu elsewhere → Ketu; Saturn in
    Aquarius with Rahu elsewhere → Rahu, and vice versa); otherwise the
    shared ``stronger_lord`` resolution applies. Standard SJC/K.N. Rao
    reading (Gary Gomes following Rao).
    """
    if sign == 7:  # Scorpio: Mars / Ketu
        mars_si = planet_sigs.get(Graha.MARS)
        ketu_si = planet_sigs.get(Graha.KETU)
        if mars_si == 7 and ketu_si != 7:
            return Graha.KETU
        if ketu_si == 7 and mars_si != 7:
            return Graha.MARS
    elif sign == 10:  # Aquarius: Saturn / Rahu
        sat_si = planet_sigs.get(Graha.SATURN)
        rahu_si = planet_sigs.get(Graha.RAHU)
        if sat_si == 10 and rahu_si != 10:
            return Graha.RAHU
        if rahu_si == 10 and sat_si != 10:
            return Graha.SATURN
    return stronger_lord(sign, planet_sigs)


def chara_years(sign: int, planet_sigs: Dict[Graha, int]) -> int:
    """Chara duration for one sign with the Rao dual-lord exception."""
    lord = rao_dual_lord(sign, planet_sigs)
    return _count_years(sign, planet_sigs.get(lord, sign))


def chara_cycle_years(planet_sigs: Dict[Graha, int]) -> List[int]:
    """Chara durations (Rao exception) for all 12 signs, zodiacal order."""
    return [chara_years(s, planet_sigs) for s in range(12)]


#: Odd-footed signs (Jaimini footedness, not index parity): Aries,
#: Taurus, Gemini, Libra, Scorpio, Sagittarius.
ODD_FOOTED = frozenset({0, 1, 2, 6, 7, 8})


def chara_direction(lagna: int) -> int:
    """Whole-cycle direction for Chara dasa (+1 direct, -1 reverse).

    K.N. Rao 9th-from-lagna rule: direct (savya) when the 9th sign from
    lagna is odd-footed, reverse (apasavya) otherwise. Matches the
    Savya/Apasavya lagna groups on all 12 lagnas.
    """
    ninth = (int(lagna) + 8) % 12
    return 1 if ninth in ODD_FOOTED else -1


def rasi_dasa_tree(birth_jd: float, sequence: List[Tuple[int, int]],
                   sign_durations: List[int], y_per_d: float = 365.2425,
                   max_level: PeriodLevel = PeriodLevel.PRATYANTARDASA,
                   parity_ads: bool = False,
                   ad_direction: Optional[int] = None) -> List[DasaPeriod]:
    """Build an MD tree for a rasi-dasa sign sequence.

    ``sequence`` is [(sign, years), ...] in MD order; ``sign_durations``
    holds each cycle sign's own MD-year value (for proportional ADs).
    Antardasas run the 12 signs from the MD sign — forward, in parity
    direction (odd MD forward, even MD backward) when ``parity_ads``,
    or in a fixed cycle direction when ``ad_direction`` is given.
    """
    total = sum(sign_durations)
    periods: List[DasaPeriod] = []
    current_jd = birth_jd
    for sign, years in sequence:
        dur_days = years * y_per_d
        md = DasaPeriod(
            lord_index=100 + sign,
            lord_name=Rasi(sign).full_name,
            start_jd=current_jd,
            end_jd=current_jd + dur_days,
            duration_years=float(years),
            level=PeriodLevel.MAHADASA,
        )
        if max_level.value >= PeriodLevel.ANTARDASA.value and total > 0:
            direction = 1
            if ad_direction is not None:
                direction = 1 if ad_direction >= 0 else -1
            elif parity_ads and sign % 2 == 1:
                direction = -1
            order_signs = [(sign + direction * k) % 12 for k in range(12)]
            ratios = [float(sign_durations[s]) for s in order_signs]
            names = {k: Rasi(s).full_name
                     for k, s in enumerate(order_signs)}
            order = [100 + s for s in order_signs]
            md.sub_periods = _subdivide(md, ratios, y_per_d, 1, max_level,
                                        names, order)
        periods.append(md)
        current_jd += dur_days
    return periods
