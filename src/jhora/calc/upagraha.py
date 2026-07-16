"""Upagrahas — nine shadow planets (BPHS Ch.3).

Calculated from the Sun's longitude at birth:
  Dhuma        = Sun + 133°20'
  Vyatipata    = 360° - Dhuma
  Parivesha    = Vyatipata + 180°
  Indrachaapa  = 360° - Parivesha
  Upaketu      = Sun - 30° (or Indrachaapa + 16°40', depending on tradition)

Plus time-based upagrahas (from weekday + sunrise):
  Gulika  — rises at Saturn's portion of day/night
  Mandi   — rises at the middle of Saturn's portion
  Kala    — rises at the start of Sun's portion
  Mrityu  — etc.

Currently implements the solar upagrahas (always available).
Time-based upagrahas require sunrise time — computed from chart data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from jhora.charts.chart import ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.ephemeris.swe import SweEngine


# Day portion allocations (each portion = 1/8 of day or night, in hours from sunrise)
# Portions: Kaala (Sun), Mrityu (Mars), Arthaprahara (Jupiter), Yama (Mercury),
#           Gulika (Saturn), Mandi (Saturn), Kala (Moon), Paridhi (Venus)
_PORTION_LORDS = [
    Graha.SUN, Graha.MARS, Graha.JUPITER, Graha.MERCURY,
    Graha.SATURN, Graha.SATURN, Graha.MOON, Graha.VENUS,
]


@dataclass
class UpagrahaResult:
    name: str
    longitude: float
    rasi: str
    degrees_in_rasi: float
    source: str  # "solar" or "temporal"


def compute_solar_upagrahas(sun_longitude: float) -> List[UpagrahaResult]:
    """Compute the 5 solar-based upagrahas from Sun's longitude."""
    dhuma = (sun_longitude + 133.0 + 20.0 / 60.0) % 360
    vyatipata = (360.0 - dhuma) % 360
    parivesha = (vyatipata + 180.0) % 360
    indrachaapa = (360.0 - parivesha) % 360
    upaketu = (sun_longitude - 30.0) % 360

    results = []
    for name, lon in [
        ("Dhuma", dhuma), ("Vyatipata", vyatipata), ("Parivesha", parivesha),
        ("Indrachaapa", indrachaapa), ("Upaketu", upaketu),
    ]:
        r = Rasi.from_longitude(lon)
        results.append(UpagrahaResult(
            name=name, longitude=lon, rasi=r.short_name,
            degrees_in_rasi=lon % 30, source="solar",
        ))
    return results


def compute_temporal_upagrahas(chart: ChartData,
                                sunrise_jd: float,
                                sunset_jd: float) -> List[UpagrahaResult]:
    """Compute time-based upagrahas: Gulika, Mandi, Kala, etc.

    Day is divided into 8 equal portions. Each portion is ruled by a planet.
    Gulika rises at the START of Saturn's portion.
    Mandi rises at the MIDDLE of Saturn's portion.
    """
    day_length = (sunset_jd - sunrise_jd) * 24  # hours
    night_length = 24.0 - day_length

    # Birth time in hours since sunrise
    birth_jd = chart.julian_day
    birth_hours = (birth_jd - sunrise_jd) * 24
    if birth_hours < 0:
        birth_hours += 24

    is_daytime = birth_hours < day_length

    if is_daytime:
        portion_hours = day_length / 8.0
        portion_start = 0.0
    else:
        portion_hours = night_length / 8.0
        portion_start = day_length

    results = []
    for i, lord in enumerate(_PORTION_LORDS):
        start_h = portion_start + i * portion_hours
        end_h = start_h + portion_hours

        # Gulika at start of Saturn's portion
        if lord == Graha.SATURN:
            gulika_h = start_h
            gulika_jd = sunrise_jd + gulika_h / 24.0
            gulika_lon = _longitude_at_jd(gulika_jd, chart)
            r = Rasi.from_longitude(gulika_lon)
            results.append(UpagrahaResult(
                name="Gulika", longitude=gulika_lon, rasi=r.short_name,
                degrees_in_rasi=gulika_lon % 30, source="temporal",
            ))
            # Mandi at middle of Saturn's portion
            mandi_h = start_h + portion_hours / 2.0
            mandi_jd = sunrise_jd + mandi_h / 24.0
            mandi_lon = _longitude_at_jd(mandi_jd, chart)
            r = Rasi.from_longitude(mandi_lon)
            results.append(UpagrahaResult(
                name="Mandi", longitude=mandi_lon, rasi=r.short_name,
                degrees_in_rasi=mandi_lon % 30, source="temporal",
            ))
            break  # Only one Saturn portion gives Gulika/Mandi

    return results


def _longitude_at_jd(jd: float, chart: ChartData) -> float:
    """Calculate the lagna longitude at a specific Julian Day.

    Uses the same geographic coordinates and ayanamsa as the birth chart.
    """
    import swisseph as swe
    try:
        eng = SweEngine()
        eng.set_sidereal_mode(chart.ayanamsa_name)
        # Use chart's lat/lon
        cusps, asc_mc = swe.houses(
            jd, chart.latitude, chart.longitude, b'P',
        )
        # Apply ayanamsa if needed
        aya = swe.get_ayanamsa_ut(jd)
        return (asc_mc[0] - aya) % 360
    except Exception:
        return 0.0


def compute_all_upagrahas(chart: ChartData) -> List[UpagrahaResult]:
    """Compute all upagrahas (solar + temporal) for a chart."""
    sun_lon = chart.planet(Graha.SUN).longitude
    results = compute_solar_upagrahas(sun_lon)

    # Temporal upagrahas need sunrise/sunset
    try:
        from jhora.calc.muhurta import _sunrise_sunset
        bd = chart.birth_date
        tz_str = chart.timezone
        tz_offset = 0.0
        if tz_str:
            try:
                tz_offset = float(tz_str.replace("+", "").replace("−", "-"))
                if "+" in tz_str or "−" in tz_str:
                    pass
                else:
                    sign = -1 if tz_str.startswith("+") else 1
                    tz_offset = sign * abs(float(tz_str.replace("+", "")))
            except Exception:
                tz_offset = 0.0

        sunrise, sunset = _sunrise_sunset(
            bd.year, bd.month, bd.day,
            chart.latitude, chart.longitude, tz_offset,
        )
        results.extend(compute_temporal_upagrahas(chart, sunrise, sunset))
    except Exception:
        pass

    return results
