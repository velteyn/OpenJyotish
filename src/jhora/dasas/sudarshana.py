"""Sudarshana Chakra dasa — the annual/monthly/daily progression dasa.

Parasara's Sudarshana Chakra progresses the lagna (and, for the progression
chart, the Moon and the Sun) at the rate of one sign per year: the mahadasas
are the twelve signs from the lagna, one year each on a twelve-year cycle.
Antardasas divide a year into twelve equal parts; by default they run
zodiacally from the sign of the mahadasa sign's lord, or from the mahadasa
sign itself when the option is off. Pratyantardasas divide an antardasa the
same way from its own sign.

The reference's own help calls this "the best tool for predicting annual,
monthly and daily fortune according to Parasara".
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    _single_lord,
    normalize_planets,
    planet_signs,
)
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.rasi import Rasi


def _zodiacal(start: int, n: int = 12) -> List[int]:
    return [(start + k) % 12 for k in range(n)]


class SudarshanaDasa(DasaBase):
    """Twelve sign mahadasas from the lagna, one year each."""

    system_name = "sudarshana"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = int(chart["lagna_lon"] // 30) % 12
        planet_sigs = planet_signs(normalize_planets(chart.get("planets", {})))
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        from_lord = getattr(opts, "sudarshana_ad_from_lord", True)

        periods: List[DasaPeriod] = []
        current = birth_jd
        for k in range(12):
            sign = (lagna + k) % 12
            end = current + y_per_d
            md = DasaPeriod(
                lord_index=100 + sign, lord_name=Rasi(sign).full_name,
                start_jd=current, end_jd=end, duration_years=1.0,
                level=PeriodLevel.MAHADASA,
            )
            start = sign
            if from_lord:
                lord = _single_lord(sign)
                start = planet_sigs.get(lord, sign)
            md.sub_periods = self._split(
                md, _zodiacal(start), PeriodLevel.ANTARDASA)
            periods.append(md)
            current = end
        return periods

    def _split(self, parent: DasaPeriod, sub_signs: List[int],
               level: PeriodLevel) -> List[DasaPeriod]:
        span = parent.end_jd - parent.start_jd
        step = span / len(sub_signs)
        out: List[DasaPeriod] = []
        cursor = parent.start_jd
        for sign in sub_signs:
            end = cursor + step
            out.append(DasaPeriod(
                lord_index=100 + sign, lord_name=Rasi(sign).full_name,
                start_jd=cursor, end_jd=end,
                duration_years=(end - cursor) / 365.2425,
                level=level,
            ))
            cursor = end
        return out
