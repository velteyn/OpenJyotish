"""
Ashtottari Dasa — 108-year nakshatra-based dasa system (Brihat Parasara Hora Sastra).

The Ashtottari dasa is the second most popular dasa after Vimsottari. It uses
8 planets (Ketu is excluded) with a total cycle of 108 years.

Planet years: Sun(6), Moon(15), Mars(8), Mercury(17), Saturn(10),
              Jupiter(19), Rahu(12), Venus(21)
Total: 108 years

Algorithm:
  1. Find Moon's nakshatra
  2. Determine the starting lord from the Ashtottari nakshatra-lord mapping
  3. Compute fraction of nakshatra remaining (same method as Vimsottari)
  4. First dasa lord = starting lord, duration = lord_years × fraction_remaining
  5. Subsequent dasas follow the fixed 8-planet cycle
  6. Each mahadasa has antardasas using the same proportional ratios

References:
  - Brihat Parasara Hora Sastra, Chapter 46
  - Original Vedic astrology binary (dasa engine at 0x0046c890)
  - "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao
"""

from typing import Dict, List, Optional

from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


class AshtottariDasa(DasaBase):
    """Ashtottari dasa — 108-year conditional nakshatra dasa.

    Uses 8 planets: Sun, Moon, Mars, Mercury, Saturn, Jupiter, Rahu, Venus.
    Ketu is excluded from this dasa system.
    """

    system_name = "ashtottari"

    CYCLE_LORDS = [
        Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
        Graha.SATURN, Graha.JUPITER, Graha.RAHU, Graha.VENUS,
    ]

    CYCLE_YEARS = [6.0, 15.0, 8.0, 17.0, 10.0, 19.0, 12.0, 21.0]

    # Ashtottari nakshatra-to-planet mapping.
    # Each nakshatra (0-26) maps to a Graha in the Ashtottari cycle.
    # The lords cycle through [Su, Mo, Ma, Me, Sa, Ju, Ra, Ve] repeatedly.
    _NAKSHATRA_LORD = {}
    for _i in range(27):
        _NAKSHATRA_LORD[Nakshatra(_i)] = CYCLE_LORDS[_i % 8]

    def __init__(self, options: Optional[DasaOptions] = None):
        super().__init__(options)
        self._cycle_index = {lord: i for i, lord in enumerate(self.CYCLE_LORDS)}

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options

        moon_lon = chart["planets"][Graha.MOON]["longitude"]
        nakshatra, pada = Nakshatra.from_longitude(moon_lon)
        nakshatra_start = nakshatra.value * (360.0 / 27.0)
        degrees_progressed = (moon_lon % 360 - nakshatra_start) % (360.0 / 27.0)
        remaining = self.compute_fraction_remaining(degrees_progressed)

        starting_lord = self._NAKSHATRA_LORD[nakshatra]
        starting_idx = self._cycle_index[starting_lord]

        lords = []
        for i in range(8):
            idx = (starting_idx + i) % 8
            lord = self.CYCLE_LORDS[idx]
            years = self.CYCLE_YEARS[idx]
            if i == 0:
                years = years * remaining
            lords.append((lord.value, years))

        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sub_lord_names = {i: self.CYCLE_LORDS[i].full_name for i in range(8)}
        return self.build_period_tree(
            lords=lords,
            start_jd=birth_jd,
            cycle_total_years=108.0,
            sub_ratios=self.CYCLE_YEARS,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            sub_lord_names=sub_lord_names,
        )

    @staticmethod
    def is_applicable(chart: Dict, condition: str = "unconditional") -> bool:
        """Check if Ashtottari dasa is applicable for this chart.

        Three standard views:
          "unconditional" — always applicable
          "rahu" — Rahu (not in lagna) in quadrant/trine from lagna lord
          "paksha" — day birth in Krishna paksha OR night birth in Sukla paksha
        """
        if condition == "unconditional":
            return True

        planets = chart.get("planets", {})
        lagna_lon = chart.get("lagna_lon", 0.0)

        if condition == "rahu" and Graha.RAHU in planets:
            rahu_lon = planets[Graha.RAHU].get("longitude", 0)
            rahu_house = int((rahu_lon - lagna_lon + 360) % 360 // 30)
            lagna_rasi = int(lagna_lon // 30) % 12
            from jhora.types.rasi import Rasi
            lagna_lord = Rasi(lagna_rasi).lord
            if rahu_house != 0:
                lord_house = int((lagna_lon - lagna_lon + 360) % 360 // 30)
                kendras = {0, 3, 6, 9}
                konas = {1, 4, 7, 10}
                return rahu_house in kendras or rahu_house in konas
            return False

        if condition == "paksha":
            if Graha.SUN in planets and Graha.MOON in planets:
                sun_lon = planets[Graha.SUN]["longitude"]
                moon_lon = planets[Graha.MOON]["longitude"]
                diff = (moon_lon - sun_lon) % 360
                is_shukla = diff < 180
                from jhora.types.nakshatra import Nakshatra
                naks, _ = Nakshatra.from_longitude(moon_lon)
                naks_start = naks.start_longitude
                naks_span = naks.span
                is_day = (lagna_lon - naks_start + 360) % 360 < naks_span / 2
                return (is_day and not is_shukla) or (not is_day and is_shukla)
            return True

        return True

    def dasa_at_date(
        self, birth_jd: float, chart: Dict, target_jd: float
    ) -> Optional[DasaPeriod]:
        periods = self.compute(birth_jd, chart)
        return self.get_active_period(periods, target_jd)