"""Shoola Dasa — Jaimini rasi dasa of longevity.

Classical method (Jaimini Sutras; standard SJC reading): the Mahadashas
cover the 12 rasis in three groups of four, starting from the strongest
Lagna trine (Lagna, 5th, 9th) by occupant count — ties keep the earlier
trine, so an empty chart starts at Lagna. Within each group the signs
run forward. Sign durations follow house nature: 7 years for
fiery-group signs (index % 3 == 0), 8 for the next, 9 for the next —
96 years total. Antardasas cycle forward proportionally. Used for
longevity, maraka periods and severe illness timing.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
    sign_occupants,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.rasi import Rasi

_GROUP_YEARS = (7, 8, 9)


class ShoolaDasa(DasaBase):
    """Three trine-groups of four rasis; 7/8/9-year durations."""

    system_name = "shoola"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        occ = sign_occupants(sigs)
        lagna = int(lagna_lon // 30) % 12
        trines = [lagna, (lagna + 4) % 12, (lagna + 8) % 12]
        base_order = {t: i for i, t in enumerate(trines)}
        trines.sort(key=lambda t: (-len(occ[t]), base_order[t]))
        durations = [_GROUP_YEARS[s % 3] for s in range(12)]
        sequence = []
        for t in trines:
            for i in range(4):
                s = (t + i) % 12
                sequence.append((s, durations[s]))
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
