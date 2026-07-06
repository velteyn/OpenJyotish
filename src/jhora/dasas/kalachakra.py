from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


_SAVYA_SEQUENCE = [7, 6, 5, 3, 4, 2, 1, 0, 8, 9, 10, 11]
_APASAVYA_SEQUENCE = [0, 1, 2, 4, 3, 5, 6, 7, 8, 9, 10, 11]


class KalachakraDasa(DasaBase):
    system_name = "kalachakra"

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        moon_lon = chart["planets"][Graha.MOON]["longitude"]
        nakshatra, pada = Nakshatra.from_longitude(moon_lon)
        is_savya = nakshatra.value % 2 == 0

        deha_rasi = self._deha_rasi(nakshatra, pada)

        sequence_raw = _SAVYA_SEQUENCE if is_savya else _APASAVYA_SEQUENCE
        seq_start = sequence_raw.index(deha_rasi.value)
        sequence = [Rasi(sequence_raw[(seq_start + i) % 12]) for i in range(12)]

        lord_names: Dict[int, str] = {}
        rasies: List[tuple] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        for pos, rasi in enumerate(sequence):
            lord_idx = 100 + rasi.value
            lord_names[lord_idx] = rasi.full_name
            rasies.append((lord_idx, 1.0))

        return self.build_period_tree(
            lords=rasies,
            start_jd=birth_jd,
            cycle_total_years=12.0,
            sub_ratios=[1.0] * 12,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
            lord_names=lord_names,
        )

    @staticmethod
    def _deha_rasi(nakshatra: Nakshatra, pada: int) -> Rasi:
        nakshatra_lords = [
            Graha.KETU, Graha.VENUS, Graha.SUN, Graha.MOON,
            Graha.MARS, Graha.RAHU, Graha.JUPITER, Graha.SATURN,
            Graha.MERCURY, Graha.KETU, Graha.VENUS, Graha.SUN,
            Graha.MOON, Graha.MARS, Graha.RAHU, Graha.JUPITER,
            Graha.SATURN, Graha.MERCURY, Graha.KETU, Graha.VENUS,
            Graha.SUN, Graha.MOON, Graha.MARS, Graha.RAHU,
            Graha.JUPITER, Graha.SATURN, Graha.MERCURY,
        ]
        nl = nakshatra_lords[nakshatra.value]
        rasi_idx = (nl.value * 4 + pada - 1) % 12
        return Rasi(rasi_idx)

    @staticmethod
    def is_savya(nakshatra: Nakshatra) -> bool:
        return nakshatra.value % 2 == 0
