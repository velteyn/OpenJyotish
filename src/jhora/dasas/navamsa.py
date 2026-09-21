"""Navamsa Dasa — Jaimini rasi dasa of the navamsa lagna lord's sign.

Classical method (PVR school, cross-checked on three charts):
seed at the sign occupied by the D1 lagna lord, running forward
(parity direction: forward iff the seed index is even — all three
observed seeds are even, so the odd-seed branch is the mainstream
default, documented), with fixed 9-year Mahadashas — 108 years total.
Antardasas cycle forward proportionally (house convention; the standard AD
method uncompared). An alternative school runs the Chara cycle on D-9
positions; this engine documents that variant without implementing it.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    _single_lord,
    normalize_planets,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod


class NavamsaDasa(DasaBase):
    """Twelve 9-year rasi dasas from the D1 lagna lord's sign."""

    system_name = "navamsa"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = int(chart["lagna_lon"] // 30) % 12
        planets = normalize_planets(chart.get("planets", {}))
        start = int(planets.get(_single_lord(lagna), 0.0) // 30) % 12
        direction = 1 if start % 2 == 0 else -1
        sequence = [((start + direction * i) % 12, 9) for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, [9] * 12, y_per_d,
                              opts.subdivision_level, parity_ads=False)
