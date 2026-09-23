"""Kalachakra dasa — Raghavaacharya method (nine mahadasas)."""

from typing import Dict, List, Optional, Tuple

from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.rasi import Rasi
from jhora.dasas.base import DasaBase, DasaOptions

#: Sign durations in years (Ar..Pi).
_SIGN_YEARS = [7, 16, 9, 21, 5, 9, 16, 7, 10, 4, 4, 10]

#: Nakshatra index -> group name (PVR Table 44-47; Savya-2 holds six:
#: Bharani, Pushyami, Chitra, Poorvashadha, Uttarabhaadrapada, Revati).
_GROUPS: Dict[int, str] = {}
for _i in (0, 2, 6, 8, 12, 14, 18, 20, 24):
    _GROUPS[_i] = "savya1"
for _i in (1, 7, 13, 19, 25, 26):
    _GROUPS[_i] = "savya2"
for _i in (3, 9, 15, 21):
    _GROUPS[_i] = "apasavya1"
for _i in (4, 5, 10, 11, 16, 17, 22, 23):
    _GROUPS[_i] = "apasavya2"

#: group -> 4 pada sequences (sign indices) and paramayush.
_SEQUENCES: Dict[str, List[Tuple[List[int], int]]] = {
    "savya1": [
        ([0, 1, 2, 3, 4, 5, 6, 7, 8], 100),
        ([9, 10, 11, 7, 6, 5, 3, 4, 2], 85),
        ([1, 0, 11, 10, 9, 8, 0, 1, 2], 83),
        ([3, 4, 5, 6, 7, 8, 9, 10, 11], 86),
    ],
    "savya2": [
        ([7, 6, 5, 3, 4, 2, 1, 0, 11], 100),
        ([10, 9, 8, 0, 1, 2, 3, 4, 5], 85),
        ([6, 7, 8, 9, 10, 11, 7, 6, 5], 83),
        ([3, 4, 2, 1, 0, 11, 10, 9, 8], 86),
    ],
    "apasavya1": [
        ([8, 9, 10, 11, 0, 1, 2, 4, 3], 86),
        ([5, 6, 7, 11, 10, 9, 8, 7, 6], 83),
        ([5, 4, 3, 2, 1, 0, 8, 9, 10], 85),
        ([11, 0, 1, 2, 4, 3, 5, 6, 7], 100),
    ],
    "apasavya2": [
        ([11, 10, 9, 8, 7, 6, 5, 4, 3], 86),
        ([2, 1, 0, 8, 9, 10, 11, 0, 1], 83),
        ([2, 4, 3, 5, 6, 7, 11, 10, 9], 85),
        ([8, 7, 6, 5, 4, 3, 2, 1, 0], 100),
    ],
}

#: Antardasa pattern per mahadasa sign, by chakra (0=Ar .. 11=Pi). Within a
#: mahadasa the nine antardasas are these signs; durations are their sign-years
#: scaled to the mahadasa length. (P.V.R. Rao, Kalachakra Dasa Tutorial.)
_AD_PATTERNS: Dict[str, Dict[int, List[int]]] = {
    "savya": {
        0: [0, 1, 2, 3, 4, 5, 6, 7, 8],
        1: [9, 10, 11, 7, 6, 5, 3, 4, 2],
        2: [1, 0, 11, 10, 9, 8, 0, 1, 2],
        3: [3, 4, 5, 6, 7, 8, 9, 10, 11],
        4: [7, 6, 5, 3, 4, 2, 1, 0, 11],
        5: [10, 9, 8, 0, 1, 2, 3, 4, 5],
        6: [6, 7, 8, 9, 10, 11, 7, 6, 5],
        7: [3, 4, 2, 1, 0, 11, 10, 9, 8],
        8: [0, 1, 2, 3, 4, 5, 6, 7, 8],
        9: [9, 10, 11, 7, 6, 5, 3, 4, 2],
        10: [1, 0, 11, 10, 9, 8, 0, 1, 2],
        11: [3, 4, 5, 6, 7, 8, 9, 10, 11],
    },
    "apasavya": {
        0: [8, 7, 6, 5, 4, 3, 2, 1, 0],
        1: [2, 4, 3, 5, 6, 7, 11, 10, 9],
        2: [2, 1, 0, 8, 9, 10, 11, 0, 1],
        3: [11, 10, 9, 8, 7, 6, 5, 4, 3],
        4: [11, 0, 1, 2, 4, 3, 5, 6, 7],
        5: [5, 4, 3, 2, 1, 0, 8, 9, 10],
        6: [5, 6, 7, 11, 10, 9, 8, 7, 6],
        7: [8, 9, 10, 11, 0, 1, 2, 4, 3],
        8: [8, 7, 6, 5, 4, 3, 2, 1, 0],
        9: [2, 4, 3, 5, 6, 7, 11, 10, 9],
        10: [2, 1, 0, 8, 9, 10, 11, 0, 1],
        11: [11, 10, 9, 8, 7, 6, 5, 4, 3],
    },
}


def _is_savya(nak_index: int) -> bool:
    return _GROUPS[nak_index].startswith("savya")


def _pada(lon: float) -> Tuple[int, int, float]:
    """(nakshatra index, pada 0..3, fraction of the pada traversed)."""
    nak = int(lon / (360.0 / 27.0)) % 27
    within = lon % (360.0 / 27.0)
    pada = int(within / (360.0 / 108.0))
    frac = (within % (360.0 / 108.0)) / (360.0 / 108.0)
    return nak, pada, frac


class KalachakraDasa(DasaBase):
    """Nine-sign Kalachakra dasa (Raghavaacharya method)."""

    system_name = "kalachakra"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        moon_lon = chart["planets"][Graha.MOON]["longitude"]
        nak, pada, frac = _pada(moon_lon)
        group = _GROUPS[nak]
        sequence, paramayush = _SEQUENCES[group][pada]

        # Position of birth within the cycle: the pada fraction traversed
        # maps linearly onto the cycle's paramayush.
        birth_point = frac * paramayush

        # Build the timeline: nine signs (looped past the paramayush).
        signs: List[Tuple[int, float]] = []      # (sign, full years)
        total = 0.0
        idx = 0
        while total < birth_point + 120.0:
            sign = sequence[idx % 9]
            yrs = float(_SIGN_YEARS[sign])
            signs.append((sign, yrs))
            total += yrs
            idx += 1

        # Find the running sign and its balance.
        acc = 0.0
        start_i = 0
        for i, (sign, yrs) in enumerate(signs):
            if acc + yrs > birth_point:
                start_i = i
                break
            acc += yrs

        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = opts.subdivision_level
        chakra = "savya" if _is_savya(nak) else "apasavya"

        periods: List[DasaPeriod] = []
        cursor = birth_jd
        for i in range(start_i, len(signs)):
            sign, yrs = signs[i]
            first = (i == start_i)
            dur = (acc + yrs - birth_point) if first else yrs
            if first:
                acc += yrs
            end = cursor + dur * y_per_d
            md = DasaPeriod(
                lord_index=100 + sign, lord_name=Rasi(sign).full_name,
                start_jd=cursor, end_jd=end, duration_years=dur,
                level=PeriodLevel.MAHADASA,
            )
            if max_level.value >= PeriodLevel.ANTARDASA.value:
                md.sub_periods = self._split(md, sign, chakra,
                                             PeriodLevel.ANTARDASA, max_level, y_per_d)
            periods.append(md)
            cursor = end
        return periods

    def _split(self, parent: DasaPeriod, sign: int, chakra: str,
               level: PeriodLevel, max_level: PeriodLevel,
               y_per_d: float) -> List[DasaPeriod]:
        seq = _AD_PATTERNS[chakra][sign]
        span = parent.end_jd - parent.start_jd
        total_years = sum(_SIGN_YEARS[s] for s in seq)
        out: List[DasaPeriod] = []
        cursor = parent.start_jd
        for s in seq:
            end = cursor + span * (_SIGN_YEARS[s] / total_years)
            sub = DasaPeriod(
                lord_index=100 + s, lord_name=Rasi(s).full_name,
                start_jd=cursor, end_jd=end,
                duration_years=(end - cursor) / y_per_d,
                level=level,
            )
            if level.value < max_level.value:
                sub.sub_periods = self._split(
                    sub, s, chakra, PeriodLevel(level.value + 1),
                    max_level, y_per_d)
            out.append(sub)
            cursor = end
        return out
