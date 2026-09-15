"""Karaka Dasa — Jaimini rasi dasa seeded by a chara karaka.

Classical method (Jaimini Sutras, Upadesa Khanda; standard SJC reading):
the Mahadashas run the 12 rasis in zodiacal order STARTING from the
sign occupied by the chosen karaka planet — Dara (spouse) for marriage
timing, Putra for children, Matri for mother, Bhratri for siblings.
Each sign's duration follows the Chara rule (lord distance, odd signs
forward, even signs backward, own sign 12, full circle 11, dual
Scorpio/Aquarius lords under the Rao own-sign exception);
antardasas cycle the 12 signs from the MD sign in parity direction
(odd MD forward, even MD backward), proportional to each sign's own
duration.
"""

from typing import Dict, List, Optional

from jhora.calc.karaka import compute_chara_karakas, karaka_dict
from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    chara_cycle_years,
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.graha import Graha

ROLE_TO_SHORT = {
    "putra": "PutK", "matri": "MK", "matru": "MK",
    "bhratri": "BK", "bhratru": "BK", "dara": "DK",
}


class KarakaDasa(DasaBase):
    """Rasi dasa sequence starting from a chara karaka's sign."""

    system_name = "karaka"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        role = str(getattr(opts, "karaka_role", "Dara")).strip().lower()
        if role not in ROLE_TO_SHORT:
            raise ValueError(
                f"Unknown karaka role {role!r}; choose from "
                "Putra, Matri, Bhratri, Dara")
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        karakas = karaka_dict(compute_chara_karakas(full))
        holder = karakas[ROLE_TO_SHORT[role]].graha
        start = sigs[holder]
        durations = chara_cycle_years(sigs)
        sequence = [((start + i) % 12, durations[(start + i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=True)
