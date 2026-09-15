"""Yogardha Dasa — Jaimini rasi dasa averaging Chara and Sthira.

Classical method (standard mainstream form, independently
confirmed by two implementations): seed at the stronger of lagna and
7th house (same BPHS stronger-sign determination as Brahma), running
forward — reverse iff the seed index is odd. Each Mahadasha lasts the
mean of its Chara lord-distance duration (Rao dual-lord exception, no
exaltation adjustment) and its Sthira modality duration (7/8/9), so
half-year increments occur; antardasas run proportionally in cycle
direction. An alternative school seeds at lagna; this engine documents
that variant without implementing it.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import (
    chara_years,
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.rasi import Rasi


def _modality_years(sign: int) -> int:
    r = Rasi(sign)
    if r.is_movable:
        return 7
    if r.is_fixed:
        return 8
    return 9


class YogardhaDasa(DasaBase):
    """Twelve rasi dasas of averaged Chara/Sthira years; lagna/7th seed."""

    system_name = "yogardha"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        seventh = Rasi((lagna.value + 6) % 12)
        start = _stronger_rasi(lagna, seventh, full).value
        direction = 1 if start % 2 == 0 else -1
        durations = [(chara_years(s, sigs) + _modality_years(s)) / 2.0
                     for s in range(12)]
        sequence = [((start + direction * i) % 12,
                     durations[(start + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False,
                              ad_direction=direction)
