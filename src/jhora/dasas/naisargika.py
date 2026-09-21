"""Naisargika Dasa — the natural fixed-age graha dasa (120 years).

Canonical mainstream form: Varahamihira (Brihat Jataka) via Kalyanavarma
and Vaidyanatha — Moon 1, Mars 2, Mercury 9, Venus 20, Jupiter 18,
Sun 20, Saturn 50, in that fixed order from birth (age 0). No balance,
no start computation: every native runs Moon 0–1, Mars 1–3, Mercury
3–12, Venus 12–32, Jupiter 32–50, Sun 50–70, Saturn 70–120.

Deliberately the seven-planet mainstream: Yavanacarya's eighth
Lagna period is objected to in the texts themselves and excluded.
Antardasas subdivide each MD proportionally to the planets' own
MD-year values starting from the MD lord — documented convention
(Brihat Jataka gives MDs only).
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha

_ORDER = [Graha.MOON, Graha.MARS, Graha.MERCURY, Graha.VENUS,
          Graha.JUPITER, Graha.SUN, Graha.SATURN]
_YEARS = [1.0, 2.0, 9.0, 20.0, 18.0, 20.0, 50.0]


class NaisargikaDasa(DasaBase):
    """Fixed natural-age Mahadashas for all creatures."""

    system_name = "naisargika"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = (opts.subdivision_level if opts.include_subperiods
                     else PeriodLevel.MAHADASA)
        periods = []
        cursor = birth_jd
        for graha, yrs in zip(_ORDER, _YEARS):
            dur_days = yrs * y_per_d
            md = DasaPeriod(
                lord_index=graha.value,
                lord_name=graha.full_name,
                start_jd=cursor,
                end_jd=cursor + dur_days,
                duration_years=yrs,
                level=PeriodLevel.MAHADASA,
            )
            if max_level.value >= PeriodLevel.ANTARDASA.value:
                idx = _ORDER.index(graha)
                rot = [_ORDER[(idx + k) % len(_ORDER)] for k in range(7)]
                ratios = [float(_YEARS[_ORDER.index(g)]) for g in rot]
                names = {k: g.full_name for k, g in enumerate(rot)}
                md.sub_periods = _subdivide(
                    md, ratios, y_per_d, 1, max_level, names,
                    [g.value for g in rot])
            periods.append(md)
            cursor += dur_days
        return periods
