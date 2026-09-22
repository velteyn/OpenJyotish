"""Rasi-Bhukta Vimsottari dasa.

A variation of Vimsottari where the **antardasas are the twelve rasis**
(equal parts), instead of the Vimsottari sub-lords. The mahadasas are the
standard Vimsottari nine planets from the Moon's nakshatra balance; within
each mahadasa the twelve rasis run zodiacally from the **mahadasa lord's
sign**.

Decoded from the reference builder and validated structurally (see
``tools/emu`` and ``REFERENCE.md``). Pratyantardasas belong to eight planets
in kakshya order — not implemented here (MD/AD only).
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaOptions
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


class RasiBhuktaVimsottariDasa(VimsottariDasa):
    """Vimsottari mahadasas with the twelve rasis as antardasas."""

    system_name = "rasi-bhukta-vimsottari"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        mds = super().compute(birth_jd, chart, opts)
        signs = {g: int(p["longitude"] // 30) % 12
                 for g, p in chart["planets"].items()}
        for md in mds:
            lord_sign = signs[Graha(md.lord_index)]
            span = md.end_jd - md.start_jd
            step = span / 12.0
            subs: List[DasaPeriod] = []
            cursor = md.start_jd
            for k in range(12):
                sign = (lord_sign + k) % 12
                end = cursor + step
                subs.append(DasaPeriod(
                    lord_index=100 + sign,
                    lord_name=Rasi(sign).full_name,
                    start_jd=cursor,
                    end_jd=end,
                    duration_years=(end - cursor) / 365.2425,
                    level=PeriodLevel.ANTARDASA,
                ))
                cursor = end
            md.sub_periods = subs
        return mds
