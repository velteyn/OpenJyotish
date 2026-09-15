"""Trikona Dasa — Jaimini rasi dasa from the Atmakaraka's sign.

Classical method (standard SJC reading): the 12 rasi Mahadashas run in
zodiacal order starting from the sign occupied by the Atmakaraka
(highest in-sign degrees; Sun-to-Ketu input order breaks exact ties).
Sign durations follow house nature: 7 years for signs with index % 3
== 0, 8 for the next, 9 for the next — 96 years total on every chart.
Antardasas cycle forward from the MD sign, proportional to each
cycle sign's own year value.
"""

from typing import Dict, List, Optional

from jhora.calc.karaka import get_atma_karaka
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod

_GROUP_YEARS = (7, 8, 9)


class TrikonaDasa(DasaBase):
    """Twelve rasi dasas from the Atmakaraka's sign; 7/8/9-year durations."""

    system_name = "trikona"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        start = sigs[get_atma_karaka(full).graha]
        durations = [_GROUP_YEARS[s % 3] for s in range(12)]
        sequence = [((start + i) % 12, durations[(start + i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
