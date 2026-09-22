"""Drig dasa — the phalita rasi dasa of religious and spiritual activity.

Drig is a rasi dasa built on Jaimini sign-aspects (rasi drishti). Following the
mainstream Parasara reading:

* The cycle starts from the lagna and takes the **9th, 10th and 11th signs**
  from it, in that order.
* For each of those signs the dasa lists the sign itself together with the
  three signs that aspect it — movable signs aspect the fixed signs and vice
  versa (excluding the adjacent sign), dual signs aspect the other dual signs.
* Each sign's mahadasa lasts **7 years (movable), 8 (fixed) or 9 (dual)**,
  giving a 96-year cycle.
* Antardasas divide a mahadasa into twelve equal parts, in a fixed sign cycle
  keyed by the mahadasa sign (the same cycle the classical tradition uses for
  the drig sequence).

The order of the surrounding group and of the antardasa cycle is the one the
mainstream tradition uses; it is deterministic given the lagna.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.rasi import Rasi

_ALL = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()

#: Fixed antardasa sign cycles, one per sign axis (sign % 6). Each entry is a
#: permutation of offsets from the cycle's start sign.
_AD_CYCLES: Dict[int, List[int]] = {
    0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    1: [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5],
    2: [0, 3, 6, 9, 4, 7, 10, 1, 8, 11, 2, 5],
    3: [0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    4: [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7],
    5: [0, 9, 6, 3, 8, 5, 2, 11, 4, 1, 10, 7],
}


def _relates(a: int, b: int) -> bool:
    """Jaimini rasi-drishti aspect predicate between two signs."""
    if a == b:
        return True
    ra, rb = a % 3, b % 3
    if ra == 0 and rb == 1 and (a + 1) % 12 != b and (b + 1) % 12 != a:
        return True
    if ra == 1 and rb == 0 and (a + 1) % 12 != b and (b + 1) % 12 != a:
        return True
    if ra == 2 and rb == 2:
        return True
    return False


def drig_group(sign: int) -> List[int]:
    """The sign and the three signs aspecting it, in the tradition's order."""
    if sign % 3 == 0:
        step = -1
    elif sign % 3 == 1:
        step = 1
    else:
        step = 1 if sign % 2 == 0 else -1
    group = [sign]
    cursor = (sign + step) % 12
    for _ in range(11):
        if _relates(sign, cursor):
            group.append(cursor)
        cursor = (cursor + step) % 12
    return group


def mahadasa_sequence(lagna_sign: int) -> List[int]:
    """The 12 mahadasa signs: 9th/10th/11th from lagna, each expanded."""
    sequence: List[int] = []
    for house_offset in (8, 9, 10):
        sequence.extend(drig_group((lagna_sign + house_offset) % 12))
    return sequence


def modality_years(sign: int) -> int:
    """7 (movable), 8 (fixed) or 9 (dual) years."""
    return (7, 8, 9)[sign % 3]


def antardasa_sequence(md_sign: int) -> List[int]:
    """The twelve antardasa signs of a mahadasa in ``md_sign``."""
    offsets = _AD_CYCLES[md_sign % 6]
    return [(md_sign + 6 + off) % 12 for off in offsets]


class DrigDasa(DasaBase):
    """Drig rasi dasa: 9th/10th/11th from lagna, Jaimini aspects, 7/8/9 years."""

    system_name = "drig"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_sign = int(chart["lagna_lon"] // 30) % 12
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        current = birth_jd
        periods: List[DasaPeriod] = []
        for sign in mahadasa_sequence(lagna_sign):
            years = modality_years(sign)
            end = current + years * y_per_d
            md = DasaPeriod(
                lord_index=100 + sign,
                lord_name=Rasi(sign).full_name,
                start_jd=current,
                end_jd=end,
                duration_years=float(years),
                level=PeriodLevel.MAHADASA,
            )
            if opts.subdivision_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = self._subdivide(
                    md, antardasa_sequence(sign),
                    PeriodLevel.ANTARDASA, opts.subdivision_level)
            periods.append(md)
            current = end
        return periods

    def _subdivide(self, parent: DasaPeriod, sub_signs: List[int],
                   level: PeriodLevel, max_level: PeriodLevel
                   ) -> List[DasaPeriod]:
        """Equal sub-periods over ``sub_signs``, recursing to ``max_level``."""
        span = parent.end_jd - parent.start_jd
        step = span / len(sub_signs)
        out: List[DasaPeriod] = []
        cursor = parent.start_jd
        for sign in sub_signs:
            end = cursor + step
            period = DasaPeriod(
                lord_index=100 + sign,
                lord_name=Rasi(sign).full_name,
                start_jd=cursor,
                end_jd=end,
                duration_years=float((end - cursor) / 365.2425),
                level=level,
            )
            if level.value < max_level.value:
                period.sub_periods = self._subdivide(
                    period, antardasa_sequence(sign),
                    PeriodLevel(level.value + 1), max_level)
            out.append(period)
            cursor = end
        return out
