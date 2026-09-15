"""Moola Dasa — Jaimini rasi dasa of roots and past karma.

Simplified implementation: fixed 12-year cycle, strongest-planet seed;
the reference binary's corrections (D-60 involvement, Moola-trikona /
Moon / Sun / Lagna options) are pending.

Classical method: the 12 rasi Mahadashas run in zodiacal order starting
from the sign of the STRONGEST planet — strength scored as occupant
count × 100, plus exaltation (+2) or debilitation (−2) × 30, plus the
dispositor's occupant count × 10 (ties keep the first planet in
Sun→Ketu order; a fully tied chart falls back to the Atmakaraka).
Every Mahadasha lasts 12 years (144-year cycle); antardasas cycle
forward proportionally. Used for root causes, past-life karma and
research-level rectification.
"""

from typing import Dict, List, Optional

from jhora.calc.karaka import get_atma_karaka
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    _ALL_GRAHAS,
    _strength_score,
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.graha import Graha


class MoolaDasa(DasaBase):
    """Twelve 12-year rasi dasas from the strongest planet's sign."""

    system_name = "moola"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        best = None
        best_score = None
        for g in _ALL_GRAHAS:
            if g not in sigs:
                continue
            cnt, ex, disp, _lon = _strength_score(g, sigs)
            score = cnt * 100 + ex * 30 + disp * 10
            # strict-greater: exact ties keep the first planet in
            # Sun-to-Ketu order.
            if best_score is None or score > best_score:
                best, best_score = g, score
        if best is None:
            full = {g: {"longitude": lon} for g, lon in planets.items()}
            try:
                best = get_atma_karaka(full).graha
            except Exception:
                best = Graha.SUN
        start = sigs.get(best, 0)
        sequence = [((start + i) % 12, 12) for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, [12] * 12, y_per_d,
                              opts.subdivision_level, parity_ads=False)
