"""Trikona Dasa — Jaimini rasi dasa of the purusharthas.

Classical method (PVR/JHora school, binary-verified on three charts):
seed at the stronger of the lagna, 5th and 9th houses (same BPHS
stronger-sign determination as Brahma), running forward when the seed
index is even and backward otherwise. Durations follow the Chara
lord-distance rule (inclusive sign-to-lord count minus one, footed
directions, own sign 12, full circle 11, dual Scorpio/Aquarius lords
under the Rao own-sign exception; no exaltation adjustment) —
reproducing JHora exactly, including the Rao-exception Scorpio.
Antardasas cycle forward proportionally (house convention; JHora shows
equal splits in kendra-group order — e.g. Vi MD [Vi,Ge,Pi,Sg,Ta,Aq,
Sc,Le,Cp,Li,Cn,Ar], Ge MD [Sg,Pi,Ge,Vi,Ar,Cn,Li,Cp,Le,Sc,Aq,Ta] —
grouping rule uninduced, needs one more MD sample). An alternative
school seeds at the Atmakaraka with fixed 7/8/9 years; this engine
documents that variant without implementing it.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import (
    chara_cycle_years,
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.rasi import Rasi


class TrikonaDasa(DasaBase):
    """Twelve rasi dasas from the strongest trine; Chara durations."""

    system_name = "trikona"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        trines = [lagna, Rasi((lagna.value + 4) % 12),
                  Rasi((lagna.value + 8) % 12)]
        seed = _stronger_rasi(
            _stronger_rasi(trines[0], trines[1], full), trines[2], full)
        start = seed.value
        direction = 1 if start % 2 == 0 else -1
        durations = chara_cycle_years(sigs)
        sequence = [((start + direction * i) % 12,
                     durations[(start + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
