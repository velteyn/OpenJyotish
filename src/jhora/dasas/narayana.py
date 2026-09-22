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

        seed_rasi = self._seed_rasi(lagna_rasi, planets, chart, opts)

        lord_names: Dict[int, str] = {}
        rasies: List[tuple] = []
        y_per_d = 365.2425 if opts.year_definition == "solar" else 360.0

        sequence = self._compute_sequence(seed_rasi)

        # Variant: Sama uses equal 10-year periods; Paka doubles the seed
        # lord's period; Ayur orders by the lord's ayur (longevity) years.
        variant = opts.narayana_variant
        for rasi in sequence:
            if variant == "sama":
                yrs = 10.0
            elif variant == "paka" and rasi == seed_rasi:
                yrs = _rasi_vimsottari_years(rasi) * 2.0
            else:
                yrs = _rasi_vimsottari_years(rasi)
            lord_idx = 100 + rasi.value
            lord_names[lord_idx] = rasi.full_name
            rasies.append((lord_idx, yrs))

        if variant == "sama":
            sub_ratios = [10.0 for _ in range(12)]
        elif variant == "paka":
            sub_ratios = [
                2.0 * _rasi_vimsottari_years(Rasi(i)) if Rasi(i) == seed_rasi
                else _rasi_vimsottari_years(Rasi(i))
                for i in range(12)
            ]
        else:
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

    def _seed_rasi(self, lagna_rasi: Rasi, planets: Dict, chart: Dict,
                   opts: DasaOptions) -> Rasi:
        """Seed sign of the dasa (Narayana family: overridden per variant).

        Base Narayana seeds from the sign occupied by the lagna lord (the
        Paka rasi). When ``narayana_chart`` is set the lord's position is
        taken from that divisional chart instead of D-1.
        """
        lagna_lord = _LORD_NAME_TO_GRAHA.get(lagna_rasi.lord, Graha.SUN)
        seed_chart = (chart.get("seed_varga_positions")
                      if opts.narayana_chart else None)
        if seed_chart:
            lord_lon = seed_chart.get(lagna_lord)
            if lord_lon is None:
                lord_lon = planets[lagna_lord]["longitude"]
        else:
            lord_lon = planets[lagna_lord]["longitude"]
        return self._find_seed(lagna_lord, lord_lon)

    @staticmethod
    def _find_seed(lagna_lord: Graha, lord_lon: float) -> Rasi:
        lord_rasi = Rasi.from_longitude(lord_lon)
        return NarayanaDasa._stronger_rasi(lord_rasi, Rasi((lord_rasi.value + 6) % 12))

    @staticmethod
    def _stronger_rasi(r1: Rasi, r2: Rasi) -> Rasi:
        return r1

    @staticmethod
    def _compute_sequence(start: Rasi) -> List[Rasi]:
        """The twelve dasa signs: a single-direction run from ``start``.

        Direction is fixed by the foot of the **9th sign from the seed**
        (Sanjay Rath, *Narayana Dasa*): odd (vishama-pada) ninth → zodiacal
        (forward), even → anti-zodiacal (backward). The walk then visits all
        twelve signs one step at a time.
        """
        ninth = (start.value + 8) % 12
        direction = 1 if ninth % 2 == 0 else -1
        return [Rasi((start.value + k * direction) % 12) for k in range(12)]
