"""Trikona Dasa — Jaimini rasi dasa of the purusharthas.

Classical method (PVR school, cross-checked on three charts):
seed at the stronger of the lagna, 5th and 9th houses (same BPHS
stronger-sign determination as Brahma), running forward when the seed
index is even and backward otherwise. Durations follow the Chara
lord-distance rule (inclusive sign-to-lord count minus one, footed
directions, own sign 12, full circle 11, dual Scorpio/Aquarius lords
under the Rao own-sign exception; no exaltation adjustment) —
reproducing the published tables exactly, including the Rao-exception Scorpio.
Antardasas split each MD equally in modality-gated order (d = +1 for
even MD signs, −1 for odd): the cycle starts at the MD itself when
MD is odd and at 7th-from-MD when even; then movable MDs run plain
zodiacal, dual MDs run kendra-group order (groups [S, S+4d, S−4d],
within-step +3d), and fixed MDs run a constant +5d progression —
induced from four complete sample charts (Vi, Ge, Cp, Aq MDs). An
alternative school seeds at the Atmakaraka with fixed 7/8/9 years;
this engine documents that variant without implementing it.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import (
    chara_cycle_years,
    normalize_planets,
    planet_signs,
)
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.rasi import Rasi


def _trikona_ad_order(md: int) -> List[int]:
    """12-sign antardasa order for a Trikona Mahadasha (equal splits).

    Cycle starts at the MD itself when MD is odd, at 7th-from-MD when
    even; then movable MDs run plain zodiacal, dual MDs run
    kendra-group order ([S, S+4d, S−4d], within-step +3d), and fixed
    MDs run a constant +5d progression — with d = +1 for even MD
    signs and −1 for odd.
    """
    r = Rasi(md)
    d = 1 if md % 2 == 0 else -1
    start = md if md % 2 == 1 else (md + 6) % 12
    if r.is_movable:
        return [(start + d * k) % 12 for k in range(12)]
    if r.is_fixed:
        return [(start + 5 * d * k) % 12 for k in range(12)]
    order = []
    for g in (start, (start + 4 * d) % 12, (start - 4 * d) % 12):
        for k in range(4):
            order.append((g + 3 * d * k) % 12)
    return order


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
        periods: List[DasaPeriod] = []
        current_jd = birth_jd
        for sign, years in sequence:
            md = DasaPeriod(
                lord_index=100 + sign,
                lord_name=Rasi(sign).full_name,
                start_jd=current_jd,
                end_jd=current_jd + years * y_per_d,
                duration_years=float(years),
                level=PeriodLevel.MAHADASA,
            )
            if opts.subdivision_level.value >= PeriodLevel.ANTARDASA.value:
                # NOTE: built manually (not via rasi_dasa_tree) because
                # the AD cycle need not start at the MD sign, while
                # _subdivide always rotates sub_order to the parent lord.
                order_signs = _trikona_ad_order(sign)
                ad_days = (md.end_jd - md.start_jd) / 12.0
                names = {k: Rasi(s).full_name
                         for k, s in enumerate(order_signs)}
                order = [100 + s for s in order_signs]
                ads: List[DasaPeriod] = []
                current_ad = md.start_jd
                for k, s in enumerate(order_signs):
                    ad = DasaPeriod(
                        lord_index=100 + s,
                        lord_name=names[k],
                        start_jd=current_ad,
                        end_jd=current_ad + ad_days,
                        duration_years=ad_days / y_per_d,
                        level=PeriodLevel.ANTARDASA,
                    )
                    if opts.subdivision_level.value > \
                            PeriodLevel.ANTARDASA.value:
                        ad.sub_periods = _subdivide(
                            ad, [1.0] * 12, y_per_d, 2,
                            opts.subdivision_level, names, order)
                    ads.append(ad)
                    current_ad += ad_days
                md.sub_periods = ads
            periods.append(md)
            current_jd += years * y_per_d
        return periods
