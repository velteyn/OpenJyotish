"""Tithi Pravesha — annual ingress charts for year-ahead predictions.

When the Sun returns to the native's birth tithi each year, the chart cast at
that moment predicts the year ahead. This is the Vedic equivalent of the solar
return (Tajaka) but uses the tithi angle instead of exact solar degree.

Types:
  Tithi Pravesha — annual (Sun returns to natal tithi)
  Masa Pravesha  — monthly (Moon returns to natal tithi each month)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import swisseph as swe

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_EPHE_PATH = Path(__file__).resolve().parents[3] / "jhcore" / "ephe"
if _EPHE_PATH.exists():
    swe.set_ephe_path(str(_EPHE_PATH.resolve()))


@dataclass
class TithiPraveshaEntry:
    year: int
    event_date: str
    julian_day: float
    tithi_angle: float
    chart: Optional[ChartData] = None


def _tithi_angle(chart: ChartData) -> float:
    """Natal tithi angle: Moon - Sun longitude difference (0-360)."""
    moon = chart.planet(Graha.MOON).longitude
    sun = chart.planet(Graha.SUN).longitude
    return (moon - sun) % 360.0


def _jd_str(jd: float) -> str:
    y, m, d, h = swe.revjul(jd)
    mi = int((h - int(h)) * 60)
    return f"{int(y)}-{m:02d}-{int(d):02d} {int(h):02d}:{mi:02d} UT"


def _from_jd(jd: float) -> tuple:
    y, m, d, h = swe.revjul(jd)
    return int(y), m, int(d), h


def _sun_lon(jd: float) -> float:
    return swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]


def _moon_lon(jd: float) -> float:
    return swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]


def _moon_sun_angle(jd: float) -> float:
    """Moon - Sun angle (0-360) at a given JD."""
    return (_moon_lon(jd) - _sun_lon(jd)) % 360.0


class TithiPraveshaCalculator:
    """Compute annual Tithi Pravesha charts for a given birth chart."""

    def __init__(self, natal_chart: ChartData):
        self.natal = natal_chart
        self.natal_tithi = _tithi_angle(natal_chart)
        self.natal_sun = natal_chart.planet(Graha.SUN).longitude
        self.builder = ChartBuilder()
        self.birth_year = natal_chart.birth_date.year

    def compute(self, target_year: int,
                lat: float = None, lon: float = None, tz: str = None,
                ) -> TithiPraveshaEntry:
        """Compute Tithi Pravesha chart for a given target year."""
        lat = lat if lat is not None else self.natal.latitude
        lon = lon if lon is not None else self.natal.longitude
        tz = tz if tz is not None else self.natal.timezone

        # Search window: around the solar return (birthday)
        # Solar return happens near the birthday each year
        bd = self.natal.birth_date
        jd_start = swe.julday(target_year, bd.month, bd.day - 15, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(target_year, bd.month, bd.day + 15, 0.0, swe.GREG_CAL)

        # Find when Moon-Sun angle equals natal tithi angle
        best_jd = None
        best_diff = float("inf")
        step = 0.01  # ~15 minutes in days

        jd = jd_start
        while jd < jd_end:
            angle = _moon_sun_angle(jd)
            diff = _angle_diff(angle, self.natal_tithi)
            if diff < best_diff:
                best_diff = diff
                best_jd = jd
            # If within 0.1°, we're close enough
            if diff < 0.1:
                break
            jd += step

        if best_jd is None:
            # Fallback: binary search for exact match
            jd_lo, jd_hi = jd_start, jd_end
            for _ in range(50):
                jd_mid = (jd_lo + jd_hi) / 2
                angle = _moon_sun_angle(jd_mid)
                diff = _angle_diff(angle, self.natal_tithi)
                if diff < 0.01:
                    best_jd = jd_mid
                    break
                a_lo = _moon_sun_angle(jd_lo)
                if _crosses(a_lo, angle, self.natal_tithi):
                    jd_hi = jd_mid
                else:
                    jd_lo = jd_mid
            if best_jd is None:
                best_jd = jd_mid

        # Cast chart
        y, m, d, h = _from_jd(best_jd)
        try:
            chart = self.builder.build(
                year=y, month=m, day=d, hour=h,
                lat=lat, lon=lon, tz=tz,
            )
        except Exception:
            chart = None

        return TithiPraveshaEntry(
            year=target_year,
            event_date=_jd_str(best_jd),
            julian_day=best_jd,
            tithi_angle=self.natal_tithi,
            chart=chart,
        )

    def compute_range(self, start_year: int, end_year: int,
                      lat: float = None, lon: float = None, tz: str = None,
                      ) -> List[TithiPraveshaEntry]:
        """Compute Tithi Pravesha charts for a range of years."""
        return [self.compute(y, lat, lon, tz) for y in range(start_year, end_year + 1)]

    def masa_pravesha(self, year: int, month: int,
                      lat: float = None, lon: float = None, tz: str = None,
                      ) -> TithiPraveshaEntry:
        """Monthly Masa Pravesha: when Moon returns to natal tithi each month."""
        lat = lat if lat is not None else self.natal.latitude
        lon = lon if lon is not None else self.natal.longitude
        tz = tz if tz is not None else self.natal.timezone

        jd_start = swe.julday(year, month, 1, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(year, month + 1 if month < 12 else year + 1,
                            1 if month < 12 else 1, 0.0, swe.GREG_CAL)

        best_jd = None
        best_diff = float("inf")
        jd = jd_start
        while jd < jd_end:
            angle = _moon_sun_angle(jd)
            diff = _angle_diff(angle, self.natal_tithi)
            if diff < best_diff:
                best_diff = diff
                best_jd = jd
            if diff < 0.05:
                break
            jd += 0.0005  # ~40 seconds

        y, m, d, h = _from_jd(best_jd)
        try:
            chart = self.builder.build(year=y, month=m, day=d, hour=h,
                                       lat=lat, lon=lon, tz=tz)
        except Exception:
            chart = None

        return TithiPraveshaEntry(
            year=year,
            event_date=_jd_str(best_jd),
            julian_day=best_jd,
            tithi_angle=self.natal_tithi,
            chart=chart,
        )


def _angle_diff(a: float, b: float) -> float:
    """Smallest angular difference between two angles in degrees."""
    return abs(((a - b + 180) % 360) - 180)


def _crosses(a1: float, a2: float, target: float) -> bool:
    """Check if the angle moves across the target between a1 and a2."""
    d1 = _angle_diff(a1, target)
    d2 = _angle_diff(a2, target)
    # Crosses if on opposite sides of target
    return ((a1 - target) % 360) * ((a2 - target) % 360) < 180 * 180 < 1
