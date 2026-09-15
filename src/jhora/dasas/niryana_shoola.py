"""Niryana-Shoola Dasa — Jaimini rasi dasa of the motion of prana.

Classical method (PVR, textbook Example 84): seed at the stronger of
the 2nd and 8th houses from lagna (same BPHS stronger-sign
determination as Brahma), running forward when the seed is odd
(1-based odd sign) and backward otherwise. Sign durations are fixed
by modality: 7 years for movable signs (Aries, Cancer, Libra,
Capricorn), 8 for fixed (Taurus, Leo, Scorpio, Aquarius), 9 for dual
(Gemini, Virgo, Sagittarius, Pisces) — 96 years total on every chart.
Antardasas cycle forward from the MD sign, proportional to each
cycle sign's own year value. Used for ayur timing through the 8th
house (randhra). Sibling of Shoola Dasa (fixed rhythm, different
seed); not to be confused with Shoola's trine-groups.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import normalize_planets, rasi_dasa_tree
from jhora.types.dasa import DasaPeriod
from jhora.types.rasi import Rasi


def _modality_years(sign: int) -> int:
    r = Rasi(sign)
    if r.is_movable:
        return 7
    if r.is_fixed:
        return 8
    return 9


class NiryanaShoolaDasa(DasaBase):
    """Twelve rasi dasas from the stronger of 2nd/8th; 7/8/9 years."""

    system_name = "niryana-shoola"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        second = Rasi((lagna.value + 1) % 12)
        eighth = Rasi((lagna.value + 7) % 12)
        # _stronger_rasi needs planet longitudes; planets may be keyed by
        # Graha, int or name — normalize to {Graha: {"longitude": ...}}.
        planets = normalize_planets(chart.get("planets", {}))
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        start = _stronger_rasi(second, eighth, full).value
        direction = 1 if (start + 1) % 2 == 1 else -1
        durations = [_modality_years(s) for s in range(12)]
        sequence = [((start + direction * i) % 12,
                     durations[(start + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
