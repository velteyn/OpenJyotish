from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


_LORD_NAME_TO_GRAHA = {
    "Sun": Graha.SUN, "Moon": Graha.MOON, "Mars": Graha.MARS,
    "Mercury": Graha.MERCURY, "Jupiter": Graha.JUPITER,
    "Venus": Graha.VENUS, "Saturn": Graha.SATURN,
}

_DEFAULT_RASI_YEARS = [7, 10, 6, 10, 7, 17, 20, 7, 16, 19, 19, 16]

SUBDIVISION_RATIOS = [
    _DEFAULT_RASI_YEARS[i]
    for i in range(12)
]


def _rasi_vimsottari_years(rasi: Rasi) -> float:
    lord_name = rasi.lord
    g = _LORD_NAME_TO_GRAHA.get(lord_name)
    if g is not None:
        return g.vimsottari_years
    return _DEFAULT_RASI_YEARS[rasi]


class Sudasa(DasaBase):
    system_name = "sudasa"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        moon_lon = chart["planets"][Graha.MOON]["longitude"]

        sree_lagna_lon = self._compute_sree_lagna(lagna_lon, moon_lon)
        sree_rasi = Rasi.from_longitude(sree_lagna_lon)

        lord_names: Dict[int, str] = {}
        rasies: List[tuple] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        start_rasi = sree_rasi
        direction = 1

        current_lon = float(start_rasi) * 30.0
        for i in range(12):
            rasi_idx = (int(current_lon // 30)) % 12
            r = Rasi(rasi_idx)
            yrs = _rasi_vimsottari_years(r)
            lord_idx = 100 + rasi_idx
            lord_names[lord_idx] = r.full_name
            rasies.append((lord_idx, yrs))

            current_lon = (current_lon + 30.0) % 360.0

        sub_lord_names = {i: Rasi(i).full_name for i in range(12)}
        return self.build_period_tree(
            lords=rasies,
            start_jd=birth_jd,
            cycle_total_years=120.0,
            sub_ratios=SUBDIVISION_RATIOS,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            lord_names=lord_names,
            sub_lord_names=sub_lord_names,
        )

    @staticmethod
    def _compute_sree_lagna(lagna_lon: float, moon_lon: float) -> float:
        sl_lon = lagna_lon + moon_lon
        if sl_lon < 0:
            sl_lon += 360.0
        return sl_lon % 360.0
