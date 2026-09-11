"""Special lagnas: Bhrigu Bindu, Indu, Varnada, Pranapada, Vighati, Bhava,
Hora, Ghati, Sree, Upapada, and User's Special Lagna.

These are mathematical points used in various Vedic predictive techniques.
The Bhava/Hora/Ghati lagnas are seeded by the Sun's longitude at sunrise and
advance since sunrise; Sree Lagna combines lagna with the Moon's nakshatra
fraction; Upapada is the arudha pada of the 12th house. The User's Special
Lagna is configurable: choose a planet, a speed factor n, and optionally
reverse direction (for Rahu/Ketu).  Displayed as e.g. "Ju9" in charts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

from jhora.charts.chart import ChartData, ChartBuilder
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.calc.muhurta import sunrise_sunset_hours

# Graha → Swiss Ephemeris body ID (used by swe.rise_trans / calc_planet)
_PLANET_BODY_MAP: Dict[Graha, int] = {
    Graha.SUN:     0,
    Graha.MOON:    1,
    Graha.MARS:    2,
    Graha.MERCURY: 3,
    Graha.JUPITER: 4,
    Graha.VENUS:   5,
    Graha.SATURN:  6,
    Graha.RAHU:    10,   # swe.TRUE_NODE
    Graha.KETU:    11,   # swe.OSCU_APOG
}

_PLANET_ABBREV: Dict[Graha, str] = {
    Graha.SUN:     "Su",
    Graha.MOON:    "Mo",
    Graha.MARS:    "Ma",
    Graha.MERCURY: "Me",
    Graha.JUPITER: "Ju",
    Graha.VENUS:   "Ve",
    Graha.SATURN:  "Sa",
    Graha.RAHU:    "Ra",
    Graha.KETU:    "Ke",
}


@dataclass
class SpecialLagna:
    name: str
    longitude: float
    sign: str
    description: str


@dataclass
class UserSpecialLagnaConfig:
    planet: Graha
    speed_factor: float
    reverse: bool = False


# KP Vimsottari sub-lord proportions (planet: fraction of nakshatra)
_KP_SUB_PROPORTIONS = {
    Graha.KETU:     7 / 120,
    Graha.VENUS:   20 / 120,
    Graha.SUN:      6 / 120,
    Graha.MOON:    10 / 120,
    Graha.MARS:     7 / 120,
    Graha.RAHU:    18 / 120,
    Graha.JUPITER: 16 / 120,
    Graha.SATURN:  19 / 120,
    Graha.MERCURY: 17 / 120,
}

_KP_ORDER = [Graha.KETU, Graha.VENUS, Graha.SUN, Graha.MOON, Graha.MARS,
             Graha.RAHU, Graha.JUPITER, Graha.SATURN, Graha.MERCURY]


def bhrigu_bindu(cd: ChartData) -> float:
    """Bhrigu Bindu: midpoint of Rahu and Moon longitudes."""
    rahu = cd.planet(Graha.RAHU).longitude
    moon = cd.planet(Graha.MOON).longitude
    diff = (moon - rahu + 360) % 360
    if diff > 180:
        mid = (rahu + moon + 360) / 2
    else:
        mid = (rahu + moon) / 2
    return mid % 360


def indu_lagna(cd: ChartData) -> float:
    """Indu Lagna (financial prosperity point): 9th from Moon in its own sign."""
    moon = cd.planet(Graha.MOON).longitude
    moon_rasi = int(moon / 30)
    # 9th house from Moon = moon_rasi + 8 signs
    ninth_rasi = (moon_rasi + 8) % 12
    # Degrees within that sign = Moon's degrees_in_rasi
    moon_deg = moon % 30
    return (ninth_rasi * 30 + moon_deg) % 360


def varnada_lagna(cd: ChartData) -> float:
    """Varnada Lagna: based on lagna + Hora Lagna signs."""
    lagna = cd.ascendant
    lagna_rasi = int(lagna / 30)
    if cd.hora_lagna:
        hl_rasi = int(cd.hora_lagna.longitude / 30)
    else:
        # Approximate: Hora lagna = Sun's sign for day, Moon's for night
        sun_lon = cd.planet(Graha.SUN).longitude
        hl_rasi = int(sun_lon / 30)
    varnada = (lagna_rasi + hl_rasi) % 12
    if varnada == 0:
        varnada = 12
    # Degree = remainder of lagna degrees in sign
    return (varnada * 30 + (lagna % 30) / 30) % 360


def _sunrise_local_hours(cd: ChartData) -> float:
    """Sunrise as local decimal hours via the single precise source."""
    tz_east = -ChartBuilder._parse_tz(cd.timezone)
    sr, _ss = sunrise_sunset_hours(cd.birth_date, cd.latitude,
                                   cd.longitude, tz_east)
    return sr


def pranapada_lagna(cd: ChartData) -> float:
    """Pranapada Lagna: based on birth time in ghatis."""
    # Birth time in hours from midnight (true local time; birth_date is
    # date-only by design, the exact moment lives in the Julian day).
    birth_hours = cd.time_of_day_hours
    sunrise = _sunrise_local_hours(cd)
    # Time from sunrise in ghatis (1 ghati = 24 minutes)
    from_sunrise = (birth_hours - sunrise + 24) % 24
    ghatis = from_sunrise / 0.4
    return (cd.planet(Graha.SUN).longitude + ghatis * 6.0) % 360


def vighati_lagna(cd: ChartData) -> float:
    """Vighati Lagna: finer time division."""
    birth_hours = cd.time_of_day_hours
    sunrise = _sunrise_local_hours(cd)
    from_sunrise = (birth_hours - sunrise + 24) % 24
    vighatis = from_sunrise * 60  # 1 vighati = 24 seconds
    return (cd.planet(Graha.SUN).longitude + vighatis * 0.1) % 360


# ── Sunrise-based special lagnas (Bhava / Hora / Ghati) ─────────────────────

# Seeded by Sun's longitude at sunrise, advancing since sunrise.
# Rates (per P.V.R. Narasimha Rao, "Vedic Astrology: An Integrated Approach"):
#   Bhava Lagna (BL): 1°  per 4 min  (1 rasi / 2 hr = 15°/hr)
#   Hora  Lagna (HL): 1°  per 2 min  (1 rasi / 1 hr = 30°/hr)
#   Ghati Lagna (GL): 1°15' per min  (1 rasi / 24 min)
_DEG_PER_MIN = {
    "bhava": 1.0 / 4.0,
    "hora":  1.0 / 2.0,
    "ghati": 5.0 / 4.0,
}


def _chart_swe(cd: ChartData):
    from jhora.ephemeris.swe import SweEngine
    engine = SweEngine()
    engine.set_sidereal_mode(cd.ayanamsa_name)
    return engine


def _local_date(cd: ChartData):
    """Return (year, month, day) of the birth's LOCAL calendar date."""
    from datetime import datetime as _dt, timedelta as _td
    from jhora.charts.chart import ChartBuilder
    tz = ChartBuilder._parse_tz(cd.timezone)
    y, m, d, ut_hour = _chart_swe(cd).revjul(cd.julian_day)
    # local time = UT - tz_offset hours
    ut = _dt(int(y), int(m), int(d)) + _td(hours=ut_hour)
    local = ut - _td(hours=tz)
    return local.year, local.month, local.day


def _sunrise_jd(cd: ChartData) -> Optional[float]:
    """JD (UT) of sunrise on the birth's local calendar date."""
    from jhora.ephemeris.swe import SE_SUN
    from jhora.charts.chart import ChartBuilder
    tz = ChartBuilder._parse_tz(cd.timezone)
    swe = _chart_swe(cd)
    y, m, d = _local_date(cd)
    jd_start = swe.julday(y, m, d, 0.1667 + tz)  # local ~00:10 onwards
    return swe.rise_trans(jd_start, SE_SUN, cd.latitude, cd.longitude, rise=True)


def _sun_at_sunrise(cd: ChartData) -> Optional[float]:
    """Sun's sidereal longitude at the sunrise of the birth's local date."""
    from jhora.ephemeris.swe import SE_SUN
    sr = _sunrise_jd(cd)
    if sr is None:
        return None
    return _chart_swe(cd).calc_planet(SE_SUN, sr).longitude % 360.0


def _minutes_since_sunrise(cd: ChartData) -> Optional[float]:
    sr = _sunrise_jd(cd)
    if sr is None:
        return None
    return (cd.julian_day - sr) * 1440.0


# ── User's Special Lagna ─────────────────────────────────────────────────────

def _planet_rise(cd: ChartData, planet: Graha) -> Tuple[Optional[float], Optional[float]]:
    """Return (longitude_at_rise, rise_jd) for *planet* on the birth's local date.

    For Ketu, uses Rahu's rise and adds 180° to Rahu's longitude at that time.
    """
    from jhora.charts.chart import ChartBuilder
    swe = _chart_swe(cd)
    y, m, d = _local_date(cd)
    tz_offset = ChartBuilder._parse_tz(cd.timezone)
    jd_start = swe.julday(y, m, d, 0.1667 + tz_offset)

    if planet == Graha.KETU:
        # Ketu is opposite Rahu — use Rahu's rise, add 180°
        body_id = _PLANET_BODY_MAP[Graha.RAHU]
        rise_jd = swe.rise_trans(jd_start, body_id, cd.latitude, cd.longitude, rise=True)
        if rise_jd is None:
            return None, None
        rahu_lon = swe.calc_planet(body_id, rise_jd).longitude
        ketu_lon = (rahu_lon + 180.0) % 360.0
        return ketu_lon, rise_jd

    body_id = _PLANET_BODY_MAP[planet]
    rise_jd = swe.rise_trans(jd_start, body_id, cd.latitude, cd.longitude, rise=True)
    if rise_jd is None:
        return None, None
    lon = swe.calc_planet(body_id, rise_jd).longitude
    return lon, rise_jd


def user_special_lagna(cd: ChartData, planet: Graha, speed_factor: float,
                       reverse: bool = False) -> Optional[float]:
    """Compute User's Special Lagna (USL).

    Base = planet's longitude at its rising on the birth date.
    Rate = speed_factor × 15°/hr  (= speed_factor × 0.25°/min).
    If reverse is True the rate is negated (for Rahu/Ketu).
    """
    base, rise_jd = _planet_rise(cd, planet)
    if base is None or rise_jd is None:
        return None
    deg_per_min = speed_factor * 15.0 / 60.0
    if reverse:
        deg_per_min = -deg_per_min
    minutes_since = (cd.julian_day - rise_jd) * 1440.0
    return (base + minutes_since * deg_per_min) % 360.0


def user_special_lagna_name(config: UserSpecialLagnaConfig) -> str:
    """Display name for a USL config, e.g. 'Ju9' or 'Ra3R'."""
    abbrev = _PLANET_ABBREV[config.planet]
    if config.speed_factor == int(config.speed_factor):
        factor_str = str(int(config.speed_factor))
    else:
        factor_str = f"{config.speed_factor:.1f}"
    suffix = "R" if config.reverse else ""
    return f"{abbrev}{factor_str}{suffix}"


def bhava_lagna(cd: ChartData) -> Optional[float]:
    """Bhava Lagna (BL): Sun at sunrise advanced 1° per 4 minutes."""
    base = _sun_at_sunrise(cd)
    minutes = _minutes_since_sunrise(cd)
    if base is None or minutes is None:
        return None
    return (base + minutes * _DEG_PER_MIN["bhava"]) % 360.0


def hora_lagna(cd: ChartData) -> Optional[float]:
    """Hora Lagna (HL): Sun at sunrise advanced 1° per 2 minutes."""
    base = _sun_at_sunrise(cd)
    minutes = _minutes_since_sunrise(cd)
    if base is None or minutes is None:
        return None
    return (base + minutes * _DEG_PER_MIN["hora"]) % 360.0


def ghati_lagna(cd: ChartData) -> Optional[float]:
    """Ghati/Ghatika Lagna (GL): Sun at sunrise advanced 1°15' per minute."""
    base = _sun_at_sunrise(cd)
    minutes = _minutes_since_sunrise(cd)
    if base is None or minutes is None:
        return None
    return (base + minutes * _DEG_PER_MIN["ghati"]) % 360.0


def sree_lagna(cd: ChartData) -> float:
    """Sree Lagna (SL): lagna + Moon's traversed fraction of its nakshatra × 360°.

    Moon's advancement within its nakshatra, expressed as a fraction of the
    whole zodiac, added to the lagna. (Verified against the SN Rao worked
    example: Moon 15°29' Leo, lagna 14°19' Scorpio -> SL 12°23' Capricorn.)
    """
    from jhora.types.nakshatra import Nakshatra
    moon_lon = cd.planet(Graha.MOON).longitude
    lagna_lon = cd.ascendant
    nakshatra, _pada = Nakshatra.from_longitude(moon_lon)
    start = nakshatra.start_longitude
    span = nakshatra.span
    fraction_in_nakshatra = ((moon_lon - start) % span) / span
    return (lagna_lon + fraction_in_nakshatra * 360.0) % 360.0


def upapada_lagna(cd: ChartData) -> int:
    """Upapada Lagna/sign: Arudha Pada of the 12th house from lagna."""
    from jhora.calc.arudha import bhava_arudha
    planets = {g: {"longitude": cd.planet(g).longitude} for g in cd.planets}
    return int(bhava_arudha(12, cd.ascendant, planets))


def compute_time_lagnas(cd: ChartData) -> Dict:
    """Return dict of the sunrise-based + derived special lagnas.

    Keys: 'bhava', 'hora', 'ghati', 'sree', 'upapada'.
    Positions may be None when ephemeris sunrise cannot be determined.
    """
    return {
        "bhava": bhava_lagna(cd),
        "hora": hora_lagna(cd),
        "ghati": ghati_lagna(cd),
        "sree": sree_lagna(cd),
        "upapada": upapada_lagna(cd),
    }


def compute_special_lagnas(cd: ChartData) -> list:
    """Compute all special lagnas for a chart."""
    results = []
    for name, func, desc in [
        ("Bhrigu Bindu", bhrigu_bindu, "Midpoint of Rahu and Moon — destiny point"),
        ("Indu Lagna", indu_lagna, "Financial prosperity point (9th from Moon)"),
        ("Varnada Lagna", varnada_lagna, "Social standing point"),
        ("Pranapada Lagna", pranapada_lagna, "Life force indicator"),
        ("Vighati Lagna", vighati_lagna, "Fine time indicator"),
    ]:
        lon = func(cd)
        r = Rasi.from_longitude(lon)
        results.append(SpecialLagna(
            name=name, longitude=lon, sign=r.short_name, description=desc,
        ))

    # Sunrise-based lagnas (Bhava / Hora / Ghati)
    for name, lon, desc in [
        ("Bhava Lagna", bhava_lagna(cd), "House-based lagna (self, 15°/hr from sunrise)"),
        ("Hora Lagna", hora_lagna(cd), "Wealth/time lagna (30°/hr from sunrise)"),
        ("Ghati Lagna", ghati_lagna(cd), "Power/fame lagna (30°/24min from sunrise)"),
    ]:
        if lon is not None:
            r = Rasi.from_longitude(lon)
            results.append(SpecialLagna(
                name=name, longitude=lon, sign=r.short_name, description=desc,
            ))

    # Sree Lagna (longitude)
    sl = sree_lagna(cd)
    results.append(SpecialLagna(
        "Sree Lagna", sl, Rasi.from_longitude(sl).short_name,
        "Prosperity lagna (lagna + Moon's nakshatra fraction)",
    ))

    # Upapada Lagna (rasi-based — a sign, not a point)
    ul = upapada_lagna(cd)
    ul_rasi = Rasi(ul)
    results.append(SpecialLagna(
        "Upapada Lagna", ul * 30.0, ul_rasi.short_name,
        "Arudha pada of the 12th house (marriage/success)",
    ))
    return results


# ── KP Sub-lords ──────────────────────────────────────────────────────────────

def kp_sublord(longitude: float, level: int = 1) -> list:
    """Find the KP sub-lord(s) for a given longitude at specified depth.

    Level 1 = sub-lord, 2 = sub-sub-lord, up to 5.
    Returns list of (Graha, span_start, span_end).
    """
    nakshatra_span = 13.333333  # 13°20'
    nakshatra_index = int(longitude / nakshatra_span)
    start = nakshatra_index * nakshatra_span
    span = nakshatra_span

    results = []
    current = longitude - start
    current_start = start

    for lvl in range(level):
        cumulative = 0.0
        for g in _KP_ORDER:
            sub_width = span * _KP_SUB_PROPORTIONS[g]
            if cumulative + sub_width >= current:
                results.append({
                    "graha": g,
                    "name": g.full_name,
                    "start": current_start + cumulative,
                    "end": current_start + cumulative + sub_width,
                    "level": lvl + 1,
                })
                current = current - cumulative
                span = sub_width
                current_start = current_start + cumulative
                break
            cumulative += sub_width

    return results


def kp_sublord_string(longitude: float, level: int = 3) -> str:
    """Human-readable KP sub-lord chain (e.g. 'Moon-Rahu-Jupiter')."""
    subs = kp_sublord(longitude, level)
    return "-".join(s["name"] for s in subs)
