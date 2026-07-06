from typing import Dict, List, Optional
from jhora.types.graha import Graha
from jhora.types.nakshatra import Nakshatra
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.dasas.base import DasaBase, DasaOptions


class YoginiDasa(DasaBase):
    system_name = "yogini"

    YOGINIS = [
        (0, "Mangala", 1.0, Graha.KETU),
        (1, "Pingala", 2.0, Graha.VENUS),
        (2, "Dhanya", 3.0, Graha.SUN),
        (3, "Bhramari", 4.0, Graha.MOON),
        (4, "Bhadrika", 5.0, Graha.MARS),
        (5, "Ulka", 6.0, Graha.RAHU),
        (6, "Siddha", 7.0, Graha.JUPITER),
        (7, "Sankata", 8.0, Graha.SATURN),
    ]

    CYCLE_YEARS = [y for _, _, y, _ in YOGINIS]

    _LORD_IDX = {}
    for _i, _name, _yrs, _g in YOGINIS:
        _LORD_IDX[_g] = _i

    def compute(
        self, birth_jd: float, chart: Dict, options: Optional[DasaOptions] = None
    ) -> List[DasaPeriod]:
        opts = options or self.options
        moon_lon = chart["planets"][Graha.MOON]["longitude"]
        nakshatra, pada = Nakshatra.from_longitude(moon_lon)
        nakshatra_start = nakshatra.value * (360.0 / 27.0)
        degrees_progressed = (moon_lon % 360 - nakshatra_start) % (360.0 / 27.0)
        remaining = self.compute_fraction_remaining(degrees_progressed)

        nakshatra_lord = nakshatra.lord
        lord_to_yogini = {
            "Ketu": 0, "Venus": 1, "Sun": 2, "Moon": 3,
            "Mars": 4, "Rahu": 5, "Jupiter": 6, "Saturn": 7,
            "Mercury": 0,
        }
        start_idx = lord_to_yogini.get(nakshatra_lord, 0)

        lords = []
        for i in range(8):
            idx = (start_idx + i) % 8
            yogini_idx, _, yrs, graha = self.YOGINIS[idx]
            if i == 0:
                yrs = yrs * remaining
            lords.append((graha.value, yrs))

        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        return self.build_period_tree(
            lords=lords,
            start_jd=birth_jd,
            cycle_total_years=36.0,
            sub_ratios=self.CYCLE_YEARS,
            y_per_d=y_per_d,
            max_level=opts.subdivision_level,
        )

    def dasa_at_date(
        self, birth_jd: float, chart: Dict, target_jd: float
    ) -> Optional[DasaPeriod]:
        periods = self.compute(birth_jd, chart)
        return self.get_active_period(periods, target_jd)
