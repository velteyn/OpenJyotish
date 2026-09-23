"""KP (Krishnamurti Paddhati) — cusps, lord chains and Ruling Planets.

Tradition: K.S. Krishnamurti's KP reads every point — a planet or a bhava
cusp — through a fourfold Vimsottari chain (sign lord, star lord, sub lord,
sub-sub lord) and uses Placidus bhava cusps rather than whole-sign houses.
Ruling Planets are the day lord (the weekday lord at local sunrise) together
with the star and sign lords of the Moon and of the lagna; KP applies them
to horary judgement and to electional timing.

Sources: K.S. Krishnamurti, *Krishnamurti Padhdhati* reader series. The
sub-division proportions are the Vimsottari years (Ketu 7 ... Mercury 17),
and the first sub of a nakshatra is its own lord — the same rotation repeats
at every deeper level. KP practice normally works in the Krishnamurti
ayanamsa; this module honours whichever ayanamsa the chart was built with
and reports it, so a Lahiri cusp chain is never silently taken for a KP one.

The nodes rule nakshatras but own no sign in mainstream KP, so a sign lord is
always one of the seven planets while star/sub/sub-sub lords may be nodes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.calc.muhurta import sunrise_sunset_hours
from jhora.calc.special_lagnas import kp_sublord
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi

#: Sign rulership used for the KP chain: the seven planets only (Aquarius is
#: Saturn's, Scorpio is Mars's); Rahu/Ketu own no sign.
SIGN_LORDS: Dict[Rasi, Graha] = {
    Rasi.ARIES: Graha.MARS,
    Rasi.TAURUS: Graha.VENUS,
    Rasi.GEMINI: Graha.MERCURY,
    Rasi.CANCER: Graha.MOON,
    Rasi.LEO: Graha.SUN,
    Rasi.VIRGO: Graha.MERCURY,
    Rasi.LIBRA: Graha.VENUS,
    Rasi.SCORPIO: Graha.MARS,
    Rasi.SAGITTARIUS: Graha.JUPITER,
    Rasi.CAPRICORN: Graha.SATURN,
    Rasi.AQUARIUS: Graha.SATURN,
    Rasi.PISCES: Graha.JUPITER,
}

#: Weekday lords indexed by Python's weekday (Monday = 0).
_DAY_LORDS: Tuple[Graha, ...] = (
    Graha.MOON, Graha.MARS, Graha.MERCURY, Graha.JUPITER,
    Graha.VENUS, Graha.SATURN, Graha.SUN,
)

_GRAHA_BY_NAME: Dict[str, Graha] = {g.full_name: g for g in Graha}


@dataclass(frozen=True)
class LordChain:
    """The fourfold KP chain for a zodiac longitude."""

    sign_lord: Graha
    star_lord: Graha
    sub_lord: Graha
    sub_sub_lord: Graha

    @property
    def string(self) -> str:
        return "-".join(
            g.full_name for g in (
                self.sign_lord, self.star_lord, self.sub_lord, self.sub_sub_lord,
            )
        )


@dataclass(frozen=True)
class KPCusp:
    """A Placidus bhava cusp with its KP chain."""

    house: int
    longitude: float
    sign: Rasi
    chain: LordChain


@dataclass(frozen=True)
class KPPlanet:
    """A planet placed by cusp, with its KP chain."""

    graha: Graha
    longitude: float
    sign: Rasi
    house: int
    chain: LordChain


@dataclass(frozen=True)
class RulingPlanet:
    """A Ruling Planet with every role it plays in the chart."""

    graha: Graha
    roles: Tuple[str, ...]

    @property
    def role_string(self) -> str:
        return ", ".join(self.roles)


@dataclass
class KPChart:
    """KP view of a chart: cusp table, planet table and Ruling Planets."""

    cusps: List[KPCusp]
    planets: List[KPPlanet]
    ruling_planets: List[RulingPlanet]
    day_lord: Graha
    ayanamsa: str
    cusp_system: str = "Placidus"


def cusp_longitudes(cd: ChartData) -> List[float]:
    """The twelve bhava cusp longitudes (Placidus, from the chart)."""
    cusps = [float(c) for c in cd.house_cusps]
    if len(cusps) >= 13:
        cusps = cusps[1:13]
    cusps = cusps[:12]
    if len(cusps) != 12:
        raise ValueError(f"expected 12 house cusps, got {len(cusps)}")
    return cusps


def house_of(longitude: float, cusps: List[float]) -> int:
    """The bhava (1-12) whose cusp interval contains a longitude."""
    lon = longitude % 360.0
    for i in range(12):
        start = cusps[i] % 360.0
        end = cusps[(i + 1) % 12] % 360.0
        if start < end:
            if start <= lon < end:
                return i + 1
        elif lon >= start or lon < end:
            return i + 1
    return 1


def lord_chain(longitude: float) -> LordChain:
    """Build the sign/star/sub/sub-sub chain for a longitude."""
    lon = longitude % 360.0
    rasi = Rasi.from_longitude(lon)
    nakshatra, _pada = Nakshatra.from_longitude(lon)
    subs = kp_sublord(lon, 2)
    if len(subs) < 2:
        raise ValueError("KP sub-lord chain could not be resolved")
    return LordChain(
        sign_lord=SIGN_LORDS[rasi],
        star_lord=_GRAHA_BY_NAME[nakshatra.lord],
        sub_lord=subs[0]["graha"],
        sub_sub_lord=subs[1]["graha"],
    )


def day_lord(cd: ChartData) -> Graha:
    """The weekday lord at local sunrise (Hindu day boundary).

    A birth before sunrise belongs to the previous weekday, so the lord is
    taken from the prior day in that case.
    """
    tz_east = -ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
    sunrise, _sunset = sunrise_sunset_hours(
        cd.birth_date, cd.latitude, cd.longitude, tz_east
    )
    weekday = cd.birth_date.weekday()  # Monday = 0
    if cd.time_of_day_hours < sunrise:
        weekday = (weekday - 1) % 7
    return _DAY_LORDS[weekday]


def ruling_planets(cd: ChartData) -> List[RulingPlanet]:
    """The KP Ruling Planets, de-duplicated with their roles merged."""
    moon_lon = cd.planet(Graha.MOON).longitude
    lagna_lon = cd.lagna.longitude

    entries: List[Tuple[Graha, str]] = [
        (day_lord(cd), "day lord"),
        (_GRAHA_BY_NAME[Nakshatra.from_longitude(moon_lon)[0].lord],
         "Moon's star lord"),
        (SIGN_LORDS[Rasi.from_longitude(moon_lon)], "Moon's sign lord"),
        (_GRAHA_BY_NAME[Nakshatra.from_longitude(lagna_lon)[0].lord],
         "lagna's star lord"),
        (SIGN_LORDS[Rasi.from_longitude(lagna_lon)], "lagna's sign lord"),
    ]

    order: List[Graha] = []
    roles: Dict[Graha, List[str]] = {}
    for graha, role in entries:
        if graha not in roles:
            roles[graha] = []
            order.append(graha)
        roles[graha].append(role)
    return [RulingPlanet(g, tuple(roles[g])) for g in order]


class KPComputer:
    """Compute the KP cusp/planet tables and Ruling Planets for a chart."""

    def __init__(self, chart: ChartData):
        self.chart = chart

    def compute(self) -> KPChart:
        cd = self.chart
        cusps = cusp_longitudes(cd)

        cusp_rows = [
            KPCusp(
                house=i + 1,
                longitude=cusps[i],
                sign=Rasi.from_longitude(cusps[i]),
                chain=lord_chain(cusps[i]),
            )
            for i in range(12)
        ]

        planet_rows = []
        for g in Graha:
            if g not in cd.planets:
                continue
            lon = cd.planets[g].longitude
            planet_rows.append(
                KPPlanet(
                    graha=g,
                    longitude=lon,
                    sign=Rasi.from_longitude(lon),
                    house=house_of(lon, cusps),
                    chain=lord_chain(lon),
                )
            )

        return KPChart(
            cusps=cusp_rows,
            planets=planet_rows,
            ruling_planets=ruling_planets(cd),
            day_lord=day_lord(cd),
            ayanamsa=cd.ayanamsa_name,
        )


def kp_chart(cd: ChartData) -> KPChart:
    """Convenience wrapper: the KP view of a chart."""
    return KPComputer(cd).compute()


# ── KP view of the Vimsottari dasa ──────────────────────────────────────────
#
# KP does not change the Vimsottari periods; it changes how a running period
# is read. Each dasa lord is judged through its *natal* position: the Placidus
# bhava it occupies and its fourfold chain (sign / star / sub / sub-sub lord).
# The sub lord of the dasa lord is the deciding factor in KP, so the same
# Vimsottari years are presented with that chain attached.

_LEVEL_NAMES: Tuple[str, ...] = (
    "Mahadasa", "Antardasa", "Pratyantardasa", "Sukshma", "Prana", "Deha",
)


@dataclass(frozen=True)
class KPDasaLord:
    """A Vimsottari mahadasa lord read through its KP chain."""

    graha: Graha
    start_jd: float
    end_jd: float
    duration_years: float
    house: int
    chain: LordChain


@dataclass(frozen=True)
class KPDasaLevel:
    """One level of the running Vimsottari chain, read KP-style."""

    level: str
    graha: Graha
    start_jd: float
    end_jd: float
    house: int
    chain: LordChain


def _vimsottari_periods(cd: ChartData) -> List:
    """The Vimsottari period tree for a chart (standard periods)."""
    from jhora.dasas.vimsottari import VimsottariDasa

    chart = {
        "planets": {g.value: {"longitude": p.longitude}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
    }
    return VimsottariDasa().compute(cd.julian_day, chart)


def _planet_annotations(cd: ChartData) -> Dict[Graha, KPPlanet]:
    return {p.graha: p for p in kp_chart(cd).planets}


def kp_dasa_lords(cd: ChartData) -> List[KPDasaLord]:
    """The Vimsottari mahadasas, each lord annotated with its KP chain.

    The years are the standard Vimsottari periods; the KP-specific view is
    the fourfold chain and Placidus bhava of each lord's natal position.
    """
    annotations = _planet_annotations(cd)
    rows: List[KPDasaLord] = []
    for md in _vimsottari_periods(cd):
        try:
            graha = Graha(md.lord_index)
        except ValueError:
            continue
        kp = annotations.get(graha)
        if kp is None:
            continue
        rows.append(KPDasaLord(
            graha=graha,
            start_jd=md.start_jd,
            end_jd=md.end_jd,
            duration_years=md.duration_years,
            house=kp.house,
            chain=kp.chain,
        ))
    return rows


def kp_dasa_levels(cd: ChartData, when=None,
                   max_levels: int = 3) -> List[KPDasaLevel]:
    """The running Vimsottari chain (MD, AD, PD, …) with KP chains.

    ``when`` is a local ``datetime`` (or ``date``); it defaults to the current
    instant. Each active lord is annotated with the Placidus bhava and KP
    chain of its natal position.
    """
    annotations = _planet_annotations(cd)
    target = _target_jd(cd, when)
    rows: List[KPDasaLevel] = []
    nodes = _vimsottari_periods(cd)
    while nodes and len(rows) < max_levels:
        active = next(
            (p for p in nodes if p.start_jd <= target < p.end_jd), None)
        if active is None:
            break
        try:
            graha = Graha(active.lord_index)
        except ValueError:
            break
        kp = annotations.get(graha)
        if kp is None:
            if graha not in cd.planets:
                break
            chain = lord_chain(cd.planets[graha].longitude)
            house = house_of(cd.planets[graha].longitude, cusp_longitudes(cd))
        else:
            chain, house = kp.chain, kp.house
        rows.append(KPDasaLevel(
            level=_LEVEL_NAMES[min(len(rows), len(_LEVEL_NAMES) - 1)],
            graha=graha,
            start_jd=active.start_jd,
            end_jd=active.end_jd,
            house=house,
            chain=chain,
        ))
        nodes = active.sub_periods or []
    return rows


def _target_jd(cd: ChartData, when) -> float:
    """Julian day (UT) for a local date/datetime; now when ``when`` is None."""
    import swisseph as swe

    from datetime import date as _date, datetime as _datetime, timedelta

    if when is None:
        now = _datetime.now()
    elif isinstance(when, _datetime):
        now = when
    elif isinstance(when, _date):
        now = _datetime(when.year, when.month, when.day, 12, 0)
    else:
        raise TypeError("when must be a date/datetime or None")
    offset = ChartBuilder._parse_tz(cd.timezone, cd.birth_date)
    utc = now + timedelta(hours=offset)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )
