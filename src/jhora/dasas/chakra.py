"""Chakra Dasa — Parasara's time-of-day rasi dasa (120 years).

Canonical mainstream form (spec gate 1.3): the PVR Kaala/Chakra paper
computation, golden-tested against the paper's Rajiv Gandhi (dawn start)
and Kennedy (daytime start) tables:

- the birth part of day comes from the same sunrise/sunset geometry as
  Kaala dasa (see ``kaala.day_parts``);
- dawn or dusk birth: dasas start from the sign after lagna;
  daytime birth: from the sign containing the lagna lord;
  nighttime birth: from the sign containing lagna;
- twelve Mahadashas run zodiacally at ten years each (120 total);
- antardasas split each parent into twelve equal children starting
  from the parent sign — the shared rasi-dasa default (also the
  mirrored implementation's convention; the paper does not specify
  sub-periods, so this is documented convention, not canon).

Needs birth latitude/longitude/timezone in the chart dict
(``lat``/``lon``/``tz``); raises ValueError otherwise.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from jhora.calc.muhurta import sunrise_sunset_hours
from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.dasas.jaimini_common import (
    normalize_planets,
    planet_signs,
    stronger_lord,
)
from jhora.dasas.kaala import _tz_east, day_parts, kaala_fraction
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


class ChakraDasa(DasaBase):
    """Twelve ten-year rasi dasas from the time-of-day seed."""

    system_name = "chakra"

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
                "Chakra dasa needs birth latitude/longitude/timezone "
                "in the chart dict (keys 'lat'/'lon'/'tz')")
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = (opts.subdivision_level if opts.include_subperiods
                     else PeriodLevel.MAHADASA)
        wall_jd = birth_jd + tz_east / 24.0
        base = datetime(2000, 1, 1)
        wall = base + timedelta(days=wall_jd - 2451544.5)
        date = datetime(wall.year, wall.month, wall.day)
        wall_hour = wall.hour + wall.minute / 60.0 + wall.second / 3600.0
        part, _frac = kaala_fraction(
            wall_hour, day_parts(date, lat, lon, tz_east))
        lagna = int(chart["lagna_lon"] // 30) % 12
        if part in ("dawn", "dusk"):
            seed = (lagna + 1) % 12
        elif part == "day":
            planet_sigs = planet_signs(
                normalize_planets(chart.get("planets", {})))
            lord = stronger_lord(lagna, planet_sigs)
            seed = planet_sigs.get(lord, lagna)
        else:
            seed = lagna
        periods = []
        cursor = birth_jd
        for k in range(12):
            sign = (seed + k) % 12
            dur_days = 10.0 * y_per_d
            md = DasaPeriod(
                lord_index=100 + sign,
                lord_name=Rasi(sign).full_name,
                start_jd=cursor,
                end_jd=cursor + dur_days,
                duration_years=10.0,
                level=PeriodLevel.MAHADASA,
            )
            if max_level.value >= PeriodLevel.ANTARDASA.value:
                order_signs = [(sign + j) % 12 for j in range(12)]
                ratios = [10.0] * 12
                names = {j: Rasi(s).full_name for j, s in enumerate(order_signs)}
                md.sub_periods = _subdivide(
                    md, ratios, y_per_d, 1, max_level, names,
                    [100 + s for s in order_signs])
            periods.append(md)
            cursor += dur_days
        return periods
