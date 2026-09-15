"""Sthira Dasa — Jaimini rasi dasa of longevity from the Brahma sign.

Classical method (standard SJC reading, Jaimini Sutras 2.1.55–60 via
the Sastri/Somanatha worked tradition): the 12 rasi Mahadashas run in
zodiacal order starting from the sign occupied by the Brahma planet
(same determination as ``BrahmaDasa``). Sign durations are fixed by
modality: 7 years for movable signs (Aries, Cancer, Libra,
Capricorn), 8 for fixed (Taurus, Leo, Scorpio, Aquarius), 9 for dual
(Gemini, Virgo, Sagittarius, Pisces) — 96 years total on every chart.
Antardasas cycle forward from the MD sign, proportional to each
cycle sign's own year value. Used for ayur (longevity) timing with
Brahma, Rudra and Maheshwara.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.brahma import _brahma_planet
from jhora.dasas.jaimini_common import (
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


class SthiraDasa(DasaBase):
    """Twelve rasi dasas from the Brahma planet's sign; 7/8/9 years."""

    system_name = "sthira"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        start = sigs[_brahma_planet(lagna, full)]
        durations = [_modality_years(s) for s in range(12)]
        sequence = [((start + i) % 12, durations[(start + i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
