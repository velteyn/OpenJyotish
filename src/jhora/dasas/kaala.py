"""Kaala Dasa — Parasara's time-of-day graha dasa (120 years).

Canonical mainstream form (spec gate 1.4): the PVR Kaala/Chakra paper
computation, golden-tested against the paper's own Rajiv Gandhi, Kennedy
and Reagan tables:

- the day divides into four parts from sunrise/sunset (single precise
  source): daybreak-to-sunset in sixths gives dawn + day + dusk;
  sunset-to-sunrise in sixths gives dusk + night + dawn;
- the fraction elapsed in the birth part sets F = fraction × 120;
  cycle 1 (Sun..Ketu, weights 1..9/45) spans F years, cycle 2 spans
  120 − F years — eighteen Mahadashas total;
- antardasas apply the same fraction recursively (two-phase rule):
  frac × parent then (1 − frac) × parent, each split 1..9 — eighteen
  children per level, the only structure-preserving extension of the
  paper (independently converged by the mirrored implementation).

Needs birth latitude/longitude/timezone in the chart dict
(``lat``/``lon``/``tz``) for the sunrise geometry; raises ValueError
otherwise.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from jhora.calc.muhurta import sunrise_sunset_hours
from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha

_PLANETS = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN,
            Graha.RAHU, Graha.KETU]
_WEIGHTS = list(range(1, 10))
_W_SUM = 45.0


def _tz_east(tz: str) -> float:
    """Signed hours EAST of UTC ("+0530" → +5.5)."""
    return -ChartBuilder._parse_tz(tz)


def day_parts(date: datetime, lat: float, lon: float,
              tz_east: float) -> List[Tuple[str, float, float]]:
    """Four labelled parts of the local day as (name, start_h, end_h).

    Dawn/day/dusk from today's sunrise→sunset sixths; dusk/night/dawn
    from surrounding sunsets/sunrises. Hours are local wall-clock.
    """
    prev_ss = sunrise_sunset_hours(
        date - timedelta(days=1), lat, lon, tz_east)[1]
    tsr, tss = sunrise_sunset_hours(date, lat, lon, tz_east)
    nsr = sunrise_sunset_hours(
        date + timedelta(days=1), lat, lon, tz_east)[0]
    day_sixth = (tss - tsr) / 6.0
    night_sixth = ((24.0 - prev_ss) + tsr) / 6.0
    dawn = (tsr - night_sixth, tsr + day_sixth)
    day = (dawn[1], tss - day_sixth)
    dusk = (day[1], tss + ((24.0 - tss) + nsr) / 6.0)
    night = (dusk[1], dawn[0] + 24.0)
    return [("dawn",) + dawn, ("day",) + day,
            ("dusk",) + dusk, ("night",) + night]


def kaala_fraction(wall_hour: float, parts: List[Tuple[str, float, float]]
                   ) -> Tuple[str, float]:
    """Day-part name + elapsed fraction for a birth wall-hour."""
    h = wall_hour % 24.0
    for name, start, end in parts:
        span = end - start
        if start <= h < end or (end > 24.0 and (h >= start or h < end - 24.0)):
            return name, (h - start) % 24.0 / span
    return "day", 0.0


class KaalaDasa(DasaBase):
    """Eighteen time-of-day Mahadashas (two Sun..Ketu cycles)."""

    system_name = "kaala"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        try:
            lat = float(chart["lat"])
            lon = float(chart["lon"])
            tz_east = _tz_east(str(chart["tz"]))
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "Kaala dasa needs birth latitude/longitude/timezone "
                "in the chart dict (keys 'lat'/'lon'/'tz')")
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = (opts.subdivision_level if opts.include_subperiods
                     else PeriodLevel.MAHADASA)
        wall_jd = birth_jd + tz_east / 24.0
        base = datetime(2000, 1, 1)
        wall = base + timedelta(days=wall_jd - 2451544.5)
        date = datetime(wall.year, wall.month, wall.day)
        wall_hour = wall.hour + wall.minute / 60.0 + wall.second / 3600.0
        _part, frac = kaala_fraction(
            wall_hour, day_parts(date, lat, lon, tz_east))
        self._frac = frac
        self._y_per_d = y_per_d
        self._max_level = max_level
        periods = []
        cursor = birth_jd
        for cycle_len in (frac * 120.0, (1.0 - frac) * 120.0):
            unit = cycle_len / _W_SUM
            for gi, graha in enumerate(_PLANETS):
                yrs = (gi + 1) * unit
                dur_days = yrs * y_per_d
                md = DasaPeriod(
                    lord_index=graha.value,
                    lord_name=graha.full_name,
                    start_jd=cursor,
                    end_jd=cursor + dur_days,
                    duration_years=yrs,
                    level=PeriodLevel.MAHADASA,
                )
                if max_level.value >= PeriodLevel.ANTARDASA.value:
                    md.sub_periods = self._children(
                        [graha.value], 1, cursor, yrs)
                periods.append(md)
                cursor += dur_days
        return periods

    def _children(self, prefix: List[int], depth: int,
                  start_jd: float, parent_years: float) -> List[DasaPeriod]:
        """Two-phase recursive subdivision (18 children per level)."""
        level_map = {1: PeriodLevel.ANTARDASA, 2: PeriodLevel.PRATYANTARDASA,
                     3: PeriodLevel.SUKSHMA, 4: PeriodLevel.PRANA,
                     5: PeriodLevel.DEHA}
        out = []
        cursor = start_jd
        for phase in (self._frac, 1.0 - self._frac):
            phase_years = phase * parent_years
            for gi, graha in enumerate(_PLANETS):
                yrs = (gi + 1) / _W_SUM * phase_years
                dur_days = yrs * self._y_per_d
                node = DasaPeriod(
                    lord_index=graha.value,
                    lord_name=graha.full_name,
                    start_jd=cursor,
                    end_jd=cursor + dur_days,
                    duration_years=yrs,
                    level=level_map.get(depth, PeriodLevel.ANTARDASA),
                )
                if depth < self._max_level.value:
                    node.sub_periods = self._children(
                        prefix + [graha.value], depth + 1,
                        cursor, yrs)
                out.append(node)
                cursor += dur_days
        return out
