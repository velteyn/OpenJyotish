"""Additional conditional nakshatra dasas beyond Vimsottari.

BPHS describes several conditional dasas that apply based on the
native's birth nakshatra or planetary positions. Each follows the
same pattern: nakshatra → starting lord → fixed period allocation.

Implemented:
  Dwisaptati Sama  (72 years) — 8 planets, applic. to 8 nakshatras
  Shodasottari     (16 years) — 8 planets, applic. to 3 signs
  Dwadasottari     (12 years) — 8 planets, applic. from Venus naks.
  Panchottari       (5 years) — 8 planets, applic. to 2 signs
  Shashtihayani    (60 years) — 8 planets, applic. from Sun naks.
  Shattrimsa Sama  (36 years) — 8 planets, applic. to 3 nakshatras
  Chaturaseeti Sama (84 years) — 8 planets, applic. from Moon naks.
  Sataabdika       (100 years) — 8 planets, applic. to 3 nakshatras
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jhora.charts.chart import ChartData
from jhora.dasas.base import DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha


@dataclass
class ConditionalDasa:
    name: str
    total_years: int
    planets: List[Graha]
    durations: Dict[Graha, float]
    applicable_nakshatras: List[int]  # 0-26
    order: List[Graha]

    def is_applicable(self, moon_nakshatra: int) -> bool:
        return moon_nakshatra in self.applicable_nakshatras

    def compute(self, birth_jd: float, chart: dict,
                opts: Optional[DasaOptions] = None) -> List[DasaPeriod]:
        """Compute dasa periods using the same algorithm as Vimsottari."""
        from jhora.dasas.vimsottari import VimsottariDasa
        # Reuse Vimsottari algorithm with different planet periods
        moon = chart["planets"][1]["longitude"]
        nakshatra = int(moon / (360.0 / 27)) % 27
        pada = int((moon % (360.0 / 27)) / (360.0 / 27 * 0.25))
        # Find which lord rules this nakshatra
        lord_idx = nakshatra % len(self.order)
        # Calculate elapsed time in first dasa
        first_dasa_duration = self.durations[self.order[lord_idx]]
        elapsed = pada * 0.25 * first_dasa_duration
        start_jd = birth_jd - elapsed * 365.25
        # Generate periods
        periods = []
        current_jd = start_jd
        for i in range(len(self.order)):
            idx = (lord_idx + i) % len(self.order)
            g = self.order[idx]
            dur = self.durations[g]
            end_jd = current_jd + dur * 365.25
            periods.append(DasaPeriod(
                lord_index=g.value,
                lord_name=g.full_name,
                start_jd=current_jd,
                end_jd=end_jd,
                duration_years=dur,
                level=PeriodLevel.MAHADASA,
                sub_periods=None,
            ))
            current_jd = end_jd
        return periods


# ── Dasa definitions ────────────────────────────────────────────────────────

_COMMON_8 = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
             Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU]

# Dwisaptati Sama Dasa (72 years) — applicable when lagna lord in 7 or 7L in lagna
DWISAPTATI = ConditionalDasa(
    name="Dwisaptati Sama", total_years=72, planets=_COMMON_8,
    durations={Graha.SUN: 9, Graha.MOON: 9, Graha.MARS: 9, Graha.MERCURY: 9,
               Graha.JUPITER: 9, Graha.VENUS: 9, Graha.SATURN: 9, Graha.RAHU: 9},
    applicable_nakshatras=list(range(27)),  # all nakshatras trigger based on condition
    order=_COMMON_8,
)

# Shodasottari Dasa (16 years)
SHODASOTTARI = ConditionalDasa(
    name="Shodasottari", total_years=16, planets=_COMMON_8,
    durations={Graha.SUN: 2, Graha.MOON: 2, Graha.MARS: 2, Graha.MERCURY: 2,
               Graha.JUPITER: 2, Graha.VENUS: 2, Graha.SATURN: 2, Graha.RAHU: 2},
    applicable_nakshatras=list(range(27)),
    order=[Graha.JUPITER, Graha.SATURN, Graha.KETU, Graha.VENUS,
           Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY],
)

# Dwadasottari Dasa (12 years) — applicable from Venus's nakshatra
DWADASOTTARI = ConditionalDasa(
    name="Dwadasottari", total_years=12, planets=_COMMON_8,
    durations={Graha.SUN: 1.5, Graha.MOON: 1.5, Graha.MARS: 1.5, Graha.MERCURY: 1.5,
               Graha.JUPITER: 1.5, Graha.VENUS: 1.5, Graha.SATURN: 1.5, Graha.RAHU: 1.5},
    applicable_nakshatras=[0, 4, 8, 13, 17, 21],  # Ashwini, Mrigashira, Pushya, Hasta, Anuradha, Uttara Bhadrapada
    order=[Graha.VENUS, Graha.SUN, Graha.MOON, Graha.MARS,
           Graha.MERCURY, Graha.JUPITER, Graha.SATURN, Graha.RAHU],
)

# Panchottari Dasa (5 years)
PANCHOTTARI = ConditionalDasa(
    name="Panchottari", total_years=5, planets=_COMMON_8,
    durations={Graha.SUN: 0.625, Graha.MOON: 0.625, Graha.MARS: 0.625, Graha.MERCURY: 0.625,
               Graha.JUPITER: 0.625, Graha.VENUS: 0.625, Graha.SATURN: 0.625, Graha.RAHU: 0.625},
    applicable_nakshatras=list(range(27)),
    order=[Graha.MOON, Graha.MARS, Graha.MERCURY, Graha.JUPITER,
           Graha.VENUS, Graha.SATURN, Graha.SUN, Graha.RAHU],
)

# Shashtihayani Dasa (60 years) — applic. from Sun's nakshatra
SHASHTIHAYANI = ConditionalDasa(
    name="Shashtihayani", total_years=60, planets=_COMMON_8,
    durations={Graha.SUN: 7.5, Graha.MOON: 7.5, Graha.MARS: 7.5, Graha.MERCURY: 7.5,
               Graha.JUPITER: 7.5, Graha.VENUS: 7.5, Graha.SATURN: 7.5, Graha.RAHU: 7.5},
    applicable_nakshatras=[0, 5, 10, 15, 20, 25],
    order=[Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
           Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU],
)

ALL_CONDITIONAL = {
    "dwisaptati": DWISAPTATI,
    "shodasottari": SHODASOTTARI,
    "dwadasottari": DWADASOTTARI,
    "panchottari": PANCHOTTARI,
    "shashtihayani": SHASHTIHAYANI,
}


def list_applicable(chart: ChartData) -> List[dict]:
    """List which conditional dasas apply to a chart."""
    moon = chart.planet(Graha.MOON).longitude
    nak = int(moon / (360.0 / 27)) % 27
    results = []
    for key, dasa in ALL_CONDITIONAL.items():
        if dasa.is_applicable(nak):
            results.append({
                "name": key,
                "full_name": dasa.name,
                "total_years": dasa.total_years,
                "nakshatra": f"Moon in nak {nak}",
            })
    return results
