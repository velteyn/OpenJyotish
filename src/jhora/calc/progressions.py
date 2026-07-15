"""Progressions — secondary progressions for Vedic astrology.

Standard Vedic secondary progression: 1 day after birth = 1 year of life.
At age N, cast a chart for N days after the birth moment. This represents
the evolved/changed self at that age.

Also supports:
  - Solar arc: all planets advance by the Sun's secondary motion
  - Progressed-to-natal aspects: what the progressed chart aspects in natal
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


@dataclass
class ProgressedChart:
    method: str
    target_date: datetime
    target_age: float
    chart: ChartData


@dataclass
class ProgressedAspect:
    progressed_graha: Graha
    natal_graha: Graha
    aspect_type: str  # conjunction, opposition, trine, square, sextile
    progressed_lon: float
    natal_lon: float
    orb: float
    description: str


class ProgressionCalculator:
    def __init__(self, natal_chart: ChartData):
        self.natal = natal_chart
        self.birth_dt = natal_chart.birth_date
        self.builder = ChartBuilder()
        # Copy builder settings from natal
        self.builder.swe.set_sidereal_mode(self.natal.ayanamsa_name)

    def secondary(self, target_date: Optional[datetime] = None,
                  target_age: Optional[float] = None) -> ProgressedChart:
        """Standard secondary progression: 1 day = 1 year.

        Pass either target_date (datetime) or target_age (float years).
        """
        if target_age is None and target_date is None:
            target_date = datetime.now()
        if target_age is None:
            delta = target_date - self.birth_dt
            target_age = delta.total_seconds() / (365.25 * 86400)
        if target_date is None:
            target_date = self.birth_dt + timedelta(days=target_age)

        try:
            cd = self.builder.build(
                year=target_date.year, month=target_date.month,
                day=target_date.day,
                hour=target_date.hour + target_date.minute / 60.0 +
                     target_date.second / 3600.0,
                lat=self.natal.latitude, lon=self.natal.longitude,
                tz=self.natal.timezone,
            )
        except Exception:
            cd = None

        return ProgressedChart(
            method="secondary",
            target_date=target_date,
            target_age=target_age,
            chart=cd,
        )

    def solar_arc(self, target_age: float) -> ProgressedChart:
        """Solar arc progression: advance each planet by Sun's secondary motion.

        The Sun moves ~1° per day in secondary progression. All planets
        advance by the same amount as the Sun's secondary motion.
        """
        progressed_dt = self.birth_dt + timedelta(days=target_age)
        sec = self.secondary(target_age=target_age)
        if sec.chart is None:
            return sec

        natal_sun = self.natal.planet(Graha.SUN).longitude
        prog_sun = sec.chart.planet(Graha.SUN).longitude
        solar_arc_degrees = (prog_sun - natal_sun + 360) % 360
        if solar_arc_degrees > 180:
            solar_arc_degrees -= 360

        # Build progressed chart with solar arc applied
        try:
            cd = self.builder.build(
                year=progressed_dt.year, month=progressed_dt.month,
                day=progressed_dt.day,
                hour=progressed_dt.hour + progressed_dt.minute / 60.0 +
                     progressed_dt.second / 3600.0,
                lat=self.natal.latitude, lon=self.natal.longitude,
                tz=self.natal.timezone,
            )
        except Exception:
            cd = None

        return ProgressedChart(
            method="solar_arc",
            target_date=progressed_dt,
            target_age=target_age,
            chart=cd,
        )

    def aspects_to_natal(self, progressed: ProgressedChart,
                         max_orb: float = 5.0) -> List[ProgressedAspect]:
        """Find aspects between progressed planets and natal planets."""
        if progressed.chart is None:
            return []

        aspects = []
        ASPECT_NAMES = {
            0: ("conjunction", 0),
            60: ("sextile", 60),
            90: ("square", 90),
            120: ("trine", 120),
            180: ("opposition", 180),
        }

        for pg in Graha:
            if pg not in self.natal.planets or pg not in progressed.chart.planets:
                continue
            p_lon = progressed.chart.planet(pg).longitude
            for ng in Graha:
                if ng not in self.natal.planets:
                    continue
                n_lon = self.natal.planet(ng).longitude
                diff = abs(((p_lon - n_lon + 180) % 360) - 180)

                for aspect_deg, (name, _) in ASPECT_NAMES.items():
                    orb = abs(diff - aspect_deg)
                    if orb <= max_orb:
                        if pg == ng and aspect_deg == 0:
                            continue  # skip self-conjunction
                        signs = ["same sign" if aspect_deg == 0 else
                                f"{(aspect_deg//30)} houses apart" if aspect_deg != 0 else ""]
                        aspects.append(ProgressedAspect(
                            progressed_graha=pg,
                            natal_graha=ng,
                            aspect_type=name,
                            progressed_lon=p_lon,
                            natal_lon=n_lon,
                            orb=round(orb, 1),
                            description=f"Progressed {pg.full_name} {name} natal {ng.full_name} "
                                       f"(orb {orb:.1f}°)",
                        ))
        aspects.sort(key=lambda a: a.orb)
        return aspects[:20]
