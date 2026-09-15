"""Navamsa Dasa — Jaimini rasi dasa computed on D-9 positions.

Classical method (mainstream textbook form): the Chara cycle applied
to navamsa placements — seed at the D-9 lagna sign, whole-cycle
direction via the Rao 9th-from-lagna rule on the D-9 lagna, Chara
lord-distance durations (Rao dual-lord exception, no exaltation
adjustment) on D-9 signs, proportional cycle-direction antardasas.
D-9 placements reuse the standard varga mapping. An alternative
school uses a fixed adhipati-seed table with 9-year Mahadashas;
this engine documents that variant without implementing it.
"""

from typing import Dict, List, Optional

from jhora.charts.varga import _map_sign
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    chara_cycle_years,
    chara_direction,
    normalize_planets,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.varga import VargaVariant


def _navamsa_sign(longitude: float) -> int:
    """D-9 sign (0-based) for a D-1 longitude via the standard mapping."""
    sign = int(longitude // 30) % 12
    pada = int((longitude % 30) // (30.0 / 9))
    return int(_map_sign(sign, pada, 9, VargaVariant.DEFAULT)) % 12


class NavamsaDasa(DasaBase):
    """Chara cycle on navamsa placements, seeded at the D-9 lagna."""

    system_name = "navamsa"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = {g: _navamsa_sign(lon) for g, lon in planets.items()}
        lagna = _navamsa_sign(chart["lagna_lon"])
        direction = chara_direction(lagna)
        durations = chara_cycle_years(sigs)
        sequence = [((lagna + direction * i) % 12,
                     durations[(lagna + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False,
                              ad_direction=direction)
