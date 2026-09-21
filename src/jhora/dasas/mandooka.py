"""Mandooka Dasa — Jaimini frog-leap rasi dasa, K.N. Rao form.

Canonical mainstream form (spec gate 1.2: K.N. Rao vs Rath). The K.N. Rao
form is the one carried by the mainstream published tables; its
1990-fixture MD order/durations are reproduced exactly:

- seed: lagna when lagna is an odd-numbered sign, else 7th from lagna;
  direct (+1) from odd seed, reverse (−1) from even seed;
- three groups of four: group starts are seed, seed±1, seed±2 and each
  group is a ±3 frog-leap walk through one modality (same direction);
- durations: sign-to-lord count by SIGN-NUMBER parity (odd signs
  forward, even signs backward — Prakriti-chakra convention, *not*
  Jaimini footedness), inclusive with no −1 deduction; lord in own
  sign 12, lord in 12th 12, lord in 7th 10; Scorpio always counts to
  Mars backward (Ketu ignored);
- antardasas: the 12-sign MD order rotated to start at the MD sign,
  equal MD/12 shares (Savya/Apasavya per the MD direction).

Provenance: K.N. Rao school tables (Jyotisha Bharati notes, all 12
lagnas) plus the independent order table cross-check. The Rath D-11
variant ("Mandooka dasa of D-11") is documented but NOT implemented
(it runs on the Rudramsa varga — follow-up).
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.dasas.jaimini_common import (
    normalize_planets,
    planet_signs,
)
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

_SINGLE_LORDS = {
    0: Graha.MARS, 1: Graha.VENUS, 2: Graha.MERCURY, 3: Graha.MOON,
    4: Graha.SUN, 5: Graha.MERCURY, 6: Graha.VENUS, 7: Graha.MARS,
    8: Graha.JUPITER, 9: Graha.SATURN, 10: Graha.SATURN,
    11: Graha.JUPITER,
}


def _count_years(sign: int, lord_si: int, lagna: int) -> int:
    """Inclusive sign-to-lord count (no −1 deduction).

    Odd-numbered signs (even 0-based indices) count forward, even signs
    backward. Lord in own sign gives 12; lord in 12th *from lagna* gives
    12 (read with rule 6 below: the reference table forces the lagna
    reading — "12th from the dasa rasi" would wrongly give Cp 12
    instead of 2 on the 1990 fixture); lord in 7th from the sign
    gives 10.
    """
    if lord_si == sign:
        return 12
    if lord_si == (lagna + 11) % 12:
        return 12  # lord in 12th from lagna
    if (lord_si - sign) % 12 == 6:
        return 10  # lord in 7th from the sign
    direction = 1 if sign % 2 == 0 else -1
    count, s = 1, sign
    while s != lord_si:
        s = (s + direction) % 12
        count += 1
    return count


def mandooka_order(lagna: int) -> List[int]:
    """Twelve MD signs: three frog-leap groups of four.

    Odd-numbered lagna starts at lagna running direct, even-numbered
    lagna starts at 7th-from-lagna running reverse. Group starts are
    seed, seed±1, seed±2; each group walks ±3 (same direction).
    """
    odd = (lagna % 2 == 0)
    seed = lagna if odd else (lagna + 6) % 12
    direction = 1 if odd else -1
    order = []
    for k in range(3):
        start = (seed + direction * k) % 12
        order.extend((start + direction * 3 * j) % 12 for j in range(4))
    return order


def mandooka_years(sign: int, planet_sigs: Dict[Graha, int],
                   lagna: int) -> int:
    """MD years for one sign (Scorpio always counts to Mars backward)."""
    if sign == 7:  # Scorpio: Ketu ignored, Mars taken, reverse
        lord_si = planet_sigs.get(Graha.MARS, sign)
        if lord_si == sign:
            return 12
        count, s = 1, sign
        while s != lord_si:
            s = (s - 1) % 12
            count += 1
        return count
    lord_si = planet_sigs.get(_SINGLE_LORDS[sign], sign)
    return _count_years(sign, lord_si, lagna)


class MandookaDasa(DasaBase):
    """Twelve frog-leap rasi dasas (K.N. Rao form)."""

    system_name = "mandooka"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = int(chart["lagna_lon"] // 30) % 12
        planet_sigs = planet_signs(normalize_planets(chart.get("planets", {})))
        order = mandooka_order(lagna)
        durations = [mandooka_years(s, planet_sigs, lagna) for s in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        max_level = (opts.subdivision_level if opts.include_subperiods
                     else PeriodLevel.MAHADASA)
        periods = []
        current_jd = birth_jd
        for sign in order:
            yrs = durations[sign]
            dur_days = yrs * y_per_d
            md = DasaPeriod(
                lord_index=100 + sign,
                lord_name=Rasi(sign).full_name,
                start_jd=current_jd,
                end_jd=current_jd + dur_days,
                duration_years=float(yrs),
                level=PeriodLevel.MAHADASA,
            )
            if max_level.value >= PeriodLevel.ANTARDASA.value:
                # Antardasas run the global MD order rotated to the MD
                # sign (KNR "same order" rule), equal MD/12 shares.
                idx = order.index(sign)
                rot = [order[(idx + k) % 12] for k in range(12)]
                ratios = [1.0] * 12
                names = {k: Rasi(s).full_name for k, s in enumerate(rot)}
                md.sub_periods = _subdivide(
                    md, ratios, y_per_d, 1, max_level, names,
                    [100 + s for s in rot])
            periods.append(md)
            current_jd += dur_days
        return periods
