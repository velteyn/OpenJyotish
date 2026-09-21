"""Yoga / Nakshatra return (pravesha) charts for year/month-ahead work.

Companions to ``tithi_pravesha.py`` (same search-and-cast machinery):

- Yoga Pravesha — annual: the moment (Sun + Moon) longitude returns to
  its natal value near the birthday. Read with Yoga Vimsottari.
- Nakshatra Pravesha — monthly: the moment the Moon returns to its
  natal sidereal longitude. Read with standard natal methods
  (Vimsottari from the Moon applies naturally).

Karana Pravesha has no canonical standalone definition in the
mainstream sources (its dasa, Karana Chaturaseeti, is prescribed for
Tithi/Karana Pravesha charts — in practice the Tithi Pravesha chart,
whose exact elongation match implies the karana match). No finder is
shipped rather than an invented one; the Karana dasa engine works on
any chart's karana.
"""

from dataclasses import dataclass
from typing import List, Optional

import swisseph as swe

from jhora.calc.tithi_pravesha import (
    _angle_diff,
    _from_jd,
    _jd_str,
)
from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha


def _sid_lon(jd: float, planet_id: int, ayanamsa: str) -> float:
    """Sidereal longitude matching the natal chart's ayanamsa.

    Absolute return charts (yoga angle, Moon longitude) must scan in
    the same sidereal frame as the chart — unlike tithi angles, they
    are NOT ayanamsa-invariant.
    """
    from jhora.ephemeris.swe import SweEngine
    eng = SweEngine()
    eng.set_sidereal_mode(ayanamsa or "lahiri")
    return eng.calc_planet(planet_id, jd).longitude % 360.0


@dataclass
class PraveshaEntry:
    kind: str
    year: int
    event_date: str
    julian_day: float
    target_angle: float
    chart: Optional[ChartData] = None


def yoga_angle(sun_lon: float, moon_lon: float) -> float:
    """Yoga point: (Sun + Moon) longitude, 0-360."""
    return (sun_lon + moon_lon) % 360.0


def _wall_ymdh(best_jd: float, tz: str) -> tuple:
    """Local wall-clock y/m/d/h for a JD (revjul returns UT)."""
    from jhora.charts.chart import ChartBuilder
    tz_east = -ChartBuilder._parse_tz(tz)
    y, m, d, h = swe.revjul(best_jd + tz_east / 24.0)
    return int(y), int(m), int(d), float(h)


def _scan(jd_start: float, jd_end: float, target: float, angle_fn,
          step: float, tol: float) -> Optional[float]:
    """Brute-force scan for an angle recurrence, finest match wins."""
    best_jd, best_diff = None, float("inf")
    jd = jd_start
    while jd < jd_end:
        diff = _angle_diff(angle_fn(jd), target)
        if diff < best_diff:
            best_diff, best_jd = diff, jd
        if diff < tol:
            break
        jd += step
    return best_jd


class YogaPraveshaCalculator:
    """Annual Yoga Pravesha charts for a natal chart."""

    def __init__(self, natal_chart: ChartData):
        self.natal = natal_chart
        self.natal_yoga = yoga_angle(
            natal_chart.planet(Graha.SUN).longitude,
            natal_chart.planet(Graha.MOON).longitude)
        self.builder = ChartBuilder()
        self.birth_year = natal_chart.birth_date.year

    def compute(self, target_year: int, lat: float = None,
                lon: float = None, tz: str = None) -> PraveshaEntry:
        from jhora.ephemeris.swe import SE_MOON, SE_SUN
        ayanamsa = self.natal.ayanamsa_name
        lat = lat if lat is not None else self.natal.latitude
        lon = lon if lon is not None else self.natal.longitude
        tz = tz if tz is not None else self.natal.timezone
        bd = self.natal.birth_date
        jd_start = swe.julday(target_year, bd.month, bd.day - 15, 0.0,
                              swe.GREG_CAL)
        jd_end = swe.julday(target_year, bd.month, bd.day + 15, 0.0,
                            swe.GREG_CAL)

        def _ya(jd: float) -> float:
            return yoga_angle(_sid_lon(jd, SE_SUN, ayanamsa),
                              _sid_lon(jd, SE_MOON, ayanamsa))

        best_jd = _scan(jd_start, jd_end, self.natal_yoga, _ya,
                        step=0.01, tol=0.1)
        y, m, d, h = _wall_ymdh(best_jd, tz)
        try:
            chart = self.builder.build(
                year=y, month=m, day=d, hour=h,
                lat=lat, lon=lon, tz=tz)
        except Exception:
            chart = None
        return PraveshaEntry(
            kind="yoga", year=target_year, event_date=_jd_str(best_jd),
            julian_day=best_jd, target_angle=self.natal_yoga, chart=chart)

    def compute_range(self, start_year: int, end_year: int,
                      lat: float = None, lon: float = None,
                      tz: str = None) -> List[PraveshaEntry]:
        """Yoga Pravesha charts for a range of years."""
        return [self.compute(y, lat, lon, tz)
                for y in range(start_year, end_year + 1)]


class NakshatraPraveshaCalculator:
    """Monthly Nakshatra Pravesha charts (lunar return to natal Moon)."""

    def __init__(self, natal_chart: ChartData):
        self.natal = natal_chart
        self.natal_moon = natal_chart.planet(Graha.MOON).longitude
        self.builder = ChartBuilder()

    def compute(self, year: int, month: int, lat: float = None,
                lon: float = None, tz: str = None) -> PraveshaEntry:
        """Moon's return to its natal longitude within a calendar month."""
        from jhora.ephemeris.swe import SE_MOON
        ayanamsa = self.natal.ayanamsa_name
        lat = lat if lat is not None else self.natal.latitude
        lon = lon if lon is not None else self.natal.longitude
        tz = tz if tz is not None else self.natal.timezone
        jd_start = swe.julday(year, month, 1, 0.0, swe.GREG_CAL)
        if month < 12:
            jd_end = swe.julday(year, month + 1, 1, 0.0, swe.GREG_CAL)
        else:
            jd_end = swe.julday(year + 1, 1, 1, 0.0, swe.GREG_CAL)

        def _ml(jd: float) -> float:
            return _sid_lon(jd, SE_MOON, ayanamsa)

        best_jd = _scan(jd_start, jd_end, self.natal_moon, _ml,
                        step=0.005, tol=0.05)
        y, m, d, h = _wall_ymdh(best_jd, tz)
        try:
            chart = self.builder.build(
                year=y, month=m, day=d, hour=h,
                lat=lat, lon=lon, tz=tz)
        except Exception:
            chart = None
        return PraveshaEntry(
            kind="nakshatra", year=year, event_date=_jd_str(best_jd),
            julian_day=best_jd, target_angle=self.natal_moon, chart=chart)
