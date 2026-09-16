"""Kendradi Rasi dasas — quadrants-first cycles (Lagna and AK seeds).

Classical method (PVR textbook ch. 19, JHora-compatible): seed at the
stronger of a reference sign and 7th from it (lagna for Lagna
Kendradi, Atmakaraka sign for AK Kendradi; same BPHS stronger-sign
determination as Brahma). Cycle direction: forward if Saturn occupies
the seed, backward if Ketu does, else forward for odd (1-based odd,
i.e. 0-based even) seeds. MDs run kendra jumps first, then
panapharas, then apoklimas: offsets [0,3,6,9,1,4,7,10,2,5,8,11].
Durations follow the Narayana-style count (same footed-minus-one
Chara rule with the Rao exception, no exaltation adjustment).
Antardasas split each MD equally among 12 signs in the directed
child order (same Saturn/Ketu/parity rule per MD sign).
"""

from typing import Dict, List, Optional

from jhora.calc.karaka import get_atma_karaka
from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.dasas.brahma import _stronger_rasi
from jhora.dasas.jaimini_common import (
    chara_years,
    normalize_planets,
    planet_signs,
)
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi

#: Kendra jumps, then panapharas, then apoklimas (PVR ch. 19).
_KENDRA_OFFSETS = [0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11]


def _cycle_direction(seed: int, planet_sigs: Dict[Graha, int]) -> int:
    """+1 forward / -1 backward for a Kendradi cycle from ``seed``."""
    occupants = [g for g, s in planet_sigs.items() if s == seed]
    if Graha.SATURN in occupants:
        return 1
    if Graha.KETU in occupants:
        return -1
    return 1 if seed % 2 == 0 else -1


def _kendradi_tree(birth_jd: float, start: int, direction: int,
                   planet_sigs: Dict[Graha, int],
                   y_per_d: float, max_level: PeriodLevel) -> List[DasaPeriod]:
    """MDs in kendra jumps; equal directed antardasas per MD."""
    durations = [chara_years(s, planet_sigs) for s in range(12)]
    periods: List[DasaPeriod] = []
    current_jd = birth_jd
    for off in _KENDRA_OFFSETS:
        sign = (start + direction * off) % 12
        years = durations[sign]
        md = DasaPeriod(
            lord_index=100 + sign,
            lord_name=Rasi(sign).full_name,
            start_jd=current_jd,
            end_jd=current_jd + years * y_per_d,
            duration_years=float(years),
            level=PeriodLevel.MAHADASA,
        )
        if max_level.value >= PeriodLevel.ANTARDASA.value:
            ad_dir = _cycle_direction(sign, planet_sigs)
            order_signs = [(sign + ad_dir * k) % 12 for k in range(12)]
            names = {k: Rasi(s).full_name
                     for k, s in enumerate(order_signs)}
            order = [100 + s for s in order_signs]
            md.sub_periods = _subdivide(md, [1.0] * 12, y_per_d, 1,
                                        max_level, names, order)
        periods.append(md)
        current_jd += years * y_per_d
    return periods


class LagnaKendradiDasa(DasaBase):
    """Kendradi cycle seeded at the stronger of lagna/7th."""

    system_name = "lagna-kendradi"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna = Rasi.from_longitude(chart["lagna_lon"])
        planets = normalize_planets(chart.get("planets", {}))
        planet_sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        seventh = Rasi((lagna.value + 6) % 12)
        start = _stronger_rasi(lagna, seventh, full).value
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return _kendradi_tree(birth_jd, start,
                              _cycle_direction(start, planet_sigs),
                              planet_sigs, y_per_d,
                              opts.subdivision_level)


class AKKendradiDasa(DasaBase):
    """Kendradi cycle seeded at the stronger of AK-sign/7th-from-AK.

    EXPERIMENTAL / SUSPENDED (2026-09-15): live JHora extraction
    (Gandhi + 1990 charts) refutes this construction on seed, order
    and cycles. Not wired to any surface. Do not re-enable without
    the dedicated research change resolving the seed rule.
    """

    system_name = "ak-kendradi"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        planet_sigs = planet_signs(planets)
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        ak_sign = planet_sigs[get_atma_karaka(full).graha]
        seventh = (ak_sign + 6) % 12
        start = _stronger_rasi(Rasi(ak_sign), Rasi(seventh), full).value
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return _kendradi_tree(birth_jd, start,
                              _cycle_direction(start, planet_sigs),
                              planet_sigs, y_per_d,
                              opts.subdivision_level)
