"""Varnada Dasa — Jaimini rasi dasa from the Varnada Lagna.

Classical method (standard SJC reading, Sanjay Rath / K.N. Rao):
the Varnada sign comes from Lagna + Hora Lagna — odd lagna
(0-based even index) → VL = (lagN + hlN − 2) mod 12 + 1, even lagna
→ VL = (lagN − hlN + 12) mod 12 + 1, with 1-based sign numbers and
the Sun's sign as Hora Lagna fallback. The 12 rasi Mahadashas run
from Varnada Lagna — forward for odd Varnada, backward for even —
with Chara lord-distance durations (odd signs forward, even signs
backward, own sign 12, full circle 11). Antardasas cycle forward
from the MD sign, proportional to each cycle sign's own year value.

Dual-lord note: Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu)
follow the mainstream Rao exception — a planet sitting in its own
dual-ruled sign alone loses to its co-lord (e.g. Mars in Scorpio
with Ketu elsewhere → count to Ketu). Otherwise the shared
``stronger_lord`` resolution applies. This matches the fixture
(Scorpio → 5 years via Ketu in Cancer) and is documented here so
readers can compare with the simplified rule.
"""

from typing import Dict, List, Optional

from jhora.dasas.base import DasaBase, DasaOptions
from jhora.dasas.jaimini_common import (
    normalize_planets,
    planet_signs,
    rasi_dasa_tree,
    stronger_lord,
)
from jhora.types.dasa import DasaPeriod
from jhora.types.graha import Graha


def _varnada_sign(lagna_lon: float, hora_lagna_lon: Optional[float],
                  sun_lon: float) -> int:
    """0-based Varnada-Lagna sign from Lagna + Hora Lagna longitudes.

    ``hora_lagna_lon`` may be None — callers then pass the Sun's
    longitude as ``sun_lon`` and the Sun's sign is used (documented
    fallback, identical to ``varnada_lagna``'s own fallback).
    """
    lagna = int(lagna_lon // 30) % 12
    hl = int(hora_lagna_lon // 30) % 12 if hora_lagna_lon is not None \
        else int(sun_lon // 30) % 12
    lag_n, hl_n = lagna + 1, hl + 1
    if lagna % 2 == 0:  # odd lagna: add
        return (lag_n + hl_n - 2) % 12
    return (lag_n - hl_n + 12) % 12


def _dual_lord(sign: int, planet_sigs: Dict[Graha, int]) -> Graha:
    """Scorpio/Aquarius lord with the Rao own-sign exception."""
    if sign == 7:  # Scorpio: Mars / Ketu
        mars_si = planet_sigs.get(Graha.MARS)
        ketu_si = planet_sigs.get(Graha.KETU)
        if mars_si == 7 and ketu_si != 7:
            return Graha.KETU
        if ketu_si == 7 and mars_si != 7:
            return Graha.MARS
    elif sign == 10:  # Aquarius: Saturn / Rahu
        sat_si = planet_sigs.get(Graha.SATURN)
        rahu_si = planet_sigs.get(Graha.RAHU)
        if sat_si == 10 and rahu_si != 10:
            return Graha.RAHU
        if rahu_si == 10 and sat_si != 10:
            return Graha.SATURN
    return stronger_lord(sign, planet_sigs)


def _varnada_years(sign: int, planet_sigs: Dict[Graha, int]) -> int:
    """Chara duration for one sign with the Rao dual-lord exception."""
    lord = _dual_lord(sign, planet_sigs)
    lord_si = planet_sigs.get(lord, sign)
    if lord_si == sign:
        return 12
    direction = 1 if sign % 2 == 0 else -1  # odd-footed forward
    count, s = 1, sign
    while s != lord_si:
        s = (s + direction) % 12
        count += 1
        if count > 12:
            break
    if count == 12:
        count = 11  # full-circle traverses 11 years, not 12
    return max(1, min(12, count))


class VarnadaDasa(DasaBase):
    """Twelve rasi dasas from Varnada Lagna in VL-parity direction."""

    system_name = "varnada"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        planets = normalize_planets(chart.get("planets", {}))
        sigs = planet_signs(planets)
        sun_lon = planets.get(Graha.SUN, 0.0)
        vl = _varnada_sign(chart["lagna_lon"], chart.get("hora_lagna_lon"),
                           sun_lon)
        durations = [_varnada_years(s, sigs) for s in range(12)]
        direction = 1 if vl % 2 == 0 else -1
        sequence = [((vl + direction * i) % 12,
                     durations[(vl + direction * i) % 12])
                    for i in range(12)]
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0
        return rasi_dasa_tree(birth_jd, sequence, durations, y_per_d,
                              opts.subdivision_level, parity_ads=False)
