"""Bhava Bala — house strength evaluation (Brihat Parasara Hora Sastra, Ch 28).

Components:
  Sthana Bala   — positional (kendra/panapara/apoklima)
  Drishti Bala  — aspect strength from planets on bhava madhya
  Dig Bala      — directional strength
  Adhipati Bala — derived from house lord's Shadbala
  Drig Bala     — aspect contribution from planets aspecting the lord
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from jhora.charts.chart import ChartData
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.angles import diff as angle_diff
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_RUPA = 60.0

# House groups
_KENDRAS = {1, 4, 7, 10}
_PANAPARAS = {2, 5, 8, 11}
_APOKLIMAS = {3, 6, 9, 12}

# Map string lord names to Graha
_LORD_TO_GRAHA: Dict[str, Graha] = {
    "Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
    "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
    "Venus": Graha.VENUS, "Saturn": Graha.SATURN,
}

# Directional (Dig Bala) parameters per house — maximum dig bala houses
# House 1 (East): Mercury + Jupiter
# House 10 (South): Sun + Mars
# House 7 (West): Saturn
# House 4 (North): Moon + Venus
_DIG_BALA_PEAK: Dict[int, List[Graha]] = {
    1: [Graha.MERCURY, Graha.JUPITER],
    10: [Graha.SUN, Graha.MARS],
    7: [Graha.SATURN],
    4: [Graha.MOON, Graha.VENUS],
}

# Graha Drishti (aspect) — as fraction of full aspect
# (signs from planet, aspect strength)
_GRAHA_DRISHTI: Dict[Graha, List[Tuple[int, float]]] = {
    Graha.SUN:     [(7, 1.0)],
    Graha.MOON:    [(7, 1.0)],
    Graha.MARS:    [(7, 1.0), (4, 0.75), (8, 0.50)],
    Graha.MERCURY: [(7, 1.0)],
    Graha.JUPITER: [(7, 1.0), (5, 0.75), (9, 0.50)],
    Graha.VENUS:   [(7, 1.0)],
    Graha.SATURN:  [(7, 1.0), (3, 0.75), (10, 0.50)],
    Graha.RAHU:    [(7, 1.0), (5, 0.75), (9, 0.50)],
    Graha.KETU:    [(7, 1.0), (4, 0.75), (8, 0.50)],
}

# Benefic/malefic classification
_BENEFICS = {Graha.MOON, Graha.MERCURY, Graha.JUPITER, Graha.VENUS}
_MALEFICS = {Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU}


@dataclass
class BhavaBalaResult:
    house: int
    sthana: float
    drishti: float
    dig: float
    adhipati: float
    drig: float
    total: float


@dataclass
class BhavaBalaReport:
    results: Dict[int, BhavaBalaResult] = field(default_factory=dict)

    def sorted_by_strength(self) -> List[BhavaBalaResult]:
        return sorted(self.results.values(), key=lambda r: r.total, reverse=True)

    def strongest(self) -> BhavaBalaResult:
        return self.sorted_by_strength()[0]

    def weakest(self) -> BhavaBalaResult:
        return self.sorted_by_strength()[-1]


class BhavaBalaComputer:
    """Compute the strength of each house (bhava) in a birth chart."""

    def __init__(self, chart: ChartData):
        self.chart = chart
        self.shadbala = ShadbalaComputer(chart)
        self._lord_shadbala: Dict[Graha, 'ShadbalaResult'] = {}
        for g in Graha:
            if g not in (Graha.RAHU, Graha.KETU):
                self._lord_shadbala[g] = self.shadbala.compute_one(g)

    def compute(self, house: int) -> BhavaBalaResult:
        sthana = self._sthana_bala(house)
        drishti = self._drishti_bala(house)
        dig = self._dig_bala(house)
        adhipati = self._adhipati_bala(house)
        drig = self._drig_bala(house)
        total = sthana + drishti + dig + adhipati + drig
        return BhavaBalaResult(
            house=house,
            sthana=sthana, drishti=drishti, dig=dig,
            adhipati=adhipati, drig=drig, total=total,
        )

    def compute_all(self) -> BhavaBalaReport:
        report = BhavaBalaReport()
        for h in range(1, 13):
            report.results[h] = self.compute(h)
        return report

    def _sthana_bala(self, house: int) -> float:
        """Positional strength: kendra=60, panapara=30, apoklima=15."""
        if house in _KENDRAS:
            return 60.0
        elif house in _PANAPARAS:
            return 30.0
        return 15.0

    def _drishti_bala(self, house: int) -> float:
        """Aspect strength: sum of aspects from all planets on the bhava madhya.

        The bhava madhya (house midpoint) is calculated from the house cusp.
        Aspect is based on sign-to-sign drishti, weighted by the planet's distance.
        """
        bhava_madhya = self._bhava_madhya(house)
        if bhava_madhya is None:
            return 0.0
        total = 0.0
        for g in Graha:
            if g not in self.chart.planets:
                continue
            p = self.chart.planet(g)
            # Signs between planet and bhava madhya
            planet_rasi = int(p.longitude / 30)
            target_rasi = int(bhava_madhya / 30)
            signs_between = (target_rasi - planet_rasi) % 12
            # Check if planet aspects this position
            asp_count = signs_between + 1  # house counting: 1-based
            for asp_houses, fraction in _GRAHA_DRISHTI.get(g, []):
                if asp_count == asp_houses:
                    # Aspect strength proportional to orbs
                    orb = self._aspect_orb(p.longitude, bhava_madhya, asp_houses)
                    total += _RUPA * fraction * orb
        return min(total, _RUPA)

    def _dig_bala(self, house: int) -> float:
        """Directional strength based on the bhava's position relative to kendras.

        Maximum dig bala at the four kendras: 1(E), 10(S), 7(W), 4(N).
        Linear interpolation between peak houses.
        """
        peaks = [1, 4, 7, 10]
        # Find closest peak house and compute distance
        min_dist = 6
        for peak in peaks:
            dist = self._circular_dist(house, peak)
            if dist < min_dist:
                min_dist = dist
        # Linear decay: 60 at peak, 0 at 6 houses away
        if min_dist >= 6:
            return 0.0
        return _RUPA * (1.0 - min_dist / 6.0)

    def _lord(self, house: int) -> Graha | None:
        """Return the Graha ruling the sign on this house cusp."""
        lord_rasi_index = (int(self.chart.ascendant / 30) + house - 1) % 12
        lord_str = Rasi(lord_rasi_index).lord
        return _LORD_TO_GRAHA.get(lord_str)

    def _adhipati_bala(self, house: int) -> float:
        """Strength derived from the house lord's Shadbala."""
        lord = self._lord(house)
        if lord is None or lord in (Graha.RAHU, Graha.KETU):
            return 30.0  # neutral for nodes
        sb_result = self._lord_shadbala.get(lord)
        if sb_result is None:
            return 30.0
        total_sb = sb_result.total_virupa
        scaled = (total_sb - 250.0) / 300.0 * _RUPA
        return max(0.0, min(_RUPA, scaled))

    def _drig_bala(self, house: int) -> float:
        """Aspect contribution from planets aspecting the house lord."""
        lord = self._lord(house)
        if lord is None or lord not in self.chart.planets:
            return 0.0
        lord_pos = self.chart.planet(lord)
        total = 0.0
        for g in Graha:
            if g not in self.chart.planets or g == lord:
                continue
            p = self.chart.planet(g)
            asp_count = self._houses_between(p.longitude, lord_pos.longitude)
            for asp_houses, fraction in _GRAHA_DRISHTI.get(g, []):
                if asp_count == asp_houses:
                    sign = 1.0 if g in _BENEFICS else -0.5
                    total += _RUPA * 0.15 * fraction * sign
        return max(-_RUPA * 0.3, min(_RUPA * 0.3, total))

    def _bhava_madhya(self, house: int) -> float:
        """Midpoint of a house from cusps. Falls back to whole-sign approximation."""
        cusps = self.chart.house_cusps
        if cusps and len(cusps) >= 12:
            this_cusp = cusps[house - 1]
            next_cusp = cusps[house % 12]
            if next_cusp < this_cusp:
                next_cusp += 360.0
            return (this_cusp + next_cusp) / 2.0 % 360.0
        # Whole-sign fallback
        lagna_rasi = int(self.chart.ascendant / 30)
        mid = (lagna_rasi + house - 1) * 30 + 15
        return mid % 360.0

    def _aspect_orb(self, planet_lon: float, target_lon: float, asp_signs: int) -> float:
        """Return 1.0 for exact aspect, decreasing with orb distance."""
        # Exact aspect longitude: planet_lon + (asp_signs-1)*30
        exact_lon = (planet_lon + (asp_signs - 1) * 30) % 360
        diff = abs(((target_lon - exact_lon + 180) % 360) - 180)
        # Full strength within 5°, linear drop to 0 at 15°
        if diff <= 5:
            return 1.0
        elif diff <= 15:
            return 1.0 - (diff - 5) / 10.0
        return 0.3

    def _houses_between(self, lon1: float, lon2: float) -> int:
        """Count houses (1-12) from lon1 to lon2."""
        r1 = int(lon1 / 30)
        r2 = int(lon2 / 30)
        diff = (r2 - r1) % 12
        return diff + 1

    @staticmethod
    def _circular_dist(a: int, b: int) -> int:
        d = abs(a - b)
        return min(d, 12 - d)
