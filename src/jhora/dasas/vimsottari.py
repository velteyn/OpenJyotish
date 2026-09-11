"""
Vimsottari Dasa (120-year nakshatra-based dasa system).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.dasa import DasaSystem, DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


class VimsottariDasa(DasaBase):
    """Vimsottari dasa — the most important dasa system in Kali Yuga.

    Algorithm:
    1. Find the seed nakshatra (Moon's by default; Lagna/Sun/tara by option)
       and its lord
    2. Compute fraction of nakshatra remaining (sesham)
    3. First dasa lord = nakshatra lord, duration = lord_years * fraction_remaining
    4. Subsequent dasas follow fixed 9-planet cycle: Ketu, Venus, Sun, Moon,
       Mars, Rahu, Jupiter, Saturn, Mercury (starting from the planet after the
       first dasa lord)
    5. Each mahadasa has antardasas in same proportion
    6. Cycle total = 120 years
    """

    system_name = "vimsottari"

    # Vimsottari lord cycle order (9 planets, total 120 years)
    CYCLE_LORDS = [
        Graha.KETU,   # 7 years
        Graha.VENUS,  # 20 years
        Graha.SUN,    # 6 years
        Graha.MOON,   # 10 years
        Graha.MARS,   # 7 years
        Graha.RAHU,   # 18 years
        Graha.JUPITER,# 16 years
        Graha.SATURN, # 19 years
        Graha.MERCURY,# 17 years
    ]

    CYCLE_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

    # Tara offsets (nakshatra counts) from the Janma (Moon) nakshatra.
    _TARA_OFFSET = {
        "kshema": 3,    # 4th star
        "utpanna": 4,   # 5th star
        "adhana": 7,    # 8th star (Aadhaana tara)
    }

    def __init__(self, options: Optional[DasaOptions] = None):
        super().__init__(options)
        self._cycle_years = dict(zip(self.CYCLE_LORDS, self.CYCLE_YEARS))
        self._lord_order = {lord: i for i, lord in enumerate(self.CYCLE_LORDS)}

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options

        seed_lon, seed_nakshatra_value = self._seed_longitude(chart, opts.start_variation)
        nakshatra = Nakshatra(seed_nakshatra_value)
        nakshatra_start = nakshatra.value * (360.0 / 27.0)
        degrees_progressed = (seed_lon % 360 - nakshatra_start) % (360.0 / 27.0)

        # Starting lord from the seed nakshatra.
        starting_lord_idx = self._lord_order[self._nakshatra_to_graha(nakshatra)]

        if opts.sesham_method == "full":
            remaining = 1.0
        else:
            remaining = self.compute_fraction_remaining(degrees_progressed)

        # Build lord sequence.
        lords = []
        for i in range(9):
            idx = (starting_lord_idx + i) % 9
            lord = self.CYCLE_LORDS[idx]
            years = self.CYCLE_YEARS[idx]
            if i == 0 and opts.sesham_method != "full":
                years = years * remaining
            lords.append((lord.value, years))

        y_per_d = self._days_per_year(opts.year_definition)

        sub_lord_names = {i: self.CYCLE_LORDS[i].full_name for i in range(9)}
        return self.build_period_tree(
            lords=lords,
            start_jd=birth_jd,
            cycle_total_years=120.0,
            sub_ratios=self.CYCLE_YEARS,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            sub_lord_names=sub_lord_names,
            sub_order=[g.value for g in self.CYCLE_LORDS],
        )

    def _days_per_year(self, year_definition: str) -> float:
        if year_definition == "tithi":
            return 354.367
        return 365.2425 if year_definition == "solar" else 360.0

    def _seed_longitude(self, chart: Dict, variation: str) -> Tuple[float, int]:
        """Return (reference longitude, seed nakshatra value) for the dasa."""
        if variation == "moon":
            lon = chart["planets"][Graha.MOON]["longitude"]
            nak, _ = Nakshatra.from_longitude(lon)
            return lon, nak.value
        if variation == "lagna":
            lon = chart.get("lagna_lon", chart["planets"][Graha.MOON]["longitude"])
            nak, _ = Nakshatra.from_longitude(lon)
            return lon, nak.value
        if variation == "sun":
            lon = chart["planets"][Graha.SUN]["longitude"]
            nak, _ = Nakshatra.from_longitude(lon)
            return lon, nak.value
        if variation in self._TARA_OFFSET:
            # Tara-based seed: nakshatra offset from Moon's nakshatra.
            moon_lon = chart["planets"][Graha.MOON]["longitude"]
            moon_nak, _ = Nakshatra.from_longitude(moon_lon)
            seed_nak = Nakshatra((moon_nak.value + self._TARA_OFFSET[variation]) % 27)
            # Reference point = start of that nakshatra (sesham ≈ full).
            return seed_nak.value * (360.0 / 27.0) + 0.001, seed_nak.value
        # Unknown variation → fall back to Moon.
        lon = chart["planets"][Graha.MOON]["longitude"]
        nak, _ = Nakshatra.from_longitude(lon)
        return lon, nak.value

    def _nakshatra_to_graha(self, n: Nakshatra) -> Graha:
        """Map nakshatra lord name to Graha enum."""
        mapping = {
            "Ketu": Graha.KETU,
            "Venus": Graha.VENUS,
            "Sun": Graha.SUN,
            "Moon": Graha.MOON,
            "Mars": Graha.MARS,
            "Rahu": Graha.RAHU,
            "Jupiter": Graha.JUPITER,
            "Saturn": Graha.SATURN,
            "Mercury": Graha.MERCURY,
        }
        return mapping[n.lord]

    def dasa_at_date(
        self, birth_jd: float, chart: Dict, target_jd: float
    ) -> Optional[DasaPeriod]:
        """Find the active Vimsottari dasa at a given date."""
        periods = self.compute(birth_jd, chart)
        return self.get_active_period(periods, target_jd)
