from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


class CharaDasa(DasaBase):
    system_name = "chara"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        lagna_lon = chart["lagna_lon"]
        start_rasi = Rasi.from_longitude(lagna_lon)

        lord_names: Dict[int, str] = {}
        rasies: List[tuple] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sequence = self._compute_sequence(start_rasi)

        for pos, rasi in enumerate(sequence):
            duration = pos + 1
            lord_idx = 100 + rasi.value
            lord_names[lord_idx] = rasi.full_name
            rasies.append((lord_idx, float(duration)))

        sub_lord_names = {i: Rasi(i).full_name for i in range(12)}
        return self.build_period_tree(
            lords=rasies,
            start_jd=birth_jd,
            cycle_total_years=78.0,
            sub_ratios=[float(i + 1) for i in range(12)],
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            lord_names=lord_names,
            sub_lord_names=sub_lord_names,
        )

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
