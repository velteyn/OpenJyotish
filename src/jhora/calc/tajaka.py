from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from jhora.ephemeris.swe import SweEngine, SEFLG_DEFAULT, SEFLG_SIDEREAL, SEFLG_SWIEPH, SEFLG_SPEED
from jhora.calc.dignities import EXALTATION
from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.dasa import DasaPeriod, PeriodLevel

_SE_FLAGS = SEFLG_SWIEPH | SEFLG_SPEED | SEFLG_SIDEREAL

_MUDDA_ORDER = [
    Graha.SUN, Graha.MOON, Graha.MARS, Graha.RAHU,
    Graha.JUPITER, Graha.SATURN, Graha.MERCURY, Graha.KETU, Graha.VENUS,
]

_MUDDA_DAYS = {
    Graha.SUN: 18,
    Graha.MOON: 30,
    Graha.MARS: 21,
    Graha.RAHU: 54,
    Graha.JUPITER: 48,
    Graha.SATURN: 57,
    Graha.MERCURY: 51,
    Graha.KETU: 21,
    Graha.VENUS: 60,
}

_MUDDA_ORDER_NAMES = [g.short_name for g in _MUDDA_ORDER]

#: Solar (Tajaka) year in days, used for every duodecimal division.
SOLAR_YEAR_DAYS = 365.2425


class TajakaLevel(IntEnum):
    """The six Tajaka return levels.

    Each level is one twelfth of the one above it, so the Tajaka year divides
    by twelve at every step (a duodecimal subdivision, as in the reference):

        annual 1 y  ->  monthly 1/12 y  ->  2.5-day 1/144 y
        ->  5-hr 1/1728 y  ->  25-min 1/20736 y  ->  2-min 1/248832 y

    The level chart for index ``i`` is cast at the commencement of the i-th
    sub-period, measured from the varsha pravesh (solar return) moment that
    begins the Tajaka year. Index is one-based, so index 1 is the anchor.
    """

    ANNUAL = 0
    MONTHLY = 1
    TWO_AND_HALF_DAY = 2
    FIVE_HOUR = 3
    TWENTY_FIVE_MIN = 4
    TWO_MIN = 5

    @property
    def label(self) -> str:
        return {
            TajakaLevel.ANNUAL: "annual",
            TajakaLevel.MONTHLY: "monthly",
            TajakaLevel.TWO_AND_HALF_DAY: "2.5-day",
            TajakaLevel.FIVE_HOUR: "5-hr",
            TajakaLevel.TWENTY_FIVE_MIN: "25-min",
            TajakaLevel.TWO_MIN: "2-min",
        }[self]

    @property
    def periods_per_year(self) -> int:
        return 12 ** int(self)

    @property
    def year_fraction(self) -> float:
        return 1.0 / self.periods_per_year

    @property
    def days(self) -> float:
        """Length of one sub-period at this level, in days."""
        return SOLAR_YEAR_DAYS * self.year_fraction


def level_offset_days(level: TajakaLevel, index: int) -> float:
    """Days from the Tajaka-year anchor to the start of sub-period ``index``.

    Index is one-based: index 1 returns 0.0 (the anchor itself). An index
    outside 1..periods_per_year is rejected rather than wrapped.
    """
    if not 1 <= index <= level.periods_per_year:
        raise ValueError(
            f"{level.label} index must be 1..{level.periods_per_year}, got {index}"
        )
    return (index - 1) * level.days


@dataclass
class TajakaData:
    chart: ChartData
    year_index: int
    muntha_sign: int
    varsha_pravesh_jd: float
    harsha_bala: Dict[Graha, int] = None
    patyayini_dasa: List[DasaPeriod] = None
    mudda_dasa: List[DasaPeriod] = None
    # Level charts (the annual chart is level ANNUAL, index 1)
    level: "TajakaLevel" = TajakaLevel.ANNUAL
    index: int = 1
    anchor_jd: Optional[float] = None
    moment_jd: Optional[float] = None
    sunrise: bool = False


def compute_muntha(natal_lagna_sign_index: int, year_number: int) -> int:
    return (natal_lagna_sign_index + year_number - 1) % 12


def find_varsha_pravesh_jd(
    swe_engine: SweEngine,
    natal_sun_lon: float,
    birth_jd: float,
    target_year: int,
    target_month: int = 1,
    target_day: int = 1,
) -> float:
    tz_offset = 0.0
    utc_birth = birth_jd

    birthday_in_target = swe_engine.julday(target_year, target_month, target_day, 0.0)

    approx_jd = birthday_in_target

    jd_start = max(approx_jd - 15, utc_birth)
    return swe_engine.solcross_ut(natal_sun_lon, jd_start)


def build_tajaka_chart(
    swe_engine: SweEngine,
    chart_builder: ChartBuilder,
    natal_chart: ChartData,
    target_year: int,
    tropical: bool = False,
) -> TajakaData:
    natal_sun_lon = natal_chart.sun.longitude
    birth_year = natal_chart.birth_date.year
    birth_month = natal_chart.birth_date.month
    birth_day = natal_chart.birth_date.day
    birth_jd = natal_chart.julian_day

    if tropical:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        swe_engine._flags = flags | SEFLG_SIDEREAL
        natal_sun_trop = swe_engine.calc_planet(swe.SUN, birth_jd, flags).longitude
        target_lon = natal_sun_trop
        return_flags = None
    else:
        target_lon = natal_sun_lon
        return_flags = _SE_FLAGS

    orig_flags = swe_engine._flags
    if return_flags:
        swe_engine._flags = return_flags

    try:
        jd_cross = find_varsha_pravesh_jd(
            swe_engine, target_lon, birth_jd, target_year, birth_month, birth_day,
        )
    finally:
        swe_engine._flags = orig_flags
    if tropical:
        swe_engine.set_sidereal_mode(natal_chart.ayanamsa_name)

    # Build chart at the return moment
    y, m, d, h = swe_engine.revjul(jd_cross)
    lat = natal_chart.latitude
    lon = natal_chart.longitude
    tz = natal_chart.timezone

    chart = chart_builder.build(
        int(y), int(m), int(d), h,
        lat, lon, tz,
        ayanamsa=natal_chart.ayanamsa_name,
    )

    year_index = target_year - birth_year + 1
    natal_lagna_sign = int(natal_chart.ascendant // 30) % 12
    muntha = compute_muntha(natal_lagna_sign, year_index)

    return TajakaData(
        chart=chart,
        year_index=year_index,
        muntha_sign=muntha,
        varsha_pravesh_jd=jd_cross,
        level=TajakaLevel.ANNUAL,
        index=1,
        anchor_jd=jd_cross,
        moment_jd=jd_cross,
    )


def cast_chart_at_jd(
    swe_engine: SweEngine,
    chart_builder: ChartBuilder,
    natal_chart: ChartData,
    jd: float,
) -> ChartData:
    """Cast a chart at a Julian day, for the birth place and ayanamsa."""
    y, m, d, h = swe_engine.revjul(jd)
    return chart_builder.build(
        int(y), int(m), int(d), h,
        natal_chart.latitude, natal_chart.longitude, natal_chart.timezone,
        ayanamsa=natal_chart.ayanamsa_name,
    )


def sunrise_jd_of(swe_engine: SweEngine, jd: float, lat: float,
                  lon: float) -> float:
    """Sunrise (UT Julian day) on the UT day containing ``jd``.

    Falls back to ``jd`` when the Sun does not rise (polar latitudes).
    """
    y, m, d, _h = swe_engine.revjul(jd)
    day_start = swe_engine.julday(int(y), int(m), int(d), 0.0)
    sr = swe_engine.rise_trans(day_start, swe.SUN, lat, lon, rise=True)
    return sr if sr is not None else jd


def build_tajaka_level_chart(
    swe_engine: SweEngine,
    chart_builder: ChartBuilder,
    natal_chart: ChartData,
    target_year: int,
    level: TajakaLevel = TajakaLevel.ANNUAL,
    index: int = 1,
    sunrise: bool = False,
) -> TajakaData:
    """Build a Tajaka chart for a level and one-based sub-period index.

    The Tajaka year begins at the varsha pravesh (solar return) moment, and
    every level is a duodecimal division of the year measured from that
    anchor. Index 1 of any level is the anchor itself; index i is the start of
    the i-th sub-period. ``sunrise=True`` casts the chart at sunrise on the
    computed day instead of at the exact moment.
    """
    birth_year = natal_chart.birth_date.year
    natal_sun_lon = natal_chart.sun.longitude

    anchor_jd = find_varsha_pravesh_jd(
        swe_engine, natal_sun_lon, natal_chart.julian_day,
        target_year, natal_chart.birth_date.month, natal_chart.birth_date.day,
    )

    moment_jd = anchor_jd + level_offset_days(level, index)
    if sunrise:
        moment_jd = sunrise_jd_of(
            swe_engine, moment_jd, natal_chart.latitude, natal_chart.longitude
        )

    chart = cast_chart_at_jd(swe_engine, chart_builder, natal_chart, moment_jd)

    year_index = target_year - birth_year + 1
    natal_lagna_sign = int(natal_chart.ascendant // 30) % 12
    muntha = compute_muntha(natal_lagna_sign, year_index)

    return TajakaData(
        chart=chart,
        year_index=year_index,
        muntha_sign=muntha,
        varsha_pravesh_jd=anchor_jd,
        harsha_bala=compute_harsha_bala(chart, moment_jd),
        patyayini_dasa=compute_patyayini_dasa(
            chart.planets, chart.ascendant, moment_jd),
        mudda_dasa=compute_mudda_dasa(
            natal_chart.moon.longitude, year_index - 1, moment_jd),
        level=level,
        index=index,
        anchor_jd=anchor_jd,
        moment_jd=moment_jd,
        sunrise=sunrise,
    )


def build_dasa_pravesh_chart(
    swe_engine: SweEngine,
    chart_builder: ChartBuilder,
    natal_chart: ChartData,
    period: DasaPeriod,
) -> ChartData:
    """Cast a dasa pravesh (period-commencement) chart at a period's start."""
    return cast_chart_at_jd(
        swe_engine, chart_builder, natal_chart, period.start_jd
    )


def compute_harsha_bala(
    chart: ChartData, varsha_pravesh_jd: float
) -> Dict[Graha, int]:
    planets = chart.planets
    lagna_lon = chart.ascendant

    # Determine day/night: Sun in houses 7-12 (above horizon) → night
    sun_lon = planets[Graha.SUN].longitude
    sun_house = (int(sun_lon // 30) - int(lagna_lon // 30)) % 12 + 1
    is_night = sun_house >= 7

    scores: Dict[Graha, int] = {}
    for g in Graha:
        if g == Graha.KETU:
            continue
        scores[g] = 0

    # Source 1: specific house placement
    house_bonus = {
        Graha.SUN: 9, Graha.MOON: 3, Graha.MARS: 6,
        Graha.MERCURY: 1, Graha.JUPITER: 11, Graha.VENUS: 5, Graha.SATURN: 12,
    }
    for g, target_house in house_bonus.items():
        lon = planets[g].longitude
        h = (int(lon // 30) - int(lagna_lon // 30)) % 12 + 1
        if h == target_house:
            scores[g] += 5

    # Source 2: exaltation or own sign
    for g in Graha:
        if g == Graha.KETU:
            continue
        lon = planets[g].longitude
        sign = int(lon // 30) % 12
        lord_of_sign = {0: Graha.MARS, 1: Graha.VENUS, 2: Graha.MERCURY,
                        3: Graha.MOON, 4: Graha.SUN, 5: Graha.MERCURY,
                        6: Graha.VENUS, 7: Graha.MARS, 8: Graha.JUPITER,
                        9: Graha.SATURN, 10: Graha.SATURN, 11: Graha.JUPITER}[sign]
        if g == lord_of_sign:
            scores[g] += 5
            continue
        if g in EXALTATION and sign == EXALTATION[g][0]:
            scores[g] += 5
    if Graha.KETU in scores:
        del scores[Graha.KETU]

    # Source 3: gender-based house strength
    feminine = {Graha.MOON, Graha.MERCURY, Graha.VENUS, Graha.SATURN}
    masculine = {Graha.SUN, Graha.MARS, Graha.JUPITER}
    fem_houses = {1, 2, 3, 7, 8, 9}
    masc_houses = {4, 5, 6, 10, 11, 12}
    for g in list(scores.keys()):
        lon = planets[g].longitude
        h = (int(lon // 30) - int(lagna_lon // 30)) % 12 + 1
        if g in feminine and h in fem_houses:
            scores[g] += 5
        elif g in masculine and h in masc_houses:
            scores[g] += 5

    # Source 4: day/night bonus
    for g in list(scores.keys()):
        if is_night and g in feminine:
            scores[g] += 5
        elif not is_night and g in masculine:
            scores[g] += 5

    return scores


def compute_patyayini_dasa(
    planets: Dict[Graha, "PlanetChartData"],
    lagna_lon: float,
    varsha_pravesh_jd: float,
) -> List[DasaPeriod]:
    from jhora.charts.chart import PlanetChartData

    items: List[Tuple[float, str, int]] = []

    lagna_deg_in_sign = lagna_lon % 30
    items.append((lagna_deg_in_sign, "Lagna", -1))

    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
               Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
        lon = planets[g].longitude % 30
        items.append((lon, g.short_name, g.value))

    items.sort(key=lambda x: x[0])

    # Patyamsa = current krisamsa - previous krisamsa (skip first)
    patyamsas: List[float] = []
    for i in range(len(items)):
        if i == 0:
            continue
        patyamsa = items[i][0] - items[i - 1][0]
        patyamsas.append(patyamsa)

    total_patyamsa = sum(patyamsas)
    if total_patyamsa <= 0:
        return []

    solar_year_days = 365.2425
    periods: List[DasaPeriod] = []
    start_jd = varsha_pravesh_jd

    for i, patyamsa in enumerate(patyamsas):
        _, name, lord_idx = items[i + 1]
        fraction = patyamsa / total_patyamsa
        days = solar_year_days * fraction
        end_jd = start_jd + days
        periods.append(DasaPeriod(
            lord_index=lord_idx,
            lord_name=name,
            start_jd=start_jd,
            end_jd=end_jd,
            duration_years=days / 365.2425,
        ))
        start_jd = end_jd

    return periods


def compute_mudda_dasa(
    natal_moon_lon: float,
    completed_years: int,
    varsha_pravesh_jd: float,
    *,
    seed_longitude: Optional[float] = None,
    progress_seed: bool = True,
) -> List[DasaPeriod]:
    """Mudda (Varsha Vimsottari) dasa, compressed into the Tajaka year.

    Seed options:
      * ``seed_longitude`` selects the seed point. ``None`` (default) seeds
        from the natal Moon; pass the annual chart's lagna longitude to seed
        from the varshaphal chart instead. Sources differ on which is
        canonical, so the choice is always explicit at the call site.
      * ``progress_seed=False`` keeps the seed fixed for the year instead of
        advancing it by ``completed_years``.
    """
    seed_lon = natal_moon_lon if seed_longitude is None else seed_longitude
    nakshatra, pada = Nakshatra.from_longitude(seed_lon)
    nakshatra_lord_name = nakshatra.lord
    nakshatra_lord_map = {
        "Ketu": Graha.KETU, "Venus": Graha.VENUS, "Sun": Graha.SUN,
        "Moon": Graha.MOON, "Mars": Graha.MARS, "Rahu": Graha.RAHU,
        "Jupiter": Graha.JUPITER, "Saturn": Graha.SATURN, "Mercury": Graha.MERCURY,
    }
    first_lord = nakshatra_lord_map.get(nakshatra_lord_name, Graha.KETU)

    first_idx = _MUDDA_ORDER.index(first_lord)
    if progress_seed:
        progressed_idx = (first_idx + completed_years) % 9
    else:
        progressed_idx = first_idx

    # Dasa balance: fraction of nakshatra remaining
    nakshatra_span = 13.3333333
    nakshatra_start = nakshatra.start_longitude
    offset_in_nakshatra = (seed_lon - nakshatra_start) % 360
    fraction_remaining = (nakshatra_span - offset_in_nakshatra) / nakshatra_span
    if fraction_remaining < 0:
        fraction_remaining = 0

    periods: List[DasaPeriod] = []
    start_jd = varsha_pravesh_jd
    solar_year_days = 360.0  # Mudda uses 360-day "year" (1 day = 1° Sun motion)

    for offset in range(9):
        g = _MUDDA_ORDER[(progressed_idx + offset) % 9]
        days = _MUDDA_DAYS[g]
        if offset == 0:
            days = days * fraction_remaining
        end_jd = start_jd + days
        periods.append(DasaPeriod(
            lord_index=g.value,
            lord_name=g.short_name,
            start_jd=start_jd,
            end_jd=end_jd,
            duration_years=days / 365.2425,
        ))
        start_jd = end_jd

    return periods
