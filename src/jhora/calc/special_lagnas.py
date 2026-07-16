"""Special lagnas: Bhrigu Bindu, Indu Lagna, Varnada, Pranapada, Vighati.

These are mathematical points used in various Vedic predictive techniques.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


@dataclass
class SpecialLagna:
    name: str
    longitude: float
    sign: str
    description: str


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


def pranapada_lagna(cd: ChartData) -> float:
    """Pranapada Lagna: based on birth time in ghatis."""
    bd = cd.birth_date
    # Birth time in hours from midnight
    birth_hours = bd.hour + bd.minute / 60.0 + bd.second / 3600.0
    sunrise = _sunrise_approx(cd)
    # Time from sunrise in ghatis (1 ghati = 24 minutes)
    from_sunrise = (birth_hours - sunrise + 24) % 24
    ghatis = from_sunrise / 0.4
    return (cd.planet(Graha.SUN).longitude + ghatis * 6.0) % 360


def vighati_lagna(cd: ChartData) -> float:
    """Vighati Lagna: finer time division."""
    bd = cd.birth_date
    birth_hours = bd.hour + bd.minute / 60.0 + bd.second / 3600.0
    sunrise = _sunrise_approx(cd)
    from_sunrise = (birth_hours - sunrise + 24) % 24
    vighatis = from_sunrise * 60  # 1 vighati = 24 seconds
    return (cd.planet(Graha.SUN).longitude + vighatis * 0.1) % 360


def _sunrise_approx(cd: ChartData) -> float:
    """Approximate sunrise hour (6 AM for simplicity)."""
    try:
        bd = cd.birth_date
        lat = cd.latitude
        if lat > 23.5 and bd.month in [6, 7]:
            return 5.0
        elif lat > 23.5 and bd.month in [12, 1]:
            return 7.0
        return 6.0
    except Exception:
        return 6.0


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
