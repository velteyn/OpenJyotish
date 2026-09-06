from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions

#: The seven grahas (Rahu/Ketu excluded) that can become the Brahma planet.
_GRAHAS = [g for g in Graha if g.is_planet]

#: Weekday ordering used by the "sixth planet from him" exception
#: (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) — the BPHS list.
_WEEKDAY_LIST = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
    Graha.JUPITER, Graha.VENUS, Graha.SATURN,
]


def _rasi_lord(rasi: Rasi) -> Graha:
    """Return the Graha which rules a rasi."""
    name = rasi.lord
    for g in _GRAHAS:
        if g.full_name == name:
            return g
    return Graha.SUN


def _lord_of_house(lagna_rasi: Rasi, house_num: int) -> Graha:
    """Lord of a 1-based house (1..12) from lagna."""
    rasi = Rasi((lagna_rasi.value + house_num - 1) % 12)
    return _rasi_lord(rasi)


def _planet_rasi(g: Graha, planets: Dict) -> Rasi:
    lon = planets[g]["longitude"]
    return Rasi.from_longitude(lon)


def _in_hindside(rasi: Rasi, ref_rasi: Rasi) -> bool:
    """True if rasi is in the first six houses from the reference (hindside)."""
    offset = (rasi.value - ref_rasi.value) % 12
    return 0 <= offset < 6


def _planet_strong(g: Graha, planets: Dict) -> bool:
    """Strength test for the Brahma scoring: is the planet strong (>= friend)."""
    from jhora.calc.dignities import DignityChecker
    lon = planets[g]["longitude"]
    rasi_idx = int(lon // 30) % 12
    deg = lon % 30
    dignity = DignityChecker().get_dignity(g, rasi_idx, deg)
    # Exalted/Moolatrikona/own/friend count as strong; neutral/debilitated do not.
    return dignity in ("exalted", "own", "moolatrikona", "friend")


def _longitude(g: Graha, planets: Dict) -> float:
    return planets[g]["longitude"] % 360.0


def _stronger_planet(p1: Graha, p2: Graha, planets: Dict) -> Graha:
    """Return the stronger of two planets (higher advancement of longitude in
    its rasi breaks a tie — the final 'stronger planet' test)."""
    l1 = _longitude(p1, planets)
    l2 = _longitude(p2, planets)
    return p1 if l1 > l2 else p2


def _stronger_rasi(r1: Rasi, r2: Rasi, planets: Dict) -> Rasi:
    """Return the stronger of two rasis (BPHS 'stronger of lagna and 7th').

    Tie-break uses planet count in each rasi, then co-lord association
    (Jupiter/Mercury/dispositor), then the higher advancement of the rasi lord.
    """
    def _in_rasi(rasi: Rasi) -> int:
        return sum(1 for g in _GRAHAS if _planet_rasi(g, planets) == rasi)

    c1, c2 = _in_rasi(r1), _in_rasi(r2)
    if c1 != c2:
        return r1 if c1 > c2 else r2

    def _co_count(rasi: Rasi) -> int:
        lord = _rasi_lord(rasi)
        count = 0
        for g in (Graha.JUPITER, Graha.MERCURY, lord):
            if _planet_rasi(g, planets) == rasi:
                count += 1
        return count

    cc1, cc2 = _co_count(r1), _co_count(r2)
    if cc1 != cc2:
        return r1 if cc1 > cc2 else r2

    # Higher advancement of the rasi lord's longitude.
    return _stronger_planet(_rasi_lord(r1), _rasi_lord(r2), planets)


def _brahma_planet(lagna_rasi: Rasi, planets: Dict) -> Graha:
    """Compute the Brahma planet per BPHS ('Sthira/Brahma dasa' article).

    From the stronger of lagna and 7th, score the 6th, 8th and 12th lords on
    strength, odd sign and hindside; the top scora (ties broken by strength)
    is Brahma. The 8th-from-AK / in-8th / Saturn exceptions map to the sixth
    planet from it in the weekday list.
    """
    seventh = Rasi((lagna_rasi.value + 6) % 12)
    ref = _stronger_rasi(lagna_rasi, seventh, planets)

    lords = [_lord_of_house(ref, h) for h in (6, 8, 12)]
    lords = [l for l in lords if l in _GRAHAS]

    scores: Dict[Graha, int] = {}
    for l in lords:
        h = _planet_rasi(l, planets)
        score = 0
        if _planet_strong(l, planets):
            score += 1
        if h.is_odd:
            score += 1
        if _in_hindside(h, ref):
            score += 1
        scores[l] = score

    top = sorted(scores, key=lambda g: (scores[g], _longitude(g, planets)), reverse=True)
    if not top:
        return Graha.SUN
    winner = top[0]
    if len(top) > 1 and scores[top[1]] == scores[winner]:
        winner = _stronger_planet(top[0], top[1], planets)

    # Exception: if the winner is Saturn, or occupies the 8th from the atma
    # karaka (approximated by the strongest planet as karaka proxy), take the
    # sixth planet from it in the weekday list. Applied once.
    return _apply_exception(winner, planets)


def _apply_exception(brahma: Graha, planets: Dict) -> Graha:
    """Apply the BPHS 'sixth planet from him' exceptions, once."""
    ak = max(_GRAHAS, key=lambda g: _longitude(g, planets))
    ak_rasi = _planet_rasi(ak, planets)
    brahma_rasi = _planet_rasi(brahma, planets)

    in_eighth_from_ak = brahma_rasi == Rasi((ak_rasi.value + 7) % 12)
    if brahma == Graha.SATURN or in_eighth_from_ak:
        idx = _WEEKDAY_LIST.index(brahma)
        return _WEEKDAY_LIST[(idx + 5) % 7]
    return brahma


def _rasi_duration(rasi: Rasi) -> float:
    """Dasa years for a rasi: movable=7, fixed=8, dual=9 (BPHS 'Sthira' verse).

    The four movable + four fixed + four dual signs give a full cycle of
    4*7 + 4*8 + 4*9 = 96 years.
    """
    if rasi.is_movable:
        return 7.0
    if rasi.is_fixed:
        return 8.0
    return 9.0


class BrahmaDasa(DasaBase):
    system_name = "brahma"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        planets = chart["planets"]
        lagna_rasi = Rasi.from_longitude(lagna_lon)

        brahma = _brahma_planet(lagna_rasi, planets)
        brahma_lon = _longitude(brahma, planets)
        seed_rasi = Rasi.from_longitude(brahma_lon)

        lord_names: Dict[int, str] = {}
        rasies: List[Tuple[int, float]] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        # First mahadasa balance: fraction of the seed sign already elapsed.
        frac_elapsed = (brahma_lon % 30) / 30.0
        first_years = _rasi_duration(seed_rasi) * (1.0 - frac_elapsed)

        for i in range(12):
            rasi = Rasi((seed_rasi.value + i) % 12)
            yrs = _rasi_duration(rasi)
            if i == 0:
                yrs = first_years
            lord_idx = 100 + rasi.value
            lord_names[lord_idx] = rasi.full_name
            rasies.append((lord_idx, yrs))

        sub_ratios = [_rasi_duration(Rasi(i)) for i in range(12)]
        sub_lord_names = {i: Rasi(i).full_name for i in range(12)}

        return self.build_period_tree(
            lords=rasies,
            start_jd=birth_jd,
            cycle_total_years=96.0,
            sub_ratios=sub_ratios,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            lord_names=lord_names,
            sub_lord_names=sub_lord_names,
        )
