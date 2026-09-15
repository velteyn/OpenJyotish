"""Shoola Dasa — Jaimini rasi dasa of longevity.

Classical method (PVR/JHora school; PVR textbook worked answers):
seed at the stronger of a reference house and 7th from it (same BPHS
stronger-sign determination as Brahma) — lagna for self (house 1),
9th for Pitri (father), 7th for Dara (spouse), 5th for Putra
(children) — running forward zodiacally with fixed 9-year Mahadashas
— 108 years total on every chart. Antardasas cycle forward
proportionally (equal 9-year shares structurally). Used for
longevity, maraka periods and severe illness timing; JHora's
antardasa-start options are out of scope.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import (
    normalize_planets,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.rasi import Rasi


class ShoolaDasa(DasaBase):
    """Twelve 9-year rasi dasas from the stronger of lagna/7th."""

    system_name = "shoola"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        house = max(1, min(12, int(getattr(opts, "seed_house", 1))))
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        ref = Rasi((lagna.value + house - 1) % 12)
        seventh = Rasi((ref.value + 6) % 12)
        planets = normalize_planets(chart.get("planets", {}))
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        start = _stronger_rasi(ref, seventh, full).value
        durations = [9] * 12
        sequence = [((start + i) % 12, 9) for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
