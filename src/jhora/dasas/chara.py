"""Chara Dasa — the general-purpose Jaimini rasi dasa.

Classical method (standard SJC/K.N. Rao reading): the 12 rasi
Mahadashas start at Lagna and run once through all 12 signs in a
single direction for the whole cycle — direct (savya) when the 9th
sign from lagna is odd-footed (Aries, Taurus, Gemini, Libra, Scorpio,
Sagittarius — Jaimini footedness, not index parity), reverse
(apasavya) otherwise.
Each sign lasts its Chara lord-distance duration (odd signs forward,
even signs backward, own sign 12, full circle 11, dual Scorpio /
Aquarius lords under the Rao own-sign exception); antardasas run the
cycle direction from the MD sign, proportional to each cycle sign's
own year value.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    chara_cycle_years,
    chara_direction,
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod


class CharaDasa(DasaBase):
    system_name = "chara"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        lagna = int(lagna_lon // 30) % 12
        direction = chara_direction(lagna)
        planet_sigs = planet_signs(
            normalize_planets(chart.get("planets", {})))
        durations = chara_cycle_years(
            planet_sigs,
            exaltation_exception=getattr(
                opts, "chara_exaltation_exception", False))
        sequence = [((lagna + direction * i) % 12,
                     durations[(lagna + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False,
                              ad_direction=direction)

    @staticmethod
    def _compute_sequence(start) -> List:
        """Twelve distinct signs from ``start`` in cycle direction.

        Direction follows the Rao 9th-from-lagna rule; kept as a helper
        for tests and callers that need the sign order alone.
        """
        from jhora.types.rasi import Rasi
        start_idx = start.value if isinstance(start, Rasi) else int(start) % 12
        direction = chara_direction(start_idx)
        return [Rasi((start_idx + direction * i) % 12) for i in range(12)]
