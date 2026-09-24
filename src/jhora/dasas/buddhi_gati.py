"""Buddhi Gati Dasa — Agni Purana tradition, most-used form.

"Direction of the buddhi (intellect)": a graha dasa whose mahadasa order
is read off the chart instead of a fixed sequence. The houses are swept
starting from the 4th from lagna; each occupied house contributes its
planets ordered by descending longitude in the base varga; a planet's
years are the zodiacal count from lagna to its sign, stepped by the
planets already sequenced, +1 when exalted / -1 when debilitated in
that varga. The base varga is D-1 and configurable (the classical
varga option). Sub-levels divide each period into equal shares running
the base order rotated to start at the parent lord.

Provenance: Agni Purana tradition as carried by the mainstream published
tables and the most-used tools (the GAP survey's remaining dasa gap).
No school variant is known; nothing here is guessed.
"""

from typing import Dict, List, Optional, Tuple

from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.dasas.jaimini_common import normalize_planets
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha

#: The base progression repeats until this many years are covered, and
#: never more than two full cycles (the most-used presentation span).
LIFESPAN_YEARS = 144.0
MAX_CYCLES = 2

#: Dignity signs in the base varga: (exalted set, debilitated set).
#: The seven planets use the standard exaltation signs; the nodes use
#: the inclusive two-sign reading (Rahu Taurus/Gemini, Ketu
#: Scorpio/Sagittarius) carried by the most-used published tables.
_DIGNITY = {
    Graha.SUN: ({0}, {6}),
    Graha.MOON: ({1}, {7}),
    Graha.MARS: ({9}, {3}),
    Graha.MERCURY: ({5}, {11}),
    Graha.JUPITER: ({3}, {9}),
    Graha.VENUS: ({11}, {5}),
    Graha.SATURN: ({6}, {0}),
    Graha.RAHU: ({1, 2}, {7, 8}),
    Graha.KETU: ({7, 8}, {1, 2}),
}


def _dignity_delta(planet: Graha, sign: int) -> int:
    """+1 exalted / -1 debilitated in the base varga, else 0."""
    ex, deb = _DIGNITY.get(planet, (set(), set()))
    if sign in ex:
        return 1
    if sign in deb:
        return -1
    return 0


def buddhi_gati_progression(
    planet_lons: Dict[Graha, float], lagna: int
) -> List[Tuple[Graha, int]]:
    """Base (lord, years) progression from varga longitudes + varga lagna.

    Houses are swept from the 4th from lagna (lagna+3); empty houses are
    skipped; planets sharing a house run in descending-longitude order;
    years = (lagna + already-sequenced - planet-sign) mod 12 adjusted
    for dignity. Zero/negative spans are KEPT: they never open a
    mahadasa, but they keep their seat in the sub-level rotation order.
    """
    signs = {g: int(lon // 30) % 12 for g, lon in planet_lons.items()}
    occupants: Dict[int, List[Graha]] = {}
    for g, s in signs.items():
        occupants.setdefault(s, []).append(g)
    order: List[Tuple[Graha, int]] = []
    placed = 0
    for h in range(12):
        sign = (lagna + 3 + h) % 12
        housemates = occupants.get(sign, [])
        if not housemates:
            continue
        housemates.sort(key=lambda g: planet_lons[g], reverse=True)
        for g in housemates:
            yrs = (lagna + placed - signs[g]) % 12 + _dignity_delta(g, signs[g])
            placed += 1
            order.append((g, yrs))
    return order


class BuddhiGatiDasa(DasaBase):
    """Buddhi Gati mahadasas with rotated equal-share sub-levels."""

    system_name = "buddhi-gati"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        varga = chart.get("buddhi_gati_varga") or {}
        lons = normalize_planets(varga.get("planets", chart.get("planets", {})))
        lagna_lon = varga.get("lagna_lon", chart.get("lagna_lon", 0.0))
        lagna = int(lagna_lon // 30) % 12
        base = buddhi_gati_progression(lons, lagna)
        if not base:
            return []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = (opts.subdivision_level if opts.include_subperiods
                     else PeriodLevel.MAHADASA)
        lords = [g for g, _ in base]
        lord_idx = [int(g) for g in lords]
        names = {i: lords[i].full_name for i in range(len(lords))}
        periods: List[DasaPeriod] = []
        current_jd = birth_jd
        covered = 0.0
        cycles = 0
        while covered < LIFESPAN_YEARS and cycles < MAX_CYCLES:
            for g, yrs in base:
                if yrs <= 0:
                    continue  # never opens a mahadasa
                dur_days = yrs * y_per_d
                md = DasaPeriod(
                    lord_index=int(g),
                    lord_name=g.full_name,
                    start_jd=current_jd,
                    end_jd=current_jd + dur_days,
                    duration_years=float(yrs),
                    level=PeriodLevel.MAHADASA,
                )
                if max_level.value >= PeriodLevel.ANTARDASA.value:
                    md.sub_periods = _subdivide(
                        md, [1.0] * len(base), y_per_d, 1, max_level,
                        names, lord_idx,
                        ad_method=opts.ad_method)
                periods.append(md)
                current_jd += dur_days
                covered += yrs
                if covered >= LIFESPAN_YEARS:
                    break
            cycles += 1
        return periods
