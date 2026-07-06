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


def _rasi_vimsottari_years(rasi: Rasi) -> float:
    lord_name = rasi.lord
    g = _LORD_NAME_TO_GRAHA.get(lord_name)
    if g is not None:
        return g.vimsottari_years
    return _DEFAULT_RASI_YEARS[rasi]


class NarayanaDasa(DasaBase):
    system_name = "narayana"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        planets = chart["planets"]
        lagna_rasi = Rasi.from_longitude(lagna_lon)
        lagna_lord_name = lagna_rasi.lord
        lagna_lord = _LORD_NAME_TO_GRAHA.get(lagna_lord_name, Graha.SUN)

        lagna_lord_lon = planets[lagna_lord]["longitude"]
        seed_rasi = self._find_seed(lagna_lord, lagna_lord_lon)

        lord_names: Dict[int, str] = {}
        rasies: List[tuple] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sequence = self._compute_sequence(seed_rasi)

        for rasi in sequence:
            yrs = _rasi_vimsottari_years(rasi)
            lord_idx = 100 + rasi.value
            lord_names[lord_idx] = rasi.full_name
            rasies.append((lord_idx, yrs))

        sub_ratios = [_rasi_vimsottari_years(Rasi(i)) for i in range(12)]

        sub_lord_names = {i: Rasi(i).full_name for i in range(12)}
        return self.build_period_tree(
            lords=rasies,
            start_jd=birth_jd,
            cycle_total_years=120.0,
            sub_ratios=sub_ratios,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            lord_names=lord_names,
            sub_lord_names=sub_lord_names,
        )

    @staticmethod
    def _find_seed(lagna_lord: Graha, lord_lon: float) -> Rasi:
        lord_rasi = Rasi.from_longitude(lord_lon)
        return NarayanaDasa._stronger_rasi(lord_rasi, Rasi((lord_rasi.value + 6) % 12))

    @staticmethod
    def _stronger_rasi(r1: Rasi, r2: Rasi) -> Rasi:
        return r1

    @staticmethod
    def _compute_sequence(start: Rasi) -> List[Rasi]:
        result = []
        current = start
        direction = 1 if start.is_movable else -1 if start.is_fixed else 1

        for i in range(12):
            result.append(current)
            if current.is_movable:
                direction = 1
            elif current.is_fixed:
                direction = -1
            if direction == 1:
                current = Rasi((current.value + 1) % 12)
            else:
                current = Rasi((current.value - 1) % 12)

        return result
