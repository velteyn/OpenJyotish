"""Ephemeris viewer — daily planet positions for any date range."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import swisseph as swe

from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra

_PLANETS = [
    (Graha.SUN, swe.SUN),
    (Graha.MOON, swe.MOON),
    (Graha.MARS, swe.MARS),
    (Graha.MERCURY, swe.MERCURY),
    (Graha.JUPITER, swe.JUPITER),
    (Graha.VENUS, swe.VENUS),
    (Graha.SATURN, swe.SATURN),
    (Graha.RAHU, swe.MEAN_NODE),
    (Graha.KETU, -1),  # Ketu = Rahu + 180°
]


@dataclass
class EphemerisDay:
    date: datetime
    planets: dict  # Graha → (longitude, sign, nakshatra, pada, retrograde)


def _ketu_from_rahu(rahu_lon: float) -> float:
    return (rahu_lon + 180) % 360


def generate_ephemeris(start: datetime, end: datetime,
                       step_days: int = 7) -> List[EphemerisDay]:
    """Generate daily planet positions for a date range."""
    results = []
    current = start
    while current <= end:
        jd = swe.julday(current.year, current.month, current.day,
                        current.hour + current.minute / 60.0,
                        swe.GREG_CAL)
        planets = {}
        rahu_lon = None
        for graha, se_id in _PLANETS:
            if se_id == -1:
                if rahu_lon is not None:
                    lon = _ketu_from_rahu(rahu_lon)
                else:
                    continue
            else:
                result = swe.calc_ut(jd, se_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
                lon = result[0][0]
                speed = result[0][3]
                is_retro = speed < 0
                if graha == Graha.RAHU:
                    rahu_lon = lon
            r = Rasi.from_longitude(lon)
            n, pada = Nakshatra.from_longitude(lon)
            planets[graha] = {
                "longitude": lon,
                "sign": r.short_name,
                "sign_full": r.full_name,
                "nakshatra": n.name.replace("_", " ").title(),
                "pada": pada,
                "retrograde": is_retro if graha != Graha.RAHU and graha != Graha.KETU else True,
            }
        results.append(EphemerisDay(date=current, planets=planets))
        current += timedelta(days=step_days)
    return results
